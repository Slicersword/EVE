# Build choices and unresolved specifications

Use this worksheet before buying parts or confirming commissioning. The software
defines interfaces and pins; component ratings and chassis geometry must match your build.
No hardware test or completed stage is assumed.

## Required hardware decisions

| Choice | Reference contract | Record before proceeding |
|---|---|---|
| Wheel drivers | Two TB6612FNG-compatible dual-channel boards with STBY/AIN/BIN/PWM | Exact manufacturer/module, logic supply, continuous/peak current and cooling |
| Four DC motors | N20 6 V / 100 RPM, one per channel, operated at 5 V | Exact variant's load/stall current, wheel diameter, mass and resulting speed/torque |
| Two head motors | 28BYJ-48 5 V with matching ULN2003/ULN2003A | Winding/connector order, bracket, load, safe travel, and unpowered retention |
| Power | Two regulated 5 V USB banks, shared logic ground; separate 9 V boost for audio | Printed per-port ratings, cable drop, actual peak/continuous current, protection and cutoff |
| Display | HDMI + USB-touch, target 1024×600 | Model, power input/load and mounting dimensions |
| Distance boards | Three VL53L0X breakouts with separate XSHUT | Breakout supply range, pull-ups/level shifting and safe XSHUT voltage |
| Tilt board | MPU6050 on Pi I2C | Module supply/logic ratings, AD0 state, fixed mounting and orientation |
| Cliff boards | Three KY-033 modules with a TCRT5000 and 74HC14D. Digital outputs go to Mega. | Record board labels, supply rating, final floor gap and each channel's measured floor and no-floor levels. |
| Touch | Two TTP233 modules | Exact suffix/jumper mode: direct/momentary active-high Q, 3.3 V-compatible |
| Camera | Camera Module 3, Pi 4 CSI ribbon and physical shutter | Cable orientation, indicator circuit and clearance |
| Microphones | Two INMP441 I2S modules | Opposite L/R slots, both-channel test, ALSA EVEINMP441/eve_mic setup and threshold |
| Amplifier | PAM8610 with added regulated 5 V-to-9 V boost, 4 Ω / 3 W speakers | Exact converter continuous/peak ratings and efficiency, bank input current, measured safe output limit |
| Structure | Four-wheel base with safe head retention | Dimensions, mass, fasteners, sensor placement and cable routing |

Stop at the relevant stage if a required rating is unknown. An L298N, bipolar stepper
driver, USB-only webcam or raw 3S pack needs an explicitly reviewed implementation;
renaming a configuration value does not provide compatibility.

The main build choice is **two 5 V power banks**, not the optional lithium packs.
INA219 remains disabled and unwired. A 20 A BMS does not define a charging system;
cell series count, matching charger, protection and a different power review would
all be needed before a later conversion. A buck is not the amplifier's boost converter.

## Private build record

Use the [progress notebook](PROGRESS.md) notes or a printed sheet. Fill this in with
actual labels and measurements; blank values mean unverified, not zero.

| Record | Your value / evidence |
|---|---|
| Bank A model, port rating, cable, loaded voltage/current | ____________________ |
| Bank B model, port rating, cable, combined peak/current | ____________________ |
| Audio boost model, input rating, measured 9 V load result | ____________________ |
| Driver-board manufacturer and continuous/current limits | ____________________ |
| N20 variant, current evidence, wheel diameter, robot mass | ____________________ |
| Display model and power/data wiring verified from its manual | ____________________ |
| ToF/IMU breakout supply and SDA/SCL pull-up rail | ____________________ |
| TCRT digital pin, height, each floor type, floor/edge values | ____________________ |
| TTP233 exact suffix, output mode and measured logic level | ____________________ |
| Mic left/right result, quiet/speech levels, VAD threshold | ____________________ |
| Amplifier volume/output limit for each speaker | ____________________ |
| Head centre marks, safe pan/tilt limits and retention result | ____________________ |
| Source revision, firmware ID, stopping distance and date | ____________________ |

Keep tokens, passwords, personal notes and identifying network details out of a
public repository. Website notes/export files are your private build record.

## Software and user preferences

| Option | Default / supported choice | How to adjust |
|---|---|---|
| OS | Pi OS Desktop 64-bit Bookworm / Python 3.11 | Validate newer OS or Pi hardware separately |
| Serial device | `/dev/ttyUSB0`, 115200 baud | Prefer the actual `/dev/serial/by-id/…` path; used by runtime and flasher |
| Language | English; English/Hindi/Marathi input supported | `robot.language`: `en`, `hi`, `mr` |
| Local timezone | UTC (offset 0) | `behavior.utc_offset_minutes`; e.g. 330 for India |
| Camera/tracking | Off | Enable after M08/M10 acceptance |
| Microphone capture | Off | Install local STT and calibrate at M13 |
| Overlapping speech and listening | Turn-taking | Optional local echo route in M13, after a successful acoustic test |
| Network | Loopback only | SSH tunnel, or explicit trusted-LAN mode |
| Local language model | Off; basic offline replies work alone | Separate on-Pi loopback server/model, with measured RAM/latency |
| Cloud | Off | Optional fixed public questions only |
| Reverse/pivot | Off | Requires additional coverage and a separate physical review |
| Website | GitHub Pages from main, independent of ChatGPT; separate offline build | Keep the public repository and Pages enabled |
| Project license | Not selected | Maintainer must choose before representing this as open-source licensed |

See [Configuration](CONFIGURATION.md) for practical changes. Copy this table into
a private record; do not publish personal network details, tokens or calibration logs.
