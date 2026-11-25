# Supported boundaries and remaining validation

This repository provides software and an end-to-end build procedure. Building the
physical robot requires selecting compatible components, measuring power and
performing each hands-on acceptance test.

| Area | Boundary |
|---|---|
| Hardware commissioning | Every M00–M17 stage starts unconfirmed; no real robot is exercised by CI |
| Electrical specification | Motor, driver-board, supply and wiring ratings must be recorded and measured per build |
| Sensors | All three ToF, all three cliff channels and MPU6050 must pass live response/freshness tests |
| Firmware | Host harness runs the real sketch; AVR CI compiles target binaries; USB upload/bootloader behavior needs the Mega |
| Voice | Turn-taking by default. Optional local echo-cancel route needs the M13 acoustic test. Listening can overlap speech, but inference can still delay the next utterance |
| Voice stop | Requests ordinary motion Stop. Microphone recognition can be delayed or unavailable. The physical cutoff remains independent |
| Optional LLM | Adapter only; model weights/server not included; Pi RAM/latency must be tested |
| Cloud privacy | Disabled by default. Opt-in requests use a small fixed public catalog |
| Web integrations | Helpers exist but are not connected to conversation; no general web-browsing feature |
| Autonomy | Bounded commands and optional face tracking; no SLAM, docking or route navigation |
| Self-modification | No autonomous source editing or execution of model output |
| Battery system | Two regulated 5 V banks; no SOC/current monitoring, charging control or bare 3S support; PAM8610 uses a separately verified 9 V boost branch |
| Head position | Manual reference, no encoder/homing switch; loss of steps is undetected; coils release after stopping |
| Mechanical design | No CAD/STL or universal chassis/fastener dimensions; use the assembly guide and record your choices |
| Platform | Pi OS Desktop Bookworm / Pi 4 reference target; other hardware/OS needs separate validation |
| Simulation | Fake serial/sensors only; physical features disabled and state isolated under data/sim |
| Website | GitHub Pages renders main automatically; a separate static builder provides the offline version |
| Licensing | Project license unselected; third-party licenses are retained |

Some stage checks confirm availability only. Dialogue, reminders, sleep/wake,
sound and physical behavior still require their interactive tests. A successful
automated check never records a physical test as passed without builder confirmation.

## Coverage of older EVE builds

The current checkout preserves the original 90-expression catalog, artwork and
sound files and the prepared home activities from the 6 November handover. This
build uses the current Pi/Mega interface and setup guide.

| Older work | Current Git build |
|---|---|
| Expression artwork and audio | The original artwork and 90 WAVs are in Git. The guide and robot display all 90 expressions using the same eyes-and-mouth style. Live sound is opt-in. |
| Family games, story branches, recipe sessions, timers, messages, music and memory capsules | Bundled and accessible from the token-protected Home page. Household data and chosen music are supplied locally. |
| Expression Studio and spoken Home shortcuts | The current studio auditions all 90 sounds. Fixed spoken shortcuts run riddles, story branches, recipe navigation and music stop. Private household records open through authenticated Home. |
| Earlier audio and privacy modes | Optional local echo-cancel routing is present. Instant interruption of in-progress speech, family voice profiles and separate guest/focus modes are outside this build. Sleep ends motion and pauses the camera. Enabled microphones remain available for voice wake. |
| Earlier reminder scheduling | Relative reminders and named kitchen timers survive restarts and remain until acknowledged. Recurrence, snooze and spoken clock-time scheduling are outside the current workflow. |
| Older joystick controller, alternative local model experiments and maintenance tools | Current controls use bounded motion commands. Models use a separate loopback adapter. Doctor, verification and protected source updates are available. |
| Chassis CAD, build photos and historical reports | The Git build includes assembly and connection guides. Older CAD and image originals remain in historical archives. |
| Earlier firmware, field calibration, measurements and device state | Use the firmware and guide from this checkout. Physical commissioning must be performed on the assembled robot. |

Fresh installation still needs an internet connection for Pi OS packages,
Arduino tooling and the optional speech model. The automated checkout test covers
bundled assets, simulated runtime and access controls. Only an on-Pi test can
verify the actual GPIO wiring, USB serial port, audio output, sensors and motion
interlocks.
