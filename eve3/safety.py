"""M05 - fail-closed safety gate. Every check must pass; anything missing or stale counts as unsafe.
All wheel and head commands go through here before they reach the Mega (which checks again itself)."""
from __future__ import annotations
import math, threading, time
from dataclasses import dataclass
from .config import POWER_FLAGS, missing_flags
from .sensors import Frame, valid_tof_mm


@dataclass(frozen=True)
class Verdict:
    ok: bool
    reason: str = ""


class SafetyGate:
    def __init__(self, cfg: dict, session, clock=time.monotonic):
        self.cfg, self.session, self._clock = cfg, session, clock
        self.stop_mm = float(cfg["drive"]["obstacle_stop_mm"])
        self.timeout_s = cfg["safety"]["sensor_timeout_ms"] / 1000
        self.max_tilt = float(cfg["safety"]["max_tilt_deg"])
        self.tof_range = tuple(cfg["sensors"]["tof_range_mm"])
        self.latched = ""
        self._lock = threading.RLock()

    def latch(self, reason: str):
        with self._lock:
            if not self.latched:
                self.latched = str(reason)[:120]

    def sensors_reason(self, frame: Frame, check_obstacle=True) -> str:
        now = self._clock()

        def fresh(t):
            return type(t) in (int, float) and math.isfinite(t) and 0 < t <= now and now - t <= self.timeout_s
        if not fresh(frame.cliff_at):
            return "cliff data stale or missing (Mega telemetry)"
        if not self.cfg["sensors"]["cliff_calibration"]["calibrated"]:
            return "cliff sensors not calibrated"
        if len(frame.cliff) != 3 or any(c is not False for c in frame.cliff):
            return "cliff"
        if not fresh(frame.tof_at):
            return "distance data stale or missing"
        if len(frame.tof_mm) != 3 or not all(valid_tof_mm(v, *self.tof_range) for v in frame.tof_mm):
            return "distance reading invalid or missing"
        if not fresh(frame.imu_at):
            return "tilt data stale or missing"
        tilt = frame.tilt_deg
        if type(tilt) not in (int, float) or not math.isfinite(tilt):
            return "tilt reading invalid or missing"
        if abs(tilt) > self.max_tilt:
            return "tilt"
        if check_obstacle and min(frame.tof_mm[0], frame.tof_mm[1]) < self.stop_mm:
            return "obstacle"
        return ""

    def _common(self, frame, link, flags, firmware_flag, check_obstacle) -> Verdict:
        with self._lock:
            if self.latched:
                return Verdict(False, f"latched: {self.latched} (fix the cause, then send clear)")
            missing = missing_flags(self.cfg, flags)
            if missing:
                return Verdict(False, "commissioning incomplete: " + ", ".join(missing))
            if self.cfg["firmware"].get(firmware_flag) is not True:
                return Verdict(False, f"firmware.{firmware_flag} is off")
            if not link.online():
                return Verdict(False, "Mega link offline")
            if not link.firmware_ok:
                return Verdict(False, "Mega firmware does not match this config (gen_header, compile, upload)")
            if not self.session.active():
                return Verdict(False, "no attended session (start one first)")
            reason = self.sensors_reason(frame, check_obstacle)
            if reason in ("cliff", "tilt"):
                self.latched = reason                     # remember why, even after the sensor recovers
            if reason:
                return Verdict(False, reason)
            if link.telemetry.get("latched") is not False:
                return Verdict(False, "Mega is latched (send clear)")
            return Verdict(True)

    def drive_verdict(self, frame, link, test=False) -> Verdict:
        flags = POWER_FLAGS + ("contained_ground_area",) + (() if test else ("drive_verified",))
        return self._common(frame, link, flags, "drive_enabled", True)

    def head_verdict(self, frame, link, test=False) -> Verdict:
        verdict = self._common(frame, link, POWER_FLAGS + (() if test else ("head_verified",)), "head_enabled", False)
        if verdict.ok and link.telemetry.get("drive_active") is not False:
            return Verdict(False, "wheels are moving")
        return verdict

    def clear(self, frame, link) -> Verdict:
        """Owner asks to re-arm after a stop. Only succeeds when everything reads safe and the Mega agrees."""
        with self._lock:
            if not link.online():
                return Verdict(False, "Mega link offline")
            if not link.firmware_ok:
                return Verdict(False, "Mega firmware does not match this config (gen_header, compile, upload)")
            reason = self.sensors_reason(frame, check_obstacle=False)
            if reason:
                return Verdict(False, reason)
            try:
                link.clear_stop()
            except Exception as exc:
                return Verdict(False, f"Mega refused clear: {exc}")
            self.latched = ""
            return Verdict(True, "cleared")
