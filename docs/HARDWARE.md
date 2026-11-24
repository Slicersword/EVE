# Parts, power and wiring reference

Source of truth: shipped `config/eve.json` and generated `firmware/eve_controller/eve_config.h`.
This documents the reference EVE pin contract; inspect actual board labels and voltage requirements before
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
| Microphone / speakers / amplifier | 1 input, 1 output set | ALSA capture/playback; choose supported devices and verify their power requirements |
| Independent 5 V USB power banks | 2 | Bank A Pi-side; Bank B actuator/audio-side; current capacity requires verification |
| Direct-powered cooling fans | As needed | Pi fan; any charger-side fan wired according to charger instructions |
| Chassis, switch/protection, leads, mounts | To suit dimensions/load | Record ratings, dimensions and quantities in the build worksheet |

This repository does not supply CAD/STL files, a dimensioned chassis drawing, a PCB schematic or verified
part purchase links. Select parts using [Build choices](DECISIONS.md) before purchasing.

## Power boundaries

- **Bank A:** Pi via USB-C; display and Pi fan only if their combined load is verified.
- **Bank B:** wheel driver motor rails, stepper motor supply and audio branch, subject to measured load.
- Keep independent bank positive rails separate. Establish common ground between the relevant Pi/Mega,
  sensor and motor-driver logic grounds. Check that no board unintentionally backfeeds USB.
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

XSHUT is deliberately never driven high by the Pi. The sensor breakout's own pull-up releases the
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

Keep stepper power on the verified external motor supply, not a GPIO output. Select a supported geared
assembly that holds its load when coils are released; firmware releases coils after stopping.
Manual centre marking is required; there is no automatic homing sensor.

## Sensor order matters

| Data | Index 0 | Index 1 | Index 2 |
|---|---|---|---|
| distance_mm / XSHUT / ToF address | Front-left | Front-right | Rear |
| cliff_raw / edge_level / Mega D pin | Front-left | Rear-centre | Front-right |

Do not copy ToF order into cliff calibration. Default range acceptance is 30–1000 mm. Forward obstruction
stopping uses the first two distance values; the rear value must still be valid/fresh. Reverse and pivot
remain disabled because the build has no verified all-direction cliff coverage.

## Connect power and ground by branch

| Connection | Reference route | Check before applying power |
|---|---|---|
| Pi power | Bank A regulated 5 V to USB-C | Pi 4 supply guidance is 5 V / 3 A; include all attached loads in your budget |
| Mega logic | Pi USB to Mega USB | USB carries serial and logic power; no Bank B positive connection to Mega 5 V/VIN |
| Driver VCC (logic) | Mega 5 V to each TB6612 logic VCC | Identified module must accept 5 V logic and supply; STBY must default low |
| Driver VM (motors) | Protected Bank B 5 V actuator branch through cutoff | Board/motors/current and local decoupling must be suitable |
| ULN2003 motor supply | Same switched actuator branch | Correct rated 5 V motor/board, connector pinout and flyback/common connection |
| Amplifier | Separately switched/accessible Bank B audio branch | Rated voltage, current and ground; actuator cutoff still cuts all motor rails |
| ToF/IMU supply | Pi-side supply compatible with identified breakout | Supply input rating and SDA/SCL pull-ups compatible with Pi 3.3 V |
| Touch-pad supply | Pi 3.3 V for 3.3 V-compatible pads | Outputs stay at Pi-safe logic levels; no 5 V pull-up |
| Cliff/PIR supply | Mega-side supply matching each module | Digital output levels meet Mega input specifications |
| Signal ground | Pi/Mega GND, sensor GND and Bank B/driver GND common | No motor return current through a thin sensor/USB ground path |

Do not join Bank A positive to Bank B positive. Do not connect Bank B directly to
Mega 5 V while the Pi's USB cable supplies it. Route high-current returns to the
power distribution point and use the common logic ground for signal reference.
The reference has no direct Pi-to-Mega GPIO connection.

For TB6612 breakouts, connect motor outputs AO1/AO2 and BO1/BO2 (some label them
A01/A02 and B01/B02) to one motor per channel. Never connect an output to a supply
rail. Match continuous and startup/stall load to the actual board's thermal rating;
the chip's short peak rating is not a continuous board rating.

## Unpowered wiring checklist

1. Identify pin 1 and the component side of the Pi header; BCM2 is physical pin 3,
   while physical pin 2 is a 5 V supply. Never substitute one numbering scheme for the other.
2. Connect ground, then power distribution with supplies unplugged. Check polarity,
   shorts and continuity with a meter before plugging in either bank.
3. Connect one sensor's SDA/SCL and its own XSHUT; repeat for each ToF and the MPU6050.
   Verify breakout schematics and idle bus voltage. A bare sensor and a regulated,
   level-shifted breakout have different supply/logic requirements.
4. Connect digital sensors to Mega in the table's order. Connect touch and LED only
   through compatible Pi-side interfaces and an appropriate LED series resistor.
5. Wire STBY/direction/PWM and each ULN2003's IN1–IN4. Leave motor power off. Do not
   use the Pi header to supply motor current.
6. Connect HDMI/USB touch and Mega USB; connect the CSI camera only while the Pi is
   unpowered, using its connector's documented orientation. USB webcams need a different adapter.
7. Inspect loose strands, exposed conductors, fuses, strain relief and the physical
   cutoff. Then begin M00 with only the Pi/logic domain powered.

## Manufacturer references

- [Raspberry Pi power and initial setup](https://www.raspberrypi.com/documentation/computers/getting-started.html)
- [Pi GPIO electrical behavior](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)
- [Arduino Mega 2560](https://docs.arduino.cc/hardware/mega-2560)
- [SparkFun TB6612FNG hookup and board details](https://learn.sparkfun.com/tutorials/tb6612fng-hookup-guide/all)
- [ST VL53L0X datasheet](https://www.st.com/resource/en/datasheet/vl53l0x.pdf)
- [ST multiple-VL53L0X application note](https://www.st.com/resource/en/application_note/dm00280486.pdf)

These establish device interfaces. Your breakout's schematic, ratings and protection
still control how that particular board is connected.
