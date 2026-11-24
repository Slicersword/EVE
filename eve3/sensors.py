"""M04 - sensors. 3x GY-530 VL53L0X (XSHUT BCM5/6/13 -> 0x30/0x31/0x32), MPU-6050 (0x68), and the three
KY-033 cliff sensors + PIR that arrive through Mega telemetry.

Order of the ToF tuple: (front-left, front-right, rear). Order of cliff: (front-left, rear-centre, front-right).
A reading that is missing, stale or out of range is None / unsafe - nothing is ever invented.
Hardware libraries are imported only inside start() so everything else runs on a PC.
"""
from __future__ import annotations
import math, threading, time
from dataclasses import dataclass, replace, asdict


@dataclass(frozen=True)
class Frame:
    tof_mm: tuple = (None, None, None)
    tof_at: float = 0.0
    tilt_deg: float | None = None
    imu_at: float = 0.0
    cliff: tuple = (True, True, True)      # True = unsafe; the default fails closed
    cliff_raw: tuple = (None, None, None)
    cliff_at: float = 0.0
    pir: bool = False

    def dict(self):
        return asdict(self)


def valid_tof_mm(v, lo=30, hi=1000) -> bool:
    return type(v) in (int, float) and math.isfinite(v) and lo <= v <= hi


def decode_cliff(raw, edge_level, calibrated: bool) -> tuple:
    """Digital KY-033. A channel is unsafe when it reads its calibrated edge level, or anything unexpected."""
    if not calibrated or len(raw) != 3:
        return (True, True, True)
    return tuple(r not in (0, 1) or r == e for r, e in zip(raw, edge_level))


def calibrate_cliff(floor_rows, edge_rows) -> dict:
    """Needs >= 10 steady readings on the floor and >= 10 over an edge; every channel must flip."""
    for rows in (floor_rows, edge_rows):
        if len(rows) < 10 or any(len(r) != 3 or any(v not in (0, 1) for v in r) for r in rows):
            raise ValueError("need at least 10 rows of three 0/1 values for both floor and edge")
    levels = []
    for i, name in enumerate(("front-left", "rear-centre", "front-right")):
        floor, edge = {r[i] for r in floor_rows}, {r[i] for r in edge_rows}
        if len(floor) != 1 or len(edge) != 1 or floor == edge:
            raise ValueError(f"{name} cliff sensor: reading flickers or does not change between floor and edge "
                             "(turn the blue trimmer on that KY-033 and repeat)")
        levels.append(next(iter(edge)))
    return {"calibrated": True, "edge_level": levels}


class ToFArray:
    def __init__(self, xshut=(5, 6, 13), addresses=(0x30, 0x31, 0x32)):
        self.xshut, self.addresses = tuple(xshut), tuple(addresses)
        self.sensors, self._lines, self.i2c = [], [], None

    def start(self):
        import board, busio, digitalio, adafruit_vl53l0x
        self.close()
        self.i2c = busio.I2C(board.SCL, board.SDA)
        for pin in self.xshut:
            line = digitalio.DigitalInOut(getattr(board, f"D{pin}"))
            line.switch_to_output(value=False)           # hold LOW = sensor off
            self._lines.append(line)
        time.sleep(0.02)
        for line, address in zip(self._lines, self.addresses):
            line.switch_to_input()                        # release; the board's own pull-up wakes it (never drive HIGH)
            time.sleep(0.02)
            sensor = adafruit_vl53l0x.VL53L0X(self.i2c, io_timeout_s=0.10)   # answers at the default 0x29
            sensor.set_address(address)
            self.sensors.append(sensor)

    def sample(self) -> tuple:
        if len(self.sensors) != 3:
            raise RuntimeError("ToF sensors not started")
        out = []
        for sensor in self.sensors:
            value = float(sensor.range)
            out.append(value if valid_tof_mm(value) else None)
        return tuple(out)

    def close(self):
        for line in self._lines:
            try:
                line.switch_to_output(value=False)
                line.deinit()
            except Exception:
                pass
        if self.i2c is not None:
            try:
                self.i2c.deinit()
            except Exception:
                pass
        self._lines, self.sensors, self.i2c = [], [], None


def _s16(v):
    return v - 65536 if v & 0x8000 else v


class MPU6050:
    def __init__(self, bus_factory=None, address=0x68, inverted=False):
        self._bus_factory, self.address, self.bus = bus_factory, address, None
        self.inverted = inverted                      # True if the board is mounted upside down

    def start(self):
        if self._bus_factory is None:
            import smbus2
            self._bus_factory = lambda: smbus2.SMBus(1)
        self.close()
        self.bus = self._bus_factory()
        if self.bus.read_byte_data(self.address, 0x75) not in (0x68, 0x69, 0x70, 0x72):
            raise RuntimeError("MPU6050 WHO_AM_I mismatch")
        self.bus.write_byte_data(self.address, 0x6B, 0x00)     # wake
        self.bus.write_byte_data(self.address, 0x1C, 0x00)     # +-2 g
        time.sleep(0.05)

    def sample(self) -> float:
        b = self.bus.read_i2c_block_data(self.address, 0x3B, 6)
        if len(b) != 6:
            raise RuntimeError("short MPU6050 read")
        ax, ay, az = (_s16((b[i] << 8) | b[i + 1]) / 16384.0 for i in (0, 2, 4))
        norm = math.sqrt(ax * ax + ay * ay + az * az)
        if not 0.5 <= norm <= 1.5:
            raise ValueError("acceleration is not close to 1 g (moving, or bad read)")
        return math.degrees(math.atan2(math.hypot(ax, ay), -az if self.inverted else az))

    def close(self):
        if self.bus is not None:
            try:
                self.bus.close()
            except Exception:
                pass
        self.bus = None


class SensorHub:
    """Holds the latest frame. Writers: the sensor thread (ToF, IMU) and the Mega reader (cliff, PIR)."""

    def __init__(self, cliff_calibration: dict | None = None):
        cal = cliff_calibration or {}
        self.edge_level = tuple(cal.get("edge_level", (0, 0, 0)))
        self.calibrated = cal.get("calibrated") is True
        self._frame = Frame()
        self._lock = threading.Lock()

    def _set(self, **changes):
        with self._lock:
            self._frame = replace(self._frame, **changes)

    def update_tof(self, tof, at=None):
        self._set(tof_mm=tuple(tof), tof_at=time.monotonic() if at is None else at)

    def update_imu(self, tilt, at=None):
        self._set(tilt_deg=tilt, imu_at=time.monotonic() if at is None else at)

    def update_mega(self, telemetry: dict, at=None):
        raw = tuple(telemetry["cliff_raw"])
        self._set(cliff=decode_cliff(raw, self.edge_level, self.calibrated), cliff_raw=raw,
                  cliff_at=time.monotonic() if at is None else at, pir=bool(telemetry["pir"]))

    def snapshot(self) -> Frame:
        with self._lock:
            return self._frame


class SensorReader:
    """Polls ToF + IMU. A failed device is restarted every `retry_s`; while it is down its data goes stale,
    which the safety gate treats as unsafe."""

    def __init__(self, hub: SensorHub, tof, imu, retry_s: float = 5.0, clock=time.monotonic):
        self.hub, self.clock, self.retry_s = hub, clock, retry_s
        self.devices = {"tof": [tof, False, -1e9, "not started"], "imu": [imu, False, -1e9, "not started"]}

    def _poll_one(self, name, publish):
        dev = self.devices[name]
        device, started, last_try, _ = dev
        if not started:
            if self.clock() - last_try < self.retry_s:
                return
            dev[2] = self.clock()
            try:
                device.start()
                dev[1], dev[3] = True, ""
            except Exception as exc:
                dev[3] = f"{type(exc).__name__}: {exc}"[:160]
                return
        try:
            publish(device.sample())
            dev[3] = ""
        except ValueError as exc:                       # implausible value: skip this sample, keep the device
            dev[3] = str(exc)[:160]
        except Exception as exc:                        # bus error: restart the device later
            dev[1], dev[2], dev[3] = False, self.clock(), f"{type(exc).__name__}: {exc}"[:160]
            try:
                device.close()
            except Exception:
                pass

    def poll(self):
        self._poll_one("tof", self.hub.update_tof)
        self._poll_one("imu", self.hub.update_imu)

    def status(self) -> dict:
        return {name: {"ok": d[1] and not d[3], "error": d[3]} for name, d in self.devices.items()}

    def close(self):
        for dev in self.devices.values():
            try:
                dev[0].close()
            except Exception:
                pass
            dev[1] = False
