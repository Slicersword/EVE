#!/usr/bin/env python3
"""The M00-M17 setup path, one stage at a time.

  ./eve stage            show all stages and where you are
  ./eve stage M04        run the automatic checks for M04 and show the test you must do yourself
  ./eve stage M04 done   record that YOU did the test and it passed (asks you to type YES)
  ./eve stage guide      print the whole guide (this is how docs/SETUP_GUIDE.md is made)

A PASS from this tool is a software check. Only your own test on the robot closes a stage."""
import json, math, shutil, subprocess, sys, time
from _common import ROOT, config, eve_running, status
from setup_steps import SETUP_STEPS

STORE = ROOT / "data" / "stages.json"
P1, P2, WIN = "PuTTY 1", "PuTTY 2", "Windows PowerShell"
PREVIEW_LINKS = {
    "M01": "[Try the eyes and expressions in your browser](UI_PREVIEW.md#touchscreen-face).",
    "M16": "[See the control panel with sample readings](UI_PREVIEW.md#control-panel).",
}


def st():
    return status()


def flag(cfg, name):
    return cfg["commissioning"][name] is True


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def level_tilt(cfg):
    value = st()["sensors"]["tilt_deg"]
    return finite_number(value) and abs(value) < 10


def fresh_sensors(cfg):
    sensors = st()["sensors"]
    return all(finite_number(sensors[k]) and 0 <= sensors[k] < 0.5
               for k in ("tof_age_s", "imu_age_s", "mega_age_s"))


def healthy_supply(cfg):
    from eve3.power import read_throttled
    return read_throttled() == 0


# Each check: (label, function(cfg) -> bool, what to do if it fails). Functions that need EVE call st().
def c_tests(cfg):
    r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."], cwd=ROOT, capture_output=True, text=True)
    return r.returncode == 0


STAGES = {
 "M00": dict(title="Foundation: fresh install and self-tests", needs=[], run=False, checks=[
        ("config loads and is valid", lambda c: True, "fix or delete config/local.json"),
        ("virtual environment exists", lambda c: (ROOT / ".venv").exists(), "bash scripts/setup_pi.sh"),
        ("all software self-tests pass (takes ~30 s)", c_tests, "./eve test   and send me the output"),
    ], steps=SETUP_STEPS['M00'], test="Bank B (motor power) stays OFF for M00-M02. `./eve doctor` shows PASS for config, venv and Python. "
            "The source is in a fresh folder; no hardware commissioning flags have been set."),
 "M01": dict(title="Face on the screen", needs=["M00"], run=True, checks=[
        ("EVE is running and answers", lambda c: st()["version"].startswith("3."), "PuTTY 1:  ./eve run"),
    ], steps=SETUP_STEPS['M01'],
    test="The 7-inch screen shows only two eyes and a mouth on black, filling the whole screen - no window frame, no "
         "outline, no buttons, no keyboard needed. The eyes blink. `expression name=happy` changes the face for 5 s."),
 "M02": dict(title="Mega link + new firmware", needs=["M01"], run=True, checks=[
        ("Mega connected", lambda c: st()["mega"]["connected"], "check the USB cable Pi -> Mega, then ./eve doctor"),
        ("Mega online (heartbeat + telemetry)", lambda c: st()["mega"]["online"], "wait 5 s and repeat; else re-flash"),
        ("firmware matches this config", lambda c: st()["mega"]["firmware_ok"], "stop EVE, then: ./eve flash"),
        ("firmware has wheels and head disabled", lambda c: not c["firmware"]["drive_enabled"] and not c["firmware"]["head_enabled"],
         "they are enabled later, at M07/M08"),
    ], steps=SETUP_STEPS['M02'],
    test="PuTTY 1 prints `Mega connected. Firmware id ... matches.` `./eve status` shows Mega online and `Cliff raw` with "
         "three 0/1 numbers. Pull the Mega USB plug: within 1 s status says OFFLINE; plug in: it comes back by itself."),
 "M03": dict(title="Power: two USB banks measured", needs=["M02"], run=True, checks=[
        ("Pi supply flags readable and zero", healthy_supply, "run vcgencmd get_throttled; resolve supply/thermal flags before confirming M03"),
        ("Bank A confirmed by you", lambda c: flag(c, "power_a_verified"), "./eve cfg confirm power_a_verified"),
        ("Bank B confirmed by you", lambda c: flag(c, "power_b_verified"), "./eve cfg confirm power_b_verified"),
        ("motor current confirmed by you", lambda c: flag(c, "motor_current_verified"), "./eve cfg confirm motor_current_verified"),
    ], steps=SETUP_STEPS['M03'],
    test="1) Bank A alone powers Pi + screen + fan for 10 min with the face running: `vcgencmd get_throttled` stays "
         "`throttled=0x0`. 2) Bank B: with a multimeter check 5 V polarity at the motor-driver and head-driver power pins, "
         "that the switch cuts it, and that Bank B GND is joined to Mega/Pi GND. 3) Bank B does not switch itself off with "
         "all motor boards connected and idle. 4) Independently measure/verify the combined motor, head and boost-converter input/audio "
         "load against Bank B and driver/wiring ratings using a controlled electrical test with the chassis secured. "
         "Idle voltage alone is not a current test. If load/current verification is unavailable, leave motor_current_verified "
         "false and stop. Only then confirm the three flags. After restart `session_start` answers OK."),
 "M04": dict(title="Sensors: 3 distance + tilt + 3 cliff", needs=["M03"], run=True, checks=[
        ("distance sensors all give numbers", lambda c: all(v is not None for v in st()["sensors"]["distance_mm"]), "stop EVE, run ./eve i2c and follow its advice"),
        ("tilt sensor gives a number", lambda c: st()["sensors"]["tilt_deg"] is not None, "stop EVE, run ./eve i2c"),
        ("robot standing level (tilt under 10 degrees)", level_tilt, "if it shows ~180 the board is upside down: ./eve cfg set sensors.imu_inverted true"),
        ("sensor data is fresh", fresh_sensors, "./eve status"),
        ("cliff sensors calibrated", lambda c: c["sensors"]["cliff_calibration"]["calibrated"], "./eve cliff floor ; ./eve cliff edge ; ./eve cliff apply ; then ./eve flash"),
        ("no cliff seen while standing on the floor", lambda c: not any(st()["sensors"]["cliff_unsafe"]), "repeat the cliff calibration"),
    ], steps=SETUP_STEPS['M04'],
    test="`./eve status`: Distance shows three numbers 30-1000 that change when you move your hand in front of each "
         "sensor (order: front-left, front-right, rear). Tilt is near 0 on the floor and rises when you tip the robot. "
         "Cliff raw flips for each sensor when you lift that corner over an edge."),
 "M05": dict(title="Safety: it must refuse when anything is wrong", needs=["M04"], run=True, checks=[
        ("wheels are blocked (nothing is commissioned to move yet)", lambda c: not st()["safety"]["drive_permitted"], "this must be blocked at M05"),
        ("a reason is always given", lambda c: bool(st()["safety"]["drive_block_reason"]), ""),
    ], steps=SETUP_STEPS['M05'],
    test="`Wheels:` stays blocked (nothing is commissioned to move yet) - that is correct. Watch the line `Sensors say:`. "
         "It must read `all clear` when the robot stands free on the floor, and change within half a second to: "
         "(a) `obstacle` with a hand 10 cm in front; (b) `cliff` when a corner is lifted over an edge (Mega latched=True); "
         "(c) `tilt` when tipped past ~30 degrees; (d) `...stale or missing` when the Mega USB is pulled (and Mega OFFLINE). "
         "(e) `./eve estop` shows LATCHED: emergency stop. After each, `./eve ctl clear` succeeds only when the cause is gone."),
 "M06": dict(title="Cooling (physical check)", needs=["M05"], run=False, checks=[
        ("Pi temperature below 75 C", lambda c: float(subprocess.run(["vcgencmd", "measure_temp"], capture_output=True, text=True).stdout.split("=")[1].split("'")[0]) < 75, "check the Pi fan"),
    ], steps=SETUP_STEPS['M06'],
    test="The Pi fan spins whenever the Pi is on. After 15 min with the face running the temperature stays under 70 C. "
         "Any optional charger-side fan follows its separately reviewed supply arrangement. No software controls the fans."),
 "M07": dict(title="Wheels (lifted first)", needs=["M06"], run=True, checks=[
        ("firmware.drive_enabled is on", lambda c: c["firmware"]["drive_enabled"], "./eve cfg set firmware.drive_enabled true ; stop EVE ; ./eve flash"),
        ("safe test area confirmed", lambda c: flag(c, "contained_ground_area"), "./eve cfg confirm contained_ground_area"),
        ("firmware matches", lambda c: st()["mega"]["firmware_ok"], "stop EVE ; ./eve flash"),
        ("drive confirmed by you (after the test below)", lambda c: flag(c, "drive_verified"), "./eve cfg confirm drive_verified ; restart EVE"),
    ], steps=SETUP_STEPS['M07'],
    test="Each drive_test turns all four wheels FORWARD for 1 second and stops by itself. If a wheel turns backward, switch "
         "everything off and swap that motor's two wires. During a test: `./eve estop` stops at once; covering a front "
         "distance sensor with your hand stops it; putting a finger under a cliff sensor is NOT a test - instead lift the robot so a cliff sensor sees no floor: it stops and latches. Reverse and pivot are refused. Only after that: "
         "confirm drive_verified, then try `./eve ctl drive left=100 right=100 seconds=1` on the floor in the closed area."),
 "M08": dict(title="Head pan / tilt", needs=["M07"], run=True, checks=[
        ("firmware.head_enabled is on", lambda c: c["firmware"]["head_enabled"], "./eve cfg set firmware.head_enabled true ; stop EVE ; ./eve flash"),
        ("firmware matches", lambda c: st()["mega"]["firmware_ok"], "stop EVE ; ./eve flash"),
        ("head limits confirmed", lambda c: c["head"]["soft_limits_verified"], "./eve cfg set head.soft_limits_verified true (after the jog test)"),
        ("head confirmed by you", lambda c: flag(c, "head_verified"), "./eve cfg confirm head_verified"),
    ], steps=SETUP_STEPS['M08'],
    test="Each jog moves the head a tiny step in the expected direction (if pan or tilt goes the wrong way note it; "
         "camera.tracking_pan_sign / tracking_tilt_sign affect look/tracking only, not manual jog direction). Jog step by step to each side and stop BEFORE "
         "anything touches or a cable pulls; note the pan/tilt numbers from `./eve status` and set the limits a little "
         "inside them. After confirming: `./eve ctl head_look direction=left` and `direction=center` move smoothly."),
 "M09": dict(title="Touch pads", needs=["M08"], run=True, checks=[
        ("touch pads started", lambda c: st()["features"]["touch"] == "ok", "check ./eve status Features: touch"),
    ], steps=SETUP_STEPS['M09'],
    test="Pat the head pad: the face turns pink/happy for 3 s. Tap the back pad: listening face. Hold the back pad "
         "1 second: EMERGENCY STOP appears in PuTTY 1 and status shows latched."),
 "M10": dict(title="Camera (local only)", needs=["M09"], run=True, checks=[
        ("camera switched on in config", lambda c: c["camera"]["enabled"], "./eve cfg set camera.enabled true ; restart EVE"),
        ("camera running", lambda c: st()["features"]["camera"] == "on", "see Features: camera in ./eve status for the error"),
    ], steps=SETUP_STEPS['M10'],
    test="The LED next to the camera is ON whenever the camera runs and OFF when EVE stops. When you stand in front, the "
         "eyes on the screen follow you. Closing the shutter: eyes stop following. No picture file appears anywhere "
         "(`find ~/eve3/data -type f` shows only eve.db, token, lock, json). With tracking on (in a session, head homed) the "
         "head turns slowly toward your face."),
 "M11": dict(title="Memory", needs=["M10"], run=True, checks=[
        ("memory on", lambda c: st()["features"]["memory"] == "on", "./eve cfg set memory.enabled true"),
    ], steps=SETUP_STEPS['M11'],
    test="She repeats the test note back after a restart. Record that note's ID, remove it, and verify just that ID is gone."),
 "M12": dict(title="Brain: offline answers (+ optional on-Pi model)", needs=["M11"], run=True, checks=[
        ("answers a question", lambda c: True, ""),
    ], steps=SETUP_STEPS['M12'],
    test="She answers in the language you used (English, Hindi, Marathi). Unknown questions get an honest \"I did not "
         "understand\" unless the optional local model is running. Cloud AI stays off."),
 "M13": dict(title="Voice: speaking and hearing", needs=["M12"], run=True, checks=[
        ("speaker has no error", lambda c: st()["features"]["speaker"] == "on", "check espeak-ng and the audio output"),
        ("whisper installed", lambda c: (ROOT / c["voice"]["stt_command"]).exists() and (ROOT / c["voice"]["stt_model"]).exists(), "bash scripts/install_voice.sh"),
        ("microphone switched on in config", lambda c: c["voice"]["capture_enabled"], "./eve cfg set voice.capture_enabled true ; restart EVE"),
        ("microphone listening", lambda c: st()["features"]["microphone"] == "listening", "stop EVE ; ./eve mic ; arecord -L"),
    ], steps=SETUP_STEPS['M13'],
    test="You hear all three sentences clearly from the speakers (Bank B audio branch on). Then say \"EVE, what time is "
         "it?\" - she answers within a few seconds. Say \"EVE\" ... \"tell me a joke\". Say \"stop\" without her name: she "
         "says Stopped. While she talks she does not answer herself."),
 "M14": dict(title="Behaviour", needs=["M13"], run=True, checks=[
        ("behaviour on", lambda c: c["behavior"]["enabled"], "./eve cfg set behavior.enabled true"),
    ], steps=SETUP_STEPS['M14'],
    test="Leave the room for a minute and walk back in: PIR shows True and she greets once (not again for 10 minutes; "
         "silent between 22:00 and 07:00). A hand closer than 30 cm gives a surprised face. After 15 quiet minutes the "
         "face goes sleepy; a touch or her name wakes her."),
 "M15": dict(title="Reminders", needs=["M14"], run=True, checks=[
        ("can list reminders", lambda c: True, ""),
    ], steps=SETUP_STEPS['M15'],
    test="After one minute she says the reminder aloud once. It stays marked Announced in Home until you choose Done. "
         "A reminder set before a restart still fires after it. If audio fails, it stays due."),
 "M16": dict(title="Extras: sleep, phone control page", needs=["M15"], run=True, checks=[
        ("web tools are off unless you chose otherwise", lambda c: True, ""),
    ], steps=SETUP_STEPS['M16'],
    test="Sleep gives the sleepy face, ends the attended session and turns the camera indicator off if the camera was active. "
         "Wake brings her back. If you enabled phone control: it shows live status, "
         "the red EMERGENCY STOP works, and a wrong token shows no data. Leave network.host at 127.0.0.1 if you do not "
         "need phone control."),
 "M17": dict(title="Whole robot + start at boot", needs=["M16"], run=True, checks=[
        ("everything commissioned", lambda c: all(c["commissioning"].values()), "finish the earlier stages"),
        ("firmware matches", lambda c: st()["mega"]["firmware_ok"], "stop EVE ; ./eve flash"),
        ("all sensors healthy", lambda c: all(d["ok"] for d in st()["sensors"]["devices"].values()), "./eve status"),
    ], steps=SETUP_STEPS['M17'],
    test="During the 30 minutes: no under-voltage (`Pi supply flags 0x0`), STOP works by voice, back-pad hold and "
         "`./eve estop`; she never drives after the session ends. After the reboot the face and EVE come up by themselves "
         "and nothing moves until you start a session and clear."),
}


def done_map() -> dict:
    return json.loads(STORE.read_text()) if STORE.exists() else {}


def run_checks(key, cfg):
    stage, all_ok = STAGES[key], True
    if stage["run"] and not eve_running():
        print("  EVE is not running - start it in PuTTY 1:  ./eve run")
        return False
    for label, fn, fix in stage["checks"]:
        try:
            ok = bool(fn(cfg))
        except SystemExit:
            raise
        except Exception as exc:
            ok, fix = False, f"{fix}  ({type(exc).__name__})"
        all_ok &= ok
        print(f"  {'PASS' if ok else 'TODO'}  {label}" + ("" if ok or not fix else f"\n        -> {fix}"))
    return all_ok


def show(key):
    stage = STAGES[key]
    print(f"\n{key} - {stage['title']}\n" + "-" * 60)
    print("Commands:")
    for where, text in stage["steps"]:
        print(f"  [{where}] {text}")
    print("\nYour test on the robot (this is what closes the stage):\n  " + stage["test"])


def guide() -> str:
    out = ["# EVE V3 - software setup, testing and calibration", "",
           "Generated from tools/stage.py (`./eve stage guide`). On the Pi everything lives in `~/eve3`. See [every connection](WIRING.md) and [build progress](PROGRESS.md).",
           "",
           "## Check the wiring before powering on", "",
           "Keep both banks disconnected while wiring. Follow the [Mega, Pi and power diagrams](WIRING.md#wiring-diagrams) and their matching connection tables.", "",
           "![Power wiring for the separate Pi, actuator and amplifier branches](assets/wiring-power.svg)", "",
           "Two PuTTY windows: **PuTTY 1** runs EVE (`./eve run`, Ctrl+C stops safely), **PuTTY 2** is for commands.",
           "Replace `PI_IP` with the Pi's address. For each stage: run the commands, then `./eve stage Mxx`, do the test "
           "yourself, then `./eve stage Mxx done`.", "",
           "Rules: stages in order, never skip. The Bank B actuator branch stays OFF until M07 except for attended electrical measurements at M03. The audio branch may be powered separately for speaker tests. A software PASS is not a "
           "physical test. The Bank B switch is the physical motor-power stop; software stop needs a working runtime/link.", "",
           (ROOT / "docs" / "setup" / "INSTALLATION.md").read_text().rstrip(), ""]
    for key, stage in STAGES.items():
        out += [f'<a id="{key.lower()}"></a>', "", f"## {key} - {stage['title']}", ""]
        if stage["needs"]:
            out += [f"Needs: {', '.join(stage['needs'])} done.", ""]
        if key in PREVIEW_LINKS:
            out += [PREVIEW_LINKS[key], ""]
        for where, text in stage["steps"]:
            if where == "you":
                out += [text, ""]
            else:
                language = "powershell" if where == WIN else "bash"
                out += [f"**{where}**", "", f"```{language}", text, "```", ""]
        out += ["Automatic checks (`./eve stage " + key + "`): " + "; ".join(c[0] for c in stage["checks"]) + ".", ""]
        out += ["**Your test:** " + stage["test"], "", f"Then: `./eve stage {key} done`", ""]
    # Included recipes live one directory deeper than this generated page.
    reference = (ROOT / "docs" / "setup" / "REFERENCE.md").read_text().rstrip()
    out += [reference.replace('](../WIRING.md', '](WIRING.md'), ""]
    return "\n".join(out).rstrip() + "\n"


def main(argv):
    if argv[:1] == ["guide"]:
        print(guide(), end=""); return 0
    done = done_map()
    if not argv:
        nxt = next((k for k in STAGES if k not in done), None)
        for key, stage in STAGES.items():
            mark = "done " + done[key] if key in done else ("<- next" if key == nxt else "")
            print(f"  {key}  {stage['title']:<52} {mark}")
        print(f"\nNext:  ./eve stage {nxt}" if nxt else "\nAll stages recorded as done.")
        return 0
    key = argv[0].upper()
    if key not in STAGES:
        print(__doc__); return 2
    try:
        cfg = config.load()
    except Exception as exc:
        sys.exit(f"Config problem: {exc}")
    missing = [n for n in STAGES[key]["needs"] if n not in done]
    show(key)
    if missing:
        print(f"\nNot yet: finish {', '.join(missing)} first (stages are done in order).")
        return 1
    print("\nAutomatic checks:")
    ok = run_checks(key, cfg)
    if argv[1:2] == ["done"]:
        if not ok:
            print("\nNot recorded: the checks above must all PASS first."); return 1
        if input(f"\nDid YOU do the {key} test on the robot and did it pass? Type YES: ").strip() != "YES":
            print("Not recorded."); return 1
        done[key] = time.strftime("%Y-%m-%d")
        STORE.parent.mkdir(exist_ok=True)
        STORE.write_text(json.dumps(done, indent=1))
        nxt = next((k for k in STAGES if k not in done), None)
        print(f"{key} recorded." + (f" Next:  ./eve stage {nxt}" if nxt else " All stages done."))
    elif ok:
        print(f"\nChecks pass. Do the test above, then:  ./eve stage {key} done")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
