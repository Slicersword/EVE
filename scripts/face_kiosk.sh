#!/usr/bin/env bash
# M01 - shows the face full-screen on the Pi's own 7-inch display (no keyboard / F11 needed).
# Works from PuTTY too: it finds the desktop session of the logged-in Pi user.
cd "$(dirname "$0")/.." || exit 1
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
PORT="$("$PY" -c 'from eve3.config import load; print(load()["network"]["port"])')" || exit 1
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
if [ -z "${WAYLAND_DISPLAY:-}" ] && [ -z "${DISPLAY:-}" ]; then
  sock="$(ls "$XDG_RUNTIME_DIR"/wayland-[0-9] 2>/dev/null | head -n1)"
  if [ -n "$sock" ]; then export WAYLAND_DISPLAY="$(basename "$sock")"; else export DISPLAY=:0; fi
fi
B="$(command -v chromium || command -v chromium-browser)"
[ -n "$B" ] || { echo "chromium is not installed: bash scripts/setup_pi.sh"; exit 1; }
pkill -u "$USER" -f "user-data-dir=$HOME/.config/eve3-kiosk" 2>/dev/null
exec "$B" --kiosk --noerrdialogs --disable-infobars --no-first-run --disable-session-crashed-bubble \
  --disable-features=Translate --password-store=basic --ozone-platform-hint=auto --check-for-update-interval=31536000 \
  --user-data-dir="$HOME/.config/eve3-kiosk" "http://127.0.0.1:${PORT}/" >/dev/null 2>&1
