#!/usr/bin/env python3
"""Cliff sensor calibration (KY-033 x3). EVE must be running in PuTTY 1. Wheels do not move.

  python3 tools/calibrate_cliff.py floor    robot standing on the normal floor, all three sensors over floor
  python3 tools/calibrate_cliff.py edge     all three sensors hanging over a table edge / stair (hold the robot!)
  python3 tools/calibrate_cliff.py apply    save the result
Then:  bash scripts/flash_mega.sh"""
import json, sys, time
from _common import ROOT, config, status
from eve3.sensors import calibrate_cliff

STORE = ROOT / "data" / "cliff_samples.json"


def main(argv):
    if len(argv) != 1 or argv[0] not in ("floor", "edge", "apply"):
        print(__doc__); return 2
    samples = json.loads(STORE.read_text()) if STORE.exists() else {}
    if argv[0] == "apply":
        try:
            result = calibrate_cliff(samples.get("floor", []), samples.get("edge", []))
        except ValueError as exc:
            sys.exit(f"Cannot calibrate: {exc}")
        config.save_local(ROOT, {"sensors": {"cliff_calibration": result}})
        print(f"Saved. Edge level per sensor (front-left, rear, front-right): {result['edge_level']}")
        print("Next: stop EVE (Ctrl+C in PuTTY 1), then run:  ./eve flash")
        return 0
    rows = []
    print(f"Reading 15 samples for '{argv[0]}' - keep the robot still ...")
    for _ in range(15):
        s = status()["sensors"]
        if s["mega_age_s"] is None or s["mega_age_s"] > 0.5 or None in s["cliff_raw"]:
            sys.exit("No fresh data from the Mega. Check `python3 tools/evectl.py status` first.")
        rows.append(s["cliff_raw"])
        time.sleep(0.2)
    samples[argv[0]] = rows
    STORE.parent.mkdir(exist_ok=True)
    STORE.write_text(json.dumps(samples))
    print(f"{argv[0]}: first {rows[0]} ... last {rows[-1]}   (front-left, rear, front-right)")
    if len({tuple(r) for r in rows}) > 1:
        print("WARNING: readings changed while sampling. Adjust the blue trimmer on the flickering sensor and repeat.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
