"""M02 - single owner of the Mega serial port: SYNC, correlated ACKs, heartbeats, telemetry."""
from __future__ import annotations
import glob, threading, time
from .protocol import MAX_FRAME, decode, encode, parse_telemetry

BY_ID_GLOB = "/dev/serial/by-id/usb-1a86_USB*"       # CH340 on the Mega clone


def find_port(configured: str | None) -> str:
    # An explicit setting must win, especially when more than one USB serial board is attached.
    if configured:
        return configured
    hits = sorted(glob.glob(BY_ID_GLOB))
    if len(hits) > 1:
        raise ValueError("Multiple serial boards found; set serial.port to the Mega's by-id path")
    return hits[0] if hits else "/dev/ttyUSB0"


def open_serial(port: str, baud: int = 115200):
    import serial                                     # pyserial, imported only on the robot
    return serial.Serial(port, baud, timeout=0.08, write_timeout=0.15)


class MegaLink:
    def __init__(self, opener, expected_id: str = "", ack_timeout_s: float = 0.25,
                 hb_max_age_s: float = 0.35, telemetry_max_age_s: float = 0.5, on_telemetry=None):
        self._opener = opener                         # callable -> object with read_until/write/close
        self.expected_id = expected_id
        self.ack_timeout_s = ack_timeout_s
        self.hb_max_age_s, self.telemetry_max_age_s = hb_max_age_s, telemetry_max_age_s
        self.on_telemetry = on_telemetry
        self.ser = None
        self.seq = 1
        self.synced = False
        self.synced_at = 0.0
        self.firmware_id = ""
        self.telemetry: dict = {}
        self.telemetry_at = 0.0
        self.hb_ack_at = 0.0
        self.last_error = "not opened"
        self._stop = threading.Event()
        self._thread = None
        self._wlock = threading.RLock()
        self._slock = threading.RLock()
        self._pending: dict[int, tuple[threading.Event, list]] = {}
        self._hb: dict[int, float] = {}

    # -- lifecycle ---------------------------------------------------------
    def open(self, settle_s: float = 2.0):
        self.close()
        self.ser = self._opener()
        self.seq, self.synced, self.last_error = 1, False, ""
        self.telemetry, self.telemetry_at, self.hb_ack_at = {}, 0.0, 0.0
        self._stop.clear()
        if settle_s and self._stop.wait(settle_s):    # opening the port resets the Mega; let it boot
            return
        try:
            self.ser.reset_input_buffer()
        except Exception:
            pass
        self._thread = threading.Thread(target=self._reader, name="eve3-mega-rx", daemon=True)
        self._thread.start()
        try:
            ack = self.request("SYNC", timeout_s=0.6)
            self.firmware_id = ack.split(",", 1)[1] if "," in ack else ""
            self.synced_at = time.monotonic()
            self.synced = True
        except Exception as exc:
            self.close()
            self.last_error = f"SYNC failed: {exc}"
            raise

    def close(self):
        if self.ser is not None:
            try:
                self._send("STOP")
            except Exception:
                pass
        self._stop.set()
        self.synced = False
        with self._wlock:
            ser, self.ser = self.ser, None
        if ser is not None:
            try:
                ser.close()
            except Exception:
                pass
        with self._slock:
            for event, box in self._pending.values():
                box.append("ERR,CLOSED")
                event.set()
            self._pending.clear()
            self._hb.clear()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=1)
        self._thread = None

    # -- state -------------------------------------------------------------
    def online(self, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        return bool(self.synced and self.ser is not None
                    and 0 < self.hb_ack_at and now - self.hb_ack_at < self.hb_max_age_s
                    and 0 < self.telemetry_at and now - self.telemetry_at < self.telemetry_max_age_s)

    @property
    def firmware_ok(self) -> bool:
        return bool(self.synced and self.expected_id and self.firmware_id == self.expected_id)

    # -- tx ----------------------------------------------------------------
    def _send(self, payload, pending=None, heartbeat=False) -> int:
        with self._wlock:
            if self.ser is None:
                raise RuntimeError("Mega not open")
            seq = self.seq
            self.seq = (seq + 1) & 0xFFFF or 1
            with self._slock:
                if pending:
                    self._pending[seq] = pending
                if heartbeat:
                    now = time.monotonic()
                    self._hb = {s: t for s, t in self._hb.items() if now - t < 1}
                    self._hb[seq] = now
            try:
                data = encode(seq, payload)
                if self.ser.write(data) != len(data):
                    raise IOError("short serial write")
            except Exception:
                with self._slock:
                    self._pending.pop(seq, None)
                    self._hb.pop(seq, None)
                raise
            return seq

    def request(self, payload, timeout_s=None) -> str:
        """Send and wait for the ACK carrying the same sequence number. Raises on ERR or timeout."""
        timeout_s = self.ack_timeout_s if timeout_s is None else timeout_s
        pending = (threading.Event(), [])
        seq = self._send(payload, pending=pending)
        try:
            if not pending[0].wait(timeout_s):
                raise TimeoutError(f"no ACK for {payload.split(',')[0]}")
            reply = pending[1][0]
            if not (reply == "ACK" or reply.startswith("ACK,")):
                raise RuntimeError(reply)
            return reply
        finally:
            with self._slock:
                self._pending.pop(seq, None)

    def heartbeat(self):
        self._send("HB", heartbeat=True)

    def drive(self, left: int, right: int):
        self._send(f"DRIVE,{int(left)},{int(right)}")

    def stop_motion(self):
        self._send("DRIVE,0,0")

    def emergency_stop(self):
        self._send("STOP")

    def head(self, pan: int, tilt: int):
        self._send(f"HEAD,{int(pan)},{int(tilt)}")

    def clear_stop(self):
        return self.request("CLEAR")

    def set_manual_home(self):
        return self.request("HOMESET")

    def release_head(self):
        self._send("HEADSTOP")

    # -- rx ----------------------------------------------------------------
    def _consume(self, line: bytes):
        seq, payload = decode(line)
        now = time.monotonic()
        if payload == "ACK" or payload.startswith(("ACK,", "ERR,")):
            with self._slock:
                sent = self._hb.pop(seq, None)
                if sent is not None and payload == "ACK" and 0 <= now - sent <= self.ack_timeout_s:
                    self.hb_ack_at = now
                pending = self._pending.get(seq)
                if pending:
                    pending[1].append(payload)
                    pending[0].set()
        elif payload.startswith("T,"):
            self.telemetry = parse_telemetry(payload)
            self.telemetry_at = now
            if self.on_telemetry:
                self.on_telemetry(self.telemetry, now)

    def _reader(self):
        buf, discarding = bytearray(), False
        ser = self.ser
        while not self._stop.is_set() and ser is not None:
            try:
                chunk = ser.read_until(b"\n", MAX_FRAME + 1)
                if not chunk:
                    continue
                if not discarding:
                    buf.extend(chunk)
                    if len(buf) > MAX_FRAME:
                        buf.clear()
                        discarding = True
                if not chunk.endswith(b"\n"):
                    continue
                if discarding:
                    discarding = False
                    continue
                frame = bytes(buf)
                buf.clear()
                try:
                    self._consume(frame)
                except (ValueError, UnicodeError):
                    continue                           # corrupt frame: ignore, never guess
            except Exception as exc:
                if not self._stop.is_set():
                    self.last_error = f"serial read failed: {type(exc).__name__}"
                    self.synced = False
                return
