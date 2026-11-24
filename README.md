# Build EVE from scratch

**[Open the GitHub-hosted build website](https://slicersword.github.io/EVE/)**

EVE is a four-wheel home robot built around a Raspberry Pi 4 and Arduino Mega 2560.
It has a touchscreen face, a pan/tilt head, distance/cliff/tilt sensing, local voice,
English/Hindi/Marathi commands, and optional local notes and reminders.

Start with no saved progress: identify your parts, assemble and wire the robot,
install the software, then test one stage at a time. All commissioning flags ship
false, actuator outputs are disabled, and cliff calibration is unset.

## Your build path

| Step | What you will do | Guide |
|---|---|---|
| 1 | Check tools, parts, computer and operating system | [Before you begin](docs/GETTING_STARTED.md) |
| 2 | Choose compatible components and record their ratings | [Parts and wiring](docs/HARDWARE.md) · [Build choices](docs/DECISIONS.md) |
| 3 | Assemble the chassis, head, display and sensors | [Assembly](docs/ASSEMBLY.md) |
| 4 | Follow the complete sequence and connect each subsystem | [Build guide](docs/BUILD_GUIDE.md) |
| 5 | Install, flash and calibrate in ordered M00–M17 stages | [Software setup](docs/SETUP_GUIDE.md) |
| 6 | Prove stop behavior and complete attended acceptance | [Testing](docs/TESTING.md) |

Each stage includes commands, automatic checks, a hands-on test, and a clear
condition for continuing. Commands run on the Pi through SSH/PuTTY unless labelled
Windows PowerShell. The `eve` launcher selects the Python virtual environment.

## What is included

The repository contains the Python runtime (`eve3/`), Mega sketch (`firmware/`),
setup and diagnostic tools, configuration examples, host tests, and the source for
the companion website. The website is generated directly from these documents and
source files; it includes offline search, copy buttons and full source listings.

The reference design uses two independent regulated 5 V USB supplies/banks and two
TB6612-style dual motor drivers. Confirm your motor current and actual board
variants before wiring. A bare 3S battery and an L298N board require different
power and driver implementations.

## Verification and limits

Host tests exercise the runtime, protocol and the real sketch using a fake Arduino
core. CI also compiles both locked and enabled firmware for Mega 2560, checks the
generated files, and validates the website. Consult [verification](docs/VERIFICATION.md)
for observed results and [limitations](docs/KNOWN_LIMITATIONS.md) before purchasing parts.

No software test can certify your wiring, motor current, sensor placement or stopping
distance. The full build requires hands-on measurements and commissioning.
Chassis dimensions and exact motor/power-bank models are builder choices, recorded
in the [build worksheet](docs/DECISIONS.md).

Voice is half-duplex: microphone input is ignored during speech. There is no mapping,
automatic docking, battery monitoring or autonomous source editing. Basic conversation
runs locally; external AI and network integrations are disabled by default.

## Find help or change a setting

- [Troubleshooting](docs/TROUBLESHOOTING.md): installation, power, I2C, serial, motion, face and audio.
- [Configuration](docs/CONFIGURATION.md): local overrides, languages, timezone, optional features.
- [Safety](docs/SAFETY.md) and [privacy](docs/PRIVACY.md): operating boundaries and data handling.
- [Architecture](docs/ARCHITECTURE.md): source layout and Pi/Mega responsibilities.
- [Website](docs/WEBSITE.md): offline build, free hosting and repository synchronization.
- [Contributing](CONTRIBUTING.md), [security](SECURITY.md) and [changes](CHANGELOG.md).

Project licensing remains an explicit maintainer choice. Public access alone does
not grant an open-source license; included third-party files retain their own licenses.
