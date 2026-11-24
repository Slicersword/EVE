#!/usr/bin/env bash
# M00 - park the OLD EVE install so it cannot fight V3 for the Mega, the I2C bus or port 8765.
# Nothing is deleted: folders are MOVED to ~/eva_old_<date>/ and services are only stopped + disabled.
#   bash scripts/retire_old.sh          show what would happen
#   bash scripts/retire_old.sh --yes    do it
set -uo pipefail
DEST="$HOME/eva_old_$(date +%Y%m%d)"
DO=0; [ "${1:-}" = "--yes" ] && DO=1
say() { echo "$@"; }
act() { if [ $DO = 1 ]; then "$@"; else echo "   would run: $*"; fi; }
found=0
for unit in eve.service evea-ui.service eve2.service; do
  if systemctl --user list-unit-files "$unit" 2>/dev/null | grep -q "$unit"; then
    found=1; say "old user service: $unit"; act systemctl --user disable --now "$unit"
  fi
done
for file in "$HOME"/.config/autostart/eva-*.desktop "$HOME"/.config/autostart/eve-*.desktop; do
  [ -e "$file" ] || continue
  case "$file" in *eve3*) continue ;; esac
  found=1; say "old autostart: $file"; act mkdir -p "$DEST/autostart"; act mv "$file" "$DEST/autostart/"
done
for dir in "$HOME/eve_robot" "$HOME/eve_master"; do
  [ -d "$dir" ] || continue
  found=1; say "old folder: $dir"; act mkdir -p "$DEST"; act mv "$dir" "$DEST/"
done
if pgrep -u "$USER" -f "eve.main|eva_touchscreen|python -m eve2" >/dev/null 2>&1; then
  found=1; say "old EVE program is still running"; act pkill -u "$USER" -f "eve.main|eva_touchscreen|python -m eve2"
fi
[ $found = 0 ] && say "Nothing old found. Good."
[ $found = 1 ] && [ $DO = 0 ] && say && say "Nothing changed yet. To do it:  bash scripts/retire_old.sh --yes"
[ $found = 1 ] && [ $DO = 1 ] && say && say "Done. Old files are in $DEST (old cliff calibration is in its eve.json)." \
  && say "Undo:  mv $DEST/eve_robot $DEST/eve_master ~/ 2>/dev/null; systemctl --user enable --now eve.service"
exit 0
