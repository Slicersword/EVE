#!/usr/bin/env bash
# M02 - build the Mega firmware from the current config and upload it.
# BEFORE: stop EVE (Ctrl+C in PuTTY 1) and switch Bank B (motor power) OFF.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python; [ -x "$PY" ] || PY=python3
if "$PY" -c 'import sys; sys.path.insert(0,"tools"); from _common import eve_running; sys.exit(0 if eve_running() else 1)'; then
  echo "EVE is running. Stop it first (Ctrl+C in PuTTY 1)."; exit 1
fi
ACLI="$(command -v arduino-cli || echo "$HOME/bin/arduino-cli")"
[ -x "$ACLI" ] || { echo "arduino-cli not found: bash scripts/setup_pi.sh"; exit 1; }
PORT="$(ls /dev/serial/by-id/usb-1a86_* 2>/dev/null | head -n1 || true)"; PORT="${PORT:-/dev/ttyUSB0}"
[ -e "$PORT" ] || { echo "Mega not found on USB ($PORT). Check the cable."; exit 1; }
"$PY" tools/gen_header.py
"$ACLI" compile --fqbn arduino:avr:mega firmware/eve_controller
if [ "${1:-}" != "--yes" ]; then
  read -r -p "Bank B (motor power) is OFF and nothing can move? Type YES to upload to $PORT: " answer
  [ "$answer" = "YES" ] || { echo "Not uploaded."; exit 1; }
fi
"$ACLI" upload --fqbn arduino:avr:mega -p "$PORT" firmware/eve_controller
mkdir -p data
cp -f firmware/eve_controller/eve_config.h "data/eve_config.last_flashed.h"
echo
echo "Uploaded. Start EVE again (./eve run) - it must print: Firmware id ... matches."
