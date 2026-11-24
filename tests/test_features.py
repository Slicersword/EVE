import array, json, os, tempfile, threading, time, unittest, urllib.error, urllib.request
from pathlib import Path
from eve3 import ai, camera, intents, integrations, voice
from eve3.behavior import Behavior, Context
from eve3.memory import Memory
from eve3.runtime import Runtime, VOICE_COMMANDS
from eve3.scheduler import Scheduler
from eve3.server import host_allowed, serve
from eve3.sim import FakeMega
from eve3.touch import TouchPads
from eve3 import firmware
from tests.helpers import Clock, cfg_with


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.m = Memory(":memory:", max_notes=3)

    def test_notes_need_consent_and_are_bounded(self):
        for consent in (False, None, "yes", 1):
            with self.assertRaises(PermissionError):
                self.m.add_note("keys are in the drawer", consent)
        self.m.add_note("  keys are\nin the drawer \x00", True)
        self.assertEqual(self.m.notes()[0]["text"], "keys are in the drawer")
        for bad in ("", "   ", "x" * 301, None, 5):
            with self.assertRaises(ValueError):
                self.m.add_note(bad, True)
        self.m.add_note("b", True); self.m.add_note("c", True)
        with self.assertRaises(ValueError):
            self.m.add_note("d", True)
        self.assertTrue(self.m.forget_note(self.m.notes()[0]["id"]))
        self.assertFalse(self.m.forget_note(999))

    def test_reminders_and_erase(self):
        self.m.add_reminder(100, "milk"); self.m.add_reminder(200, "call")
        self.assertEqual(self.m.pop_due(150), ["milk"])
        self.assertEqual(self.m.pop_due(150), [])                            # fires once
        self.m.add_note("n", True); self.m.put("k", "v")
        self.m.erase_all()
        self.assertEqual((self.m.notes(), self.m.pending_reminders(), self.m.get("k")), ([], [], None))

    def test_file_is_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = Memory(Path(tmp) / "d" / "eve.db")
            if os.name == "posix":
                self.assertEqual(os.stat(m.path).st_mode & 0o077, 0)
            m.close()

    def test_sql_text_is_data_not_code(self):
        self.m.add_note("x'); DROP TABLE notes;--", True)
        self.assertEqual(len(self.m.notes()), 1)


class SchedulerTests(unittest.TestCase):
    def test_add_in_tick_and_limits(self):
        clock = Clock(1_000_000.0)
        s = Scheduler(Memory(":memory:"), clock=clock)
        for bad in (0, 4, -5, 8 * 86400, "60", None):
            self.assertFalse(s.add_in(bad, "x")[0], bad)
        self.assertTrue(s.add_in(60, "medicine")[0])
        self.assertEqual(s.tick(), [])
        clock.advance(61)
        self.assertEqual(s.tick(), ["medicine"])
        self.assertEqual(s.tick(), [])

    def test_add_at_uses_local_time_and_rolls_to_tomorrow(self):
        clock = Clock(1_700_000_000.0)                                      # 2023-11-14 22:13:20 UTC = 03:43 IST next day
        s = Scheduler(Memory(":memory:"), clock=clock, utc_offset_minutes=330)
        s.add_at(4, 0, "soon"); s.add_at(3, 0, "tomorrow")
        pending = {p["text"]: p["in_s"] for p in s.pending()}
        self.assertAlmostEqual(pending["soon"], 16 * 60 + 40, delta=2)
        self.assertAlmostEqual(pending["tomorrow"], 86400 - 43 * 60 - 20, delta=2)
        self.assertFalse(s.add_at(24, 0, "x")[0])


class IntentTests(unittest.TestCase):
    def test_stop_in_three_languages_wins(self):
        for text in ("stop", "EVE STOP!", "ruk ja", "रुको", "थांब", "thamb", "bas", "please stop and go forward"):
            self.assertEqual(intents.parse(text).name, "stop", text)

    def test_commands(self):
        cases = {"go forward": "forward", "पुढे ये": "forward", "aage chal": "forward", "turn left": "turn_left",
                 "दाएं मुड़": "turn_right", "look at me": "look_center", "वर बघ": "look_up", "go to sleep": "sleep",
                 "उठ जा": "wake", "what time is it": "time", "किती वाजले": "time", "tell me a joke": "joke",
                 "एक गोष्ट सांग": "story", "who are you": "who", "तू कोण आहेस": "who", "namaste": "greet",
                 "what do you remember": "recall"}
        for text, name in cases.items():
            got = intents.parse(text)
            self.assertIsNotNone(got, text)
            self.assertEqual(got.name, name, text)

    def test_words_inside_other_words_do_not_match(self):
        for text in ("this history lesson", "unstoppable", "basket", "", "   ", "!!!"):
            self.assertIsNone(intents.parse(text), text)

    def test_remind_and_remember(self):
        r = intents.parse("remind me in 5 minutes to take medicine")
        self.assertEqual((r.name, r.args), ("remind", {"seconds": 300, "text": "take medicine"}))
        self.assertEqual(intents.parse("५ मिनट बाद याद दिलाना दवाई").args, {"seconds": 300, "text": "दवाई"})
        self.assertEqual(intents.parse("2 तास नंतर आठवण कर दूध").args["seconds"], 7200)
        self.assertEqual(intents.parse("set a timer for 30 seconds").args, {"seconds": 30, "text": "timer"})
        self.assertEqual(intents.parse("remind me").name, "remind_unclear")
        self.assertEqual(intents.parse("remember that keys are in the drawer").args["text"], "keys are in the drawer")
        self.assertEqual(intents.parse("remember").name, "remember_unclear")

    def test_wake_word(self):
        wake = ["eve", "eva", "ईवा"]
        self.assertEqual(intents.strip_wake("Hey Eva, what time is it?", wake), (True, "what time is it"))
        self.assertEqual(intents.strip_wake("अरे ईवा थांब", wake), (True, "थांब"))
        self.assertEqual(intents.strip_wake("everyone is here", wake), (False, "everyone is here"))
        self.assertEqual(intents.strip_wake("Eve", wake), (True, ""))


class BrainTests(unittest.TestCase):
    def brain(self, cfg=None, post=None):
        self.memory = Memory(":memory:")
        self.posts = []
        def default_post(url, payload, timeout, headers=None):
            self.posts.append((url, payload, headers)); return "model says hi"
        cfg = cfg or cfg_with()
        return ai.Brain(cfg, self.memory, Scheduler(self.memory), clock=lambda: 1_700_000_000.0, post=post or default_post)

    def test_language_detection(self):
        self.assertEqual(ai.detect_lang("what time is it"), "en")
        self.assertEqual(ai.detect_lang("किती वाजले"), "mr")
        self.assertEqual(ai.detect_lang("कितने बजे हैं"), "hi")
        self.assertEqual(ai.detect_lang("tu kasa ahes"), "mr")
        self.assertEqual(ai.detect_lang("tum kaise ho"), "hi")
        for text, lang in (("एक विनोद सांग", "mr"), ("एक चुटकुला सुनाओ", "hi"), ("मला एक गोष्ट सांग", "mr"),
                           ("मुझे कहानी सुनाओ", "hi"), ("तू कोण आहेस", "mr"), ("तुम कौन हो", "hi"), ("नमस्कार", "mr")):
            self.assertEqual(ai.detect_lang(text), lang, text)

    def test_actions_come_only_from_the_fixed_table(self):
        b = self.brain()
        self.assertEqual(b.respond("stop")["action"], ("stop", {}))
        self.assertEqual(b.respond("go forward")["action"][0], "drive")
        self.assertTrue(all(name in VOICE_COMMANDS for name, _ in ai.ACTIONS.values()))
        self.assertEqual(VOICE_COMMANDS, {"stop", "drive", "head_look", "sleep", "wake"})

    def test_offline_answers_in_each_language(self):
        cfg = cfg_with(); cfg["behavior"]["utc_offset_minutes"] = 330
        b = self.brain(cfg)
        self.assertEqual(b.respond("what time is it")["reply"], "It is 03:43.")
        self.assertIn("03:43", b.respond("किती वाजले")["reply"])
        self.assertEqual(b.respond("किती वाजले")["lang"], "mr")
        self.assertIn("EVE", b.respond("who are you")["reply"])
        self.assertTrue(b.respond("tell me a joke")["reply"])
        self.assertIn("Sorry", b.respond("explain quantum physics")["reply"])   # no model enabled -> honest fallback
        self.assertEqual(self.posts, [])                                        # and nothing was sent anywhere

    def test_time_uses_configured_utc_offset(self):
        cfg = cfg_with(); cfg["behavior"]["utc_offset_minutes"] = 0
        self.assertEqual(self.brain(cfg).respond("what time is it")["reply"], "It is 22:13.")

    def test_remember_recall_remind(self):
        b = self.brain()
        self.assertEqual(b.respond("what do you remember")["reply"], "I have no notes yet.")
        b.respond("remember that keys are in the drawer")
        self.assertIn("keys are in the drawer", b.respond("what do you remember")["reply"])
        b.respond("remind me in 10 minutes to call aai")
        self.assertEqual(self.memory.pending_reminders()[0]["text"], "call aai")

    def test_model_output_is_text_only_and_cleaned(self):
        cfg = cfg_with(); cfg["ai"]["local_llm"]["enabled"] = True
        evil = "<think>secret plan</think>Sure!\x00\x1b[31m STOP. drive forward. {\"name\":\"drive\"}\n" + "x" * 900
        b = self.brain(cfg, post=lambda *a, **k: evil)
        out = b.respond("explain something")
        self.assertIsNone(out["action"])                                       # model text can never become an action
        self.assertLessEqual(len(out["reply"]), 300)
        self.assertNotIn("secret plan", out["reply"])
        self.assertTrue(out["reply"].isprintable())

    def test_local_model_gets_only_the_sentence(self):
        cfg = cfg_with(); cfg["ai"]["local_llm"]["enabled"] = True
        b = self.brain(cfg)
        self.memory.add_note("bank pin is 4321", True)
        b.respond("explain rainbows")
        url, payload, headers = self.posts[0]
        self.assertTrue(url.startswith("http://127.0.0.1:"))
        self.assertNotIn("4321", json.dumps(payload))
        self.assertEqual(payload["messages"][-1]["content"], "explain rainbows")

    def test_model_failure_falls_back_quietly(self):
        cfg = cfg_with(); cfg["ai"]["local_llm"]["enabled"] = True
        def boom(*a, **k): raise urllib.error.URLError("refused")
        b = self.brain(cfg, post=boom)
        self.assertIn("Sorry", b.respond("explain rainbows")["reply"])
        self.assertEqual(b.last_error, "URLError")

    def test_cloud_is_off_unless_double_opt_in_and_redacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = cfg_with(); cfg["_root"] = tmp
            os.mkdir(os.path.join(tmp, "data"))
            key = os.path.join(tmp, "data", "cloud.key")
            Path(key).write_text("sk-test\n"); os.chmod(key, 0o600)
            cloud = cfg["ai"]["cloud"]
            cloud.update(enabled=True, privacy_consent=False, endpoint="https://example.invalid/v1/chat", model="m")
            b = self.brain(cfg)
            b.respond("explain rainbows")
            self.assertEqual(self.posts, [])                                   # consent missing -> nothing sent
            cloud["privacy_consent"] = True
            self.memory.add_note("secret family note", True)
            b.respond("call me on 98765 43210 or a.b@mail.com about rainbows")
            url, payload, headers = self.posts[0]
            sent = json.dumps(payload)
            self.assertNotIn("98765", sent); self.assertNotIn("mail.com", sent); self.assertNotIn("secret family note", sent)
            self.assertEqual(headers["Authorization"], "Bearer sk-test")
            cloud["max_requests_per_day"] = 1
            b.respond("explain clouds")
            self.assertEqual(len(self.posts), 1)                               # daily limit
            if os.name == "posix":
                os.chmod(key, 0o644); cloud["max_requests_per_day"] = 50
                b.respond("explain rain")
                self.assertEqual(len(self.posts), 1)                           # world-readable key refused
            cloud["send_private_data"] = True; os.chmod(key, 0o600)
            b.respond("explain snow")
            self.assertEqual(len(self.posts), 1)

    def test_redact(self):
        self.assertEqual(ai.redact("mail a@b.co or 020-2555-1234 see http://x.y/z"), "mail [email] or [number] see [link]")


class VoiceTests(unittest.TestCase):
    @staticmethod
    def pcm(amplitude, chunks=1):
        return array.array("h", [amplitude, -amplitude] * 800).tobytes() * chunks

    def test_rms(self):
        self.assertEqual(voice.rms(b""), 0.0)
        self.assertAlmostEqual(voice.rms(self.pcm(1000)), 1000.0, delta=1)

    def test_segmenter_cuts_speech_and_ignores_clicks(self):
        seg = voice.Segmenter(threshold=500, silence_s=0.3, max_s=2.0, min_s=0.3)
        out = [seg.feed(self.pcm(0)) for _ in range(5)]
        out += [seg.feed(self.pcm(2000)) for _ in range(5)]
        out += [seg.feed(self.pcm(0)) for _ in range(3)]
        got = [o for o in out if o]
        self.assertEqual(len(got), 1)
        self.assertEqual(len(got[0]), 3200 * (2 + 5 + 3))                      # 2 lead-in + speech + trailing pause
        out = [seg.feed(self.pcm(2000))] + [seg.feed(self.pcm(0)) for _ in range(3)]
        self.assertFalse(any(out))                                             # one loud chunk = click, dropped
        out = [seg.feed(self.pcm(2000)) for _ in range(25)]
        self.assertEqual(len([o for o in out if o]), 1)                        # cut at max length

    def test_speaker_uses_argument_list_and_cleans_text(self):
        calls = []
        sp = voice.Speaker(cfg_with(), run=lambda args, **kw: calls.append((args, kw)))
        sp.speak_now(voice.clean_speech("-v evil; rm -rf /\n\x07hello"), "hi")
        args, kw = calls[0]
        self.assertEqual(args[:5], ["espeak-ng", "-v", "hi", "-s", "150"])
        self.assertEqual(args[5:], ["--", "-v evil; rm -rf / hello"])
        self.assertNotIn("shell", kw)
        self.assertFalse(sp.speaking)
        self.assertFalse(sp.say("", "en"))
        self.assertLessEqual(len(voice.clean_speech("x" * 999)), 300)

    def test_speaker_reports_nonzero_exit_without_exposing_speech(self):
        from types import SimpleNamespace
        speaker = voice.Speaker(cfg_with(), run=lambda *args, **kwargs: SimpleNamespace(returncode=2))
        speaker.speak_now("private words", "en")
        self.assertEqual(speaker.last_error, "speech command exited 2")
        self.assertFalse(speaker.speaking)

    def test_transcribe_deletes_the_clip(self):
        seen = {}
        class R: stdout = " hello eve \n"
        def run(args, **kw):
            seen["path"] = args[args.index("-f") + 1]
            seen["existed"] = os.path.exists(seen["path"])
            return R()
        cfg = cfg_with()
        self.assertEqual(voice.transcribe(cfg, self.pcm(1000, 5), run=run), "hello eve")
        self.assertTrue(seen["existed"])
        self.assertFalse(os.path.exists(seen["path"]))
        def boom(args, **kw):
            seen["path"] = args[args.index("-f") + 1]; raise TimeoutError()
        with self.assertRaises(TimeoutError):
            voice.transcribe(cfg, self.pcm(1000, 5), run=boom)
        self.assertFalse(os.path.exists(seen["path"]))
        class Blank: stdout = "[BLANK_AUDIO]"
        self.assertEqual(voice.transcribe(cfg, self.pcm(0, 5), run=lambda *a, **k: Blank()), "")

    def test_listener_ignores_own_voice(self):
        heard, speaking = [], [True]
        lis = voice.Listener(cfg_with(), heard.append, lambda: speaking[0], transcriber=lambda cfg, pcm: "hello")
        for amp in [3000] * 6 + [0] * 8:
            lis.handle_chunk(self.pcm(amp))
        self.assertEqual(heard, [])
        speaking[0] = False
        for amp in [3000] * 6 + [0] * 8:
            lis.handle_chunk(self.pcm(amp))
        self.assertEqual(heard, ["hello"])


class CameraBehaviorTouchTests(unittest.TestCase):
    def test_face_offset_and_tracking_step(self):
        self.assertIsNone(camera.face_offset([], 640, 360))
        self.assertEqual(camera.face_offset([(270, 130, 100, 100)], 640, 360), (0.0, 0.0))
        dx, dy = camera.face_offset([(0, 0, 10, 10), (500, 200, 120, 120)], 640, 360)   # biggest face wins
        self.assertGreater(dx, 0.5); self.assertGreater(dy, 0.3)
        self.assertEqual(camera.tracking_step(None), (0, 0))
        self.assertEqual(camera.tracking_step((0.05, -0.05)), (0, 0))
        self.assertEqual(camera.tracking_step((0.5, -0.5)), (8, -8))
        self.assertEqual(camera.tracking_step((0.5, -0.5), pan_sign=-1), (-8, -8))

    def test_behavior(self):
        clock = Clock(1_700_000_000.0 + 8 * 3600)                              # 11:43 IST
        cfg = cfg_with(); cfg["behavior"]["utc_offset_minutes"] = 330
        b = Behavior(cfg, clock=clock)
        now = clock()
        self.assertEqual(b.tick(Context(last_interaction=now)), {"expression": "idle", "greet": False})
        out = b.tick(Context(presence=True, last_interaction=now))
        self.assertEqual(out, {"expression": "happy", "greet": True})
        self.assertFalse(b.tick(Context(presence=True, last_interaction=now))["greet"])     # only on arrival
        b.tick(Context(last_interaction=now)); clock.advance(60)
        self.assertFalse(b.tick(Context(presence=True, last_interaction=now))["greet"])     # cool-down
        self.assertEqual(b.tick(Context(latched=True, speaking=True))["expression"], "alert")
        self.assertEqual(b.tick(Context(speaking=True, last_interaction=clock()))["expression"], "speaking")
        self.assertEqual(b.tick(Context(obstacle_mm=200, last_interaction=clock()))["expression"], "surprised")
        clock.advance(16 * 60)
        self.assertEqual(b.tick(Context(last_interaction=now))["expression"], "sleepy")
        self.assertTrue(b.sleeping)
        b.tick(Context(presence=True, last_interaction=now))
        self.assertFalse(b.sleeping)

    def test_behavior_is_quiet_at_night(self):
        clock = Clock(1_700_000_000.0)                                         # 03:43 IST
        cfg = cfg_with(); cfg["behavior"]["utc_offset_minutes"] = 330
        b = Behavior(cfg, clock=clock)
        self.assertTrue(b.is_night())
        self.assertEqual(b.tick(Context(presence=True, last_interaction=clock())), {"expression": "happy", "greet": False})

    def test_touch(self):
        events, made = [], []
        class Btn:
            def __init__(self, pin, hold): made.append(self); self.pin = pin
            def close(self): pass
        t = TouchPads(cfg_with(), lambda: events.append("head"), lambda: events.append("tap"), lambda: events.append("hold"), Btn)
        t.start()
        head, back = made
        self.assertEqual((head.pin, back.pin), (27, 22))
        head.when_pressed(); back.when_released()
        back.when_held(); back.when_released()                                  # release after a hold is not a tap
        self.assertEqual(events, ["head", "tap", "hold"])
        def broken(pin, hold): raise RuntimeError("no gpio")
        t2 = TouchPads(cfg_with(), None, None, None, broken); t2.start()
        self.assertIn("no gpio", t2.error)                                      # reported, not fatal


class IntegrationToolTests(unittest.TestCase):
    def test_off_by_default_and_allow_list(self):
        with self.assertRaises(PermissionError):
            integrations.call(cfg_with(), "wikipedia", "Pune")
        cfg = cfg_with(); cfg["integrations"]["web_tools_enabled"] = True
        with self.assertRaises(KeyError):
            integrations.call(cfg, "shell", "ls")

    def test_inputs_validated_and_output_bounded(self):
        urls = []
        def fetch(url): urls.append(url); return {"extract": "A " * 900, "rates": {"INR": 83.2}}
        self.assertLessEqual(len(integrations.wikipedia("Pune city", fetch)), 400)
        self.assertIn("Pune%20city", urls[0])
        for bad in ("", "../../etc/passwd", "a" * 80, "x?y=1", "a/b"):
            with self.assertRaises(ValueError):
                integrations.wikipedia(bad, fetch)
        self.assertEqual(integrations.exchange_rate("usd", "inr", fetch), 83.2)
        with self.assertRaises(ValueError):
            integrations.exchange_rate("US", "INR", fetch)


class RuntimeServerTests(unittest.TestCase):
    """Whole robot on the pretend Mega: every command path, the web API and the voice path."""

    class Dev:
        def __init__(self, value): self.value = value
        def start(self): pass
        def sample(self):
            if isinstance(self.value, Exception): raise self.value
            return self.value
        def close(self): pass

    class Quiet:
        enabled, speaking, last_error = True, False, ""
        def __init__(self): self.said = []
        def start(self): pass
        def stop(self): pass
        def say(self, text, lang="en"): self.said.append((text, lang)); return True

    def boot(self, cfg=None, tof=(600.0, 600.0, 600.0), fw_match=True):
        cfg = cfg or cfg_with(all=True)
        cfg["touch"]["enabled"] = False
        self.cfg = cfg
        self.mega = FakeMega(firmware_id=firmware.firmware_id(cfg) if fw_match else "old000000000",
                             drive_enabled=cfg["firmware"]["drive_enabled"], head_enabled=cfg["firmware"]["head_enabled"])
        self.voice = self.Quiet()
        rt = Runtime(cfg, opener=lambda: self.mega, tof=self.Dev(tof), imu=self.Dev(1.0), throttled=lambda: 0,
                     speaker=self.voice, memory=Memory(":memory:"))
        rt.settle_s = 0
        rt.start()
        self.addCleanup(rt.stop)
        self.wait(lambda: rt.link.online() and rt.hub.snapshot().tof_at > 0 and rt.hub.snapshot().cliff_at > 0)
        return rt

    def wait(self, cond, timeout=4.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if cond():
                return
            time.sleep(0.02)
        self.fail("condition not reached in time")

    def arm(self, rt):
        self.assertEqual(rt.execute("session_start", {"minutes": 5})[0], True)
        self.assertEqual(rt.execute("clear"), (True, "cleared"))
        self.wait(lambda: rt.link.telemetry.get("latched") is False)

    def test_shipped_config_nothing_moves(self):
        rt = self.boot(cfg_with())
        for name, args in (("session_start", {"minutes": 5}), ("clear", {}), ("drive", {"left": 100, "right": 100}),
                           ("drive_test", {"left": 60, "right": 60, "wheels_lifted": True}), ("head_home", {"confirm": True}),
                           ("head_jog", {"pan": 4, "confirm": True}), ("head_look", {"direction": "left"})):
            self.assertFalse(rt.execute(name, args)[0], name)
        self.assertFalse(any(p.startswith(("DRIVE,1", "DRIVE,6", "HEAD", "HOMESET")) for p in self.mega.log))
        s = rt.status()
        self.assertFalse(s["safety"]["drive_permitted"] or s["safety"]["head_permitted"])
        self.assertEqual(len(s["commissioning"]["missing"]), 6)

    def test_full_drive_cycle_and_obstacle_stop(self):
        rt = self.boot()
        self.assertFalse(rt.execute("drive", {"left": 100, "right": 100})[0])       # not armed yet
        self.arm(rt)
        self.assertEqual(rt.execute("drive", {"left": 100, "right": 100, "seconds": 2.0}), (True, "moving"))
        self.wait(lambda: self.mega.left == 100)
        time.sleep(0.5)
        self.assertEqual(self.mega.left, 100)                                       # kept alive by renewals
        rt.reader.devices["tof"][0].value = (100.0, 600.0, 600.0)                   # hand in front
        self.wait(lambda: self.mega.left == 0, 1.0)
        self.assertEqual(rt.drive.last_stop_reason, "obstacle")
        self.assertFalse(rt.status()["safety"]["drive_permitted"])

    def test_cliff_latches_everything(self):
        rt = self.boot(); self.arm(rt)
        rt.execute("drive", {"left": 100, "right": 100, "seconds": 2.0})
        self.wait(lambda: self.mega.left == 100)
        self.mega.cliff = [1, 1, 0]
        self.wait(lambda: self.mega.left == 0 and rt.gate.latched == "cliff", 1.5)
        self.mega.cliff = [1, 1, 1]
        time.sleep(0.3)
        self.assertFalse(rt.execute("drive", {"left": 100, "right": 100})[0])       # still latched
        self.assertTrue(rt.execute("clear")[0])
        self.wait(lambda: rt.link.telemetry.get("latched") is False)
        self.assertTrue(rt.execute("drive", {"left": 100, "right": 100})[0])

    def test_sensor_loss_and_link_loss_stop_motion(self):
        rt = self.boot(); self.arm(rt)
        rt.execute("drive", {"left": 100, "right": 100, "seconds": 2.0})
        self.wait(lambda: self.mega.left == 100)
        rt.reader.devices["imu"][0].value = OSError("i2c gone")
        self.wait(lambda: rt.drive.active is None, 1.5)
        self.assertIn("tilt", rt.drive.last_stop_reason)
        rt2 = self.boot(); self.arm(rt2)
        rt2.execute("drive", {"left": 100, "right": 100, "seconds": 2.0})
        self.wait(lambda: self.mega.left == 100)
        self.mega.silent = True
        self.wait(lambda: rt2.drive.active is None, 1.5)
        self.assertFalse(rt2.status()["mega"]["online"])

    def test_firmware_mismatch_blocks_motion(self):
        rt = self.boot(fw_match=False)
        rt.execute("session_start", {"minutes": 5}); rt.execute("clear")
        ok, why = rt.execute("drive", {"left": 100, "right": 100})
        self.assertFalse(ok); self.assertIn("firmware", why)

    def test_estop_from_touch_and_soft_stop(self):
        rt = self.boot(); self.arm(rt)
        rt.execute("drive", {"left": 100, "right": 100, "seconds": 2.0})
        self.wait(lambda: self.mega.left == 100)
        self.assertTrue(rt.execute("stop")[0])
        self.wait(lambda: self.mega.left == 0, 1.0)
        self.assertEqual(rt.gate.latched, "")
        rt.execute("drive", {"left": 100, "right": 100, "seconds": 2.0})
        rt._touch_back_hold()
        self.wait(lambda: self.mega.latched and self.mega.left == 0, 1.0)
        self.assertFalse(rt.execute("drive", {"left": 100, "right": 100})[0])

    def test_head_home_jog_and_look(self):
        rt = self.boot(); self.arm(rt)
        self.assertFalse(rt.execute("head_home", {})[0])
        self.assertTrue(rt.execute("head_home", {"confirm": True})[0])
        self.wait(lambda: rt.head.homed)
        self.assertTrue(rt.execute("head_jog", {"pan": 8, "confirm": True})[0])
        self.wait(lambda: self.mega.pan == 8 and rt.head.target is None)
        self.assertFalse(rt.execute("head_look", {"direction": "left"})[0])         # limits not verified
        self.assertFalse(rt.execute("head_look", {"direction": "sideways"})[0])
        rt.head.limits_verified = True
        self.assertTrue(rt.execute("head_look", {"direction": "left"})[0])
        self.wait(lambda: self.mega.pan == -200)

    def test_voice_can_only_use_the_allowed_commands(self):
        rt = self.boot(); self.arm(rt)
        for name in ("clear", "session_start", "estop", "head_home", "head_jog", "drive_test", "erase_memory", "note_add", "say"):
            ok, why = rt.execute(name, {"confirm": True, "minutes": 5}, source="voice")
            self.assertFalse(ok, name); self.assertIn("owner", why)
        out = rt.converse("go forward")
        self.assertEqual(out["action"], {"command": "drive", "ok": True, "message": "moving"})
        out = rt.converse("रुक जा")
        self.assertEqual(out["action"]["command"], "stop")
        self.wait(lambda: self.mega.left == 0, 1.0)
        rt.session.end()
        out = rt.converse("go forward")
        self.assertFalse(out["action"]["ok"])
        self.assertIn("attended", out["reply"])                                     # she says why not

    def test_wake_word_rules(self):
        rt = self.boot(cfg_with())
        rt._heard("what time is it")                                               # no wake word: ignored
        self.assertEqual(self.voice.said, [])
        rt._heard("Eve, what time is it")
        self.assertEqual(len(self.voice.said), 1)
        rt._heard("and tell me a joke")                                            # follow-up window
        self.assertEqual(len(self.voice.said), 2)
        rt._awake_until = 0
        rt._heard("stop")                                                          # STOP never needs the wake word
        self.assertEqual(self.voice.said[-1][0], "Stopped.")

    def test_control_thread_survives_an_unexpected_error(self):
        rt = self.boot(); self.arm(rt)
        rt.execute("drive", {"left": 100, "right": 100, "seconds": 2.0})
        self.wait(lambda: self.mega.left == 100)
        boom, real = [6], rt.drive.tick
        def exploding():
            if boom[0] > 0:
                boom[0] -= 1
                raise RuntimeError("pretend bug")
            real()
        rt.drive.tick = exploding
        self.wait(lambda: boom[0] == 0, 3.0)
        self.assertEqual(self.mega.left, 0)                                    # stopped while the error lasted
        self.wait(lambda: rt.link.online(), 2.0)                               # heartbeats never stopped
        self.assertTrue(rt.execute("drive", {"left": 100, "right": 100, "seconds": 1.0})[0])

    def test_bad_arguments_never_crash(self):
        rt = self.boot(); self.arm(rt)
        for name, args in (("drive", {}), ("drive", {"left": "fast", "right": 1}), ("drive", []), ("head_goto", {"pan": 1}),
                           ("nope", {}), (None, {}), ("say", {"text": 5}), ("say", {"text": "x", "lang": "xx"}),
                           ("expression", {"name": "<script>"}), ("remind", {"seconds": "soon", "text": "x"}),
                           ("note_add", {"text": "x"}), ("erase_memory", {}), ("session_start", {"minutes": 999}),
                           ("chat", {"text": ""}), ("note_forget", {})):
            self.assertFalse(rt.execute(name, args)[0], (name, args))

    def test_reminder_is_spoken_and_memory_commands(self):
        rt = self.boot(cfg_with())
        self.assertTrue(rt.execute("note_add", {"text": "keys in drawer", "consent": True})[0])
        self.assertEqual(rt.execute("notes")[1][0]["text"], "keys in drawer")
        rt.memory.add_reminder(time.time() - 1, "medicine")
        self.wait(lambda: any("medicine" in t for t, _ in self.voice.said))
        self.assertTrue(rt.execute("erase_memory", {"confirm": True})[0])
        self.assertEqual(rt.execute("notes")[1], [])

    def test_web_api_auth_limits_and_pages(self):
        rt = self.boot(cfg_with())
        server = serve(rt, "127.0.0.1", 0)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f"http://127.0.0.1:{server.server_address[1]}"

        def call(path, body=None, token=None, headers=None, raw=None):
            h = dict(headers or {})
            if token: h["X-EVE-Token"] = token
            data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
            req = urllib.request.Request(base + path, data=data, headers=h, method="POST" if data is not None else "GET")
            try:
                with urllib.request.urlopen(req, timeout=5) as r:
                    return r.status, r.read()
            except urllib.error.HTTPError as e:
                return e.code, e.read()
        code, page = call("/")
        self.assertEqual(code, 200); self.assertIn(b"EVE", page)
        self.assertNotIn(rt.token.encode(), page)                                  # the token is never put in a page
        self.assertNotIn(rt.token.encode(), call("/control")[1])
        code, body = call("/api/status")
        self.assertEqual(code, 200)
        self.assertNotIn(rt.token, body.decode())
        self.assertEqual(json.loads(body)["mega"]["online"], True)
        self.assertEqual(call("/api/command", {"name": "estop"})[0], 401)
        self.assertEqual(call("/api/command", {"name": "estop"}, token="wrong")[0], 401)
        self.assertEqual(rt.gate.latched, "")
        code, body = call("/api/command", {"name": "chat", "args": {"text": "who are you"}}, token=rt.token)
        self.assertEqual(code, 200); self.assertIn("EVE", json.loads(body)["message"]["reply"])
        self.assertEqual(call("/api/command", raw=b"{not json", token=rt.token)[0], 400)
        self.assertEqual(call("/api/command", raw=b"x" * 5000, token=rt.token)[0], 413)
        self.assertEqual(call("/api/command", {"name": "estop"}, token=rt.token, headers={"Host": "evil.example.com"})[0], 403)
        self.assertEqual(call("/api/status", headers={"Host": "evil.example.com"})[0], 403)
        self.assertEqual(call("/../config/eve.json")[0], 404)
        self.assertEqual(call("/api/command", {"name": "estop"}, token=rt.token)[0], 200)
        self.assertEqual(rt.gate.latched, "emergency stop")

    def test_host_check(self):
        for good in ("127.0.0.1:8765", "localhost:8765", "192.168.1.20:8765", "eve.local", "[::1]:8765"):
            self.assertTrue(host_allowed(good), good)
        for bad in ("evil.example.com", "", "localhost.evil.com:80"):
            self.assertFalse(host_allowed(bad), bad)

    def test_token_file_is_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = cfg_with(); cfg["_root"] = tmp
            rt = self.boot(cfg)
            rt.write_token()
            path = os.path.join(tmp, "data", "token")
            self.assertEqual(Path(path).read_text(), rt.token)
            if os.name == "posix":
                self.assertEqual(os.stat(path).st_mode & 0o077, 0)


if __name__ == "__main__":
    unittest.main()
