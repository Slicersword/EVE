"""M11 - local memory in one SQLite file on the Pi. Nothing here ever leaves the device.
Notes are stored only with explicit consent ("remember that ..."). Conversations are not stored."""
from __future__ import annotations
import os, sqlite3, threading, time
from pathlib import Path

MAX_TEXT = 300


def clean_text(text, limit=MAX_TEXT) -> str:
    if not isinstance(text, str):
        raise ValueError("text required")
    text = " ".join("".join(ch if ch.isprintable() else " " for ch in text).split())
    if not text or len(text) > limit:
        raise ValueError(f"text must be 1..{limit} characters")
    return text


class Memory:
    def __init__(self, path: str | Path, max_notes: int = 500):
        self.path, self.max_notes = str(path), max_notes
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._lock = threading.Lock()
        if self.path != ":memory:":
            try:
                os.chmod(self.path, 0o600)
            except OSError:
                pass
        with self._lock, self._db:
            self._db.executescript(
                "CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY, text TEXT NOT NULL, created REAL NOT NULL);"
                "CREATE TABLE IF NOT EXISTS reminders(id INTEGER PRIMARY KEY, due REAL NOT NULL, text TEXT NOT NULL,"
                " done INTEGER NOT NULL DEFAULT 0, announced INTEGER NOT NULL DEFAULT 0);"
                "CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT NOT NULL);")
            if not any(col[1] == "announced" for col in self._db.execute("PRAGMA table_info(reminders)")):
                self._db.execute("ALTER TABLE reminders ADD COLUMN announced INTEGER NOT NULL DEFAULT 0")

    def _q(self, sql, args=()):
        with self._lock, self._db:
            return self._db.execute(sql, args).fetchall()

    # -- notes ---------------------------------------------------------------
    def add_note(self, text, consent) -> int:
        if consent is not True:
            raise PermissionError("a note is saved only when the person clearly asks EVE to remember it")
        text = clean_text(text)
        if self._q("SELECT COUNT(*) FROM notes")[0][0] >= self.max_notes:
            raise ValueError("memory is full; forget some notes first")
        with self._lock, self._db:
            return self._db.execute("INSERT INTO notes(text, created) VALUES(?, ?)", (text, time.time())).lastrowid

    def notes(self, limit=20) -> list[dict]:
        return [{"id": i, "text": t} for i, t in self._q("SELECT id, text FROM notes ORDER BY id DESC LIMIT ?", (int(limit),))]

    def forget_note(self, note_id) -> bool:
        with self._lock, self._db:
            return self._db.execute("DELETE FROM notes WHERE id=?", (int(note_id),)).rowcount > 0

    # -- reminders -----------------------------------------------------------
    def add_reminder(self, due_epoch: float, text) -> int:
        text = clean_text(text, 200)
        if self._q("SELECT COUNT(*) FROM reminders WHERE done=0")[0][0] >= 50:
            raise ValueError("too many reminders waiting")
        with self._lock, self._db:
            return self._db.execute("INSERT INTO reminders(due, text) VALUES(?, ?)", (float(due_epoch), text)).lastrowid

    def pending_reminders(self) -> list[dict]:
        return [{"id": i, "due": d, "text": t, "announced": bool(a)}
                for i, d, t, a in self._q("SELECT id, due, text, announced FROM reminders WHERE done=0 ORDER BY due, id")]

    def next_due(self, now: float) -> dict | None:
        rows = self._q("SELECT id, due, text FROM reminders WHERE done=0 AND announced=0 AND due<=? ORDER BY due, id LIMIT 1", (now,))
        if rows:
            ident, due, text = rows[0]
            return {"id": ident, "due": due, "text": text}
        return None

    def mark_announced(self, reminder: dict):
        # Match the original item even if an erase happened during playback.
        self._q("UPDATE reminders SET announced=1 WHERE id=? AND done=0 AND due=? AND text=?",
                (reminder["id"], reminder["due"], reminder["text"]))

    def cancel_reminder(self, ident: int) -> bool:
        with self._lock, self._db:
            return self._db.execute("UPDATE reminders SET done=1 WHERE id=? AND done=0", (ident,)).rowcount > 0

    def cancel_reminders(self) -> int:
        with self._lock, self._db:
            return self._db.execute("UPDATE reminders SET done=1 WHERE done=0").rowcount

    # -- small counters (for example the cloud daily limit) ------------------------
    def get(self, key, default=None):
        rows = self._q("SELECT value FROM kv WHERE key=?", (key,))
        return rows[0][0] if rows else default

    def put(self, key, value):
        self._q("INSERT INTO kv(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))

    def erase_all(self):
        with self._lock, self._db:
            self._db.executescript("DELETE FROM notes; DELETE FROM reminders; DELETE FROM kv;")
        with self._lock:
            self._db.execute("VACUUM")

    def close(self):
        with self._lock:
            self._db.close()
