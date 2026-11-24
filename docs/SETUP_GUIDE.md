# EVE V3 - software setup, testing and calibration

Generated from tools/stage.py (`./eve stage guide`). On the Pi everything lives in `~/eve3`.
Two PuTTY windows: **PuTTY 1** runs EVE (`./eve run`, Ctrl+C stops safely), **PuTTY 2** is for commands.
Replace `PI_IP` with the Pi's address. For each stage: run the commands, then `./eve stage Mxx`, do the test yourself, then `./eve stage Mxx done`.

Rules: stages in order, never skip. Bank B stays OFF until M07 except for the attended electrical measurements at M03. A software PASS is not a physical test. The Bank B switch is the physical motor-power stop; software stop needs a working runtime/link.

## Before M00: choose an installation route

Target: 64-bit Raspberry Pi Bookworm with a working desktop login, SSH/PuTTY access and internet.
The desktop must be running on the Pi for the face kiosk; PuTTY alone does not create a desktop session.
Keep Bank B off. Substitute your real Pi login/IP and local ZIP path. Do not paste window labels or prose.
If an existing ~/eve3 folder is present, preserve it and choose a new installation folder; these routes
refuse to overwrite it. Do not mix this V3 tree into an old EVE_SOURCE directory.

### Route A — clone this repository on the Pi

**PuTTY 1**

```bash
sudo apt-get update && sudo apt-get install -y git
```

```bash
git clone https://github.com/Slicersword/EVE.git "$HOME/eve3" && cd "$HOME/eve3" && bash scripts/retire_old.sh
```

If the repository is private, use GitHub's supported authenticated clone flow. Do not paste credentials
into a clone URL or this chat. Preview the old folders/services listed above before parking them.
Only after confirming this is the intended old installation:

```bash
cd "$HOME/eve3" && bash scripts/retire_old.sh --yes && bash scripts/setup_pi.sh
```

Reconnect PuTTY, then continue with M00 below.

### Route B — transfer the complete ZIP from Windows

Download EVE_complete_build.zip from the provided deliverable, or GitHub's Code → Download ZIP.
The extraction below accepts EVE/, EVE-main/ or the original EVE_SOURCE_V3/ archive root.
This is an alternative to Route A, not an extra installation step.

**Windows PowerShell**

```powershell
pscp "C:\path\to\EVE_complete_build.zip" PI_USER@PI_IP:EVE_complete_build.zip
```

**PuTTY 1**

```bash
sudo apt-get update && sudo apt-get install -y unzip
```

```bash
bash <<'EVE_INSTALL'
set -euo pipefail
if [ -e "$HOME/eve3" ]; then
  echo "STOP: ~/eve3 exists. Preserve it and choose a fresh installation folder."
  exit 1
fi
stage_dir=$(mktemp -d)
trap 'rm -rf "$stage_dir"' EXIT
unzip -q "$HOME/EVE_complete_build.zip" -d "$stage_dir"
source_dir=""
for candidate in EVE EVE-main EVE_SOURCE_V3; do
  if [ -f "$stage_dir/$candidate/eve3/runtime.py" ]; then
    source_dir="$stage_dir/$candidate"
    break
  fi
done
[ -n "$source_dir" ] || { echo "STOP: expected EVE source folder not found in ZIP"; exit 1; }
mv "$source_dir" "$HOME/eve3"
cd "$HOME/eve3"
chmod +x eve scripts/*.sh tools/*.py
bash scripts/retire_old.sh
EVE_INSTALL
```

Review the parking preview, then:

```bash
cd "$HOME/eve3" && bash scripts/retire_old.sh --yes && bash scripts/setup_pi.sh
```

Reconnect PuTTY, then continue with M00. The original V3 ZIP does not contain the new repository docs/fixes;
use the complete repository ZIP for this version. ZIP installs do not have Git history or support git pull;
use the Git route for ongoing source updates.

### How the virtual environment works

The package installer creates .venv with system-site-packages, so apt-installed Pi drivers remain available.
The EVE launcher selects .venv/bin/python automatically. You do not need to activate it in each PuTTY window.
System package/firmware tooling uses the system shell; do not run the robot as root. A group change requires
logging out and back in; that is why M00 includes reconnecting PuTTY.

## M00 - Foundation: install, old EVE parked, self-tests

Choose ONE installation route in the installation section below. Use a fresh ~/eve3 folder; keep Bank B off. After the chosen route finishes, reconnect PuTTY once to apply the new groups.

**PuTTY 1**

```bash
cd "$HOME/eve3" || exit 1
./eve doctor
./eve stage M00
```

Automatic checks (`./eve stage M00`): config loads and is valid; virtual environment exists; all software self-tests pass (takes ~30 s).

**Your test:** Bank B (motor power) stays OFF for M00-M02. `./eve doctor` shows PASS for config, venv and Python. The old EVE no longer starts (its folders are parked in ~/eva_old_<date>).

Then: `./eve stage M00 done`

## M01 - Face on the screen

Needs: M00 done.

**PuTTY 1**

```bash
cd "$HOME/eve3" || exit 1
./eve run
```

**PuTTY 2**

```bash
cd "$HOME/eve3" || exit 1
./eve face
./eve ctl expression name=happy
sleep 6
./eve ctl say "Hello"
```

Automatic checks (`./eve stage M01`): EVE is running and answers.

**Your test:** The 7-inch screen shows only two eyes and a mouth on black, filling the whole screen - no window frame, no outline, no buttons, no keyboard needed. The eyes blink. `expression name=happy` changes the face for 5 s.

Then: `./eve stage M01 done`

## M02 - Mega link + new firmware

Needs: M01 done.

Stop EVE with Ctrl+C in PuTTY 1. Keep Bank B off. Flashing is performed FROM THE PI over its USB cable to the Mega; no separate Windows Arduino upload is needed.

**PuTTY 1**

```bash
cd "$HOME/eve3" || exit 1
./eve flash && ./eve run
```

**PuTTY 2**

```bash
cd "$HOME/eve3" || exit 1
./eve status
```

Automatic checks (`./eve stage M02`): Mega connected; Mega online (heartbeat + telemetry); firmware matches this config; firmware has wheels and head disabled.

**Your test:** PuTTY 1 prints `Mega connected. Firmware id ... matches.` `./eve status` shows Mega online and `Cliff raw` with three 0/1 numbers. Pull the Mega USB plug: within 1 s status says OFFLINE; plug in: it comes back by itself.

Then: `./eve stage M02 done`

## M03 - Power: two USB banks measured

Needs: M02 done.

**PuTTY 2**

```bash
vcgencmd get_throttled
vcgencmd measure_temp
```

Carry out the power and current measurements described in Your test BEFORE confirming any flag. Switch Bank B on only for these attended electrical measurements, then off again. The firmware still has both actuators disabled.

**PuTTY 2**

```bash
./eve cfg confirm power_a_verified
./eve cfg confirm power_b_verified
./eve cfg confirm motor_current_verified
```

Stop EVE with Ctrl+C in PuTTY 1, then restart to load your confirmations.

**PuTTY 1**

```bash
./eve run
```

**PuTTY 2**

```bash
./eve ctl session_start minutes=1
./eve status
```

Automatic checks (`./eve stage M03`): Pi supply flags readable and zero; Bank A confirmed by you; Bank B confirmed by you; motor current confirmed by you.

**Your test:** 1) Bank A alone powers Pi + screen + fan for 10 min with the face running: `vcgencmd get_throttled` stays `throttled=0x0`. 2) Bank B: with a multimeter check 5 V polarity at the motor-driver and head-driver power pins, that the switch cuts it, and that Bank B GND is joined to Mega/Pi GND. 3) Bank B does not switch itself off with all motor boards connected and idle. 4) Independently measure/verify the combined motor, head and audio load against Bank B and driver/wiring ratings using a controlled electrical test with the chassis secured. Idle voltage alone is not a current test. If load/current verification is unavailable, leave motor_current_verified false and stop. Only then confirm the three flags. After restart `session_start` answers OK.

Then: `./eve stage M03 done`

## M04 - Sensors: 3 distance + tilt + 3 cliff

Needs: M03 done.

Stop EVE with Ctrl+C in PuTTY 1. Keep Bank B off. Fix wiring until diagnostics report all four I2C devices. Releasing XSHUT changes bus addresses; only one process may own the sensors.

**PuTTY 1**

```bash
./eve i2c
```

After all four devices answer, start EVE.

**PuTTY 1**

```bash
./eve run
```

**PuTTY 2**

```bash
./eve status
```

Keep actuator power disconnected. Securely support the robot; never put it at an uncontrolled edge. Capture floor readings with all three cliff sensors over the normal floor.

**PuTTY 2**

```bash
./eve cliff floor
```

While securely holding/supporting the robot, expose all three cliff sensors to a drop/no floor and capture edge readings. Each sensor must give steady values and flip between floor and edge.

**PuTTY 2**

```bash
./eve cliff edge
./eve cliff apply
```

Stop EVE with Ctrl+C in PuTTY 1. Keep Bank B off; reflash the changed cliff calibration.

**PuTTY 1**

```bash
./eve flash && ./eve run
```

Automatic checks (`./eve stage M04`): distance sensors all give numbers; tilt sensor gives a number; robot standing level (tilt under 10 degrees); sensor data is fresh; cliff sensors calibrated; no cliff seen while standing on the floor.

**Your test:** `./eve status`: Distance shows three numbers 30-1000 that change when you move your hand in front of each sensor (order: front-left, front-right, rear). Tilt is near 0 on the floor and rises when you tip the robot. Cliff raw flips for each sensor when you lift that corner over an edge.

Then: `./eve stage M04 done`

## M05 - Safety: it must refuse when anything is wrong

Needs: M04 done.

**PuTTY 2**

```bash
./eve ctl session_start minutes=5
./eve ctl clear
./eve status
watch -n 0.5 ./eve status
```

Ctrl+C stops watch. Perform each refusal test described below, then clear only after fixing its cause.

Automatic checks (`./eve stage M05`): wheels are blocked (nothing is commissioned to move yet); a reason is always given.

**Your test:** `Wheels:` stays blocked (nothing is commissioned to move yet) - that is correct. Watch the line `Sensors say:`. It must read `all clear` when the robot stands free on the floor, and change within half a second to: (a) `obstacle` with a hand 10 cm in front; (b) `cliff` when a corner is lifted over an edge (Mega latched=True); (c) `tilt` when tipped past ~30 degrees; (d) `...stale or missing` when the Mega USB is pulled (and Mega OFFLINE). (e) `./eve estop` shows LATCHED: emergency stop. After each, `./eve ctl clear` succeeds only when the cause is gone.

Then: `./eve stage M05 done`

## M06 - Cooling (physical check)

Needs: M05 done.

**PuTTY 2**

```bash
vcgencmd measure_temp
```

Automatic checks (`./eve stage M06`): Pi temperature below 75 C.

**Your test:** The Pi fan spins whenever the Pi is on. After 15 min with the face running the temperature stays under 70 C. The charger-side fan runs while charging. No software controls the fans.

Then: `./eve stage M06 done`

## M07 - Wheels (lifted first)

Needs: M06 done.

**PuTTY 2**

```bash
./eve cfg set firmware.drive_enabled true
./eve cfg confirm contained_ground_area
```

Stop EVE with Ctrl+C in PuTTY 1. Bank B must be off while flashing.

**PuTTY 1**

```bash
./eve flash && ./eve run
```

Use a stable support with all four wheels free AND all cliff sensors viewing a safe floor target within their calibrated range. If that arrangement is not possible, stop and improve the support. Do not bypass a cliff check. Switch Bank B on; keep your hand at its physical switch.

**PuTTY 2**

```bash
./eve ctl session_start minutes=10
./eve ctl clear
./eve ctl drive_test left=60 right=60 wheels_lifted=true
./eve ctl drive_test left=40 right=70 wheels_lifted=true
```

Do all stopping/direction tests below BEFORE confirming drive. Default max duration is one second in drive_test.

**PuTTY 2**

```bash
./eve cfg confirm drive_verified
```

Stop EVE with Ctrl+C and restart to load the flag. For the floor test, place the robot in the contained area, start a new attended session, then clear.

**PuTTY 1**

```bash
./eve run
```

**PuTTY 2**

```bash
./eve ctl session_start minutes=5
./eve ctl clear
./eve ctl drive left=100 right=100 seconds=1
```

Automatic checks (`./eve stage M07`): firmware.drive_enabled is on; safe test area confirmed; firmware matches; drive confirmed by you (after the test below).

**Your test:** Each drive_test turns all four wheels FORWARD for 1 second and stops by itself. If a wheel turns backward, switch everything off and swap that motor's two wires. During a test: `./eve estop` stops at once; covering a front distance sensor with your hand stops it; putting a finger under a cliff sensor is NOT a test - instead lift the robot so a cliff sensor sees no floor: it stops and latches. Reverse and pivot are refused. Only after that: confirm drive_verified, then try `./eve ctl drive left=100 right=100 seconds=1` on the floor in the closed area.

Then: `./eve stage M07 done`

## M08 - Head pan / tilt

Needs: M07 done.

**PuTTY 2**

```bash
./eve cfg set firmware.head_enabled true
```

Stop EVE with Ctrl+C in PuTTY 1. Bank B off during upload. With motor power off, carefully align the head centre marks without forcing the gearbox.

**PuTTY 1**

```bash
./eve flash && ./eve run
```

Switch Bank B on with all sensors safe and the wheels stationary.

**PuTTY 2**

```bash
./eve ctl session_start minutes=10
./eve ctl clear
./eve ctl head_home confirm=true
./eve ctl head_jog pan=8 confirm=true
```

Wait for each jog to finish, inspect cable clearance, then repeat as required. Use pan=-8, tilt=8 or tilt=-8 for the other directions. Note safe position values. If limits need reducing, use the optional settings section; stop, reflash and restart before continuing. Never increase the shipped limits without physical validation.

**PuTTY 2**

```bash
./eve cfg set head.soft_limits_verified true
./eve cfg confirm head_verified
```

Stop EVE with Ctrl+C and restart to load the confirmations. Reflash first if you changed pan/tilt limits. Start a new session, clear, and set manual home again after every restart/reflash that resets the Mega.

**PuTTY 1**

```bash
./eve run
```

**PuTTY 2**

```bash
./eve ctl session_start minutes=10
./eve ctl clear
./eve ctl head_home confirm=true
./eve ctl head_look direction=left
./eve ctl head_look direction=center
```

Automatic checks (`./eve stage M08`): firmware.head_enabled is on; firmware matches; head limits confirmed; head confirmed by you.

**Your test:** Each jog moves the head a tiny step in the expected direction (if pan or tilt goes the wrong way note it; camera.tracking_pan_sign / tracking_tilt_sign affect look/tracking only, not manual jog direction). Jog step by step to each side and stop BEFORE anything touches or a cable pulls; note the pan/tilt numbers from `./eve status` and set the limits a little inside them. After confirming: `./eve ctl head_look direction=left` and `direction=center` move smoothly.

Then: `./eve stage M08 done`

## M09 - Touch pads

Needs: M08 done.

**PuTTY 2**

```bash
watch -n 0.5 ./eve status
```

Automatic checks (`./eve stage M09`): touch pads started.

**Your test:** Pat the head pad: the face turns pink/happy for 3 s. Tap the back pad: listening face. Hold the back pad 1 second: EMERGENCY STOP appears in PuTTY 1 and status shows latched.

Then: `./eve stage M09 done`

## M10 - Camera (local only)

Needs: M09 done.

**PuTTY 2**

```bash
./eve cfg set camera.enabled true
```

Stop EVE with Ctrl+C and restart.

**PuTTY 1**

```bash
./eve run
```

**PuTTY 2**

```bash
./eve status
```

Head tracking is optional; see the optional settings section after completing the camera test.

Automatic checks (`./eve stage M10`): camera switched on in config; camera running.

**Your test:** The LED next to the camera is ON whenever the camera runs and OFF when EVE stops. When you stand in front, the eyes on the screen follow you. Closing the shutter: eyes stop following. No picture file appears anywhere (`find ~/eve3/data -type f` shows only eve.db, token, lock, json). With tracking on (in a session, head homed) the head turns slowly toward your face.

Then: `./eve stage M10 done`

## M11 - Memory

Needs: M10 done.

**PuTTY 2**

```bash
./eve ctl chat "remember that the keys are in the drawer"
```

Restart EVE once, then check persistence before the erase test. This erases ALL notes and reminders; use only disposable test data.

**PuTTY 2**

```bash
./eve ctl chat "what do you remember"
./eve ctl notes
./eve ctl erase_memory confirm=true
./eve ctl notes
```

Automatic checks (`./eve stage M11`): memory on.

**Your test:** She repeats the note back, `notes` lists it, and after erase the list is empty. Restart EVE between saving and asking once: the note is still there.

Then: `./eve stage M11 done`

## M12 - Brain: offline answers (+ optional on-Pi model)

Needs: M11 done.

**PuTTY 2**

```bash
./eve ctl chat "who are you"
./eve ctl chat "किती वाजले"
./eve ctl chat "एक चुटकुला सुनाओ"
./eve ctl chat "tell me a story"
```

Optional local models need a separately installed on-Pi llama-server and model. They are not bundled or required; keep cloud AI off.

Automatic checks (`./eve stage M12`): answers a question.

**Your test:** She answers in the language you used (English, Hindi, Marathi). Unknown questions get an honest "I did not understand" unless the optional local model is running. Cloud AI stays off.

Then: `./eve stage M12 done`

## M13 - Voice: speaking and hearing

Needs: M12 done.

**PuTTY 2**

```bash
./eve ctl say "Hello, I am EVE"
./eve ctl say "नमस्ते" lang=hi
./eve ctl say "नमस्कार" lang=mr
```

Stop EVE with Ctrl+C in PuTTY 1. The first voice install requires internet and downloads whisper.cpp and its model.

**PuTTY 1**

```bash
bash scripts/install_voice.sh && ./eve mic
```

Apply the threshold command printed by the microphone tool. Change the capture device if the default is wrong; see optional settings.

**PuTTY 2**

```bash
./eve cfg set voice.capture_enabled true
```

**PuTTY 1**

```bash
./eve run
```

Automatic checks (`./eve stage M13`): speaker has no error; whisper installed; microphone switched on in config; microphone listening.

**Your test:** You hear all three sentences clearly from the speakers (Bank B audio branch on). Then say "EVE, what time is it?" - she answers within a few seconds. Say "EVE" ... "tell me a joke". Say "stop" without her name: she says Stopped. While she talks she does not answer herself.

Then: `./eve stage M13 done`

## M14 - Behaviour

Needs: M13 done.

**PuTTY 2**

```bash
watch -n 0.5 ./eve status
```

Automatic checks (`./eve stage M14`): behaviour on.

**Your test:** Leave the room for a minute and walk back in: PIR shows True and she greets once (not again for 10 minutes; silent between 22:00 and 07:00). A hand closer than 30 cm gives a surprised face. After 15 quiet minutes the face goes sleepy; a touch or her name wakes her.

Then: `./eve stage M14 done`

## M15 - Reminders

Needs: M14 done.

**PuTTY 2**

```bash
./eve ctl chat "remind me in 1 minute to drink water"
./eve ctl reminders
```

Automatic checks (`./eve stage M15`): can list reminders.

**Your test:** After one minute she says the reminder aloud, once. A reminder set before a restart still fires after it.

Then: `./eve stage M15 done`

## M16 - Extras: sleep, phone control page

Needs: M15 done.

**PuTTY 2**

```bash
./eve ctl chat "go to sleep"
sleep 5
./eve ctl chat "wake up"
```

Phone control on the trusted home network is optional; see optional settings. Keep the default loopback address if you only need the Pi screen and PuTTY.

Automatic checks (`./eve stage M16`): web tools are off unless you chose otherwise.

**Your test:** Sleep gives the sleepy face and wake brings her back. If you enabled the control page: it shows live status, the red EMERGENCY STOP works, and a wrong token shows no data. Leave network.host at 127.0.0.1 if you do not need phone control.

Then: `./eve stage M16 done`

## M17 - Whole robot + start at boot

Needs: M16 done.

**PuTTY 2**

```bash
./eve ctl session_start minutes=30
./eve ctl clear
```

Run the 30-minute attended acceptance test below. Only after it passes, stop EVE with Ctrl+C in PuTTY 1 and install autostart. Bank B off for the reboot.

**PuTTY 1**

```bash
bash scripts/install_service.sh
```

**PuTTY 2**

```bash
sudo reboot
```

Reconnect PuTTY, verify the face and runtime start, then run ./eve stage M17. No motion is permitted until a fresh attended session and clear.

Automatic checks (`./eve stage M17`): everything commissioned; firmware matches; all sensors healthy.

**Your test:** During the 30 minutes: no under-voltage (`Pi supply flags 0x0`), STOP works by voice, back-pad hold and `./eve estop`; she never drives after the session ends. After the reboot the face and EVE come up by themselves and nothing moves until you start a session and clear.

Then: `./eve stage M17 done`

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
