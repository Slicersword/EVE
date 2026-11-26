# Your EVE parts and connection map

This inventory uses the specified hardware. Quantities below are required by the
current code; inspect the actual board labels and ratings before wiring. No item
is presumed installed or tested. [Wire every part](WIRING.md) gives the complete
terminal-to-terminal connections, power branches, checks and manufacturer references.

## Core and user interface

| Part | Required quantity | Role / connection |
|---|---:|---|
| Raspberry Pi 4 Model B | 1 | Main runtime, I2C sensors, I2S microphones, camera and face |
| 64 GB+ A2 / High-Endurance microSD | 1 | Supported starting storage; image with Pi OS Desktop 64-bit Bookworm |
| 7-inch HDMI IPS touchscreen, 1024×600 | 1 | HDMI picture plus USB touch; confirm model's separate power requirements |
| Micro-HDMI-to-HDMI lead | 1 | Pi HDMI0 to display |
| USB touch data lead | 1 | Pi USB-A to display TOUCH port |
| Pi 4 thermal kit | 1 | Heatsink mounted without shorts or blocked airflow |
| Raspberry Pi cooling fan | 1 | Runs whenever the Pi has power. Match the supply to the fan's rating. |
| Arduino Mega 2560 | 1 | USB serial motor/digital sensor controller |
| USB-A-to-USB-B data cable | 1 | Pi to Mega; carries logic power and serial |
| TTP233 touch modules | 2 | Head and back; direct/momentary active-high Q output at Pi-safe voltage |

## Motors, sensors and audio

| Part | Required quantity | Role / condition |
|---|---:|---|
| N20 geared DC motors, 6 V / 100 RPM | 4 | One motor per H-bridge channel; 5 V rail derates speed/torque; stall current still needed |
| TB6612FNG dual H-bridge boards | 2 | Left pair and right pair; all channels occupied by wheels |
| 28BYJ-48 5 V steppers | 2 | Pan and tilt; verify connector sequence, head balance and unpowered retention |
| ULN2003 / ULN2003A stepper boards | 2 | Matching five-pin motor socket and four logic inputs per board |
| VL53L0X breakout boards | 3 | Front-left, front-right, rear distance; accessible XSHUT and Pi-safe I2C |
| KY-033 IR tracking / line-following modules (TCRT5000 + 74HC14D) | 3 | Downward-facing cliff detection at front-left, rear-centre and front-right. Digital outputs go to Mega D39, D40 and D41. |
| MPU6050 IMU breakout | 1 | Tilt sensing; fixed to the base, shared Pi I2C |
| HC-SR501 PIR | 1 | Presence input to Mega; identify labelled terminals |
| INMP441 I2S MEMS microphones | 2 | Shared clock/frame/data with opposite L/R slot selection |
| Raspberry Pi Camera Module 3 + Pi 4 ribbon | 1 | CSI/Picamera2; correct 15-pin cable |
| Physical camera shutter/cover | 1 | Independent image barrier |
| Camera activity LED + suitable resistor/driver | 1 circuit | Required by the camera procedure; verify this ancillary part is available |
| PAM8610 stereo amplifier board | 1 | Analogue input; needs its own 9 V boost branch from the 5 V bank |
| 4 Ω / 3 W full-range speakers | 2 for stereo | Separate bridged outputs; maximum output must be limited and verified |

## Power and mechanical items

| Part | Required quantity / status | Acceptance requirement |
|---|---|---|
| Regulated 5 V USB power banks | 2, main build | Bank A Pi/display/logic; Bank B motors/head/boost input; actual per-port current ratings needed |
| Regulated 5 V-to-9 V boost converter | 1, additional audio part | Documented continuous output, suitable input current and load-tested 9 V; see wiring guide |
| Actuator cutoff and branch protection | To measured load | Cuts wheel and stepper positive power independently of Pi software |
| Separate audio switch/protection | 1 branch | Lets amplifier be isolated while testing/rewiring |
| Wire/connectors/insulation/distribution | To measured load | Rated current, secure returns and strain relief; no motor current on breadboards |
| Chassis, wheels, motor/head brackets, standoffs | To selected geometry | No dimensioned CAD/STL supplied; record dimensions and safe travel |
| 20 A BMS, lithium packs, charger, buck converters | Optional future conversion | Not used by this two-bank guide; no charging circuit or battery monitoring is assumed |
| INA219 current sensors | Not used | Code/dependency disabled; leave unwired |

A BMS is not a charger. The BMS's 20 A label does not identify 2S/3S configuration
or approve its cells, charger, wiring or load. Complete a separate matched design
before any battery conversion. Raw battery voltage never connects to the 5 V rails.

## Signal map at a glance

| Subsystem | Controller and signals | Detailed connections |
|---|---|---|
| Left TB6612 | Mega STBY D8, AIN1/2 D22/23, PWMA D2, BIN1/2 D24/25, PWMB D3 | [Wheels](WIRING.md#wheel-drivers-and-four-motors) |
| Right TB6612 | Mega STBY D9, AIN1/2 D26/27, PWMA D4, BIN1/2 D28/29, PWMB D5 | [Wheels](WIRING.md#wheel-drivers-and-four-motors) |
| Pan / tilt ULN2003 | Pan IN1–4 D30/31/32/33; tilt D34/35/36/37 | [Head](WIRING.md#pan-and-tilt) |
| Cliff / PIR | Cliff D39/D40/D41; PIR D38 | [Cliff](WIRING.md#three-cliff-sensors) · [PIR](WIRING.md#presence-sensor) |
| ToF + MPU6050 | Pi SDA BCM2 physical 3; SCL BCM3 physical 5 | [Distance](WIRING.md#three-distance-sensors) · [Tilt](WIRING.md#tilt-sensor-mpu6050) |
| ToF XSHUT | BCM5/6/13 physical 29/31/33 | [Distance](WIRING.md#three-distance-sensors) |
| Touch head / back | BCM27/22 physical 13/15 | [Touch](WIRING.md#head-and-back-touch) |
| Two INMP441 | SCK BCM18 physical 12; WS BCM19 physical 35; SD BCM20 physical 38 | [Audio](WIRING.md#microphone-amplifier-and-speakers) |
| Camera LED | BCM25 physical 22, current-limited | [Camera](WIRING.md#camera-and-activity-led) |

Pi signals use **BCM** numbering; Mega signals use the printed **D** numbers.
Physical Pi pin 2 is 5 V, not BCM2/SDA. All grounds must provide a suitable reference
without routing motor current through delicate logic leads.

The pin contract is defined in `config/eve.json` and the generated
`firmware/eve_controller/eve_config.h`. Open **Source code** in the website menu to read either file. If a local
pin override is deliberately made, update the private wiring record and reflash
compiled changes before any motion. Shipped defaults stay locked.

Continue with [Assembly](ASSEMBLY.md), [every connection](WIRING.md), the
[inspection](WIRING.md#unpowered-inspection) and [Software setup](SETUP_GUIDE.md).
