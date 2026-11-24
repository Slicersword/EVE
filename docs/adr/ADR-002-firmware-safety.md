# ADR-002: Firmware safety rules
Date: 2026-11-23   Status: accepted
Context: V2 review found: cliff comparison against a float threshold could never trip, no AVR watchdog, head stepping not independently gated.
Decision: (1) Cliff is digital: a channel is unsafe when its pin equals the calibrated edge level; uncalibrated = unsafe. (2) AVR watchdog (1 s) enabled by default, cleared in setup. (3) Every tick re-checks: enable flag, heartbeat age, cliff, latch, lease - separately for drive and head. (4) Firmware id = hash of the generated header; the Pi computes the same hash from its config and refuses motion on mismatch. (5) Firmware logic is compiled on the PC against a fake Arduino.h and tested.
Alternatives: watchdog off (rejected: a hung loop could leave PWM on). Risk considered: old Mega bootloaders can reset-loop after a watchdog reset; in that state all pins are inputs and TB6612 STBY is pulled low, so motors are off; power-cycle recovers. `firmware.watchdog_enabled=false` is available if that ever happens.
Consequences: every calibration change needs gen_header + compile + upload. Reverse: flash the previous sketch.
