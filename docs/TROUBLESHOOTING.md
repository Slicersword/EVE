# Troubleshooting

All executable commands are in [Software setup and reference](SETUP_GUIDE.md). Start with its status,
doctor and stage instructions. Do not change commissioning flags to hide a failure.

| Symptom | Likely check / next step |
|---|---|
| Every I2C address absent | M04: stop runtime; diagnostics checks SDA/SCL idle, IMU with all ToF off, then each XSHUT individually |
| Tilt omitted from a scan | MPU6050 shares SDA/SCL; expect 0x68 or identified AD0-high 0x69; it is not an optional substitute for ToF |
| ToF stays at 0x29 with all XSHUT low | XSHUT missing/wrong pin or different breakout behavior; inspect one board at a time |
| All ToF still absent | Confirm sensor power/ground, physical pin 3 SDA and pin 5 SCL, and each XSHUT; inspect actual breakout voltage/pull-ups |
| Distance None / invalid | Missing device, measurement outside accepted 30–1000 mm, bus error or timeout; use objects in usable range |
| Tilt near 180 degrees | Sensor mounted upside down; confirm mounting then use imu_inverted in optional settings |
| 0-degree tilt | Valid when the robot is level; setup checks now accept zero |
| Cliff never flips | Height/floor/reflectivity/trimmer; each channel must be stable and differ between floor and no-floor; do not fabricate edge levels |
| Wheels lifted but blocked by cliff | Put safe targets under the cliff sensors within calibrated range; support wheels without bypassing sensors |
| Firmware mismatch | Local configuration changes affected generated header; stop, flash and restart, then compare settings IDs |
| Mega OFFLINE | USB cable/device permissions, exclusive port owner, reset settling, firmware, live heartbeat ACK and telemetry |
| Wrong serial device | Configure the port; CH340 by-id auto-discovery takes precedence when present |
| Session refused | M03 flags, live vcgencmd supply state, requested duration; measure real load |
| Supply flags nonzero | Investigate under-voltage/temperature; a clear current fault can leave historical bits until reboot; do not ignore recurrence |
| Wheels move wrong direction | Power off before changing motor leads; repeat lifted test; verify driver is compatible with the documented pin contract |
| No driver LEDs / head twitch | Check Bank B, common ground, matching ULN2003 motor connector and input order; do not raise speed to mask wiring |
| Head not homed | Align centre marks safely with power off; start session, clear, confirm manual home; repeat after Mega reset/estop |
| Head jog direction unexpected | Jog signs are mechanical/wiring convention; tracking sign settings only alter look/tracking requests |
| Face visible only on another PC | The kiosk command starts Chromium on the Pi desktop; PC localhost refers to the PC; optional SSH tunnel/LAN routes are in setup |
| Kiosk not fullscreen | Desktop session must exist; install Chromium and use kiosk launcher; no F11 required |
| Kiosk wrong port | Kiosk now loads merged local config; confirm the runtime and launcher use the same folder |
| Token unauthorized | Restart rotates token; CLI reads current local token automatically; use fresh token for phone control |
| Camera error | picamera2/camera connection, OpenCV cascade path, GPIO LED access; check indicator before camera acceptance |
| Microphone quiet / wrong device | ALSA device, threshold calibration, capture enable and installed whisper model; see M13 |
| Does not hear during speech | Expected half-duplex behavior; echo cancellation is unfinished |
| No general answers | Offline brain covers fixed intents/basic replies; optional local LLM requires a separate running server |
| Reminders do not speak | Runtime must be running; verify pending reminder, TTS queue, audio branch and actual output |
| Already running | Another PuTTY instance or user service owns the runtime lock; stop that instance before diagnostics/flashing |
| Old robot conflicts | Preview retire_old before applying; inspect remaining old service names/processes manually; it only covers known legacy names |

## Preserve evidence

Before asking for help, identify the current stage, expected and observed behavior, a short sanitized
status/doctor excerpt and whether the physical motor power was on. Never share API tokens, cloud keys,
private notes, raw family recordings or your full local configuration unreviewed.

## Recovery

The old-install parking script moves known old folders to a dated directory; it does not delete them.
Updates preserve the last two explicit backups using the software guide procedure. Revert only from your
own verified copy, with runtime stopped and motor power off. Configuration/calibration changes may require
reflashing matching firmware. Never restore readiness flags merely because a previous robot/version had them.
