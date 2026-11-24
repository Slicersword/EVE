# Parts, power and wiring reference

Source of truth: shipped `config/eve.json` and generated `firmware/eve_controller/eve_config.h`.
This documents the existing EVE pin contract; inspect actual board labels and voltage requirements before
connecting power. No electrical measurements or physical acceptance are supplied by this repository.

## Build inventory

| Item | Quantity | Details supported by the source |
|---|---:|---|
| Raspberry Pi 4B | 1 | Target: 2 GB RAM, 64-bit Bookworm; SSD storage supported |
| Touch display | 1 | 1024×600 HDMI display plus USB touch; exact power connection must be checked |
| Arduino Mega 2560 | 1 | USB serial, normally CH340 at /dev/ttyUSB0, 115200 baud |
| Wheel motors | 4 | Two motors per side; ratings and stall current must be measured |
| Dual-channel wheel drivers | 2 | Firmware uses TB6612-style STBY/AIN/BIN/PWM interface; verify actual boards |
| Pan/tilt geared stepper motors | 2 | Five-wire motors with matching ULN2003 pinout; exact model/rating not specified |
| ULN2003 stepper drivers | 2 | Four logic inputs per axis |
| GY-530 / VL53L0X ToF boards | 3 | Shared I2C; separate XSHUT control |
| MPU6050 tilt/IMU board | 1 | Same I2C bus; default address 0x68 |
| KY-033 digital cliff sensors | 3 | Digital output to Mega, individually calibrated |
| PIR presence sensor | 1 | Digital input to Mega |
| TTP223-style touch pads | 2 | Momentary active-high logic to Pi; confirm actual modules |
| Pi-compatible camera | 1 | picamera2 implementation; exact model/interface not specified |
| Camera activity LED | 1 | BCM25 control with appropriate current limiting/driver |
| Microphone / speakers / amplifier | Existing set | ALSA capture/playback; exact interface not specified |
| Independent 5 V USB power banks | 2 | Bank A Pi-side; Bank B actuator/audio-side; current capacity requires verification |
| Direct-powered cooling fans | Existing set | Pi fan; additional charger-side fan while charging |
| Chassis, switch/protection, leads, mounts | As fitted | Ratings, dimensions and quantities need inspection |

This repository does not supply CAD/STL files, a dimensioned chassis drawing, a PCB schematic or verified
part purchase links. No new hardware is required by the repository preparation.

## Power boundaries

- **Bank A:** Pi via its existing USB-C power path; display and Pi fan only if their combined load is verified.
- **Bank B:** wheel driver motor rails, stepper motor supply and audio branch, subject to measured load.
- Keep independent bank positive rails separate. Establish common ground between the relevant Pi/Mega,
  sensor and motor-driver logic grounds. Check that an existing board does not unintentionally backfeed USB.
- Wire driver logic supplies according to the identified board; logic supply and motor supply are distinct.
- Pi GPIO-connected signals must be compatible with 3.3 V logic. Verify module pull-ups/output levels;
  a board accepting 5 V on VIN does not prove every output is Pi-safe.
- Verify polarity, a working Bank B cutoff, protection arrangement and supply capacity before enabling actuators.
- INA219 is disabled. Battery state and automatic low-battery shutdown are unavailable. Never connect a raw
  3S pack to the 5 V paths described here.

## Pi GPIO / I2C wiring

Physical numbering refers to the Pi's 40-pin header. All runtime GPIO settings use **BCM** numbering.

| Function | BCM | Physical pin | Connection / expected behavior |
|---|---:|---:|---|
| Shared SDA | 2 | 3 | SDA of all three ToF boards and MPU6050 |
| Shared SCL | 3 | 5 | SCL of all three ToF boards and MPU6050 |
| 3.3 V sensor reference | — | 1 or 17 | Existing sensor VIN/VCC arrangement must be compatible; check board variant |
| Ground example | — | 6 | Common sensor/logic ground; other Pi GND pins also available |
| Front-left ToF XSHUT | 5 | 29 | Held low to disable; released as input to enable |
| Front-right ToF XSHUT | 6 | 31 | Held low to disable; released as input to enable |
| Rear ToF XSHUT | 13 | 33 | Held low to disable; released as input to enable |
| Head touch output | 27 | 13 | Active-high momentary input |
| Back touch output | 22 | 15 | Tap wakes/listens; one-second hold requests emergency stop |
| Camera activity LED | 25 | 22 | LED through suitable resistor/driver, never a bare high-current load |

XSHUT is deliberately never driven high by the Pi. The existing sensor board's own pull-up releases the
sensor. Verify this matches the actual breakout. Initially each ToF answers at 0x29; startup enables one
at a time and changes addresses to 0x30, 0x31, 0x32. A later standalone scan can differ after shutdown/reset.
The MPU6050 default is 0x68; AD0-high boards may use 0x69 (configure only after identification).

## Mega wheel-driver pins

Each side uses one dual-channel driver. A and B drive the two motors on that side.

| Driver signal | Left Mega D pin | Right Mega D pin |
|---|---:|---:|
| STBY | 8 | 9 |
| AIN1 | 22 | 26 |
| AIN2 | 23 | 27 |
| PWMA | 2 | 4 |
| BIN1 | 24 | 28 |
| BIN2 | 25 | 29 |
| PWMB | 3 | 5 |

Connect each motor to its driver's corresponding A/B motor outputs. Software sends one signed speed
per side, used for both motors. Confirm actual forward polarity during the lifted M07 test.
This is not an L298N wiring table; identify the fitted driver before applying the pin contract.

## Mega head and digital sensors

| Function | Mega D pins | Order |
|---|---|---|
| Pan ULN2003 IN1–IN4 | 30, 31, 32, 33 | Four-input half-step sequence |
| Tilt ULN2003 IN1–IN4 | 34, 35, 36, 37 | Four-input half-step sequence |
| PIR OUT | 38 | Presence |
| Cliff digital OUT | 39, 40, 41 | Front-left, rear-centre, front-right |

Keep stepper power on the verified external motor supply, not a GPIO output. Self-holding/geared motors
were selected for this robot; firmware releases coils after stopping. Physical load retention must be verified.
Manual centre marking is required; there is no automatic homing sensor.

## Sensor order matters

| Data | Index 0 | Index 1 | Index 2 |
|---|---|---|---|
| distance_mm / XSHUT / ToF address | Front-left | Front-right | Rear |
| cliff_raw / edge_level / Mega D pin | Front-left | Rear-centre | Front-right |

Do not copy ToF order into cliff calibration. Default range acceptance is 30–1000 mm. Forward obstruction
stopping uses the first two distance values; the rear value must still be valid/fresh. Reverse and pivot
remain disabled because the build has no verified all-direction cliff coverage.
