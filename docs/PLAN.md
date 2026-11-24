> Historical V3 rebuild plan from 23 November 2026. Current repository status and acceptance boundaries are in [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) and [VERIFICATION.md](VERIFICATION.md).

# EVE V3 — rebuild plan (written 2026-11-23)

Owner decision (2026-11-23): brand new V3 from scratch, full robot, old Pi state ignored, the whole
setup process is followed again from M00. Hardware and wiring are unchanged. V2 and the master backup
are reference only and are not edited.

## Blocker chain
Every motion gate needs a complete, fresh sensor frame (3x ToF + tilt + cliff) and a live Mega link.
So the order is fixed: M00 -> M01 -> M02 -> M03 -> M04 -> M05 -> (M06 physical) -> M07 -> M08 -> M09 ... M17.
Nothing after M04 that moves can be accepted until the I2C sensors answer on the real robot.

## Tasks (software = done on the PC and host-tested; robot = owner runs and confirms)

| ID | Stage | Goal | Files | Acceptance (host) | Observed on robot (owner confirms) | Rollback |
|---|---|---|---|---|---|---|
| T00 | M00 Core | config load/validate, owner overlay, stage tracker | eve3/config.py, tools/evecfg.py, tools/stage.py | config tests | `stage.py M00` all PASS | delete folder |
| T01 | M01 Face | full-screen eyes+mouth, no outline/buttons, local server | eve3/server.py, eve3/web/ | server tests | face fills the 1024x600 screen without F11 | close kiosk |
| T02 | M02 Mega | E1 framed serial, SYNC, heartbeat, new firmware | eve3/protocol.py, mega_link.py, firmware/ | protocol + link + firmware-sim tests | compile, upload, SYNC id matches | re-flash old sketch from archive |
| T03 | M03 Power | attended power session, Pi undervoltage check | eve3/power.py | power tests | owner measurements, `get_throttled` = 0x0 | flags stay false |
| T04 | M04 Sensors | ToF x3, MPU6050, cliff via Mega; I2C diagnosis | eve3/sensors.py, tools/i2c_diag.py | sensor tests with fakes | i2cdetect shows 0x68 + ToF; live values change | none (read only) |
| T05 | M05 Safety | fail-closed gate, latch, stale/None refused | eve3/safety.py | safety tests (every refusal path) | unplug test -> "unsafe"; cliff -> latched | n/a |
| T06 | M06 Cooling | physical check only (fans direct powered) | docs | n/a | Pi fan runs, temp OK | n/a |
| T07 | M07 Drive | gated drive, lease, no reverse/pivot by default | eve3/motion.py | motion tests | wheels lifted, tiny PWM, stops on lease/cliff | set drive_verified false |
| T08 | M08 Head | manual home, jog, soft limits | eve3/motion.py | head tests | STL marks aligned, jog <= 8 steps | head_release, flag false |
| T09 | M09 Touch | head/back TTP233 | eve3/touch.py | touch tests | pat -> happy face; back hold -> STOP | disable in config |
| T10 | M10 Camera | local face detect, LED, optional head tracking | eve3/camera.py | tracking math tests | LED on while camera on; nothing saved | camera.enabled false |
| T11 | M11 Memory | local sqlite notes/reminders, erase | eve3/memory.py | memory tests | note saved, erase works | delete data/eve.db |
| T12 | M12 Local AI | offline dialogue + optional local llama-server | eve3/ai.py | ai tests, privacy guard tests | answers in EN/HI/MR | ai.local_llm false |
| T13 | M13 Voice | espeak TTS, arecord capture, whisper STT, wake phrase | eve3/voice.py, intents.py | intent + VAD tests | speaks; hears "EVE, time?" | capture_enabled false |
| T14 | M14 Behavior | greet, idle, night, obstacle face | eve3/behavior.py | behavior tests | PIR greet once | behavior.enabled false |
| T15 | M15 Scheduler | reminders/timers | eve3/scheduler.py | scheduler tests | "remind me in 1 minute" fires | n/a |
| T16 | M16 Integrations | read-only web tools (off), sleep | eve3/integrations.py | allow-list tests | sleep/wake | off by default |
| T17 | M17 Integration | everything together, service install | eve3/runtime.py, systemd/ | full suite | 30 min attended run | disable service |

## Checkpoints (owner, on the robot)
- CP1 after M02: firmware id on screen equals the generated id.
- CP2 after M05: pull the Mega USB / cover a ToF sensor -> motion permitted goes false within 0.5 s.
- CP3 after M08: wheels + head only move inside an attended session and stop when it ends.
- CP4 after M17: 30 minute attended run, no undervoltage, STOP works from touch, voice and web.

A software PASS never closes a physical gate. Owner-reported errors stay open until the owner says "sorted".
