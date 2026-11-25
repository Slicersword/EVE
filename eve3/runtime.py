"""M17 - the one place where everything is put together. One process owns the Mega, I2C, camera and audio.

Threads: control (heartbeat + motion re-checks, every 100 ms), sensors (ToF + IMU), slow (behaviour,
reminders, face tracking), plus the Mega reader, speaker, listener and camera threads owned by their parts.
Every command - web, CLI, touch, voice - enters through execute(); voice/chat may use only VOICE_COMMANDS.
"""
from __future__ import annotations
import os, secrets, sqlite3, threading, time
from contextlib import nullcontext
from . import __version__, firmware, intents
from .expressions import EXPRESSIONS
from .home.activities import HomeModule
from .ai import ACTIONS, Brain, detect_lang, line
from .behavior import Behavior, Context
from .camera import Camera, tracking_step
from .config import data_path, missing_flags, COMMISSIONING_FLAGS
from .mega_link import MegaLink, find_port, open_serial
from .memory import Memory
from .motion import Drive, Head
from .power import PowerSession, read_throttled
from .safety import SafetyGate
from .scheduler import Scheduler
from .sensors import MPU6050, SensorHub, SensorReader, ToFArray
from .touch import TouchPads
from .voice import Listener, Speaker

VOICE_COMMANDS = frozenset(name for name, _ in ACTIONS.values())      # stop, drive, head_look, sleep, wake
LOOK = {"left": (-200, 0), "right": (200, 0), "up": (0, 80), "down": (0, -80), "center": (0, 0)}
MOTION_COMMANDS = {"stop", "estop", "session_start", "session_end", "drive", "drive_test", "head_goto",
                   "head_jog", "head_look", "head_release", "sleep"}


def log(message: str):
    print(time.strftime("%H:%M:%S"), message, flush=True)


class Runtime:
    def __init__(self, cfg, opener=None, tof=None, imu=None, throttled=read_throttled, speaker=None,
                 memory=None, listener_factory=Listener):
        self.cfg = cfg
        s = cfg["sensors"]
        self.hub = SensorHub(s["cliff_calibration"])
        self.reader = SensorReader(self.hub, tof or ToFArray(s["tof_xshut"], s["tof_addresses"]),
                                   imu or MPU6050(address=s["imu_address"], inverted=s["imu_inverted"]))
        self.link = MegaLink(opener or (lambda: open_serial(find_port(cfg["serial"]["port"]), cfg["serial"]["baud"])),
                             expected_id=firmware.firmware_id(cfg), ack_timeout_s=cfg["serial"]["ack_timeout_s"],
                             hb_max_age_s=cfg["safety"]["mega_watchdog_ms"] / 1000,
                             telemetry_max_age_s=cfg["safety"]["sensor_timeout_ms"] / 1000,
                             on_telemetry=self.hub.update_mega)
        self.session = PowerSession(cfg, throttled=throttled)
        self.gate = SafetyGate(cfg, self.session)
        self.drive = Drive(cfg, self.link, self.gate, self.hub)
        self.head = Head(cfg, self.link, self.gate, self.hub)
        self.memory = memory if memory is not None else (
            Memory(data_path(cfg, cfg["memory"]["db"]), cfg["memory"]["max_notes"]) if cfg["memory"]["enabled"] else None)
        self.scheduler = Scheduler(self.memory, utc_offset_minutes=cfg["behavior"]["utc_offset_minutes"]) if self.memory else None
        self.brain = Brain(cfg, self.memory, self.scheduler)
        self.speaker = speaker or Speaker(cfg)
        self.behavior = Behavior(cfg)
        self.camera = Camera(cfg)
        self.touch = TouchPads(cfg, self._touch_head, self._touch_back_tap, self._touch_back_hold)
        self.listener = listener_factory(cfg, self._heard, self._speech_output_active) if cfg["voice"]["capture_enabled"] else None
        self.token = secrets.token_urlsafe(18)
        self.expression = "idle"
        self.caption = ""
        self._cue_block_until = 0.0
        self.lang = cfg["robot"]["language"]
        self.last_interaction = time.time()
        self._override = ("", 0.0)             # (expression, until) set by touch / owner
        self._awake_until = 0.0
        self._thinking = 0
        self._reminder_lock = threading.RLock()
        self._reminder_pending = False
        self._reminder_retry_at = 0.0
        self._stop = threading.Event()
        self._motion_lock = threading.RLock()
        self._tracking_active = False
        self._threads: list[threading.Thread] = []
        self._connection_thread = None
        self._last_connect = self._power_checked = -1e9
        self.settle_s = cfg["serial"]["settle_s"]
        self.commands = {
            "stop": self._c_stop, "estop": self._c_estop, "clear": self._c_clear,
            "session_start": self._c_session_start, "session_end": self._c_session_end,
            "drive": self._c_drive, "drive_test": self._c_drive_test,
            "head_home": self._c_head_home, "head_jog": self._c_head_jog, "head_goto": self._c_head_goto,
            "head_look": self._c_head_look, "head_release": self._c_head_release,
            "say": self._c_say, "chat": self._c_chat, "expression": self._c_expression,
            "sleep": self._c_sleep, "wake": self._c_wake,
            "note_add": self._c_note_add, "notes": self._c_notes, "note_forget": self._c_note_forget,
            "erase_memory": self._c_erase_memory, "remind": self._c_remind, "reminders": self._c_reminders,
        }

        self._audio_session = secrets.token_hex(8)
        self.home = HomeModule(self, data_path(cfg, f"{cfg['storage']['data_dir']}/home_companion.sqlite3")) if self.memory else None
        if self.home:
            self.commands.update(self.home.commands())

    def audio_priority(self):
        return {
            "session": self._audio_session,
            "home_available": bool(self.home and self.home._allowed()),
            "stop_latched": bool(self.gate.latched),
            "capture_active": self.cfg["voice"]["capture_enabled"],
            "speaking": self.speaker.speaking or getattr(self.speaker, "speech_pending", False)
                        or time.monotonic() < self._cue_block_until,
            "music_stop_generation": self.home.music_stop_generation if self.home else 0,
        }

    # ------------------------------------------------------------------ lifecycle
    def start(self):
        self._stop.clear()
        self.speaker.start()
        self.touch.start()
        self.camera.start()
        if self.listener:
            self.listener.start()
        for name, target in (("control", self._control_loop), ("sensors", self._sensor_loop), ("slow", self._slow_loop)):
            thread = threading.Thread(target=target, name=f"eve3-{name}", daemon=True)
            thread.start()
            self._threads.append(thread)
        log(f"EVE {__version__} started. Expected firmware id {self.link.expected_id}.")

    def stop(self):
        self._stop.set()
        self._stop_movement("shutting down")
        for thread in self._threads:
            thread.join(timeout=2)
        self._threads = []
        self.link.close()                       # sends STOP to the Mega first
        if self._connection_thread:
            self._connection_thread.join(timeout=1)
        for part in (self.listener, self.camera, self.speaker):
            if part:
                part.stop()
        self.touch.close()
        self.reader.close()
        if self.home:
            self.home.stop()
        if self.memory:
            with self._reminder_lock:
                self.memory.close()
        log("EVE stopped safely.")

    def write_token(self):
        path = data_path(self.cfg, os.path.join(self.cfg["storage"]["data_dir"], "token"))
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as handle:
            handle.write(self.token)
        os.chmod(path, 0o600)

    # ------------------------------------------------------------------ loops
    def _connect(self):
        try:
            self.link.open(self.settle_s)
            if self._stop.is_set():
                self.link.close()
                return
            ok = "matches" if self.link.firmware_ok else "DOES NOT MATCH config - run gen_header, compile, upload"
            log(f"Mega connected. Firmware id {self.link.firmware_id} {ok}.")
        except Exception as exc:
            if self.link.last_error != getattr(self, "_logged_link_error", None):
                log(f"Mega not connected: {type(exc).__name__}: {exc}")
                self._logged_link_error = self.link.last_error
    def _control_loop(self):
        period = self.cfg["safety"]["heartbeat_ms"] / 1000
        while not self._stop.wait(period):
            try:
                self._control_tick()
            except Exception as exc:                 # never let this thread die: it feeds the Mega heartbeat
                log(f"control error: {type(exc).__name__}: {exc}")
                self._stop_movement("control error")

    def _control_tick(self):
        now = time.monotonic()
        connecting = self._connection_thread is not None and self._connection_thread.is_alive()
        if self.link.synced:
            # After SYNC, give the first heartbeat and telemetry time to arrive.
            grace = max(self.link.hb_max_age_s, self.link.telemetry_max_age_s)
            try:
                if self.link.online(now) or now - self.link.synced_at < grace:
                    self.link.heartbeat()
                else:
                    self._link_lost("Mega heartbeat or telemetry timed out")
            except Exception:
                self._link_lost("Mega heartbeat write failed")
        elif not connecting:
            if self.link.ser is not None:
                self._link_lost(self.link.last_error or "Mega link offline")
            if now - self._last_connect > 3 and not self._stop.is_set():
                self._last_connect = now
                self._connection_thread = threading.Thread(target=self._connect, name="eve3-connect", daemon=True)
                self._connection_thread.start()
        with self._motion_lock:
            self.drive.tick()
            self.head.tick()
            if self.gate.latched:
                self._tracking_active = False
        if now - self._power_checked > 5:
            self._power_checked = now
            reason = self.session.check()
            if reason:
                self.gate.latch(reason)
                self._stop_movement(reason)
                log(f"Session ended: {reason}")

    def _link_lost(self, reason):
        with self._motion_lock:
            self.session.end()
            self.gate.latch(reason)
            self._stop_movement(reason)
            self.link.close()
            self.link.last_error = reason
        log(f"Mega link lost: {reason}")

    def _stop_movement(self, reason):
        with self._motion_lock:
            self._tracking_active = False
            self.drive.stop(reason)
            self.head.stop()

    def _sensor_loop(self):
        while not self._stop.wait(0.03):
            self.reader.poll()

    def _slow_loop(self):
        while not self._stop.wait(0.25):
            try:
                self._slow_tick()
            except Exception as exc:
                log(f"behaviour error: {type(exc).__name__}")

    def _slow_tick(self):
        frame = self.hub.snapshot()
        front = [v for v in frame.tof_mm[:2] if type(v) in (int, float)]
        fresh = time.monotonic() - frame.tof_at < 1
        was_sleeping = self.behavior.sleeping
        out = self.behavior.tick(Context(
            presence=bool(frame.pir and time.monotonic() - frame.cliff_at < 1) or self.camera.face_present(),
            obstacle_mm=min(front) if front and fresh else None, latched=bool(self.gate.latched),
            speaking=self.speaker.speaking, listening_now=self._thinking > 0, last_interaction=self.last_interaction))
        if self.behavior.sleeping and not was_sleeping:
            self._sleep_motion()
        override, until = self._override
        self.expression = override if override and time.time() < until and out["expression"] in ("idle", "happy", "sleepy") else out["expression"]
        if out["greet"]:
            self._speak(self.brain.greeting(self.lang), self.lang)
        if self.scheduler:
            self._announce_reminder()
        self.camera.set_paused(self.behavior.sleeping)
        with self._motion_lock:
            self._track_face()

    def _track_face(self):
        if (self._tracking_active and not self.behavior.sleeping and self.session.active()
                and self.cfg["camera"]["allow_tracking"] is True and self.camera.face_present()
                and self.head.target is None and self.head.homed):
            c = self.cfg["camera"]
            dpan, dtilt = tracking_step(self.camera.offset, c["tracking_deadband"], c["tracking_step"],
                                        c["tracking_pan_sign"], c["tracking_tilt_sign"])
            if dpan or dtilt:
                pan, tilt = self.head.position()
                if not all(type(value) is int for value in (pan, tilt)):
                    return
                self.head.goto(max(self.head.pan_lim[0], min(self.head.pan_lim[1], pan + dpan)),
                               max(self.head.tilt_lim[0], min(self.head.tilt_lim[1], tilt + dtilt)))

    def _announce_reminder(self):
        with self._reminder_lock:
            if self._stop.is_set() or self._reminder_pending or self._speech_output_active() or time.monotonic() < self._reminder_retry_at:
                return
            reminder = self.scheduler.next_due()
            if not reminder:
                return

            def complete(success):
                with self._reminder_lock:
                    self._reminder_pending = False
                    if success and not self._stop.is_set():
                        try:
                            self.memory.mark_announced(reminder)
                            return
                        except sqlite3.Error:
                            log("Could not record the reminder announcement.")
                    self._reminder_retry_at = time.monotonic() + 5

            self._reminder_pending = True
            self.behavior.sleeping = False
            if not self._speak(line("remind_due", self.lang, text=reminder["text"]), self.lang, on_done=complete):
                complete(False)

    # ------------------------------------------------------------------ people
    def _interaction(self):
        self.last_interaction = time.time()
        self.behavior.sleeping = False
        self.camera.set_paused(False)

    def _speech_output_active(self):
        return self.speaker.speaking or getattr(self.speaker, "speech_pending", False) or time.monotonic() < getattr(self.speaker, "quiet_until", 0.0)

    def _speak(self, text, lang, on_done=None):
        self._cue_block_until = time.monotonic() + 1
        self.caption = text
        return self.speaker.say(text, lang, on_done=on_done) if on_done else self.speaker.say(text, lang)

    def _touch_head(self):
        self._interaction()
        self._override = ("love", time.time() + 3)

    def _touch_back_tap(self):
        self._interaction()
        self._awake_until = time.monotonic() + self.cfg["voice"]["follow_up_s"]     # listen without the wake word
        self._override = ("listening", time.time() + 3)

    def _touch_back_hold(self):
        self.execute("estop", {}, "owner")

    def _heard(self, text: str):
        """Called by the microphone thread with what whisper understood."""
        heard_wake, rest = intents.strip_wake(text, self.cfg["robot"]["wake_words"])
        parsed = intents.parse(rest)
        is_stop = parsed is not None and parsed.name == "stop"
        if self.cfg["voice"]["require_wake_word"] and not heard_wake and time.monotonic() > self._awake_until and not is_stop:
            return                                           # not talking to EVE
        if not rest:
            self._touch_back_tap()                           # just the name: "yes?"
            return
        self.converse(rest, microphone=True)

    def converse(self, text: str, microphone=False) -> dict:
        """Understand one sentence, act if it is an allowed action, answer. Used by voice and by chat."""
        self._interaction()
        self._thinking += 1
        try:
            verdict = self.gate.latched or ""
            lang = detect_lang(text, self.cfg["robot"]["language"])
            reply = self.home.spoken(text, lang) if self.home else None
            result = {"reply": reply, "lang": lang, "action": None} if reply is not None else self.brain.respond(text, status_reason=verdict)
            lang = self.lang = result["lang"]
            reply, done = result["reply"], None
            if result["action"]:
                name, args = result["action"]
                if microphone and self.cfg["voice"]["echo_cancel_enabled"] and name in ("drive", "head_look"):
                    ok, message = False, "use the control page for movement in echo-cancel mode"
                else:
                    ok, message = self.execute(name, dict(args), source="voice")
                done = {"command": name, "ok": ok, "message": message}
                reply = line("stopped" if name == "stop" else "sleep" if name == "sleep" else "wake" if name == "wake" else "ok", lang) \
                    if ok else line("cannot", lang, why=message)
            if reply:
                self._speak(reply, lang)
            self._awake_until = time.monotonic() + self.cfg["voice"]["follow_up_s"]
            return {"reply": reply, "lang": lang, "action": done}
        finally:
            self._thinking -= 1

    # ------------------------------------------------------------------ commands
    def execute(self, name, args=None, source="owner") -> tuple[bool, object]:
        args = {} if args is None else args
        if not isinstance(name, str) or name not in self.commands or not isinstance(args, dict):
            return False, "unknown command"
        if source != "owner" and name not in VOICE_COMMANDS:
            return False, "this needs the owner (control page or evectl)"
        try:
            with self._motion_lock if name in MOTION_COMMANDS else nullcontext():
                return self.commands[name](args)
        except (KeyError, TypeError, ValueError, PermissionError) as exc:
            return False, f"not accepted: {exc}"

    def _c_stop(self, a):
        self._stop_movement("stop requested")
        return True, "stopped"

    def _c_estop(self, a):
        self.gate.latch("emergency stop")
        try:
            self.link.emergency_stop()
        except Exception:
            pass                                             # link down = Mega already stopped itself
        self._stop_movement("emergency stop")
        log("EMERGENCY STOP")
        return True, "emergency stop - latched until the owner clears it"

    def _c_clear(self, a):
        verdict = self.gate.clear(self.hub.snapshot(), self.link)
        return verdict.ok, verdict.reason

    def _c_session_start(self, a):
        ok, message = self.session.start(a.get("minutes", 10))
        if ok:
            self._tracking_active = True
            log("Attended session started.")
        return ok, message

    def _c_session_end(self, a):
        self.session.end()
        self._stop_movement("session ended")
        return True, "session ended"

    def _c_drive(self, a):
        return self.drive.move(a["left"], a["right"], a.get("seconds", 1.0))

    def _c_drive_test(self, a):
        if a.get("wheels_lifted") is not True:
            return False, "lift the wheels off the ground and confirm wheels_lifted=true"
        return self.drive.move(a["left"], a["right"], a.get("seconds", self.drive.test_s), test=True)

    def _c_head_home(self, a):
        return self.head.home(a.get("confirm"))

    def _c_head_jog(self, a):
        return self.head.jog(a.get("pan", 0), a.get("tilt", 0), a.get("confirm"))

    def _c_head_goto(self, a):
        return self.head.goto(a["pan"], a["tilt"])

    def _c_head_look(self, a):
        pan, tilt = LOOK[a["direction"]]
        c = self.cfg["camera"]
        return self.head.goto(pan * c["tracking_pan_sign"], tilt * c["tracking_tilt_sign"])

    def _c_head_release(self, a):
        if self.head.release():
            return True, "head release sent (home again before the next move)"
        return False, "Mega head release write failed"

    def _c_say(self, a):
        lang = a.get("lang", self.lang)
        if lang not in ("en", "hi", "mr") or not isinstance(a.get("text"), str):
            return False, "text and lang (en/hi/mr) required"
        if self._speak(a["text"][:300], lang):
            return True, "speech queued"
        return False, "speaker disabled, queue full or no text to speak"

    def _c_chat(self, a):
        if not isinstance(a.get("text"), str) or not a["text"].strip():
            return False, "text required"
        return True, self.converse(a["text"])

    def _c_expression(self, a):
        if a.get("name") not in EXPRESSIONS:
            return False, "expression must be one of: " + ", ".join(EXPRESSIONS)
        self._override = (a["name"], time.time() + 5)
        return True, a["name"]

    def _c_sleep(self, a):
        self.behavior.sleeping = True
        self.last_interaction = 0.0
        self.camera.set_paused(True)
        self._sleep_motion()
        return True, "sleeping"

    def _sleep_motion(self):
        with self._motion_lock:
            self.session.end()
            self._stop_movement("sleep")

    def _c_wake(self, a):
        self._interaction()
        return True, "awake"

    def _need_memory(self):
        if not self.memory:
            raise PermissionError("memory is switched off")
        return self.memory

    def _c_note_add(self, a):
        return True, self._need_memory().add_note(a["text"], a.get("consent"))

    def _c_notes(self, a):
        return True, self._need_memory().notes()

    def _c_note_forget(self, a):
        return self._need_memory().forget_note(a["id"]), "done"

    def _c_erase_memory(self, a):
        if a.get("confirm") is not True:
            return False, "confirm=true required; this erases all notes and reminders"
        self._need_memory().erase_all()
        if self.home:
            self.home.clear_private_data()
        return True, "memory erased"

    def _c_remind(self, a):
        self._need_memory()
        return self.scheduler.add_in(a["seconds"], a["text"])

    def _c_reminders(self, a):
        self._need_memory()
        return True, self.scheduler.pending()

    # ------------------------------------------------------------------ status
    def status(self) -> dict:
        frame, now = self.hub.snapshot(), time.monotonic()
        age = lambda t: round(now - t, 2) if t else None
        drive = self.gate.drive_verdict(frame, self.link)
        head = self.gate.head_verdict(frame, self.link)
        cfg = self.cfg
        return {
            "name": cfg["robot"]["name"], "version": __version__, "expression": self.expression,
            "caption": self.caption if self.speaker.speaking else "", "sleeping": self.behavior.sleeping,
            "expression_cues_allowed": not (
                cfg["voice"]["capture_enabled"] or self.gate.latched or self.speaker.speaking
                or getattr(self.speaker, "speech_pending", False)
                or self._thinking or self.expression in ("listening", "speaking")
                or time.monotonic() < self._cue_block_until
                or self.behavior.is_night()
            ),
            "face_offset": self.camera.offset if self.camera.face_present() else None,
            "mega": {"connected": self.link.synced, "online": self.link.online(), "firmware_id": self.link.firmware_id,
                     "expected_id": self.link.expected_id, "firmware_ok": self.link.firmware_ok,
                     "latched": self.link.telemetry.get("latched"), "error": self.link.last_error},
            "sensors": {"distance_mm": list(frame.tof_mm), "tilt_deg": frame.tilt_deg, "cliff_unsafe": list(frame.cliff),
                        "cliff_raw": list(frame.cliff_raw), "pir": frame.pir, "tof_age_s": age(frame.tof_at),
                        "imu_age_s": age(frame.imu_at), "mega_age_s": age(frame.cliff_at),
                        "cliff_calibrated": self.hub.calibrated, "devices": self.reader.status()},
            "safety": {"latched": self.gate.latched, "sensor_check": self.gate.sensors_reason(frame) or "all clear",
                       "drive_permitted": drive.ok, "drive_block_reason": drive.reason,
                       "head_permitted": head.ok, "head_block_reason": head.reason},
            "power": self.session.status(),
            "head": {"homed": self.head.homed, "pan": self.link.telemetry.get("pan"), "tilt": self.link.telemetry.get("tilt"),
                     "limits_verified": self.head.limits_verified},
            "commissioning": {**cfg["commissioning"], "missing": missing_flags(cfg, COMMISSIONING_FLAGS)},
            "firmware_flags": cfg["firmware"],
            "features": {"touch": self.touch.error or "ok", "camera": self.camera.state,
                         "microphone": ("listening" if self.listener.listening else self.listener.last_error or "starting") if self.listener else "off",
                         "voice_mode": "echo cancellation" if cfg["voice"]["echo_cancel_enabled"] else "turn-taking",
                         "mic_level": round(self.listener.level) if self.listener else None,
                         "speaker": self.speaker.last_error or ("on" if self.speaker.enabled else "off"),
                         "memory": "on" if self.memory else "off",
                         "local_llm": cfg["ai"]["local_llm"]["enabled"], "cloud_ai": cfg["ai"]["cloud"]["enabled"],
                         "ai_error": self.brain.last_error, "web_tools": cfg["integrations"]["web_tools_enabled"]},
        }
