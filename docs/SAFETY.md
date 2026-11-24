# Safety and commissioning contract

## Initial state

All commissioning flags are false; firmware drive/head are disabled; cliff calibration is unset;
the Mega starts latched. No stage is recorded complete in the repository. Sensor failures must
produce refusal, not substituted values. This contract must survive updates and contributions.

## What permits motion

- Power A, Power B and motor-current confirmations; appropriate drive/head flags.
- The compiled drive/head enable flag, expected firmware-settings ID and a live Mega link.
- A fresh attended session, limited to at most 30 minutes; it is not restored after reboot.
- Fresh valid distance, tilt and cliff readings; cliff calibration; no applicable obstacle/tilt/cliff fault.
- No Pi or Mega stop latch. Head motion also requires stationary wheels, manual home and appropriate limits.

Drive tests relax only the final drive_verified requirement; head jog/home tests relax only the final
head_verified requirement. They do not bypass power checks, sensor health or link safety.
Reverse and pivot remain off unless an owner makes a separate explicit configuration decision.

## Stop behavior

| Trigger | Behavior |
|---|---|
| Owner normal stop / parsed stop phrase | Wheels stop; head lease renewal ends; this is not a latched emergency stop |
| Emergency-stop command / back-pad hold | Pi latches, sends Mega STOP, ends commanded motion; Mega loses head home |
| Unsafe distance or stale/invalid frame | Pi refuses/ends motion; Mega lease expires if Pi renewal stops |
| Cliff | Mega independently stops and latches; Pi also refuses/latches |
| Excess tilt | Pi stops/refuses and latches; Mega does not directly read tilt |
| Lost Pi heartbeat | Mega independently stops and latches |
| Lost drive/head renewals | Corresponding Mega motion lease expires |
| AVR loop hang | AVR watchdog reset if enabled; physical startup behavior still needs testing |
| Session expires | Pi stops renewing motion; a new session is required |

Voice stop is unavailable while EVE is speaking and may be delayed by transcription. Touch/software stops
need functioning electronics. Use the physical Bank B switch to cut actuator power. Software does not
provide an independent safety-rated circuit or guarantee immediate physical stopping.

A clear request requires safe fresh readings and Mega acceptance. An obstacle can still block drive
after clearing. Clear is never evidence that all commissioning has passed.

## Physical acceptance

Follow M00–M17 in [Software setup](SETUP_GUIDE.md). In particular, measure real power and current, test
all sensor channels independently, confirm wheels stop on normal stop, emergency stop, cliff, obstacle,
link loss and expiry, and establish head range before ordinary look/tracking commands.

For a lifted wheel test, keep cliff sensors over a suitable safe floor target at the calibrated distance.
If wheels and sensors cannot both be arranged safely, stop and improve the support. Do not bridge pins,
copy fake calibration or disable a gate to make a motor spin.

The historical I2C fault is still open. Do not declare it repaired from unit tests, a successful flash,
a manually set stage record or old progress reported for a previous software version.
