# Known limitations and open acceptance

This is a complete source and build-documentation repository. It is not a claim that the physical robot,
every optional capability, or unattended operation has been completed.

| Area | Current boundary / work remaining |
|---|---|
| Robot commissioning | Every M00–M17 stage starts unconfirmed; run on the real robot |
| I2C | Earlier scans found no devices; diagnose shared SDA/SCL, supply, ground and XSHUT on the build |
| Firmware | Host harness executes real sketch logic; actual AVR build/upload and bootloader behavior require validation |
| Audio duplex | Half-duplex only; microphone input ignored during speech; no acoustic echo cancellation/barge-in |
| Voice stop | Ordinary stop, not a latched estop; unavailable while speaking; recognition latency varies |
| Optional LLM | Adapter only; no model weights or model server included; Pi 2 GB performance unmeasured |
| Cloud privacy | Regex redaction is incomplete for names/addresses; leave cloud disabled for strict privacy |
| Web integrations | Wikipedia/FX helpers exist but are not wired to a runtime/chat command; no holiday helper |
| Autonomy | Bounded voice/control moves and face tracking; no mapping, route navigation, docking or SLAM |
| Self-modification | No autonomous source editing/updating/execution of model output |
| Batteries | USB-bank operation; no SOC/current/battery monitoring or automatic 3S charging control |
| Head home | Manual marks only; no hardware home feedback; positions reset after Mega reset/stop |
| Camera/audio | Exact fitted model, ALSA devices, LED behavior and latency need real hardware checks |
| Mechanical plans | No CAD/STL, chassis dimensions or verified motor/fastener ratings in the supplied archive |
| Setup/platform | Target is Raspberry Pi Bookworm; other Linux/Windows runtime support not commissioned |
| Simulation | Real serial, ToF, IMU, touch, camera and audio are disabled; fake runtime data uses data/sim/ |
| Licensing | Owner has not selected a distribution license; third-party software/models retain their licenses |

Some inherited stage checks are availability checks, not functional tests. M12/M15/M16 acceptance relies
on the owner's guided interaction. Passing automated checks never records a physical test without an
explicit owner confirmation.
