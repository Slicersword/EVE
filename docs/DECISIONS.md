# Build choices and unresolved specifications

Use this worksheet before buying parts or confirming commissioning. The software
defines interfaces and pins; component ratings and chassis geometry must match your build.
No hardware test or completed stage is assumed.

## Required hardware decisions

| Choice | Reference contract | Record before proceeding |
|---|---|---|
| Wheel drivers | Two TB6612FNG-compatible dual-channel boards with STBY/AIN/BIN/PWM | Exact manufacturer/module, logic supply, continuous/peak current and cooling |
| Four DC motors | Matched geared motors, one per channel, suitable for regulated 5 V rail | Model, rated voltage, load/stall current, gear ratio, wheel diameter and mass |
| Two head motors | 5-wire 5 V unipolar geared steppers with matching ULN2003 | Winding/connector order, bracket, load, safe travel, and unpowered retention |
| Power | Independent regulated 5 V Bank A and Bank B, shared logic ground | Output ratings, cable drop, actual peak/continuous current, protection and cutoff |
| Display | HDMI + USB-touch, target 1024×600 | Model, power input/load and mounting dimensions |
| Distance boards | Three VL53L0X breakouts with separate XSHUT | Breakout supply range, pull-ups/level shifting and safe XSHUT voltage |
| Tilt board | MPU6050 on Pi I2C | Module supply/logic ratings, AD0 state, fixed mounting and orientation |
| Cliff boards | Three digital KY-033 outputs to Mega | Supply/output polarity, final height and tests on each intended floor |
| Camera | Picamera2-supported CSI camera | Model, cable orientation, indicator circuit and clearance |
| Audio | ALSA input/output; amplifier powered from verified audio branch | Device identifiers, supply/current and sound level |
| Structure | Four-wheel base with safe head retention | Dimensions, mass, fasteners, sensor placement and cable routing |

Stop at the relevant stage if a required rating is unknown. An L298N, bipolar stepper
driver, USB-only webcam or raw 3S pack needs an explicitly reviewed implementation;
renaming a configuration value does not provide compatibility.

## Software and user preferences

| Option | Default / supported choice | How to adjust |
|---|---|---|
| OS | Pi OS Desktop 64-bit Bookworm / Python 3.11 | Validate newer OS or Pi hardware separately |
| Serial device | `/dev/ttyUSB0`, 115200 baud | Prefer the actual `/dev/serial/by-id/…` path; used by runtime and flasher |
| Language | English; English/Hindi/Marathi input supported | `robot.language`: `en`, `hi`, `mr` |
| Local timezone | UTC (offset 0) | `behavior.utc_offset_minutes`; e.g. 330 for India |
| Camera/tracking | Off | Enable after M08/M10 acceptance |
| Microphone capture | Off | Install local STT and calibrate at M13 |
| Network | Loopback only | SSH tunnel, or explicit trusted-LAN mode |
| Local language model | Off; basic offline replies work alone | Separate on-Pi loopback server/model, with measured RAM/latency |
| Cloud | Off | Keep off for private operation; regex redaction is incomplete |
| Reverse/pivot | Off | Requires additional coverage and a separate physical review |
| Website | GitHub Pages from main, independent of ChatGPT; separate offline build | Keep the public repository and Pages enabled |
| Project license | Not selected | Maintainer must choose before representing this as open-source licensed |

See [Configuration](CONFIGURATION.md) for practical changes. Copy this table into
a private record; do not publish personal network details, tokens or calibration logs.
