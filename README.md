# Build EVE from scratch

**[Open the GitHub-hosted build website](https://slicersword.github.io/EVE/)**

EVE is a four-wheel home robot built around a Raspberry Pi 4 and Arduino Mega 2560.
It has a touchscreen face, a pan/tilt head, distance/cliff/tilt sensing, local voice,
English/Hindi/Marathi commands, and optional local notes and reminders.

Read [what every feature does](docs/CAPABILITIES.md), follow [terminal-by-terminal
wiring](docs/WIRING.md), and use the optional [build progress notebook](docs/PROGRESS.md)
to save checkmarks, notes and measurements in your browser. Export/import backups
let you keep progress across devices; no account or subscription is needed.

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
the companion website. The clone includes the original 90 expression WAVs, the
expression studio, and the local home activity catalog and UI. System packages and
optional model downloads are installed in the documented setup stages. The website is generated directly from these documents and
source files; it includes offline search, copy buttons and full source listings.

The hardware path uses two regulated 5 V USB banks, two TB6612FNG wheel drivers,
four N20 motors, two 28BYJ-48/ULN2003 head drives, TCRT5000 cliff modules, two TTP233
touch pads, two INMP441 I2S microphones, Camera Module 3 and a PAM8610 amplifier.
The PAM8610 needs an added regulated 5 V-to-9 V boost branch and a verified volume
limit for the 4 Ω / 3 W speakers. Confirm actual bank/current and breakout ratings
before wiring. The optional lithium/BMS system and INA219 are not part of this build.

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
- [Daily use and backups](docs/OPERATING.md): start, stop, status, private state recovery and maintenance.
- [Configuration](docs/CONFIGURATION.md): local overrides, languages, timezone, optional features.
- [Safety](docs/SAFETY.md) and [privacy](docs/PRIVACY.md): operating boundaries and data handling.
- [Architecture](docs/ARCHITECTURE.md): source layout and Pi/Mega responsibilities.
- [Website](docs/WEBSITE.md): offline build, free hosting and repository synchronization.
- [Contributing](CONTRIBUTING.md), [security](SECURITY.md) and [changes](CHANGELOG.md).

Project licensing remains an explicit maintainer choice. Public access alone does
not grant an open-source license; included third-party files retain their own licenses.

See [coverage of older EVE builds](docs/KNOWN_LIMITATIONS.md#coverage-of-older-eve-builds) for historical features and files outside this setup.
