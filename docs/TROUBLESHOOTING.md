# Troubleshooting

Start with the current M-stage, status and doctor instructions in [Software setup](SETUP_GUIDE.md).
Stop motion and disconnect actuator power before rewiring, flashing or diagnostics.
Do not change readiness flags to hide a fault.

## Installation and permissions

| Symptom | Check and recovery |
|---|---|
| Installer reports unsupported platform | Use Pi 4 / arm64 / Raspberry Pi OS Desktop Bookworm; generic Debian, Lite and newer OS releases need separate validation |
| Package not found / apt failure | Verify OS repositories, DNS, free space and clock; preserve the first error and retry after correcting it |
| externally-managed-environment / missing Python module | Run the setup script; use the launcher or `.venv/bin/python`, never sudo pip into system Python |
| `./eve: Permission denied` | ZIP extraction can lose execute bits; run the chmod step in the ZIP route |
| Serial / I2C / GPIO permission denied | Verify dialout/i2c/gpio group membership and reconnect SSH after installation |
| Clone destination exists | Choose a fresh folder; preserve the contents instead of overwriting them |
| ZIP folder not recognized | Download the complete repository ZIP from main; transfer it without renaming internal directories |
| Config problem | Read the named field; check JSON types, spelling, finite numbers, pin uniqueness and allowed ranges |
| Unknown configuration setting | Consult the public defaults and example; the tool rejects spelling mistakes and unsupported keys |
| Cannot change a readiness flag | Perform its real test and use the confirmation command; firmware enables require measured power first |

## Power and serial link

| Symptom | Check and recovery |
|---|---|
| Mega OFFLINE | USB data cable, configured device, groups, exclusive port ownership, reset settling and live heartbeat/telemetry |
| Wrong serial device | Set the actual by-id path; runtime and upload honor the configured port even with other CH340 devices |
| Upload reports busy / access denied | Stop foreground EVE and its user service; close Arduino serial monitors; verify the selected port |
| Firmware mismatch | A compiled setting changed; stop, regenerate/compile/upload, restart and compare fingerprints |
| AVR compile fails | Use Mega 2560 FQBN and pinned AVR core; preserve the first compiler error; do not upload a partial build |
| Mega repeatedly resets | Check supply and USB first, then identified bootloader/watchdog behavior; keep actuator power disconnected |
| Session refused | Measure M03 loads, verify power flags and live Pi supply state, and request a supported duration |
| Supply flags nonzero | Resolve voltage drop, current limit, cable or heat fault; historical bits can persist until reboot after repair |
| USB bank shuts down while idle | Check its documented minimum-load/auto-off behavior; choose a suitable supply; software cannot guarantee bank output |
| Motor branch browns out during motion | Re-check startup/stall load, driver/lead ratings, distribution and protection; stop repeated attempts |
| Runtime already running / address in use | Stop the other foreground process or user service; keep one owner of serial/I2C; changing ports is not the first fix |

## Distance, tilt and cliff sensors

| Symptom | Check and recovery |
|---|---|
| Every I2C address absent | Stop runtime; run the M04 diagnostic: idle SDA/SCL, IMU with all ToF off, then each XSHUT separately |
| Tilt missing | MPU6050 shares SDA/SCL; expect 0x68, or identified AD0-high 0x69 |
| SDA/SCL stuck low | Power down; inspect shorts, wrong pins and breakout pull-ups; add one board at a time |
| ToF answers at 0x29 with all XSHUT low | Inspect that board's shutdown pin and wiring; never drive XSHUT high from the Pi |
| All ToF absent | Verify breakout power, ground, Pi physical pin 3 SDA, pin 5 SCL and each XSHUT |
| Only one ToF appears | All sensors start at the same address; individual shutdown wires are required for sequential addressing |
| Distance null / None | Device missing, bus timeout or value outside 30–1000 mm; test with an object in usable range |
| Tilt near 180 degrees | Confirm mounting, then choose inverted orientation if appropriate; do not use it to hide missing data |
| Tilt is exactly zero | Valid for a level chassis; zero is a measurement, not a missing value |
| Cliff never flips / flickers | Test final mounting height, intended floor, reflectivity, lighting and trimmer; every channel must be stable and change |
| Cliff calibration rejected | Capture both steady floor and no-floor rows for all three channels; order is front-left, rear-centre, front-right |
| Lifted wheels blocked by cliff | Place safe floor targets under the sensors within their calibrated range; keep the support secure |
| Sensor data stale | Correct bus/serial faults; repeat live response checks; never enlarge timeouts to conceal a disconnected sensor |
| Diagnostic GPIOs differ from wiring | Check `sensors.tof_xshut`; keep documentation and physical numbering aligned after any pin change |

## Wheels and head

| Symptom | Check and recovery |
|---|---|
| No motion | Read the block reason: session, power, calibration, sensors, firmware, latch and readiness are separate gates |
| Wrong wheel direction | Power off, swap that motor's two output wires, then repeat the lifted forward and stop tests |
| Driver has different labels | Confirm TB6612 interface; an L298N board needs different wiring/firmware |
| No ULN2003 LEDs | Check external motor supply, common ground, connector order and IN1–IN4 mapping |
| Stepper twitches / vibrates | Verify motor/driver winding pinout and rated voltage; do not raise speed to mask wiring or excess load |
| Stepper moves slowly | Geared half-stepping is intentionally slow; confirm sequence and mechanics before changing timing |
| Head not homed | Align centre safely without forcing gears; start session, clear and confirm manual home |
| Head loses centre after stop/reset | Expected after Mega emergency stop/reset; realign and re-home; position feedback is not available |
| Jog direction unexpected | Manual jog signs follow wiring; tracking sign settings affect look/tracking only |
| Head drops when stopped | Coils release by design; provide mechanical retention or a suitable balanced/geared assembly before proceeding |

## Face, camera, audio and optional features

| Symptom | Check and recovery |
|---|---|
| Browser works on PC but Pi face absent | The kiosk needs an actual Pi desktop session; PC localhost refers to the PC |
| Kiosk not fullscreen / F11 needed | Start through the kiosk launcher with a logged-in desktop and Chromium; see M01 |
| SSH tunnel works but Pi screen is blank | The tunnel shows the Pi's web UI on your computer; it does not create a Pi desktop |
| Blank/connection-refused face | Confirm runtime is running and network port matches the kiosk's merged local config |
| Token unauthorized / HTTP 401 | Restart rotates token; CLI reads the current local token automatically; refresh the phone/browser token |
| Camera error / LED off | Check CSI cable with power off, supported camera, cascade path and LED GPIO/driver; repeat indicator acceptance |
| No speech | Check amplifier/audio power branch, ALSA output and espeak-ng; software availability alone does not prove sound |
| Microphone quiet / wrong input | Select actual ALSA device, calibrate threshold and confirm capture enable |
| STT not installed / no transcript | Build whisper.cpp and download the multilingual model; verify paths and microphone rate/device |
| Recognition slow / poor Hindi or Marathi | Test the multilingual model with short phrases and low background noise; measure Pi load and latency |
| Does not hear while speaking | The default voice route takes turns; M13 documents the optional verified local echo-cancel route |
| Local WebRTC echo route unavailable | Check the Pi desktop session and both named routes. Reload the module after reboot or disable echo mode and restart for turn-taking |
| No general answer | Basic offline replies cover fixed intents; optional local LLM needs its own loopback server and model |
| Reminder silent / late | Check the runtime, system clock and actual output device. The due reminder stays available to retry if software playback fails |
| Autostart fails | First prove foreground operation, then inspect user-service logs, source path and desktop login |
| Website search or styles absent offline | Keep all of dist together and open index.html; rebuild/validate after source changes |
| Pages website not updated | Check Verify EVE and its Publish GitHub Pages job; fix any failed render/link check; follow Website |
| Website shows an older revision | Rebuild and republish its host; the footer/build-info identifies the source snapshot |

## Two INMP441 microphones and the audio boost

| Symptom | Check and recovery |
|---|---|
| INMP441 absent from I2C scan | Expected: it is an I2S microphone. Use the M13 I2S/ALSA setup and hardware capture list |
| EVEINMP441 card missing after setup | Confirm reboot, correct Pi 4 overlay in the real boot config, successful dtc compile and no conflicting I2S overlay; inspect boot/kernel errors before retrying |
| eve_mic device unknown | Run the user-audio helper without sudo for the same normal user that runs EVE; inspect arecord -L and the named PCM in that user's .asoundrc |
| Invalid format/channels on hardware capture | INMP441 needs 64 clocks per stereo frame. Use S32_LE/48 kHz/two channels for direct hardware tests and eve_mic for converted mono input |
| One microphone silent | With power off inspect that module's 3.3 V, GND, SCK, WS and SD. Confirm one L/R low and the other high; test channels separately |
| Two mics distort or collide | Both may be driving the same time slot; opposite L/R selections are required on shared SD |
| SD connected to BCM21 | Move it with power off to BCM20 physical 38; BCM21 physical 40 is Pi I2S output |
| Captures noise, motor clicks or repeated false speech | Shorten/secure signal leads, separate motors/audio, verify supply decoupling and grounds, then recalibrate quiet/speech threshold; keep half-duplex limits in mind |
| PAM8610 silent on 5 V | It requires 7–15 V. Use the selected, verified 5 V-to-9 V boost branch; a buck cannot step up |
| Boost output correct unloaded but sags with speech | Check 5 V input current limit, converter continuous/thermal rating, connectors and Bank B total load. A no-load meter reading is insufficient |
| Speaker crackles, smells, heats or distorts | Switch audio off. Verify output limit, speaker load/rating, clipping and supply; the amplifier can exceed 3 W |
| Amplifier speaker negative looks like ground | It is a bridged output, not an audio reference. Do not join negatives or ground them; use proper differential measurement equipment |
| Speech feature reports command exited | Test espeak-ng and the chosen playback session/output directly; the runtime now preserves a failed process result instead of reporting successful output |
| Touch pad stays on after release | Check TTP233 suffix/jumpers: toggle, delay-off or active-low mode is incompatible with the expected direct active-high Q output |
| Cliff board only has A0 | This firmware needs a digital threshold output. Identify the module's D0/DO or use a reviewed interface; analogue output is not a substitute |

## Website progress and source viewer

| Symptom | Check and recovery |
|---|---|
| Cannot tick a progress task | Choose Start tracking on this device; Pause intentionally locks editing |
| Checkmarks missing on another device/browser | There is no automatic account sync. Export JSON from the original browser and import it on the destination |
| Progress lost after clearing browsing data | Import your last export. Without a backup, cleared local storage cannot be recovered from GitHub |
| Session-only storage notice | Browser/private-mode policy or quota prevents persistence. Export before closing the page; changing permissions does not recover an already lost session |
| Import rejected | Use the original EVE JSON export, schema version 1, with recognized task IDs and bounded notes. Rejection leaves current data unchanged |
| Imported notes look like HTML | Notes are displayed as plain text; code/HTML in notes is never executed |
| Another tab has different counts | Reload before editing; simultaneous tabs do not merge. The latest save wins |
| Source viewer has no matches | Clear the file filter. Filter names such as firmware, voice.py or config |
| Source viewer or notebook never loads | Enable JavaScript and reload the full site. Keep all exported assets together offline; the static offline source pages also work without the interactive viewer |
| Website check says source snapshot stale | Regenerate the source snapshot after code/assets change, then run repository/site checks before pushing |

## Gather useful evidence

Record the stage, expected and observed behavior, component models, source revision,
firmware ID, whether actuator power was on, and a short sanitized status/doctor or
first-error excerpt. Share only relevant output. Review it for tokens, keys, private
notes, personal speech and network details.

## Recover and re-test

Updates keep two private source/state backups. With EVE stopped and actuator power
off, restore only your verified backup, check dependencies, regenerate matching
firmware and repeat affected stages. Configuration changes may require reflashing.
Power/wiring/sensor/head changes require new physical tests; an earlier acceptance
record does not transfer automatically to changed hardware.
