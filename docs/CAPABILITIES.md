# What EVE can do

EVE is an attended four-wheel home companion with a Pi touchscreen face and a Mega
motor/sensor controller. This page describes the implemented code, its required parts
and the test that demonstrates each feature. A feature appearing here does not mean
it has been accepted on a physical robot. Start every build at zero.

## Features and how you prove them

| Feature | What happens | Hardware / setup | Acceptance |
|---|---|---|---|
| Animated face | Eyes blink, expressions change and a mouth animates while speaking | 7-inch HDMI/USB touchscreen, Pi desktop and kiosk | M01: full screen, blinking, expression test; no keyboard needed |
| Short forward movements | Four N20 wheels move forward or along an arc, then stop on a time limit | Two TB6612 boards, tested sensors, measured power and attended session | M07: lifted direction tests, automatic stop, fault stop, contained floor test |
| Pan/tilt looks | Small relative jogs and named left/right/up/down/centre looks | Two 28BYJ-48 + ULN2003 sets, balanced head, manual home and measured limits | M08: every jog has clearance; head stops and remains supported unpowered |
| Distance protection | Front distance can slow/block driving; all three readings must be valid/fresh | Three VL53L0X boards on Pi I2C with separate XSHUT | M04/M05: each reading responds; obstruction blocks the right behavior |
| Drop sensing | Calibrated digital cliff values latch a stop | Three TCRT5000 digital modules on Mega | M04/M05: each floor/no-floor result changes reliably at final mounting height |
| Tilt protection | Excess tilt or missing data blocks motion | MPU6050 fixed to the base | M04/M05: near zero level; controlled tilt triggers refusal/latch |
| Presence greeting | A new presence event can produce a greeting, subject to cooldown/night hours | HC-SR501, or a local detected face | M14: arrival greets once; repeated presence does not constantly speak |
| Touch interaction | Head touch changes expression; back tap wakes/listens; back hold requests emergency stop | Two TTP233 pads in compatible direct active-high mode | M09: tap/release/hold work as described |
| Local camera face following | Finds the largest visible face and reports its screen offset | Camera Module 3, Picamera2, visible indicator and optional shutter | M10: indicator follows camera state; eyes follow a visible face locally |
| Optional head following | Makes small head corrections toward a detected face | Accepted head, home, clear sensors, active session and tracking enabled | M10: small controlled travel; shutter closes image access |
| Speech output | Speaks English, Hindi or Marathi using espeak-ng | Working analogue output and a correctly powered, limited amplifier/speaker path | M13: hear all three languages clearly at a safe level |
| Local speech recognition | Records short utterances, runs multilingual whisper.cpp, then handles supported commands | Two INMP441 microphones, I2S/ALSA profile and local model | M13: quiet/speech threshold, each mic and wake-word/command test |
| Offline conversation | Fixed local replies for greetings, identity, time/date, jokes, short stories and status | Text chat works before microphone setup | M12: examples in each language produce the intended reply |
| Local notes | Saves explicit “remember” notes, lists and deletes them | SQLite on Pi storage; memory enabled | M11: note persists after restart and can be erased |
| Timers/reminders | Stores a relative reminder and speaks it when due | Runtime running, memory/database, accurate clock and working audio | M15: short reminder, restart persistence and one delivery |
| Sleep/wake face | Sleepy expression after quiet idle time; interaction wakes it | Behavior enabled, chosen idle/night settings | M14/M16: timeout or explicit sleep/wake test |
| Control page | Local status and authorized controls using a runtime token | Loopback default; optional SSH tunnel or explicit trusted LAN | M16: live status, wrong-token refusal, stop command |
| Recovery tools | Doctor, stage checks, firmware fingerprint and safe diagnostic commands | Pi tools and the matching source/configuration | Use the relevant M-stage before confirming readiness |
| Website notebook | Tracks task checkmarks, notes and completion dates with export/import | Any supported browser; optional local storage | Export and import a test backup on [My build progress](PROGRESS.md) |

## What is enabled initially

The shipped configuration leaves wheel/head firmware outputs disabled, all physical
readiness flags false and cliff calibration unset. The camera, camera head tracking,
microphone capture, external models, cloud AI and network integrations start off.
Touch, explicit local memory, fixed offline dialogue, behavior and speech output are
configured on; they still require the right devices and installed packages.

An installation does not start a motion session. Each session is attended and expires
after the requested duration, at most 30 minutes by default. Restarting loses the
session. A command must still pass live sensor, link, latch, firmware and readiness checks.

## Words EVE understands

After M12, test text using the software guide; after M13, speak the same phrases.
Use short, clear phrases. The recognizer supports a defined set of intents, not
unrestricted natural-language robot control. Hindi/Marathi transliterations are also
included in the parser, but recognition accuracy depends on your model and room.

| Action | English example | Hindi example | Marathi example |
|---|---|---|---|
| Greeting | Hello | नमस्ते | नमस्कार |
| Identity | Who are you | तुम कौन | तू कोण |
| Time | What time is it | कितने बजे | किती वाजले |
| Story | Tell me a story | कहानी | गोष्ट |
| Joke | Tell me a joke | चुटकुला | विनोद |
| Stop | Stop | रुको | थांब |
| Forward, after commissioning | Go forward | आगे चल | पुढे जा |
| Look left | Look left | बाएं देख | डावीकडे बघ |
| Sleep | Go to sleep | सो जा | झोप |
| Explicit note | Remember that the spare cable is in the drawer | याद रख केबल दराज में है | लक्षात ठेव केबल कपाटात आहे |
| Recall notes | What do you remember | क्या याद है | काय लक्षात आहे |
| Reminder | Remind me in 1 minute to drink water | याद दिला 1 मिनट पानी | आठवण 1 मिनिट पाणी |

By default, microphone commands need “EVE” or a configured wake-word form. A back tap
or recent recognized interaction opens a short follow-up window. Recognized stop
phrases do not require a wake word, but **recognition is unavailable while speaking
or busy transcribing**. Use the physical cutoff, back hold or command-line emergency
stop in the circumstances each supports; speech is not the independent stop.

“Come here” currently requests a bounded forward action; it does not locate a person
or plan a route. Left/right drive phrases request forward arcs. Look commands use
relative step targets; they do not measure real head angle. Test supported phrases
with wheel power off before any attended movement test.

## Privacy and performance

Camera frames stay in Pi memory and are not saved by the current camera path.
Microphone processing is local; temporary clips use RAM-backed storage and are removed
after transcription. Explicit notes/reminders remain in the local database. Website
progress is separate browser data and never enters the robot. Review [Privacy](PRIVACY.md)
for practical limits and handling of private backups.

Two microphones supply two slots which are mixed to mono. They do not create a
beamforming array. Audio is **half-duplex**: the runtime discards mic input while
speaking. On a Pi 4, speech/model work can be slow; measure real latency and keep
phrases short. More swap does not make the processor faster.

An optional on-Pi language model can answer additional text questions through a
loopback server. It is separate software and is not required for basic commands.
Generated model answers are not parsed as movement instructions. Cloud stays disabled
for the private build; do not enable it expecting automatic privacy guarantees.

## Boundaries and build blockers

There is no SLAM/map, room navigation, docking, battery percentage, automatic charging,
wheel encoder control, object/person identity recognition, source-code self-editing,
full-duplex audio or unattended roaming. There is no verified protection for arbitrary
stairs, sunlight, reflective surfaces or all directions of travel. Reverse and pivot
remain disabled. Read [Known limitations](KNOWN_LIMITATIONS.md).

The listed **PAM8610 cannot run directly from the selected 5 V-only banks**. The build
therefore adds a regulated 5 V-to-9 V boost converter on a separate audio branch.
Verify that converter, combined Bank B current and the 3 W speaker output limit
before completing speech-output acceptance.
Do not treat a successful software speech command as evidence that audio hardware works.
Power-bank current ratings, exact sensor/touch breakout modes, display power arrangement
and motor stall current still need recording in [Build choices](DECISIONS.md).

Continue with [Before you begin](GETTING_STARTED.md), [your parts](HARDWARE.md),
[every connection](WIRING.md) and the ordered [setup stages](SETUP_GUIDE.md).
