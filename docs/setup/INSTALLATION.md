## Before M00: choose an installation route

Use a separate checkout if an older robot installation already exists. Keep the
motor supply off. The installer first runs the clone check with temporary state
and simulated hardware. It verifies the packaged 90 original WAVs, the web
routes and authenticated home commands before installing any system packages.
A failure at this point means stop and check that you have the complete Git
checkout or ZIP. A passing check still requires the physical M01–M17 tests.

Target: Raspberry Pi 4, Raspberry Pi OS Desktop 64-bit Bookworm, Python 3.11, a
working desktop login, SSH/PuTTY access and internet. Complete the Before you begin
page first. PuTTY opens a terminal; the desktop must also be running on the Pi for the face.

Keep the Bank B actuator branch off. Substitute your real Pi username/IP and ZIP path.
Labels such as **PuTTY 1** identify the window; they are not shell commands.

### Route A — clone the repository on the Pi

**PuTTY 1**

```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/Slicersword/EVE.git "$HOME/eve3"
cd "$HOME/eve3" || exit 1
bash scripts/setup_pi.sh
```

The clone refuses an occupied destination. Choose a fresh folder instead of
overwriting source or merging unknown files. The installer changes only required
system packages/settings, creates the virtual environment, and installs the AVR
toolchain; it does not upload firmware or start the robot.

Reconnect PuTTY once for the new groups to apply, then continue with M00.

### Route B — transfer GitHub's complete ZIP

Download **Code → Download ZIP** from the repository and save it as `EVE-main.zip`.
This is an alternative to Route A. Transfer it using WinSCP/SFTP, or PSCP installed
with PuTTY. For PSCP, replace the Windows path, username and address below.

**Windows PowerShell**

```powershell
pscp "C:\path\to\EVE-main.zip" PI_USER@PI_IP:EVE-main.zip
```

**PuTTY 1**

```bash
sudo apt-get update && sudo apt-get install -y unzip
```

```bash
bash <<'EVE_INSTALL'
set -euo pipefail
[ ! -e "$HOME/eve3" ] || { echo "STOP: choose a fresh destination; ~/eve3 already exists."; exit 1; }
stage_dir=$(mktemp -d)
trap 'rm -rf "$stage_dir"' EXIT
unzip -q "$HOME/EVE-main.zip" -d "$stage_dir"
[ -f "$stage_dir/EVE-main/eve3/runtime.py" ] || { echo "STOP: expected the complete GitHub ZIP."; exit 1; }
mv "$stage_dir/EVE-main" "$HOME/eve3"
cd "$HOME/eve3"
chmod +x eve scripts/*.sh tools/*.py
bash scripts/setup_pi.sh
EVE_INSTALL
```

Reconnect PuTTY, then continue with M00. ZIP installations have no Git history and
cannot use the automatic fast-forward update helper. Keep a private backup and
replace with a fresh full ZIP when updating.

### Select the Mega port before uploading (M02)

Leave motor power off. Identify the actual device; genuine Mega boards may use
`ttyACM`, while USB-serial clones may use `ttyUSB`. Prefer a persistent by-id path.

```bash
ls -l /dev/serial/by-id/ /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true
arduino-cli board list
```

If arduino-cli is not in PATH, use `"$HOME/bin/arduino-cli" board list`.
Set the actual device path, replacing the example:

```bash
./eve cfg set serial.port /dev/ttyUSB0
```

The flasher and runtime both honor this setting. Reconnect the same Mega USB cable
and verify permissions before repeating an upload.

### How the virtual environment works

The installer creates `.venv` with system-site-packages, so apt-installed Pi drivers
remain available. The EVE launcher selects `.venv/bin/python` automatically; you
do not need to activate it in each PuTTY window. System package/firmware tooling
uses the shell. Run the robot as your normal user, not root.

The installer targets Pi 4 / arm64 / Bookworm and stops early on another platform.
Camera/display packages are installed for the complete reference build even if
those features will be enabled at a later stage. Package installation requires
internet; host tests and the generated documentation work without hardware.
