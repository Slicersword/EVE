#!/usr/bin/env bash
# M17 only - start EVE and the face automatically when the Pi boots. Undo:  bash scripts/install_service.sh --remove
set -euo pipefail
cd "$(dirname "$0")/.."
HERE="$(pwd)"
UNIT="$HOME/.config/systemd/user/eve3.service"; AUTO="$HOME/.config/autostart/eve3-face.desktop"
if [ "${1:-}" = "--remove" ]; then
  systemctl --user disable --now eve3.service 2>/dev/null || true
  rm -f "$UNIT" "$AUTO"; systemctl --user daemon-reload; echo "Removed. EVE no longer starts by itself."; exit 0
fi
mkdir -p "$(dirname "$UNIT")" "$(dirname "$AUTO")"
sed "s|@HERE@|$HERE|g" systemd/eve3.service > "$UNIT"
printf '[Desktop Entry]\nType=Application\nName=EVE face\nExec=bash -c "sleep 8; exec %s/scripts/face_kiosk.sh"\nX-GNOME-Autostart-enabled=true\n' "$HERE" > "$AUTO"
systemctl --user daemon-reload
systemctl --user enable --now eve3.service
sudo loginctl enable-linger "$USER"
echo "Installed. Check:  systemctl --user status eve3.service     Logs:  journalctl --user -u eve3 -n 50"
