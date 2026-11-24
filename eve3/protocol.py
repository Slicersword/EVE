"""M02 - E1 serial framing shared with the Mega firmware.

Frame:  E1:<seq 1..65535>:<payload printable ASCII without '*' or ':'>*<CRC16-CCITT, 4 hex>\\n
"""
from __future__ import annotations
import re

MAX_FRAME = 195
TELEMETRY_FIELDS = 10   # cl,cc,cr,pir,homed,pan,tilt,head_busy,drive_active,latched


def crc16_ccitt(data: bytes, crc: int = 0xFFFF) -> int:
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def encode(seq: int, payload: str) -> bytes:
    if type(seq) is not int or not 1 <= seq <= 65535:
        raise ValueError("sequence must be 1..65535")
    if (not isinstance(payload, str) or not payload
            or any(ord(c) < 32 or ord(c) > 126 or c in "*:" for c in payload)):
        raise ValueError("invalid payload")
    core = f"E1:{seq}:{payload}".encode("ascii")
    frame = core + f"*{crc16_ccitt(core):04X}\n".encode("ascii")
    if len(frame) > MAX_FRAME:
        raise ValueError("frame too long")
    return frame


_RX = re.compile(rb"E1:([0-9]{1,5}):([ -)+-9;-~]+)\*([0-9a-fA-F]{4})\r?\n")


def decode(line: bytes) -> tuple[int, str]:
    if len(line) > MAX_FRAME or not line.endswith(b"\n"):
        raise ValueError("truncated or oversized frame")
    m = _RX.fullmatch(line)
    if not m:
        raise ValueError("malformed frame")
    seq = int(m[1])
    if not 1 <= seq <= 65535:
        raise ValueError("invalid sequence")
    if crc16_ccitt(line[:line.rfind(b"*")]) != int(m[3], 16):
        raise ValueError("CRC mismatch")
    return seq, m[2].decode("ascii")


def parse_telemetry(payload: str, pan_limit: int = 2048, tilt_limit: int = 2048) -> dict:
    v = payload.split(",")
    if v[0] != "T" or len(v) != TELEMETRY_FIELDS + 1:
        raise ValueError("unexpected telemetry schema")
    if not all(re.fullmatch(r"-?[0-9]{1,5}", x) for x in v[1:]):
        raise ValueError("telemetry field is not a small integer")
    a = [int(x) for x in v[1:]]
    if any(a[i] not in (0, 1) for i in (0, 1, 2, 3, 4, 7, 8, 9)):
        raise ValueError("telemetry flag out of range")
    if abs(a[5]) > pan_limit or abs(a[6]) > tilt_limit:
        raise ValueError("telemetry step out of range")
    return {"cliff_raw": tuple(a[0:3]), "pir": bool(a[3]), "homed": bool(a[4]), "pan": a[5], "tilt": a[6],
            "head_busy": bool(a[7]), "drive_active": bool(a[8]), "latched": bool(a[9])}
