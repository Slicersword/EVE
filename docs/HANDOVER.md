> Original archive handover, retained as history. For the repository prepared on 24 November 2026, see [BUILD_GUIDE.md](BUILD_GUIDE.md), [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) and [VERIFICATION.md](VERIFICATION.md).

# EVE V3 — handover, 23 November 2026

## What was done today
Owner asked for a brand-new rebuild of the whole robot ("full robot, nothing left behind") and to run the
whole setup process again from M00, ignoring the old Pi state. So `EVE_SOURCE_V3/` was written from
scratch (package `eve3`). `EVA_MASTER_BACKUP_2026-11-18/` and `EVE_SOURCE_V2/` were read for the wiring,
pin map and history, and were **not modified**. Nothing was deployed to the Pi and no firmware was flashed.

## State
- Written on the PC, tested on the PC: **105 self-tests pass**, run three times from a clean copy.
- The Mega sketch is compiled on the PC against a fake Arduino core and driven by a scripted harness
  (13 of those tests). Eight deliberate bugs were injected into the firmware; seven were caught by the
  tests, one gap (head enable flag) was then covered. This is **not** an AVR compile — `arduino-cli`
  runs on the Pi at M02.
- Everything physical is still open: M00–M17 all unconfirmed, every commissioning flag false, wheels and
  head disabled in the firmware, cliff uncalibrated.
- The I2C fault from November is untouched and unexplained; `./eve i2c` is the first on-robot step that
  matters (M04). It now names each device and says what to check.

## Decisions (full text in docs/adr/)
1. **V3 from scratch, standard library first.** Only hardware drivers are installed with pip. One process,
   one composition root (`eve3/runtime.py`). No aiohttp, no plugin loader, no code generators.
2. **Firmware safety fixes** carried over from the V2 review: the cliff test is a digital level comparison
   that actually trips, a 1-second AVR watchdog, drive and head each have their own lease and enable flag,
   and the firmware reports a fingerprint of its own settings so a stale flash blocks motion.
3. **Privacy by default.** Camera and audio stay in RAM; cloud AI needs two switches and a key file, and
   sends one redacted sentence. Model output can never become a robot command.

## How to continue
`docs/SETUP_GUIDE.md`, or on the Pi `./eve stage`. The order matters: M00 install → M01 face → M02 flash
the Mega → M03 power measurements → **M04 the I2C blocker** → M05 safety refusals → ... Each stage has
copy-paste commands labelled by window and one test the owner does and confirms with `./eve stage Mxx done`.

`scripts/retire_old.sh` parks the old install (`~/eve_robot`, `~/eve_master`, old user services and
autostart entries) by **moving** them to `~/eva_old_<date>/` — nothing is deleted, and the old cliff
calibration is still inside that folder's `config/eve.json` if it is ever wanted.

## Open / not claimed
Real AVR compile and upload; every physical gate M00–M17; the I2C fault; whisper.cpp build on the Pi
(`scripts/install_voice.sh`, ~15 min); camera and microphone behaviour on the real hardware; audio echo
handling while speaking (currently half-duplex: EVE ignores the microphone while she talks).
