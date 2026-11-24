# Daily use, maintenance and recovery

Use these steps after the relevant M00–M17 tests have passed on your own hardware.
The website checklist is a notebook; it is not an operating permit. Keep the actuator
cutoff within reach whenever motor power is on.

## Daily start

1. Keep motor power off. Inspect loose leads, obstructions, sensor windows, floor
   clearance, fan, wheels and head support. Open the camera shutter only if desired.
2. Place EVE on a flat, contained floor away from stairs, pets, children and breakables.
   Charge/check supplies using their makers' instructions; no battery level is reported.
3. Turn on Bank A. Log in to the Pi desktop for the face, or use the tested desktop
   auto-login arrangement. Wait for the foreground runtime or accepted user service.
4. In PuTTY, open your source folder and inspect status. All required sensors must
   have sensible fresh readings; Mega must be online and the fingerprint must match.
5. Make sure the head is at its marked centre before recording manual home. A reset
   or emergency stop can invalidate relative head position. Do not force a gearbox.
6. Switch on the actuator branch only after inspection. Start a short attended session,
   clear only resolved faults and home the head when appropriate. Never clear a latch
   simply because a command was refused.

On the Pi, with an already commissioned build and the runtime running:

```bash
cd "$HOME/eve3" || exit 1
./eve status
./eve ctl session_start minutes=5
./eve ctl clear
```

After safely aligning the head centre, only when head setup is accepted:

```bash
./eve ctl head_home confirm=true
```

A refused command should say why. Resolve that cause using the matching setup stage.
Do not issue movement as a daily readiness probe. A session expiring, serial loss,
sensor fault or emergency stop can prevent further movement and require investigation.

## Stop and shut down

- For an urgent mechanical problem, use the accessible actuator-power cutoff. Support
  the head if necessary; powered holding is not guaranteed. It removes motor power
  independently of the runtime.
- A back-pad hold requests emergency stop while the touch/runtime path is working.
  The CLI emergency stop also needs a live server/link to reach the controller.
- A voice stop needs a recognized utterance and cannot interrupt speech/transcription
  in this half-duplex implementation. It is an additional convenience.
- After a normal session, end the session, turn off the actuator branch and stop EVE.
  Shut the Pi down cleanly before removing Bank A or storage.

**PuTTY 2**

```bash
./eve ctl session_end
```

For a manual foreground run, Ctrl+C in PuTTY 1 stops the runtime. For the installed
user service, stop it before maintenance:

```bash
systemctl --user stop eve3.service
sudo shutdown -h now
```

Wait for shutdown to finish before disconnecting Pi power. Do not yank USB storage
while the Pi is writing. The amplifier must also be switched off using its accepted
power arrangement. Charge banks separately according to their instructions.

## Understand the status screen

| Status | Read it as |
|---|---|
| Mega online + firmware matches | Telemetry/heartbeat and configuration identity agree; this alone does not enable movement |
| Distance mm | Three distances in front-left, front-right, rear order; null is a fault/out-of-range, not zero |
| Tilt deg | Base orientation reading; a level base should be near zero |
| Cliff raw / unsafe | Three raw digital values and their calibrated interpretation in front-left, rear-centre, front-right order |
| Ages | Required streams must be fresh; a number left on screen is not proof that a sensor is still connected |
| Sensors say / LATCHED | Current condition and a remembered stop cause; remove the cause before clearing |
| Session | Remaining attended time; never saved as active through restart |
| Wheels / Head blocked | Named gate preventing movement; expected early in setup |
| Head homed / pan / tilt | Software-relative position, not measured absolute position |
| Features | Runtime startup/error states; still verify the physical device |
| Battery percent null | No INA219 or battery state measurement exists |

## Backup and restore

Keep two things: a recoverable copy of the code and a **private** copy of your local
configuration/data. GitHub contains public defaults, not your calibration, notes or
current progress. Stop EVE and the user service so SQLite is closed before copying.
Keep actuator power off throughout backup/recovery.

From your normal Pi login, with the runtime stopped:

```bash
cd "$HOME/eve3" || exit 1
umask 077
mkdir -p "$HOME/eve_private_backups"
backup_name="eve-state-$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
tar --exclude='data/sim' -czf "$HOME/eve_private_backups/$backup_name" config data
```

This includes public defaults, local overrides if present, stage/calibration records,
database and current control token. Treat the archive as private. Record the code
revision and dependency versions alongside it. It does not back up the OS, virtual
environment, downloaded models, desktop settings or boot/I2S configuration. Copy the
archive to another device; a second folder on the same storage is not disaster recovery.

Also retain your Pi OS image/version, `/boot/firmware/config.txt` and the generated
I2S overlay if used, the normal user's `.asoundrc`, and the source ZIP or Git checkout.
The microphone setup helper creates configuration backups before changes. Export
website progress separately using [My build progress](PROGRESS.md).

For recovery, extract a selected archive into a **separate temporary folder**, inspect
its contents, then restore chosen files only with the runtime stopped. Use a matching
source release and validate configuration. Run host checks, regenerate/reflash compiled
settings, reboot/reconfigure I2S if needed, and repeat the affected physical stages.
Do not import readiness flags into a different wiring/motor/head build as evidence of acceptance.
Starting EVE creates a new token; use that current token rather than an archived one.

## Updates and repeating tests

Use the update section of [Software setup](SETUP_GUIDE.md). Git installs use the
reviewed fast-forward helper, which preserves two update snapshots. ZIP installs
need a fresh source folder and deliberate private-state recovery. Read changes before
starting the robot; source backups do not install new dependencies or flash firmware.

| Changed item | Repeat at least |
|---|---|
| Power bank, lead, connector or protection | M03 measurements and loaded/thermal acceptance |
| Cliff module, position, floor type or trimmer | M04 calibration/reflash and M05/M07 stop tests |
| ToF/IMU board, wiring or mounting | M04 freshness/readings and M05 refusal tests |
| Motor, wheel, driver or firmware timing | M03 current, M05 stops and M07 lifted/contained tests |
| Head bracket, load, steps or cable | M08 centre/travel/retention; M10 tracking if enabled |
| Microphone, room noise or gain | M13 each channel, threshold, recognition and half-duplex test |
| Amplifier/speaker/supply | Electrical supply/output-limit acceptance and M13 audibility |
| Desktop, OS, service or network | M01/M16/M17 startup, authorized access and no motion after restart |

## Routine care

Check fasteners, wire abrasion, hot connectors, dust, optical windows, fan airflow and
sensor mounting. Keep records of measurements and changes in the private notebook.
Stop after unusual smell, heat, resets, jerking motion or recurring stale data. Fix the
cause before retrying; do not compensate with larger timeouts, voltage or readiness flags.
Consult [Troubleshooting](TROUBLESHOOTING.md) for symptom-specific checks.
