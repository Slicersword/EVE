#!/usr/bin/env python3
"""Compile locked and synthetic enabled variants for Mega; never upload or edit the checkout."""
import copy
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from eve3 import config, firmware


def main():
    cli = shutil.which('arduino-cli')
    if not cli:
        raise SystemExit('arduino-cli is required; this is target compilation, not a host harness check')
    cfg = config.load()
    for enabled in (False, True):
        variant = copy.deepcopy(cfg)
        if enabled:
            variant['commissioning'] = dict.fromkeys(config.COMMISSIONING_FLAGS, True)
            variant['firmware'].update(drive_enabled=True, head_enabled=True)
            variant['sensors']['cliff_calibration']['calibrated'] = True
        config.validate(variant)
        with tempfile.TemporaryDirectory() as tmp:
            sketch = Path(tmp) / 'eve_controller'
            shutil.copytree(ROOT / 'firmware/eve_controller', sketch)
            (sketch / 'eve_config.h').write_text(firmware.header_text(variant), encoding='ascii')
            print('Compiling', 'enabled fixture' if enabled else 'locked defaults', flush=True)
            subprocess.run([cli, 'compile', '--fqbn', 'arduino:avr:mega', '--warnings', 'all', str(sketch)], check=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
