## Optional settings and daily operation

Use these after the relevant M-stage has passed. Any setting change needs a runtime restart; settings
compiled into the Mega also need a fresh flash while Bank B is off. EVE prints a reflash reminder.

### Owner command reference (PuTTY 2)

```bash
cd "$HOME/eve3" || exit 1
./eve stage
./eve status
./eve status full
./eve doctor
./eve cfg show
./eve ctl token
./eve ctl stop
./eve estop
./eve ctl session_end
```

The first commands inspect state. Normal stop ends motion; estop additionally latches. A clear request
never overrides an unsafe reading. Use the physical Bank B switch if software cannot stop the robot.

### Optional camera tracking (after M08 and M10)

```bash
./eve cfg set camera.allow_tracking true
```

Restart EVE, start a new session, clear and manually home before expecting head tracking.
For reversed look/tracking orientation, adjust the relevant sign after observing the real axis:

```bash
./eve cfg set camera.tracking_pan_sign -1
```

This does not change manual head_jog signs. Disable tracking again if it moves away from the face.

### Optional IMU orientation / address (M04)

Only use these after identifying an inverted board or an AD0-high address. They are alternatives to
correcting the physical orientation/address; do not apply both merely because tilt is missing.

```bash
./eve cfg set sensors.imu_inverted true
```

```bash
./eve cfg set sensors.imu_address 105
```

Restart EVE, then repeat level/tilt tests.

### Head limits (M08)

Read the safe pan/tilt positions reached by small observed jogs. The following values are the shipped
bounds, NOT measured limits for your robot. Replace them with your measured smaller safe bounds where
necessary; negative minimums and positive maximums are required.

```bash
./eve cfg set head.pan_min_steps -650
./eve cfg set head.pan_max_steps 650
./eve cfg set head.tilt_min_steps -260
./eve cfg set head.tilt_max_steps 260
```

Stop EVE, turn Bank B off, flash, restart, then repeat home/jog acceptance before confirming soft limits.

### Audio devices (M13)

With EVE stopped:

```bash
arecord -l
aplay -l
./eve mic
```

If the microphone is not the ALSA default, choose the actual capture device shown on your Pi. This is
an example only; substitute your identified card/device, then recalibrate the threshold.

```bash
./eve cfg set voice.capture_device plughw:1,0
```

### Optional local LLM (M12)

A separately installed on-Pi model server must provide the loopback chat endpoint in config.
No model or server is bundled; 2 GB Pi performance has not been validated. Basic offline replies need neither.
After the model server is running and tested locally:

```bash
./eve cfg set ai.local_llm.enabled true
```

Restart EVE. Disable it if memory/latency harms robot operation. Keep cloud disabled for the strict privacy rule.

### Optional phone control (M16)

Only on a trusted home network:

```bash
./eve cfg set network.host 0.0.0.0
```

Restart EVE and read its fresh token:

```bash
./eve ctl token
```

On your phone open http://PI_IP:8765/control and paste that token. Wrong token must not expose status
or permit a command. The HTML control shell itself is public; data and commands are protected.
This HTTP mode is not intended for Internet access. To return to Pi-only access:

```bash
./eve cfg set network.host 127.0.0.1
```

Restart EVE again.

### View control from Windows without RDP

Keep EVE bound to 127.0.0.1. In a separate **Windows PowerShell** session:

```powershell
ssh -N -L 8765:127.0.0.1:8765 PI_USER@PI_IP
```

Keep that session open. In the Windows browser visit http://127.0.0.1:8765/control, using the token read
from PuTTY. This forwards the Pi web UI; it does not mirror the Pi desktop. Continue using the kiosk
launcher to put the face on the robot's own display.

### Service management (after M17)

```bash
systemctl --user status eve3.service
journalctl --user -u eve3.service -n 50 --no-pager
systemctl --user stop eve3.service
```

Stop the service before foreground runs, I2C diagnosis or flashing. To restart after maintenance:

```bash
systemctl --user start eve3.service
```

To remove autostart:

```bash
bash scripts/install_service.sh --remove
```

### Update and keep the previous two backups

For a Git install, with motor power off and EVE/service stopped:

```bash
bash scripts/update_repo.sh
```

The helper refuses local tracked edits or a non-main branch, backs up source and owner data privately,
fetches main, uses a fast-forward merge, then runs checks. It does not install changed dependencies,
reflash or start EVE. Review CHANGELOG after updating. It retains the last two successful update snapshots
in ~/eve_backups. If checks fail it keeps the backup and stops for review; it does not silently reset files.
ZIP installs require their own saved copy of the current source plus config/local.json and data before
replacement; do not overlay unknown local edits. Pi-side virtual environments, downloaded models and old
install parking folders are not included in these source/state backups.

To preview a backup without restoring private state:

```bash
ls -lt "$HOME/eve_backups"
```

Choose a known good backup, extract into a separate recovery directory, inspect it and recover with the
runtime stopped. Reflash any restored compiled configuration before actuator use. Do not publish backups.

## Developer verification

On Linux (Python 3.10+, g++ for firmware-harness tests), from this repository root:

```bash
python3 -m unittest discover -s tests -t .
python3 tools/check_repo.py
python3 -m compileall -q eve3 tools tests
```

After editing recipes/stages:

```bash
python3 tools/stage.py guide > docs/SETUP_GUIDE.md
```

After editing compiled defaults:

```bash
python3 tools/gen_header.py
```

Target AVR compilation (no device upload):

```bash
arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli compile --fqbn arduino:avr:mega firmware/eve_controller
```

CI repeats the host verification and separately compiles the sketch for Mega. Host firmware tests may
skip when g++ is absent; install g++ before treating the full suite as verified.

### Simulation on a Linux computer

Simulation disables real serial, I2C, GPIO touch, camera, microphone, speaker and external AI requests.
It uses fake Mega/sensor objects and separate data/sim state. All normal commissioning gates remain.
It is a software exercise, never a way to confirm a physical M-stage. To run in one terminal:

```bash
./eve sim
```

In another terminal, from the same source folder:

```bash
EVE_SIM=1 ./eve status
EVE_SIM=1 ./eve ctl chat "who are you"
```

Do not set physical readiness flags to make simulation move. The automated tests already exercise
commissioned fake configurations in temporary test state. Ctrl+C stops the simulation.
