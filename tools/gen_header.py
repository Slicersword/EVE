#!/usr/bin/env python3
"""Regenerate firmware/eve_controller/eve_config.h from config (eve.json + local.json).
Run after any change to calibration, limits or firmware flags, then compile and upload."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from eve3 import config, firmware

cfg = config.load()
out = config.ROOT / "firmware" / "eve_controller" / "eve_config.h"
out.write_text(firmware.header_text(cfg), encoding="ascii")
fw, cal = cfg["firmware"], cfg["sensors"]["cliff_calibration"]
print(f"Wrote {out}")
print(f"Firmware id : {firmware.firmware_id(cfg)}")
print(f"Drive {'ENABLED' if fw['drive_enabled'] else 'disabled'} | Head {'ENABLED' if fw['head_enabled'] else 'disabled'}"
      f" | Cliff {'calibrated ' + str(cal['edge_level']) if cal['calibrated'] else 'NOT calibrated (Mega stays latched)'}")
