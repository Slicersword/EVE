# ADR-002: Firmware safety rules

The Mega starts latched. A missing heartbeat, unsafe calibrated cliff channel or
explicit STOP stops outputs and latches. Drive and head use independent command
leases; heartbeat alone cannot sustain motion. Each compiled enable flag remains
independently enforced.

Cliff sensors are digital. An uncalibrated sensor set is unsafe. A generated-header
fingerprint must match the Pi configuration before Pi-side motion is permitted.

The AVR watchdog is enabled by default. Bootloader reset behavior must be checked
with actuator power disconnected; hardware STBY pull-downs and a physical cutoff
remain essential. A host harness exercises actual sketch logic, and separate CI
compiles the ATmega2560 target. Neither supplies physical acceptance.

Changes to compiled settings require regeneration, compilation, upload and a
matching fingerprint, followed by affected hardware tests.
