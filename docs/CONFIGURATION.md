# Configure your EVE

`config/eve.json` is the public default. `config/local.json` is an ignored, private
override. Keep shipped defaults unchanged so updates and default-state checks are predictable.
`config/local.example.json` demonstrates ordinary preferences without enabling actuators.

## Set one value at a time

Run commands on the Pi in your source directory, using the launcher installed at M00:

```bash
./eve cfg show
./eve cfg set robot.language mr
./eve cfg set behavior.utc_offset_minutes 330
./eve cfg set serial.port /dev/serial/by-id/YOUR_MEGA_DEVICE
```

Replace the last value with your actual Mega path from the firmware stage. Values
are parsed as JSON when possible: booleans are `true`/`false`, numbers need no quotes,
and a string with spaces needs shell quotes. Restart EVE after every configuration change.
The flasher and runtime use the same `serial.port`; no other attached board is selected silently.

Do not copy an example whole and mark it commissioned. Required confirmations
are recorded only after actual tests, using the relevant stage's commands.

## Settings that require a reflash

The Mega header is generated from actuator enable flags, wheel limits/timing,
head step bounds, heartbeat/lease timing, cliff calibration and Mega pins. A change
to those values changes the firmware fingerprint. Stop the runtime, disconnect
actuator power, regenerate/compile/upload using the setup guide, then verify the
matching fingerprint before any motion.

Language, timezone, Pi port, audio device, camera enable and network binding are
Pi-side settings and normally need a runtime restart only. The configuration tool
prints a reflash reminder when the generated firmware settings change.

## Choose safe values

- Pin assignments use **BCM** for Pi and **D pin numbers** for Mega. Duplicate pins,
  wrong PWM pins, unusable ToF addresses and malformed values are rejected.
- Serial baud is fixed at 115200 by the firmware. Sensor acceptance range is fixed
  at 30–1000 mm by the runtime; changing a decorative field cannot expand that range.
- Keep head limits inside physically measured safe travel. Software steps do not
  measure real angle and cannot detect a stall or slipped gear.
- The UTC offset is a fixed number of minutes. Daylight-saving transitions are not
  automatic; adjust the value when your local rules require it.
- All cloud calls, microphone capture, camera, tracking and web tools start disabled.
  Touch, speaking and explicit local memory start enabled.

## Optional features and rollback

Detailed commands for microphone selection, local models, camera tracking, trusted-LAN
control and SSH tunnelling are in [Software setup](SETUP_GUIDE.md). Change
one setting and test its result before continuing.

To undo an ordinary preference, set it back to the value in `config/eve.json` and
restart. To revoke physical readiness, first unconfirm the corresponding readiness
flag, then disable its firmware enable flag, restart/reflash and repeat the real
tests before enabling again. Do not delete `config/local.json` as a routine fix:
it may contain the only copy of your measured limits and calibration.
