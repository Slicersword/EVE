#!/usr/bin/env bash
# Explicit owner update: Bank B OFF, EVE stopped; preserve source/state and use fast-forward only.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="$(pwd)/.venv/bin/python"; [ -x "$PY" ] || PY=python3
[ -d .git ] || { echo "Git install required. ZIP installs must be backed up and replaced manually."; exit 1; }
[ "$(git branch --show-current)" = main ] || { echo "Stop: switch to a clean main branch first."; exit 1; }
HEADER=firmware/eve_controller/eve_config.h
[ -z "$(git status --porcelain -- . ":(exclude)$HEADER")" ] || { echo "Stop: local changes exist; commit or preserve them before updating."; exit 1; }
"$PY" - <<'PY'
from pathlib import Path
from eve3 import config, firmware
import subprocess
path = Path('firmware/eve_controller/eve_config.h')
if subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', str(path)]).returncode:
    if path.read_text() != firmware.header_text(config.load()):
        raise SystemExit('Stop: modified firmware header is not generated from your current owner settings.')
PY
if "$PY" -c 'import sys;sys.path.insert(0,"tools");from _common import eve_running;sys.exit(0 if eve_running() else 1)'; then
  echo "Stop EVE/service before updating. Bank B must be OFF."; exit 1
fi
read -r -p "Bank B is OFF and EVE/service stopped? Type YES: " answer
[ "$answer" = YES ] || exit 1
backup_dir="${EVE_BACKUP_DIR:-$HOME/eve_backups}"
mkdir -p "$backup_dir"
chmod 700 "$backup_dir"
umask 077
backup=$(mktemp --tmpdir="$backup_dir" --suffix=.tar.gz "eve-before-update-$(date +%Y%m%d-%H%M%S)-XXXXXX")
tar --exclude='./.git' --exclude='./.venv' --exclude='./third_party' --exclude='./models' --exclude='*/__pycache__' -czf "$backup" .
echo "Backup: $backup"
git fetch origin main
# Owner-generated header is already saved in the private backup and can be regenerated.
git restore --source=HEAD --staged --worktree -- "$HEADER"
git merge --ff-only origin/main
# Test a clean snapshot: owner's commissioning/calibration must not affect default-state tests.
verify_dir=$(mktemp -d)
trap 'rm -rf "$verify_dir"' EXIT
git archive HEAD | tar -x -C "$verify_dir"
(cd "$verify_dir" && "$PY" -m unittest discover -s tests -t . && "$PY" tools/check_repo.py)
"$PY" tools/gen_header.py
"$PY" - "$backup_dir" <<'PY'
import sys
from pathlib import Path
backups = sorted(Path(sys.argv[1]).glob('eve-before-update-*.tar.gz'), key=lambda p: p.stat().st_mtime, reverse=True)
for old in backups[2:]:
    old.unlink()
PY
echo "Updated and checked. Read CHANGELOG.md for dependency/reflash steps, then restart EVE."
