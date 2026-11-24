"""M15 - reminders and timers. Stored in memory (SQLite) so they survive a restart."""
from __future__ import annotations
import time

MAX_AHEAD_S = 7 * 24 * 3600


class Scheduler:
    def __init__(self, memory, clock=time.time, utc_offset_minutes=330):
        self.memory, self._clock, self.offset_s = memory, clock, utc_offset_minutes * 60

    def add_in(self, seconds, text) -> tuple[bool, str]:
        if type(seconds) not in (int, float) or not 5 <= seconds <= MAX_AHEAD_S:
            return False, "time must be between 5 seconds and 7 days"
        try:
            self.memory.add_reminder(self._clock() + seconds, text)
        except ValueError as exc:
            return False, str(exc)
        return True, "reminder saved"

    def add_at(self, hour, minute, text) -> tuple[bool, str]:
        if type(hour) is not int or type(minute) is not int or not (0 <= hour <= 23 and 0 <= minute <= 59):
            return False, "time must be HH:MM"
        now = self._clock()
        local_midnight = (now + self.offset_s) // 86400 * 86400 - self.offset_s
        due = local_midnight + hour * 3600 + minute * 60
        if due <= now:
            due += 86400
        return self.add_in(due - now, text) if due - now >= 5 else self.add_in(5, text)

    def tick(self) -> list[str]:
        return self.memory.pop_due(self._clock())

    def pending(self) -> list[dict]:
        now = self._clock()
        return [{"in_s": max(0, int(r["due"] - now)), "text": r["text"]} for r in self.memory.pending_reminders()]
