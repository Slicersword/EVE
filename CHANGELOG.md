# Change log

## 2026-11-24 — Git repository and complete build documentation

- Organized supplied V3 source at repository root, preserving the Pi/Mega hardware pin contract.
- Added full build/inventory/assembly/wiring, architecture, safety, privacy, troubleshooting and limitation docs.
- Replaced machine-specific paths and mixed prose/commands with portable Git/ZIP setup routes and copyable recipes.
- Fixed stage checks treating zero tilt/zero sample age as missing; M03 now reads actual zero supply flags.
- Kiosk uses merged owner port settings. Last-flashed header is recorded only after successful upload.
- Microphone transcription refuses disk fallback when its RAM directory is unavailable.
- Simulation disables physical IO/audio/cloud and isolates its data; normal commissioning flags are unchanged.
- Added CI for host checks and AVR compilation; no workflow flashes a device.
- Added regression tests for setup boundaries, simulation isolation and audio directory failure.
- No hardware is marked commissioned. I2C diagnosis and full-duplex audio remain open.

## 2026-11-23 — Supplied EVE V3 baseline

Fresh standard-library-first rebuild in EVE_SOURCE_V3: one Python runtime, new Mega firmware, safety gates,
face, local sensors/camera/voice/memory, optional model adapters and M00–M17 tools.
The supplied handover reported 105 host tests and no Pi deployment/firmware flash for V3.
Historical notes are retained in docs/HANDOVER.md and docs/adr/; current status is in docs/KNOWN_LIMITATIONS.md.
