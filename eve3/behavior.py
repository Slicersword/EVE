"""M14 - behaviour. Decides what EVE shows and says by herself. It only returns suggestions
(expression / speech); it has no access to wheels, head, pins or the Mega."""
from __future__ import annotations
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class Context:
    presence: bool = False          # PIR or a face in view
    obstacle_mm: float | None = None
    latched: bool = False
    speaking: bool = False
    listening_now: bool = False     # someone is talking / EVE is working on an answer
    last_interaction: float = 0.0   # wall-clock seconds


class Behavior:
    def __init__(self, cfg, clock=time.time):
        b = cfg["behavior"]
        self.enabled = b["enabled"] is True
        self.cooldown = float(b["greet_cooldown_s"])
        self.night = (int(b["night_start_hour"]), int(b["night_end_hour"]))
        self.tz = timezone(timedelta(minutes=b["utc_offset_minutes"]))
        self.idle_s = cfg["sleep"]["idle_minutes"] * 60
        self.warn_mm = float(cfg["drive"]["obstacle_warn_mm"])
        self._clock = clock
        self._presence = False
        self._greeted_at = -1e12
        self.sleeping = False

    def is_night(self) -> bool:
        hour = datetime.fromtimestamp(self._clock(), self.tz).hour
        start, end = self.night
        return hour >= start or hour < end if start > end else start <= hour < end

    def tick(self, ctx: Context) -> dict:
        """-> {"expression": str, "greet": bool}"""
        now = self._clock()
        greet = False
        rising = ctx.presence and not self._presence
        self._presence = ctx.presence
        if self.sleeping and (rising or now - ctx.last_interaction < 2):
            self.sleeping = False
        if not self.sleeping and self.idle_s and now - max(ctx.last_interaction, self._greeted_at) > self.idle_s and not ctx.presence:
            self.sleeping = True
        if self.enabled and rising and now - self._greeted_at > self.cooldown:
            self._greeted_at = now
            greet = not self.is_night()                                  # at night: look happy, stay quiet
        if ctx.latched:
            expression = "alert"
        elif ctx.speaking:
            expression = "speaking"
        elif ctx.listening_now:
            expression = "listening"
        elif ctx.obstacle_mm is not None and ctx.obstacle_mm < self.warn_mm:
            expression = "surprised"
        elif self.sleeping:
            expression = "sleepy"
        elif now - self._greeted_at < 4:
            expression = "happy"
        else:
            expression = "idle"
        return {"expression": expression, "greet": greet}
