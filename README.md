# EVE — home companion robot

EVE is a Raspberry Pi 4 + Arduino Mega home robot with a touch-screen face, four-wheel drive,
stepper pan/tilt head, distance/cliff/tilt sensing, local voice, and consent-based memory.
This repository contains the V3 Python runtime, Mega firmware, owner tools, and complete build and
commissioning documentation. It is intended for the existing EVE hardware and pin map.

**Status: software tested; physical commissioning pending.** The shipped configuration is locked:
all six commissioning flags are false, wheels/head are disabled, and cliff calibration is unset.
A passing software test does not prove the physical robot safe or operational.

## Build your EVE

Start with the [complete build guide](docs/BUILD_GUIDE.md). It links the parts list, assembly,
wiring, installation, calibration, and final acceptance in the order you need them.

| Read | Purpose |
|---|---|
| [Build guide](docs/BUILD_GUIDE.md) | Whole build and M00–M17 roadmap |
| [Parts, wiring and pin map](docs/HARDWARE.md) | Pi, Mega, sensor order, power boundaries |
| [Software setup and tests](docs/SETUP_GUIDE.md) | Copyable commands for PuTTY; Git and ZIP install routes |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | I2C, supply, serial, face, voice, motion and services |
| [Safety and commissioning](docs/SAFETY.md) | Motion gates, stop behavior and acceptance |
| [Privacy](docs/PRIVACY.md) | Data handling, local defaults and cloud limitations |
| [Architecture](docs/ARCHITECTURE.md) | Source layout and Pi/Mega responsibilities |
| [Known limitations](docs/KNOWN_LIMITATIONS.md) | Hardware validation and unfinished capabilities |
| [Change log](CHANGELOG.md) | Repository preparation and inherited V3 history |

## Included capabilities

- Fullscreen animated eyes and mouth; nine expressions; no face outline, camera button, or navigation tip.
- Three VL53L0X distance sensors, MPU6050 tilt, three digital KY-033 cliff sensors and PIR presence.
- Four wheel outputs through two dual-channel motor drivers; independent pan/tilt stepper control.
- Heartbeats, command leases, stale-data refusal, cliff/tilt latches, firmware-settings fingerprint,
  and an AVR watchdog. Reverse and pivot are off by default.
- Head/back touch pads; back hold requests emergency stop.
- Local face detection and optional head tracking, with camera activity LED.
- English, Hindi and Marathi intent handling, basic offline replies, espeak-ng speech,
  and optional local whisper.cpp transcription.
- SQLite notes and reminders; notes saved when explicitly requested; conversations are not logged.
- Token-protected command API and optional home-network control page.
- Two USB-bank attended operation; INA219 disabled; no battery percentage is fabricated.
- Pi service and face autostart after final acceptance.

The local LLM adapter is optional and requires a separate model/server. Voice is currently half-duplex:
EVE ignores microphone input during speech. Web lookup helpers exist but are not wired into conversation.
See the limitations before treating a feature as complete.

## Repository verification

GitHub Actions is configured to run Python tests, firmware host-harness tests, generated-guide/header
checks and an AVR compilation for Mega 2560. Local verification commands live in the software guide.
CI results become available only after this repository is pushed and the workflow runs.
No CI job accesses a real robot or uploads firmware.

Target: Raspberry Pi 4B, 64-bit Bookworm, Python 3.11, 1024×600 desktop touch screen, Arduino Mega 2560.
The host test suite runs on Linux without Pi hardware libraries. Dependencies, STT model weights and
optional LLM weights are downloaded during installation, not bundled in this repository.

## Contributions and ownership

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md) before sharing changes or logs.
No open-source license has been selected by the owner; repository access alone does not grant a license.
