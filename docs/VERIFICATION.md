# Software coverage and verification

Use the feature table to check what ships in a fresh checkout and what to accept
on the assembled robot. The host suite uses temporary state and runs with
commissioning unset. The [current GitHub workflow runs](https://github.com/Slicersword/EVE/actions/workflows/verify.yml)
show which revision passed host, AVR and site checks.

| Subsystem | Verified in the checkout or host tests | Test on your Pi and Mega |
|---|---|---|
| Fresh install and firmware source | Required files, default configuration, generated firmware header, explicit port selection and simulated upload handling | M00–M02: Pi installation, full-screen desktop, successful upload and the matching live firmware fingerprint |
| Power and motion | Both actuator outputs locked in the shipped configuration. Real sketch logic tested for leases, cliffs, stop, and head/drive exclusion. Host tests cover stale link reconnect and complete voice motion phrases | M03/M05/M07/M08: measure both banks and drivers, find safe stop distance and head travel, exercise the cutoff and all stop paths |
| ToF, tilt and cliff | Incorrect, missing and stale input blocks movement. Failed I2C reads immediately invalidate the previous reading | M04: measure every channel at the actual mounting position, including dark floors and safe simulated edges |
| Face and sound cues | All 90 WAVs and artwork load from the checkout. Tested the Happy cue after the quiet interval and cancellation when blocked | M01/M12/M13: examine the face, play a selected cue, and verify safe speaker output |
| Touch, camera and sleep | Touch gestures and the sleep capture lifecycle are exercised in the host suite. Sleep ends the motion session | M09/M10/M16: tap/hold, confirm the visible LED and local face offsets, and observe that sleep releases the camera before wake reopens it |
| Local conversation | English/Hindi/Marathi text intents, wake words, offline responses and local privacy rules tested | M12/M13: verify language selection, both mic slots, recognition latency, and no responses to EVE's own voice |
| Overlapping audio | The optional backend selects the matched desktop echo source and sink and reports a missing route | M13 optional: verify the device names on the Pi and test real room feedback and recognition while the speaker plays |
| Home activities and reminders | Authenticated Home operations and restored spoken shortcuts, durable timers, older database upgrade and playback retry tested. Sample games, stories and text catalog ship in Git | M12/M15: use a game and a branching story, test a timer through restart, mark it Done, and confirm the Pi's own speaker produces audio |
| Website and progress | Offline and Pages rendering checks cover links, assets, source listings and progress persistence/export. Wiring diagrams are regenerated from the shipped pins | Open the guide on the device you will use and keep one private progress export |

For repeatable checks see [Testing](TESTING.md). For boundaries and earlier features
outside this build see [Known limitations](KNOWN_LIMITATIONS.md#coverage-of-older-eve-builds).
Current operating choices and labels to record are in [Build choices](DECISIONS.md).
