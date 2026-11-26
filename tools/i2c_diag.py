#!/usr/bin/env python3
"""M04 - I2C diagnosis. Changes sensor shutdown GPIOs, moves no motors. Run with EVE STOPPED.

  python3 tools/i2c_diag.py

It checks /dev/i2c-1, the idle level of SDA/SCL, then switches the three distance sensors on one at a
time with their XSHUT wires (BCM5, BCM6, BCM13) and tells you in plain words what to look at."""
from __future__ import annotations
import os, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

XSHUT = (5, 6, 13)
PHYS = (29, 31, 33)
WHO = ("front-left", "front-right", "rear")
EXPECT = {
    0x29: "VL53L0X at its power-on address",
    0x68: "MPU-6050 tilt",
    0x69: "MPU-6050 tilt (AD0 high)",
}


def sh(argv) -> str:
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=10, check=True).stdout
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or f"exited with code {exc.returncode}").strip()
        raise RuntimeError(f"{argv[0]} failed. {detail}") from exc
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"{argv[0]} failed. {exc}") from exc


def parse_i2cdetect(text: str) -> tuple[list[int], list[int]]:
    found = []
    claimed = []
    saw_row = False
    for row in text.splitlines()[1:]:
        head, _, cells = row.partition(":")
        try:
            base = int(head, 16)
        except ValueError:
            continue
        saw_row = True
        cells = cells.removeprefix(" ")
        for i in range(16):
            cell = cells[i * 3:i * 3 + 2].strip()
            if cell == "UU":
                claimed.append(base + i)
            elif cell == f"{base + i:02x}":
                found.append(base + i)
    if not saw_row:
        raise RuntimeError("i2cdetect returned no address table.")
    return found, claimed


def scan(tof_addresses) -> list[int]:
    found, claimed = parse_i2cdetect(sh(["i2cdetect", "-y", "1"]))
    busy = [address for address in claimed if address in EXPECT or address in tof_addresses]
    if busy:
        raise RuntimeError(f"A driver already claims {names(busy)} (UU). Check the owner before retrying.")
    return found


def names(addresses) -> str:
    return ", ".join(f"0x{a:02X}" + (f" ({EXPECT[a]})" if a in EXPECT else "") for a in addresses) or "NONE"


def advice(all_off: list[int], per_sensor: list[bool], lines_high: bool, xshut=XSHUT, physical=PHYS,
           *, imu_address=0x68, tof_addresses=(0x30, 0x31, 0x32)) -> list[str]:
    """Pure function (tested): measurements -> what to do."""
    out = []
    if not lines_high:
        out.append("SDA and/or SCL is LOW when idle. A wire is shorted to GND, SDA/SCL go to the wrong pins, or one "
                   "sensor board is faulty. Switch off, unplug the sensors, then add them back one at a time.")
    stuck = [a for a in all_off if a == 0x29 or a in tof_addresses]
    if stuck:
        out.append(f"A distance sensor answers ({names(stuck)}) although all XSHUT wires are held LOW. That sensor's "
                   "XSHUT wire is not connected (or goes to the wrong Pi pin).")
    if imu_address not in all_off:
        alternate = 0x69 if imu_address == 0x68 else 0x68
        if alternate in all_off:
            out.append(f"The configured tilt address {imu_address:#04x} is silent. A device answers "
                       f"at {alternate:#04x}. Check the MPU-6050 AD0 setting and sensors.imu_address together.")
        else:
            out.append(f"MPU-6050 does not answer at the configured address {imu_address:#04x}. Check its supply, "
                       "GND, SDA on Pi physical pin 3 and SCL on physical pin 5. It shares the distance-sensor bus.")
    for i, seen in enumerate(per_sensor):
        if not seen:
            out.append(f"Distance sensor {WHO[i]} never answered when its XSHUT (BCM{xshut[i]}, pin {physical[i]}) was released. "
                       "Check its VIN -> 3.3 V, GND, SDA -> pin 3, SCL -> pin 5 and the XSHUT wire.")
    if not all_off and not any(per_sensor) and lines_high:
        out.append("The whole bus is silent but the lines look healthy: most likely SDA and SCL are swapped, the sensors "
                   "have no 3.3 V, or their GND is not joined to the Pi GND.")
    return out


def main() -> int:
    from _common import config, eve_running
    sensors = config.load()["sensors"]
    xshut = sensors["tof_xshut"]
    imu_address = sensors["imu_address"]
    tof_addresses = sensors["tof_addresses"]
    physical_map = {4:7, 5:29, 6:31, 7:26, 8:24, 9:21, 10:19, 11:23, 12:32, 13:33,
                    14:8, 15:10, 16:36, 17:11, 18:12, 19:35, 20:38, 21:40, 22:15,
                    23:16, 24:18, 25:22, 26:37, 27:13}
    physical = [physical_map[p] for p in xshut]
    if eve_running():
        print("Stop EVE first (Ctrl+C in PuTTY 1). This test needs the I2C bus for itself."); return 2
    print("== 1. I2C switched on? ==")
    if not os.path.exists("/dev/i2c-1"):
        print("NO /dev/i2c-1. Run:  sudo raspi-config nonint do_i2c 0 && sudo reboot"); return 1
    print("yes (/dev/i2c-1)")
    if not shutil.which("pinctrl") or not shutil.which("i2cdetect"):
        print("Tools missing. Run:  sudo apt install -y raspi-utils i2c-tools"); return 1
    touched = []
    cleanup_failed = False
    try:
        print("\n== 2. SDA (BCM2) / SCL (BCM3) idle level - both should say 'hi' ==")
        levels = sh(["pinctrl", "get", "2,3"]).strip()
        print(levels)
        if levels.count("| hi") + levels.count("| lo") < 2:
            raise RuntimeError("pinctrl did not report both SDA and SCL levels.")
        lines_high = levels.count("| hi") >= 2
        for pin in xshut:
            touched.append(pin)
            sh(["pinctrl", "set", str(pin), "op", "dl"])
        time.sleep(0.1)
        print(f"\n== 3. All distance sensors OFF - expect MPU-6050 at {imu_address:#04x} ==")
        all_off = scan(tof_addresses)
        print(names(all_off))
        per_sensor = []
        for i, pin in enumerate(xshut):
            # Input with no Pi pull lets the breakout's pull-up release XSHUT.
            sh(["pinctrl", "set", str(pin), "ip", "pn"])
            time.sleep(0.1)
            now = scan(tof_addresses)
            new = [address for address in now if address not in all_off]
            print(f"\n== 4.{i + 1} Only the {WHO[i]} sensor ON (XSHUT BCM{pin}) - expect 0x29 ==")
            print("answers:", names(now), "| new:", names(new))
            per_sensor.append(0x29 in new)
            sh(["pinctrl", "set", str(pin), "op", "dl"])
    except RuntimeError as exc:
        print(f"I2C diagnostic could not finish. {exc}", file=sys.stderr)
        return 2
    finally:
        for pin in touched:
            try:
                sh(["pinctrl", "set", str(pin), "ip", "pn"])
            except RuntimeError as exc:
                print(f"Could not release XSHUT BCM{pin}. {exc}", file=sys.stderr)
                cleanup_failed = True
    if cleanup_failed:
        return 2

    print("\n== RESULT ==")
    issues = advice(all_off, per_sensor, lines_high, xshut, physical,
                    imu_address=imu_address, tof_addresses=tof_addresses)
    for item in issues:
        print("-", item)
    if issues:
        return 1
    print("All four devices answered during isolation. Continue with the live M04 readings and cliff checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
