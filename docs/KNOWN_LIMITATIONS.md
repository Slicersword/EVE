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
| Voice | Half-duplex only; no echo cancellation/barge-in; latency and recognition quality need measurement |
| Voice stop | Ordinary stop, not a latched estop; unavailable during speech/transcription; never the sole stop |
| Optional LLM | Adapter only; model weights/server not included; Pi RAM/latency must be tested |
| Cloud privacy | Regex redaction is incomplete; keep cloud disabled for private operation |
| Web integrations | Helpers exist but are not connected to conversation; no general web-browsing feature |
| Autonomy | Bounded commands and optional face tracking; no SLAM, docking or route navigation |
| Self-modification | No autonomous source editing or execution of model output |
| Battery system | Regulated 5 V supplies/banks only; no SOC/current monitoring, charging control or bare 3S support |
| Head position | Manual reference, no encoder/homing switch; loss of steps is undetected; coils release after stopping |
| Mechanical design | No CAD/STL or universal chassis/fastener dimensions; use the assembly guide and record your choices |
| Platform | Pi OS Desktop Bookworm / Pi 4 reference target; other hardware/OS needs separate validation |
| Simulation | Fake serial/sensors only; physical features disabled and state isolated under data/sim |
| Website | GitHub Pages renders main automatically; a separate static builder provides the offline version |
| Licensing | Project license unselected; third-party licenses are retained |

Some stage checks confirm availability only. Dialogue, reminders, sleep/wake,
sound and physical behavior still require their interactive tests. A successful
automated check never records a physical test as passed without builder confirmation.
