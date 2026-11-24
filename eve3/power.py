"""M03 - power. Two USB power banks, no electrical monitoring (INA219 removed), so software cannot see
battery level. What it can do: refuse motion until the owner has recorded the M03 measurements, read the
Pi's own under-voltage flag, and limit motion to a short attended session that the owner starts."""
from __future__ import annotations
import re, subprocess, time
from .config import POWER_FLAGS, missing_flags


def read_throttled(run=subprocess.run) -> int | None:
    """Pi firmware supply flags. bit0 = under-voltage now, bit16 = under-voltage since boot. None = unknown."""
    try:
        out = run(["vcgencmd", "get_throttled"], capture_output=True, text=True, timeout=2, check=False).stdout
        m = re.fullmatch(r"throttled=0x([0-9a-fA-F]{1,8})\s*", out)
        return int(m[1], 16) if m else None
    except Exception:
        return None


class PowerSession:
    """An attended session: the owner is present, hand near the Bank B switch. Never saved to disk."""

    def __init__(self, cfg: dict, throttled=read_throttled, clock=time.monotonic):
        self.cfg, self._throttled, self._clock = cfg, throttled, clock
        self.max_minutes = cfg["power"]["session_max_minutes"]
        self.until = 0.0
        self.last_flags: int | None = None
        self.ended_reason = "not started"

    def start(self, minutes) -> tuple[bool, str]:
        if type(minutes) is not int or not 1 <= minutes <= self.max_minutes:
            return False, f"minutes must be 1..{self.max_minutes}"
        missing = missing_flags(self.cfg, POWER_FLAGS)
        if missing:
            return False, "power not verified (M03): " + ", ".join(missing)
        self.last_flags = self._throttled()
        if self.last_flags is None:
            return False, "cannot read the Pi supply state (vcgencmd)"
        if self.last_flags & 0xF:
            return False, f"Pi supply problem right now (throttled=0x{self.last_flags:x})"
        self.until, self.ended_reason = self._clock() + minutes * 60, ""
        return True, f"attended session started for {minutes} min"

    def end(self, reason="ended by owner"):
        if self.until:
            self.until, self.ended_reason = 0.0, reason

    def active(self) -> bool:
        if self.until and self._clock() >= self.until:
            self.end("session time is over")
        return bool(self.until)

    def remaining_s(self) -> int:
        return int(self.until - self._clock()) if self.active() else 0

    def check(self) -> str:
        """Call every few seconds. Ends the session on under-voltage; returns the reason or ''."""
        if not self.active():
            return ""
        self.last_flags = self._throttled()
        if self.last_flags is None or self.last_flags & 0x1:
            reason = "Pi under-voltage" if self.last_flags else "Pi supply state unreadable"
            self.end(reason)
            return reason
        return ""

    def status(self) -> dict:
        return {"session_active": self.active(), "remaining_s": self.remaining_s(), "ended_reason": self.ended_reason,
                "throttled": None if self.last_flags is None else f"0x{self.last_flags:x}",
                "battery_percent": None, "note": "no battery readings exist in this build"}
