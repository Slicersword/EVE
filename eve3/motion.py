"""M07 drive and M08 head. Nothing here talks to the Mega without a passing SafetyGate verdict.

Drive: forward and gentle arcs only; reverse and pivot are refused unless the owner enables them
(there is no rear/pivot cliff coverage). A move lasts at most `move_max_seconds` and is re-checked
every control tick; the Mega additionally stops by itself if commands stop arriving.
Head: owner aligns the printed centre marks and confirms "home"; before limits are verified only
small single-axis jogs are possible."""
from __future__ import annotations
import time


class Drive:
    def __init__(self, cfg, link, gate, hub, clock=time.monotonic):
        d = cfg["drive"]
        self.link, self.gate, self.hub, self._clock = link, gate, hub, clock
        self.max_pwm, self.test_pwm = int(d["max_pwm"]), int(d["test_pwm"])
        self.test_s, self.max_s = float(d["test_seconds"]), float(d["move_max_seconds"])
        self.reverse_ok, self.pivot_ok = d["reverse_allowed"] is True, d["pivot_allowed"] is True
        self.renew_s = d["command_lease_ms"] / 1000 / 2.5
        self.active = None            # (left, right, deadline, test)
        self._sent_at = 0.0
        self.last_stop_reason = ""

    def move(self, left, right, seconds, test=False) -> tuple[bool, str]:
        if type(left) is not int or type(right) is not int or type(seconds) not in (int, float):
            return False, "numbers required"
        if left == 0 and right == 0:
            self.stop("stop requested")
            return True, "stopped"
        limit_pwm, limit_s = (self.test_pwm, self.test_s) if test else (self.max_pwm, self.max_s)
        if abs(left) > limit_pwm or abs(right) > limit_pwm:
            return False, f"speed limit is {limit_pwm}"
        if not 0 < seconds <= limit_s:
            return False, f"duration must be within {limit_s} s"
        if (left < 0 or right < 0) and not self.reverse_ok:
            return False, "reverse is disabled"
        if (left > 0) != (right > 0) and not self.pivot_ok:
            return False, "pivot turns are disabled"
        verdict = self.gate.drive_verdict(self.hub.snapshot(), self.link, test)
        if not verdict.ok:
            self.stop(verdict.reason)
            return False, verdict.reason
        self.active = (left, right, self._clock() + seconds, test)
        self._send()
        return True, "moving"

    def _send(self):
        active = self.active
        if active is None:
            return
        try:
            self.link.drive(active[0], active[1])
            self._sent_at = self._clock()
        except Exception as exc:
            self.stop(f"Mega write failed: {type(exc).__name__}")

    def stop(self, reason=""):
        self.active, self.last_stop_reason = None, reason
        try:
            self.link.stop_motion()
        except Exception:
            pass                          # link down: the Mega's own lease/heartbeat timeout stops the wheels

    def tick(self):
        active = self.active                  # read once: another thread may clear it
        if active is None:
            return
        now = self._clock()
        if now >= active[2]:
            self.stop("move finished")
            return
        verdict = self.gate.drive_verdict(self.hub.snapshot(), self.link, active[3])
        if not verdict.ok:
            self.stop(verdict.reason)
        elif now - self._sent_at >= self.renew_s:
            self._send()


class Head:
    def __init__(self, cfg, link, gate, hub, clock=time.monotonic):
        h = cfg["head"]
        self.link, self.gate, self.hub, self._clock = link, gate, hub, clock
        self.pan_lim = (h["pan_min_steps"], h["pan_max_steps"])
        self.tilt_lim = (h["tilt_min_steps"], h["tilt_max_steps"])
        self.limits_verified = h["soft_limits_verified"] is True
        self.jog_max = int(h["jog_max_steps"])
        self.target = None            # (pan, tilt, deadline, test)
        self._sent_at = 0.0

    @property
    def homed(self) -> bool:
        return self.link.telemetry.get("homed") is True

    def position(self):
        t = self.link.telemetry
        return (t.get("pan"), t.get("tilt")) if self.homed else (None, None)

    def home(self, owner_confirmed) -> tuple[bool, str]:
        if owner_confirmed is not True:
            return False, "align the head centre marks by hand first, then confirm"
        verdict = self.gate.head_verdict(self.hub.snapshot(), self.link, test=True)
        if not verdict.ok:
            return False, verdict.reason
        try:
            self.link.set_manual_home()
        except Exception as exc:
            return False, f"Mega refused home: {exc}"
        return True, "this position is now the head centre"

    def _start(self, pan, tilt, test):
        if not (self.pan_lim[0] <= pan <= self.pan_lim[1] and self.tilt_lim[0] <= tilt <= self.tilt_lim[1]):
            return False, "outside head limits"
        cur = self.position()
        steps = abs(pan - cur[0]) + abs(tilt - cur[1])
        self.target = (pan, tilt, self._clock() + steps * 0.002 + 0.5, test)
        self._send()
        return True, "moving"

    def _send(self):
        target = self.target
        if target is None:
            return
        try:
            self.link.head(target[0], target[1])
            self._sent_at = self._clock()
        except Exception:
            self.target = None

    def goto(self, pan, tilt) -> tuple[bool, str]:
        if type(pan) is not int or type(tilt) is not int:
            return False, "whole numbers required"
        if not self.limits_verified:
            return False, "head limits not verified yet; use small jogs"
        verdict = self.gate.head_verdict(self.hub.snapshot(), self.link)
        if not verdict.ok:
            return False, verdict.reason
        if not self.homed:
            return False, "head not homed"
        return self._start(pan, tilt, False)

    def jog(self, dpan, dtilt, clearance_confirmed) -> tuple[bool, str]:
        if clearance_confirmed is not True:
            return False, "check nothing blocks the head and confirm before every jog"
        if type(dpan) is not int or type(dtilt) is not int:
            return False, "whole numbers required"
        if bool(dpan) == bool(dtilt) or max(abs(dpan), abs(dtilt)) > self.jog_max:
            return False, f"jog one axis at a time by 1..{self.jog_max} steps"
        verdict = self.gate.head_verdict(self.hub.snapshot(), self.link, test=True)
        if not verdict.ok:
            return False, verdict.reason
        if not self.homed:
            return False, "head not homed"
        if self.target is not None:
            return False, "head is still moving"
        pan, tilt = self.position()
        return self._start(pan + dpan, tilt + dtilt, True)

    def release(self):
        self.target = None
        try:
            self.link.release_head()
        except Exception:
            pass

    def tick(self):
        """Renew the Mega's head lease while a move is in progress and still safe."""
        target = self.target                  # read once: another thread may clear it
        if target is None:
            return
        pan, tilt, deadline, test = target
        if self.position() == (pan, tilt) or self._clock() >= deadline:
            self.target = None
        elif not self.gate.head_verdict(self.hub.snapshot(), self.link, test).ok or not self.homed:
            self.target = None            # stop renewing; the Mega holds position when its lease expires
        elif self._clock() - self._sent_at >= 0.1:
            self._send()
