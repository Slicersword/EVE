#!/usr/bin/env bash
# M00 - run once on the Pi (PuTTY) from the eve3 folder:   bash scripts/setup_pi.sh
# Installs packages, switches I2C on, creates .venv. Does NOT flash the Mega, move anything or start EVE.
set -euo pipefail
cd "$(dirname "$0")/.."
# Fail before package changes on an unsupported platform.
. /etc/os-release
[ "${VERSION_CODENAME:-}" = bookworm ] && [ "$(dpkg --print-architecture)" = arm64 ] \
  && grep -q 'Raspberry Pi 4' /proc/device-tree/model 2>/dev/null \
  || { echo "Target: Raspberry Pi 4, Raspberry Pi OS Desktop 64-bit Bookworm. See docs/GETTING_STARTED.md."; exit 1; }
[ "$(id -u)" -ne 0 ] || { echo "Run as your normal Pi user; the installer invokes sudo where needed."; exit 1; }
chmod +x eve scripts/*.sh tools/*.py 2>/dev/null || true
sudo apt-get update
sudo apt-get install -y python3-venv python3-dev python3-smbus2 python3-serial python3-gpiozero python3-lgpio python3-libgpiod \
  python3-picamera2 python3-opencv opencv-data i2c-tools raspi-utils espeak-ng alsa-utils g++ git cmake curl
sudo apt-get install -y chromium || sudo apt-get install -y chromium-browser
sudo raspi-config nonint do_i2c 0
python3 -m venv --system-site-packages .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
sudo usermod -aG i2c,dialout,gpio,video,audio "$USER"
if ! command -v arduino-cli >/dev/null && [ ! -x "$HOME/bin/arduino-cli" ]; then
  mkdir -p "$HOME/bin"
  installer=$(mktemp)
  trap 'rm -f "$installer"' EXIT
  curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/v1.3.1/install.sh -o "$installer"
  BINDIR="$HOME/bin" sh "$installer" 1.3.1
fi
ACLI="$(command -v arduino-cli || echo "$HOME/bin/arduino-cli")"
"$ACLI" core update-index
"$ACLI" core install arduino:avr@1.8.6
mkdir -p data && chmod 700 data
.venv/bin/python tools/doctor.py
echo
echo "Setup finished. Close PuTTY and log in again once (new groups), then:  cd ~/eve3 && ./eve stage M00"
