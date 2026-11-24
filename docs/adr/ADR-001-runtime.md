# ADR-001: One runtime and a separate actuator controller

The Pi runs one standard-library-first Python composition root in eve3/runtime.py.
Hardware libraries load at device startup so host tests run without Pi drivers.
The Mega owns time-critical motor output and independent cliff/heartbeat checks.

One serial owner, a framed CRC protocol, explicit configuration and gated commands
keep control paths inspectable. Models return text; they do not execute code.
Public defaults, builder overrides, runtime data and generated documentation each
have separate paths. Builder state never belongs in the tracked repository.
