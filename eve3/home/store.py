"""Bounded private records for deliberately saved home activities."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import threading
import time


class HomeStore:
    KINDS = frozenset({"story", "recipe", "message", "capsule"})

    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(fd)
        os.chmod(path, 0o600)
        self.db = sqlite3.connect(path, check_same_thread=False, timeout=.2)
        self.db.execute("PRAGMA secure_delete=ON")
        self.db.execute("CREATE TABLE IF NOT EXISTS records ("
                        "id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, "
                        "body TEXT NOT NULL, updated REAL NOT NULL)")
        self.db.commit()

    def save(self, kind, value, record_id=None):
        if kind not in self.KINDS:
            raise ValueError("unknown record kind")
        body = json.dumps(value, ensure_ascii=False, allow_nan=False)
        if len(body.encode("utf-8")) > 16000:
            raise ValueError("record too large")
        with self.lock, self.db:
            if record_id is not None:
                if type(record_id) is not int or record_id <= 0:
                    raise ValueError("invalid record id")
                cursor = self.db.execute("UPDATE records SET body=?,updated=? WHERE id=? AND kind=?",
                                         (body, time.time(), record_id, kind))
                if cursor.rowcount != 1:
                    raise ValueError("record not found")
                return record_id
            if self.db.execute("SELECT COUNT(*) FROM records").fetchone()[0] >= 300:
                raise ValueError("home record limit reached; delete an old entry")
            return self.db.execute("INSERT INTO records(kind,body,updated) VALUES(?,?,?)",
                                   (kind, body, time.time())).lastrowid

    def list(self, kind):
        with self.lock:
            rows = self.db.execute("SELECT id,body,updated FROM records WHERE kind=? ORDER BY id DESC LIMIT 300", (kind,)).fetchall()
            return [{"id": row[0], "value": json.loads(row[1]), "updated": row[2]} for row in rows]

    def get(self, kind, record_id):
        if type(record_id) is not int or record_id <= 0:
            raise ValueError("invalid record id")
        return next((r for r in self.list(kind) if r["id"] == record_id), None)

    def delete(self, kind, record_id):
        if kind not in self.KINDS or type(record_id) is not int or record_id <= 0:
            raise ValueError("invalid record")
        with self.lock, self.db:
            return self.db.execute("DELETE FROM records WHERE kind=? AND id=?", (kind, record_id)).rowcount > 0

    def counts(self):
        with self.lock:
            return dict(self.db.execute("SELECT kind,COUNT(*) FROM records GROUP BY kind").fetchall())

    def clear(self):
        with self.lock, self.db:
            self.db.execute("DELETE FROM records")

    def close(self):
        with self.lock:
            self.db.close()
