#!/usr/bin/env python3
"""Hardware-free repository checks. Does not import/open hardware drivers or modify owner state."""
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from eve3 import config, firmware


def main():
    failures = []
    cfg = config.validate(json.loads((ROOT / 'config/eve.json').read_text()))
    if any(cfg['commissioning'].values()):
        failures.append('Shipped commissioning flags must all be false')
    if cfg['firmware']['drive_enabled'] or cfg['firmware']['head_enabled']:
        failures.append('Shipped actuator enables must be false')
    if cfg['sensors']['cliff_calibration']['calibrated']:
        failures.append('Shipped cliff calibration must be unset')
    if cfg['ai']['cloud']['enabled'] or cfg['hardware']['ina219_enabled']:
        failures.append('Cloud and INA219 must remain disabled by default')
    header = (ROOT / 'firmware/eve_controller/eve_config.h').read_text()
    if header != firmware.header_text(cfg):
        failures.append('Generated firmware header differs from shipped defaults')
    generated = subprocess.run([sys.executable, str(ROOT / 'tools/stage.py'), 'guide'],
                               cwd=ROOT, text=True, capture_output=True, check=True).stdout
    if generated != (ROOT / 'docs/SETUP_GUIDE.md').read_text():
        failures.append('SETUP_GUIDE.md is stale; regenerate it from tools/stage.py')
    diagrams = subprocess.run([sys.executable, str(ROOT / 'tools/draw_wiring.py'), '--check'],
                              cwd=ROOT, text=True, capture_output=True)
    if diagrams.returncode:
        failures.append(diagrams.stderr.strip() or 'Wiring diagrams are stale')
    snapshot = subprocess.run([sys.executable, str(ROOT / 'tools/build_source_index.py'), '--check'],
                              cwd=ROOT, text=True, capture_output=True)
    if snapshot.returncode:
        failures.append(snapshot.stderr.strip() or 'Public source viewer snapshot is stale')
    checked = 0
    for doc in [ROOT / 'README.md', ROOT / 'CONTRIBUTING.md', *sorted((ROOT / 'docs').rglob('*.md'))]:
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', doc.read_text()):
            if '://' in target or target.startswith(('#', 'mailto:')):
                continue
            path = target.split('#', 1)[0]
            if path and not (doc.parent / path).exists():
                failures.append(f'{doc.relative_to(ROOT)}: broken link {target}')
            checked += 1
    for path in [ROOT / 'README.md', ROOT / 'docs/SETUP_GUIDE.md', ROOT / 'tools/setup_steps.py']:
        if 'OneDrive - ' in path.read_text():
            failures.append(f'{path.name}: machine-specific owner path')
    example = json.loads((ROOT / 'config/local.example.json').read_text())
    config.validate(config.deep_merge(cfg, example))
    for filename in ['eve', *[str(p.relative_to(ROOT)) for p in (ROOT / 'scripts').glob('*.sh')]]:
        if not (ROOT / filename).stat().st_mode & 0o111:
            failures.append(f'{filename}: executable bit missing')
    for required in ('.gitignore', '.github/workflows/verify.yml', '_config.yml',
                     '_layouts/manual.html', 'index.html', 'search-data.js', 'code.html',
                     'tools/build_docs.mjs', 'tools/check_site.py'):
        if not (ROOT / required).is_file():
            failures.append(f'Missing repository build support: {required}')
    if failures:
        for issue in failures:
            print('FAIL:', issue)
        return 1
    print(f'PASS: locked defaults, generated firmware header, generated setup guide, {checked} local links')
    print('Physical acceptance: NOT VERIFIED by repository checks')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
