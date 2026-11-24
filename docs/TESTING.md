# Testing and acceptance

Use two separate kinds of evidence: host checks prove specified software behavior;
hands-on tests prove the behavior of your assembled robot. Neither replaces the other.
No stage is pre-completed by this repository.

## Host verification before connecting hardware

From the repository root on Linux, with Python 3.11+ and `g++` installed:

```bash
python3 -m unittest discover -s tests -t . -v
python3 tools/check_repo.py
python3 -m compileall -q eve3 tools tests
```

The test suite includes a C++ harness that compiles and executes the actual Arduino
sketch against a fake core. It checks disabled outputs, corrupt/replayed frames,
heartbeat/command leases, cliffs, latches and head/drive exclusion. It is not an
ATmega binary or a bootloader test. The CI AVR job compiles the locked and enabled
sketch using `arduino:avr:mega` and the pinned AVR core.

For the website, Node 22 is the CI target; no npm dependencies are downloaded:

```bash
node tools/build_docs.mjs
python3 tools/check_site.py
node --check site/assets/site.js
```

The site check validates local files, links, fragments, source listings and offline
asset references. CI publishes the generated site as an artifact even when Pages
deployment is disabled. See [Website](WEBSITE.md).

## Simulation without electronics

In terminal 1:

```bash
./eve sim
```

In terminal 2, in the same directory:

```bash
EVE_SIM=1 ./eve status
EVE_SIM=1 ./eve ctl chat "who are you"
EVE_SIM=1 ./eve ctl drive left=40 right=40 seconds=1
```

Expect the chat to answer and the drive command to be refused by the shipped gates.
Simulation disables real serial, GPIO, camera, sound and external AI; data goes to
`data/sim`. It does not complete physical stages or unlock motion. Ctrl+C stops it.

## Hardware tests in order

Follow the exact commands and interactive tests in [Software setup](SETUP_GUIDE.md).
Run a stage's automatic check, perform its hands-on test, then record it only if
both passed. `./eve stage M04 done`, for example, records that specific test after
checks and an explicit builder confirmation; it does not repair or simulate hardware.

| Checkpoint | Expected observation | Stop when |
|---|---|---|
| M00–M02 | Install passes, face fullscreen, telemetry and fingerprint match | Any install, serial or firmware mismatch |
| M03 | Measured supply/current within selected component ratings; healthy Pi flags | Unknown current, voltage sag, bank trip, hot wiring |
| M04 | Each ToF responds independently; level tilt near zero; every cliff channel flips | Missing/stale reading, unstable or indistinguishable floor/edge values |
| M05 | Obstacle/cliff/tilt/USB loss/estop block and stop | Any unsafe reading accepted or latch clears while unsafe |
| M07 | Supported wheels turn forward; timeout and every stop path work | Wrong direction, continued motion, sliding support |
| M08 | Manual home and small jogs stay within observed clearance | Rubbing, cable tension, fallen head, missed/slipped steps |
| M09–M16 | Each fitted feature behaves as described | Incorrect indicator, memory consent, repeated reminder or self-triggered speech |
| M17 | 30-minute attended run and safe restart | Any unexpected motion, stale input, power fault or unreliable stop |

Voice is half-duplex and may be slow. A spoken stop is unavailable while speech is
playing or STT is busy. The physical actuator cutoff and direct CLI stop must remain
accessible; never rely on voice as the sole stop.

## Acceptance record

Keep a private record of source commit, firmware ID, component models, supply/current
measurements, sensor mounting height, floor types, head limits, stopping distance,
test date and any failures. Do not publish tokens, personal speech or private notes.

Measure actual stopping distance at the chosen PWM on each intended floor. The
configured obstacle distance is not a promise of a safe physical stopping margin.
Use a level enclosed test area, away from stairs, people and pets. Re-test after
changing wheels, mass, supply, sensor placement, wiring, firmware or motor settings.
