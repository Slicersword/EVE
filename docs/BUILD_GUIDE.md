# The complete build sequence

This is a standalone reference build. Start with unassembled components and no
commissioning records. Read [Before you begin](GETTING_STARTED.md), then follow
the steps below. Copyable installation and test commands are in [Software setup](SETUP_GUIDE.md).

Try the [touchscreen face and control panel](UI_PREVIEW.md) to see what the finished setup displays.

## 1. Select and inspect the parts

Use [Your parts](HARDWARE.md) and [every connection](WIRING.md) as the electrical contract. Record exact module
names, voltages, motor current, chassis layout and power ratings in [Build choices](DECISIONS.md).
Check board labels and manufacturer datasheets; similar-looking boards can
have different pin order, pull-ups and input voltages.

The reference uses Pi 4 + Mega, two TB6612-compatible drivers, two 5 V unipolar
geared steppers with ULN2003 boards, and two independent regulated 5 V supply domains.
The listed N20 motors run from the 5 V rail; brackets and bank capacity are verified
against measured loads. The PAM8610 has a separate regulated 9 V boost branch;
its output must be limited for the 3 W speakers. Two INMP441 microphones use I2S.
No raw battery pack, charger control or battery monitoring is implemented.

**Continue when:** all components have identified ratings, protection is selected,
and the motors fit the driver's continuous/start/stall-current envelope.

## 2. Assemble the chassis and head

Follow [Assembly](ASSEMBLY.md). Mount boards on insulated standoffs, provide wheel
clearance and an accessible power cutoff, then fit sensors and the display.
Mark a mechanically safe head centre. Stepper position is relative to a manually
confirmed centre; there are no homing switches or position feedback.

**Continue when:** nothing can short, wheels turn freely, the supported head holds
safely when coils are released, and cables cannot snag through its proposed range.

## 3. Wire with all supplies unplugged

Connect each part using the terminal tables in [Wire every part](WIRING.md).
Wire one subsystem at a time and check continuity after each. Keep independent
positive rails separate. Use Mega USB for serial; never connect Mega 5 V GPIO to Pi GPIO.
Keep actuator power disconnected until the measurements and commissioning stages.

**Continue when:** pin numbering, connector orientation, logic levels, common ground,
polarity and cutoff operation have been independently checked.

## 4. Install and verify the software

Prepare the supported OS and follow M00–M02 in [Software setup](SETUP_GUIDE.md).
Use two SSH terminals: one runs EVE and the other sends commands. The Pi compiles
and uploads the Mega sketch through USB; a separate Windows upload is unnecessary.

**Continue when:** host tests pass, the face fills the Pi screen, and Mega telemetry
reports a settings fingerprint that matches the Pi's configuration.

## 5. Measure power and calibrate sensors

Follow M03–M06. Measure the electrical loads with suitable test equipment and secure
the chassis. Calibrate all three digital cliff channels over both a safe floor target
and a controlled no-floor target. Verify each distance sensor and the IMU separately.

**Continue when:** power flags have measurements behind them, all readings
respond and remain fresh, and obstacle/cliff/tilt/stale-link/stop conditions block motion.

## 6. Commission wheels and head

Follow M07–M08 with all wheels on a stable support and cliff sensors over safe
targets. Test direction and stop paths before moving to a level, enclosed floor area.
Jog the head a few steps at a time, measure smaller safe limits, and test them again.
Reverse and pivot remain disabled in the reference configuration.

**Continue when:** every wheel turns in the expected direction, commands time out,
the physical cutoff works, sensor failures stop motion, and head travel clears all cables.

## 7. Add the companion features

Follow M09–M16 for touch, local camera, memory, multilingual dialogue, speech,
presence behavior, reminders and sleep/wake. Voice recognition downloads a separate
local model. Optional camera tracking requires head commissioning first.
Keep cloud AI disabled for private use; no external AI service is required.

**Continue when:** each fitted feature passes its interactive test. Record deliberately
omitted features in your worksheet rather than claiming full M00–M17 acceptance.

## 8. Run acceptance and enable autostart

Complete the M17 attended test and [acceptance record](TESTING.md). Install the
service only after the foreground runtime works. Reboot with actuator power off,
check the face and service, and verify that a fresh session/clear is needed for motion.

Maintain local calibration and data privately. The update procedure checks the
new revision and your local settings, saves a backup, fast-forwards Git and
regenerates the firmware header. Changes to the Mega sketch, pin map, calibration
or compiled settings require a fresh upload and a matching live settings fingerprint.

## Stage map

Use [My build progress](PROGRESS.md) to record each preparation, wiring and M-stage
task, keep notes and export a backup. It starts empty and does not change robot settings.

| Stages | Build outcome |
|---|---|
| M00–M02 | Installation, touchscreen face, Mega link and firmware |
| M03–M06 | Measured supply, distance/tilt/cliff sensors, stop behavior, cooling |
| M07–M08 | Lifted wheel tests, contained floor test, manual head home and limits |
| M09–M10 | Touch pads, camera activity indicator and local detection |
| M11–M13 | Explicit memory, three-language dialogue, speaker and local microphone/STT |
| M14–M16 | Presence, reminders, sleep/wake and optional LAN control |
| M17 | Attended acceptance, service installation and reboot check |
