# Before you begin

Build EVE in this order: parts, mechanical assembly, unpowered wiring, software,
sensors, stop tests, then motion. You can run the host tests and simulation before
buying or connecting any electronics.

## Skills and tools

You need basic wire identification, polarity and continuity measurement, secure
crimping/soldering, and safe low-voltage wiring. Get help with protection and load
measurement if those are new to you. Do not improvise lithium-cell charging circuits.

| Tool or supply | Purpose |
|---|---|
| Computer with internet | Write the Pi image, download source and use SSH |
| microSD card and reader, or supported SSD boot storage | Raspberry Pi OS and source; allow space for optional models |
| Digital multimeter and suitable load/current measurement equipment | Continuity, voltage and component/supply acceptance |
| Screwdrivers, insulated standoffs, fasteners, cable ties | Secure mounting and strain relief |
| Suitable wire, connectors, insulation and protection | Rated for measured branch current |
| Stable chassis support | Lift all four wheels while keeping cliff sensors over safe targets |
| Accessible actuator-power cutoff | Physical stop independent of Pi software |

Do not place motor current through solderless breadboard contacts. A multimeter in
current mode must be connected according to its manual, in series with the load;
placing it across a supply can short the supply.

## Choose the supported platform

The software target is **Raspberry Pi 4B, Raspberry Pi OS Desktop (64-bit), Bookworm,
Python 3.11**, plus **Arduino Mega 2560**. A 2 GB Pi is the basic runtime target;
optional local speech/model latency must be measured. The display target is
1024×600 landscape, connected by HDMI and USB touch.

The installer uses Raspberry Pi OS packages (`raspi-config`, `raspi-utils`,
`python3-picamera2`). Generic Debian/Ubuntu, Lite without a desktop, Pi 5 and newer
OS releases need their own compatibility checks. Do not assume a current default
image is Bookworm. In Imager, select a Bookworm 64-bit Desktop image if offered,
or obtain it from Raspberry Pi's official OS archive and use “Use custom”.

## Prepare a fresh Pi

1. Install [Raspberry Pi Imager](https://www.raspberrypi.com/software/) on your computer.
2. Select Pi 4, the supported Desktop image, and the intended storage device. Writing
   the image erases that device; inspect the selected device carefully.
3. In customization, set your own username/password, hostname, Wi-Fi and locale.
   Enable SSH. Do not use example credentials or assume a default `pi` account.
4. Boot with a stable Pi power supply and the display. Leave actuator power disconnected.
   Complete the desktop's first-run setup. Enable desktop auto-login for kiosk use
   on a trusted physically controlled Pi, or log in locally each time.
5. Find the Pi's IP in your router's client list. Connect using PuTTY (SSH, port 22)
   or your computer's SSH client. Accept the first host key only for the intended Pi.
6. Follow [Software setup](SETUP_GUIDE.md). It provides both Git clone and ZIP routes,
   installs packages and enables I2C. No prior installation is required.

The Pi's display needs a real desktop session. SSH/PuTTY opens a terminal only.
`127.0.0.1` means the computer where a browser is running; the guide includes an SSH
tunnel for viewing the Pi's control page from another computer without RDP.

## Recognize a successful stage

`PASS` means the named software check passed. `TODO` or `MISSING` tells you what
still needs attention. A missing optional camera/voice package matters when you
reach its stage. A successful unit test does not turn on motors or complete wiring.

Read the hands-on test, observe its result, then record only that stage as done.
Stop when a required reading is missing or a measurement is unavailable.

Continue with [Parts and wiring](HARDWARE.md) and fill out [Build choices](DECISIONS.md).
