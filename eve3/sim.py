"""A small pretend Mega (serial-like object) for tests and for `python -m eve3 --sim` on a PC.
It follows the same rules as the firmware closely enough to exercise the Pi side; the real firmware
logic is tested separately in tests/test_firmware_sim.py."""
from __future__ import annotations
import queue, threading, time
from .protocol import decode, encode


class FakeMega:
    def __init__(self, firmware_id="sim000000000", drive_enabled=True, head_enabled=True):
        self.firmware_id, self.drive_enabled, self.head_enabled = firmware_id, drive_enabled, head_enabled
        self.rx: queue.Queue = queue.Queue()
        self.cliff = [1, 1, 1]            # 1 = floor seen (safe) with edge_level 0
        self.edge_level = [0, 0, 0]
        self.pir = 0
        self.latched, self.homed = True, False
        self.pan = self.tilt = 0
        self.left = self.right = 0
        self.last_hb = self.last_drive = 0.0
        self.last_seq = 0
        self.closed = False
        self.silent = False               # True = stop answering (simulates a pulled cable)
        self.log: list[str] = []
        self._tel_at = 0.0
        self._lock = threading.Lock()

    def _cliff_safe(self):
        return all(c != e for c, e in zip(self.cliff, self.edge_level))

    def _hb_ok(self):
        return time.monotonic() - self.last_hb < 0.35

    def _reply(self, seq, payload):
        if not self.silent:
            self.rx.put(encode(seq, payload))

    def write(self, data: bytes) -> int:
        if self.closed:
            raise IOError("closed")
        try:
            seq, p = decode(data)
        except ValueError:
            return len(data)
        with self._lock:
            self.log.append(p)
            self.last_seq = seq
            if p == "SYNC":
                self.latched, self.homed, self.left, self.right = True, False, 0, 0
                self._reply(seq, f"ACK,{self.firmware_id}")
            elif p == "HB":
                self.last_hb = time.monotonic(); self._reply(seq, "ACK")
            elif p == "STOP":
                self.latched, self.homed, self.left, self.right = True, False, 0, 0; self._reply(seq, "ACK")
            elif p == "HEADSTOP":
                self.homed = False; self._reply(seq, "ACK")
            elif p == "CLEAR":
                ok = self._hb_ok() and self._cliff_safe()
                if ok:
                    self.latched = False
                self._reply(seq, "ACK" if ok else "ERR,UNSAFE")
            elif p == "HOMESET":
                ok = self.head_enabled and not self.latched and self._hb_ok()
                if ok:
                    self.homed, self.pan, self.tilt = True, 0, 0
                self._reply(seq, "ACK" if ok else "ERR,UNSAFE")
            elif p.startswith("DRIVE,"):
                l, r = (int(x) for x in p.split(",")[1:])
                if l == 0 and r == 0:
                    self.left = self.right = 0; self._reply(seq, "ACK")
                elif self.drive_enabled and not self.latched and self._hb_ok() and self._cliff_safe():
                    self.left, self.right, self.last_drive = l, r, time.monotonic(); self._reply(seq, "ACK")
                else:
                    self._reply(seq, "ERR,UNSAFE")
            elif p.startswith("HEAD,"):
                pan, tilt = (int(x) for x in p.split(",")[1:])
                if self.head_enabled and self.homed and not self.latched and self._hb_ok():
                    self.pan, self.tilt = pan, tilt; self._reply(seq, "ACK")
                else:
                    self._reply(seq, "ERR,UNSAFE")
            else:
                self._reply(seq, "ERR,CMD")
        return len(data)

    def _tick(self):
        with self._lock:
            now = time.monotonic()
            if not self.latched and (not self._hb_ok() or not self._cliff_safe()):
                self.latched, self.homed, self.left, self.right = True, False, 0, 0
            if (self.left or self.right) and now - self.last_drive > 0.3:
                self.left = self.right = 0
            if now - self._tel_at >= 0.1 and self.last_seq and not self.silent:
                self._tel_at = now
                c = self.cliff
                self.rx.put(encode(self.last_seq, f"T,{c[0]},{c[1]},{c[2]},{self.pir},{int(self.homed)},{self.pan},"
                                                  f"{self.tilt},0,{int(bool(self.left or self.right))},{int(self.latched)}"))

    def read_until(self, _terminator=b"\n", _size=None) -> bytes:
        if self.closed:
            raise IOError("closed")
        self._tick()
        try:
            return self.rx.get(timeout=0.02)
        except queue.Empty:
            return b""

    def reset_input_buffer(self):
        pass

    def close(self):
        self.closed = True
