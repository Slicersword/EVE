## INMP441 I2S setup at M13

Complete the [two-microphone wiring](../WIRING.md#microphone-amplifier-and-speakers)
with power off. Mic 1 L/R is GND; Mic 2 L/R is 3.3 V. Both SD signals share BCM20;
BCM18 is SCK and BCM19 is WS. Keep Bank B actuator power off and stop EVE/service
before changing audio configuration. This profile targets Pi 4 Bookworm only.

The INMP441 has no I2C control address. It needs an ALSA I2S capture card before
`arecord` or the robot can hear it. The supplied capture-only Device Tree overlay
uses the kernel's passive ADAU7002 I2S endpoint; it does not require an ADAU7002 chip
or a downloaded third-party kernel driver. It creates a separate EVEINMP441 card
so the Pi analogue output can remain available for the PAM8610. This is a software
profile to be accepted on the actual hardware, not a claim of a completed microphone test.

**PuTTY 1 — EVE stopped**

```bash
cd "$HOME/eve3" || exit 1
sudo apt-get install -y device-tree-compiler
sudo python3 tools/setup_i2s_mic.py --boot
sudo reboot
```

The helper backs up boot configuration, compiles/installs eve-inmp441.dtbo and adds
one marked block under an all-model section. It refuses known conflicting I2S audio
overlays instead of replacing another device. If it stops, review the named overlay;
do not stack multiple audio devices on the same I2S pins. It does not start recording,
enable the microphone, change readiness flags or set playback defaults.

Reconnect PuTTY after reboot. As your normal Pi user, **without sudo**:

```bash
cd "$HOME/eve3" || exit 1
python3 tools/setup_i2s_mic.py --user-audio
arecord -l
arecord -L
```

Look for EVEINMP441 in the hardware list and eve_mic in the named device list. The
helper preserves the rest of ~/.asoundrc and adds only the named capture PCM, with
a backup if that file already exists. Its hardware stream is fixed to S32_LE,
48 kHz, 2 channels: 64 bit clocks per stereo frame. The plug layer averages the
two slots and converts to EVE's S16_LE, 16 kHz mono format. A plain hw device at
16-bit mono does not satisfy the microphone's clock/frame requirements.

First prove a native stereo stream opens for three seconds, discarding the audio:

```bash
arecord -D hw:CARD=EVEINMP441,DEV=0 -f S32_LE -r 48000 -c 2 -t raw -d 3 > /dev/null
./eve cfg set voice.capture_device eve_mic
./eve mic
```

No sample file is created by these tests. Follow the quiet and speech prompts;
record the suggested threshold. Repeat the speech test speaking close to each mic
in turn so a working second mic cannot conceal a disconnected first mic. If needed,
a stereo recording can be inspected privately using the temporary-RAM route below.
Do not enable voice capture until both microphones respond and speech is clearly
above quiet noise.

For a short optional **private audio test**, with the runtime stopped and the
accepted amplifier at low volume, the following records in /dev/shm and removes
its own clip on exit. This is a deliberate recording test, not a permanent log:

```bash
bash <<'EVE_MIC_TEST'
set -euo pipefail
clip=$(mktemp /dev/shm/eve-mic-check-XXXXXX.wav)
trap 'rm -f "$clip"' EXIT
arecord -D hw:CARD=EVEINMP441,DEV=0 -f S32_LE -r 48000 -c 2 -d 5 "$clip"
aplay "$clip"
EVE_MIC_TEST
```

Speak near Mic 1 for the first half, then Mic 2. Their opposite channel slots should
be audible in the expected left/right outputs. Do not run this playback through an
unverified amplifier or assume a mixed mono result proves both mics. If an input is
silent, power down and inspect L/R, SD, 3.3 V, ground and slot conflict first.

Select the Pi desktop's **Headphones / analogue** playback output, not HDMI. From
an SSH session in the same logged-in user's desktop environment, `pactl list short
sinks` lists outputs and `pactl set-default-sink ACTUAL_SINK_NAME` selects the actual
name; do not paste that placeholder literally. If pactl cannot reach a sound server,
use desktop audio settings or diagnose the user's audio session. Verify real sound
with the M13 speech commands and the amplifier's output limit before acceptance.

If boot audio breaks, keep actuator power off, remove only the marked EVE INMP441
block from /boot/firmware/config.txt using an editor, and reboot. Restore its printed
backup instead only if you have made no other settings changes since. Likewise
remove only the marked user-audio block, or review its backup, to undo ~/.asoundrc.
The generated overlay can remain unused; never delete unrelated audio settings.

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
replacement; do not overlay unknown local edits. Pi-side virtual environments and
downloaded models are not included in these source/state backups.

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
python3 tools/build_source_index.py
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
