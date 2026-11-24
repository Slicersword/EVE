# Complete EVE build guide

This guide covers the existing EVE robot from parts inspection to final attended acceptance.
Software commands are consolidated in [Software setup](SETUP_GUIDE.md). Do not mark an item complete
because it is present in the source code. The baseline is the supplied EVE_SOURCE_V3 archive dated
23 November 2026; this repository does not import earlier calibration or commissioning records.

## 1. Scope and parts

Use the [parts and wiring reference](HARDWARE.md) to identify every board and connector. The exact
chassis dimensions, fastener sizes, motor ratings, battery capacities, display power load and microphone
interface were not included in the archive. Inspect the existing build and record those details before
replacement or replication. The list is a build inventory, not a verified shopping specification.

This build uses two independent 5 V USB power banks. A later two-3S-pack design with monitoring and
charging requires a separate electrical review and is not implemented here. INA219 stays disabled.
Cooling fans are directly powered; there is no software-controlled fan module.

## 2. Mechanical assembly

1. With all power unplugged, inspect the chassis, four motor mounts and wheel clearance. Secure the Pi,
   Mega and driver boards on insulated standoffs, with no exposed underside shorting to the chassis.
2. Secure the display for the intended 1024×600 landscape face. Keep display and USB leads strain-relieved.
3. Fit the geared pan/tilt steppers and their matching ULN2003 drivers. Leave enough cable slack throughout
   the proposed range. Use existing centre marks or add visible alignment marks for manual home.
   There are no homing switches in this software. Do not force a geared motor by hand.
4. Orient the three distance sensors as front-left, front-right and rear. Keep their optical windows clear.
5. Mount the three cliff sensors front-left, rear-centre and front-right. Their usable height depends on the
   real sensor, floor and adjustment. Establish it experimentally; the archive does not specify a valid height.
6. Fix the MPU6050 rigidly to the chassis. Record which face is up. Position PIR, head/back touch pads and
   camera/indicator where they can operate without obstruction.
7. Secure speakers and microphone with cable clearance and physical separation. The current software
   prevents self-listening by discarding microphone input during speech; it does not provide echo cancellation.
8. Keep the Bank B motor-power switch accessible. Provide cooling and charger-side fan airflow without
   cables touching a wheel, motor or fan. Inspect the original power protection arrangement.

## 3. Wire with power disconnected

Follow [HARDWARE.md](HARDWARE.md). Pi BCM GPIO numbers and Mega D-pin numbers are different namespaces.
Check board labels, signal voltage, polarity, continuity and common ground. Bank A and Bank B positive
rails remain separate; join only the grounds required by the signal connections. Do not power motors
or steppers from a Pi GPIO pin. Keep motor power off for initial firmware and sensor work.

The code describes pin assignments. It cannot verify your actual board variant, motor current,
regulator capacity, protection devices or electrical assembly.

## 4. Install and commission software

Open [Software setup](SETUP_GUIDE.md). Use two PuTTY windows: one owns the runtime, the other sends
commands. Installation offers Git clone and ZIP transfer routes. All commands use the installed virtual
environment through the EVE launcher unless the guide explicitly installs system packages.

| Stage | Acceptance |
|---|---|
| M00 | Fresh install, prior runtime parked, software tests pass |
| M01 | Face fills the Pi display without F11 |
| M02 | New Mega firmware compiled/uploaded; live telemetry and matching settings ID |
| M03 | Real bank voltage/current checks and stable Pi supply |
| M04 | All three distance sensors and tilt respond; cliff floor/edge calibration |
| M05 | Obstacle, cliff, tilt, stale-link and stop refusals observed |
| M06 | Direct-powered fans work and temperatures stay acceptable |
| M07 | Wheels tested on stable support, then in a contained area |
| M08 | Manual head home, small jogs, physical soft-limit validation |
| M09 | Touch response and back-hold emergency stop |
| M10 | Local camera, indicator and optional gated tracking |
| M11 | Explicit note save, persistence and erase |
| M12 | English/Hindi/Marathi offline replies |
| M13 | Speaker, local STT, wake phrase and stop phrase |
| M14 | Presence greetings, idle and night behavior |
| M15 | Timed reminder, once, including across restart |
| M16 | Sleep/wake and optional trusted-LAN phone control |
| M17 | 30-minute attended test, then service/face autostart and reboot check |

M04 is an open physical blocker: earlier I2C scans found no devices. A software rewrite cannot establish
that this wiring fault is repaired. Test the ToF sensors and MPU6050 on the robot before accepting motion.

## 5. Final acceptance and maintenance

The M17 test is an attended acceptance run, not proof of unattended autonomy. Observe supply, temperature,
sensor freshness, direction, head clearance and every stop path. After reboot, motion must remain blocked
until you begin a new session and clear. Preserve local settings/data in backups; never commit them.

For updates, use the backup-and-fast-forward procedure in Software setup. Firmware-setting changes require
regeneration, compilation, upload and a matching settings ID. Keep the previous two update backups.
