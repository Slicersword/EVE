#!/usr/bin/env python3
"""Checks what is installed on the Pi. Read-only.   python3 tools/doctor.py"""
import glob, grp, importlib, os, shutil, sys
from _common import ROOT, config

rows = []


def check(label, ok, fix=""):
    rows.append((label, bool(ok), fix))


def has_module(name):
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


def main():
    cfg = None
    try:
        cfg = config.load()
        check("config valid", True)
    except Exception as exc:
        check(f"config valid ({exc})", False, "fix config/local.json or delete it")
    check("Python 3.10+ (Pi target: 3.11)", sys.version_info >= (3, 10))
    check("running inside .venv", sys.prefix != sys.base_prefix, "use .venv/bin/python (bash scripts/setup_pi.sh creates it)")
    for module, need in (("serial", "M02 Mega"), ("smbus2", "M04 tilt"), ("adafruit_vl53l0x", "M04 distance"),
                         ("board", "M04 distance"), ("gpiozero", "M09 touch"), ("picamera2", "M10 camera"), ("cv2", "M10 camera")):
        check(f"python module {module} ({need})", has_module(module), "bash scripts/setup_pi.sh")
    for tool, need in (("i2cdetect", "M04"), ("pinctrl", "M04"), ("vcgencmd", "M03"), ("espeak-ng", "M13 speech"),
                       ("arecord", "M13 microphone"), ("g++", "tests")):
        check(f"program {tool} ({need})", shutil.which(tool), "bash scripts/setup_pi.sh")
    check("program chromium (M01 face)", shutil.which("chromium") or shutil.which("chromium-browser"), "bash scripts/setup_pi.sh")
    check("program arduino-cli (M02)", shutil.which("arduino-cli") or os.path.exists(os.path.expanduser("~/bin/arduino-cli")),
          "bash scripts/setup_pi.sh")
    check("I2C switched on (/dev/i2c-1)", os.path.exists("/dev/i2c-1"), "sudo raspi-config nonint do_i2c 0 && sudo reboot")
    ports = glob.glob("/dev/serial/by-id/*") + glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
    check("Mega USB cable seen" + (f" ({ports[0]})" if ports else ""), ports, "plug the Mega into a Pi USB port")
    try:
        mine = {grp.getgrgid(g).gr_name for g in os.getgroups()}
        for group in ("dialout", "i2c", "gpio", "video", "audio"):
            check(f"user in group {group}", group in mine, "bash scripts/setup_pi.sh, then log out of PuTTY and back in")
    except Exception:
        pass
    if cfg:
        v = cfg["voice"]
        check("whisper program built (M13 hearing)", os.path.exists(ROOT / v["stt_command"]), "bash scripts/install_voice.sh")
        check("whisper model downloaded (M13 hearing)", os.path.exists(ROOT / v["stt_model"]), "bash scripts/install_voice.sh")
        check("face-detect model present (M10)", os.path.exists(cfg["camera"]["cascade_path"]), "sudo apt install -y opencv-data")
    width = max(len(r[0]) for r in rows)
    for label, ok, fix in rows:
        print(f"{'PASS' if ok else 'MISSING':8}{label.ljust(width)}  {'' if ok else '-> ' + fix}")
    print("\nMISSING lines only matter when you reach that stage (M-number shown in brackets).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
