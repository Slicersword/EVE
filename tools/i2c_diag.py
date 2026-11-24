#!/usr/bin/env python3
"""M04 - why do the I2C sensors not answer? Read-only test, moves nothing. Run with EVE STOPPED.

  python3 tools/i2c_diag.py

It checks /dev/i2c-1, the idle level of SDA/SCL, then switches the three distance sensors on one at a
time with their XSHUT wires (BCM5, BCM6, BCM13) and tells you in plain words what to look at."""
from __future__ import annotations
import os, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

XSHUT = (5, 6, 13)
PHYS = (29, 31, 33)
WHO = ("front-left", "front-right", "rear")
EXPECT = {0x68: "MPU-6050 tilt", 0x69: "MPU-6050 tilt (AD0 high)", 0x29: "VL53L0X at its power-on address",
          0x30: "VL53L0X front-left", 0x31: "VL53L0X front-right", 0x32: "VL53L0X rear"}


def sh(argv) -> str:
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=10)
        return r.stdout + r.stderr
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"error: {exc}"


def parse_i2cdetect(text: str) -> list[int]:
    found = []
    for row in text.splitlines()[1:]:
        head, _, cells = row.partition(":")
        try:
            base = int(head, 16)
        except ValueError:
            continue
        cells = cells[1:] if cells.startswith(" ") else cells
        for i in range(16):
            cell = cells[i * 3:i * 3 + 2].strip()
            if cell and cell not in ("--", "UU"):
                try:
                    found.append(int(cell, 16))
                except ValueError:
                    pass
    return found


def scan() -> list[int]:
    return parse_i2cdetect(sh(["i2cdetect", "-y", "1"]))


def names(addresses) -> str:
    return ", ".join(f"0x{a:02X}" + (f" ({EXPECT[a]})" if a in EXPECT else " (unknown device)") for a in addresses) or "NOTHING"


def advice(all_off: list[int], per_sensor: list[bool], lines_high: bool) -> list[str]:
    """Pure function (tested): measurements -> what to do."""
    out = []
    if not lines_high:
        out.append("SDA and/or SCL is LOW when idle. A wire is shorted to GND, SDA/SCL go to the wrong pins, or one "
                   "sensor board is faulty. Switch off, unplug the sensors, then add them back one at a time.")
    stuck = [a for a in all_off if a in (0x29, 0x30, 0x31, 0x32)]
    if stuck:
        out.append(f"A distance sensor answers ({names(stuck)}) although all XSHUT wires are held LOW. That sensor's "
                   "XSHUT wire is not connected (or goes to the wrong Pi pin).")
    if 0x68 not in all_off and 0x69 not in all_off:
        out.append("MPU-6050 does not answer at 0x68. Check on its board: VCC -> Pi 3.3 V (pin 1 or 17), GND -> Pi GND, "
                   "SDA -> pin 3, SCL -> pin 5. It is on the same two wires as the distance sensors.")
    elif 0x69 in all_off:
        out.append("MPU-6050 answers at 0x69 instead of 0x68: its AD0 pin is high. Connect AD0 to GND (or leave it "
                   "open if the board has a pull-down), or set sensors.imu_address to 105.")
    for i, seen in enumerate(per_sensor):
        if not seen:
            out.append(f"Distance sensor {WHO[i]} never answered when its XSHUT (BCM{XSHUT[i]}, pin {PHYS[i]}) was released. "
                       "Check its VIN -> 3.3 V, GND, SDA -> pin 3, SCL -> pin 5 and the XSHUT wire.")
    if not all_off and not any(per_sensor) and lines_high:
        out.append("The whole bus is silent but the lines look healthy: most likely SDA and SCL are swapped, the sensors "
                   "have no 3.3 V, or their GND is not joined to the Pi GND.")
    return out or ["All four devices answered. I2C wiring is good - continue with M04."]


def main() -> int:
    from _common import eve_running
    if eve_running():
        print("Stop EVE first (Ctrl+C in PuTTY 1). This test needs the I2C bus for itself."); return 2
    print("== 1. I2C switched on? ==")
    if not os.path.exists("/dev/i2c-1"):
        print("NO /dev/i2c-1. Run:  sudo raspi-config nonint do_i2c 0 && sudo reboot"); return 1
    print("yes (/dev/i2c-1)")
    if not shutil.which("pinctrl") or not shutil.which("i2cdetect"):
        print("Tools missing. Run:  sudo apt install -y raspi-utils i2c-tools"); return 1
    print("\n== 2. SDA (BCM2) / SCL (BCM3) idle level - both should say 'hi' ==")
    levels = sh(["pinctrl", "get", "2,3"]).strip()
    print(levels)
    lines_high = levels.count("| hi") >= 2
    for pin in XSHUT:
        sh(["pinctrl", "set", str(pin), "op", "dl"])            # hold LOW = sensor off
    time.sleep(0.1)
    print("\n== 3. All three distance sensors held OFF - only the MPU-6050 (0x68) should answer ==")
    all_off = scan()
    print(names(all_off))
    per_sensor = []
    for i, pin in enumerate(XSHUT):
        sh(["pinctrl", "set", str(pin), "ip", "pn"])            # release (no Pi pull); the board's pull-up wakes it
        time.sleep(0.1)
        now = scan()
        new = [a for a in now if a not in all_off]
        print(f"\n== 4.{i + 1} Only the {WHO[i]} sensor ON (XSHUT BCM{pin}) - expect 0x29 ==")
        print("answers:", names(now), "| new:", names(new))
        per_sensor.append(0x29 in new)
        sh(["pinctrl", "set", str(pin), "op", "dl"])
    for pin in XSHUT:
        sh(["pinctrl", "set", str(pin), "ip", "pn"])            # leave the lines released
    print("\n== RESULT ==")
    for item in advice(all_off, per_sensor, lines_high):
        print("-", item)
    return 0


if __name__ == "__main__":
    sys.exit(main())
