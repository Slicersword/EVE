#!/usr/bin/env python3
"""Change your own settings safely (written to config/local.json; shipped defaults are never touched).

  python3 tools/evecfg.py show                         what you have changed so far
  python3 tools/evecfg.py set voice.capture_enabled true
  python3 tools/evecfg.py set drive.max_pwm 120
  python3 tools/evecfg.py confirm power_a_verified     commissioning flag - asks you to type a sentence
  python3 tools/evecfg.py unconfirm drive_verified
Restart EVE after a change. After changing firmware.*, drive.*, head.* limits or cliff calibration also
run:  ./eve flash"""
import json, sys
from _common import ROOT, config

WHAT_YOU_CONFIRM = {
    "power_a_verified": "Bank A runs the Pi (and screen/fan if used) and vcgencmd get_throttled stayed 0x0 under load",
    "power_b_verified": "Bank B 5 V polarity, fuse/switch and common ground are checked, and the switch cuts motor power",
    "motor_current_verified": "I measured motor + head + audio current on Bank B and the bank does not switch off",
    "contained_ground_area": "The robot is on the floor in a closed area with no stairs/edges, or its wheels are lifted",
    "drive_verified": "All four wheels turned the right way in the lifted test and stopped on STOP, cliff and timeout",
    "head_verified": "The head moved within safe limits in the jog test and nothing rubbed or pulled a cable",
}


def parse(raw: str):
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def nested(path: str, value) -> dict:
    out = value
    for key in reversed(path.split(".")):
        out = {key: out}
    return out


def save(patch: dict, path: str):
    from eve3 import firmware
    before = firmware.firmware_id(config.load())
    try:
        config.save_local(ROOT, patch)
    except config.ConfigError as exc:
        sys.exit(f"Not saved: {exc}")
    print(f"Saved {path}. Restart EVE to use it.")
    if firmware.firmware_id(config.load()) != before:
        print("This setting is also built into the Mega firmware -> stop EVE and run:  ./eve flash")


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__); return 0
    action = argv[0]
    if action == "show":
        local = ROOT / "config" / "local.json"
        print(local.read_text(encoding="utf-8") if local.exists() else "{}  (nothing changed yet)")
    elif action == "set" and len(argv) == 3:
        path, value = argv[1], parse(argv[2])
        if path.startswith("commissioning."):
            sys.exit("Use:  python3 tools/evecfg.py confirm <flag>")
        base = config.load()
        node = base
        for key in path.split("."):
            if not isinstance(node, dict) or key not in node or key.startswith("_"):
                sys.exit(f"Unknown setting: {path}")
            node = node[key]
        if isinstance(node, dict):
            sys.exit(f"{path} is a group; set one value inside it")
        save(nested(path, value), path)
    elif action == "confirm" and len(argv) == 2 and argv[1] in WHAT_YOU_CONFIRM:
        flag = argv[1]
        print(f"\nYou are confirming, from a real test on the robot:\n  {WHAT_YOU_CONFIRM[flag]}\n")
        if input("Type  I TESTED THIS  to confirm: ").strip() != "I TESTED THIS":
            sys.exit("Not confirmed. Nothing changed.")
        save({"commissioning": {flag: True}}, f"commissioning.{flag}")
    elif action == "unconfirm" and len(argv) == 2 and argv[1] in WHAT_YOU_CONFIRM:
        save({"commissioning": {argv[1]: False}}, f"commissioning.{argv[1]}")
    else:
        print(__doc__); return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
