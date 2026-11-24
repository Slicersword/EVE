#!/usr/bin/env python3
"""Talk to the running EVE from PuTTY 2.

  python3 tools/evectl.py status              short status      (status full = everything)
  python3 tools/evectl.py token               print the control-page token
  python3 tools/evectl.py estop               emergency stop
  python3 tools/evectl.py chat "what time is it"
  python3 tools/evectl.py say "नमस्ते" lang=hi
  python3 tools/evectl.py session_start minutes=10
  python3 tools/evectl.py clear
  python3 tools/evectl.py drive_test left=60 right=60 wheels_lifted=true
  python3 tools/evectl.py head_home confirm=true
  python3 tools/evectl.py head_jog pan=8 confirm=true
Any other runtime command works the same way:  <name> key=value ..."""
import json, sys
from _common import command, status, token


def value(text: str):
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text


def short(s: dict) -> str:
    m, sen, saf, p = s["mega"], s["sensors"], s["safety"], s["power"]
    lines = [
        f"Mega        : {'online' if m['online'] else 'OFFLINE ' + str(m['error'])} | firmware {m['firmware_id'] or '-'}"
        f" {'matches' if m['firmware_ok'] else 'DOES NOT MATCH (expected ' + m['expected_id'] + ')'} | latched={m['latched']}",
        f"Distance mm : {sen['distance_mm']}  (front-left, front-right, rear)  age {sen['tof_age_s']} s",
        f"Tilt deg    : {sen['tilt_deg']}  age {sen['imu_age_s']} s",
        f"Cliff raw   : {sen['cliff_raw']}  unsafe={sen['cliff_unsafe']}  calibrated={sen['cliff_calibrated']}  age {sen['mega_age_s']} s",
        f"PIR         : {sen['pir']}",
        f"Devices     : " + " | ".join(f"{k}: {'ok' if v['ok'] else v['error']}" for k, v in sen["devices"].items()),
        f"Sensors say : {saf['sensor_check']}" + (f" | LATCHED: {saf['latched']}" if saf["latched"] else ""),
        f"Session     : {'active, ' + str(p['remaining_s']) + ' s left' if p['session_active'] else 'not active (' + p['ended_reason'] + ')'}"
        f" | Pi supply flags {p['throttled']}",
        f"Wheels      : {'ALLOWED' if saf['drive_permitted'] else 'blocked - ' + saf['drive_block_reason']}",
        f"Head        : {'ALLOWED' if saf['head_permitted'] else 'blocked - ' + saf['head_block_reason']} | homed={s['head']['homed']}"
        f" pan={s['head']['pan']} tilt={s['head']['tilt']}",
        f"Face        : {s['expression']}{' (sleeping)' if s['sleeping'] else ''}",
        f"Features    : " + " | ".join(f"{k}: {v}" for k, v in s["features"].items()),
        f"To commission: {', '.join(s['commissioning']['missing']) or 'nothing left'}",
    ]
    return "\n".join(lines)


def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__); return 0
    name, rest = argv[0], argv[1:]
    if name == "status":
        s = status()
        print(json.dumps(s, indent=1, ensure_ascii=False) if rest[:1] == ["full"] else short(s)); return 0
    if name == "token":
        print(token()); return 0
    args = {}
    positional = [a for a in rest if "=" not in a]
    for item in rest:
        if "=" in item:
            key, _, raw = item.partition("=")
            args[key] = value(raw)
    if positional and name in ("chat", "say", "note_add"):
        args["text"] = " ".join(positional)
    reply = command(name, args)
    message = reply.get("message")
    if name == "chat" and reply.get("ok"):
        print("EVE:", message.get("reply") or "(no words)")
        if message.get("action"):
            print("action:", json.dumps(message["action"], ensure_ascii=False))
    else:
        print(("OK: " if reply.get("ok") else "NO: ") + (message if isinstance(message, str) else json.dumps(message, ensure_ascii=False, indent=1)))
    return 0 if reply.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
