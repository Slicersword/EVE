"""M00 - configuration. config/eve.json = shipped defaults; config/local.json = owner's own values.

Updates replace eve.json only, so calibration and commissioning flags in local.json survive.
Validation fails closed: a bad value stops start-up instead of being guessed.
"""
from __future__ import annotations
import copy, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMISSIONING_FLAGS = ("power_a_verified", "power_b_verified", "motor_current_verified",
                       "contained_ground_area", "drive_verified", "head_verified")
POWER_FLAGS = ("power_a_verified", "power_b_verified", "motor_current_verified")
_SECRET_WORDS = ("api_key", "apikey", "password", "passwd", "secret", "token")


class ConfigError(ValueError):
    pass


def deep_merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def _need(cond, message):
    if not cond:
        raise ConfigError(message)


def _int(v, lo, hi):
    return type(v) is int and lo <= v <= hi


def _no_secrets(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}" if path else key
            if any(w in key.lower() for w in _SECRET_WORDS) and isinstance(value, str) and value:
                raise ConfigError(f"{here}: secrets do not belong in config; put the key in a data/*.key file")
            _no_secrets(value, here)


def validate(cfg: dict) -> dict:
    _no_secrets(cfg)
    _need(cfg["hardware"].get("ina219_enabled") is False, "hardware.ina219_enabled must be false (INA219 removed)")
    com = cfg["commissioning"]
    _need(set(com) == set(COMMISSIONING_FLAGS), "commissioning: unknown or missing flag")
    _need(all(type(v) is bool for v in com.values()), "commissioning flags must be true/false")
    fw = cfg["firmware"]
    _need(all(type(fw.get(k)) is bool for k in ("drive_enabled", "head_enabled", "watchdog_enabled")),
          "firmware flags must be true/false")
    power_ok = all(com[k] for k in POWER_FLAGS)
    _need(power_ok or not (fw["drive_enabled"] or fw["head_enabled"]),
          "firmware.drive_enabled/head_enabled need all three power flags verified first (M03)")
    _need(not com["drive_verified"] or fw["drive_enabled"], "drive_verified needs firmware.drive_enabled")
    _need(not com["head_verified"] or fw["head_enabled"], "head_verified needs firmware.head_enabled")
    d = cfg["drive"]
    _need(_int(d["max_pwm"], 1, 255) and _int(d["test_pwm"], 1, d["max_pwm"]), "drive.max_pwm/test_pwm out of range")
    _need(_int(d["command_lease_ms"], 50, 1000), "drive.command_lease_ms must be 50..1000")
    _need(0 < d["test_seconds"] <= 2 and 0 < d["move_max_seconds"] <= 5, "drive durations out of range")
    _need(50 <= d["obstacle_stop_mm"] < d["obstacle_warn_mm"] <= 1000, "drive obstacle distances out of range")
    _need(type(d["reverse_allowed"]) is bool and type(d["pivot_allowed"]) is bool, "drive flags must be true/false")
    h = cfg["head"]
    _need(-2048 <= h["pan_min_steps"] < 0 < h["pan_max_steps"] <= 2048, "head pan limits out of range")
    _need(-2048 <= h["tilt_min_steps"] < 0 < h["tilt_max_steps"] <= 2048, "head tilt limits out of range")
    _need(_int(h["jog_max_steps"], 1, 32) and type(h["soft_limits_verified"]) is bool, "head jog/limits invalid")
    s = cfg["safety"]
    _need(_int(s["sensor_timeout_ms"], 100, 2000) and _int(s["heartbeat_ms"], 20, 200), "safety timing out of range")
    _need(s["heartbeat_ms"] * 2 < s["mega_watchdog_ms"] <= 1000, "safety.mega_watchdog_ms must exceed two heartbeats")
    _need(5 <= s["max_tilt_deg"] <= 45, "safety.max_tilt_deg out of range")
    cal = cfg["sensors"]["cliff_calibration"]
    _need(type(cal["calibrated"]) is bool and len(cal["edge_level"]) == 3
          and all(v in (0, 1) for v in cal["edge_level"]), "sensors.cliff_calibration invalid")
    cloud = cfg["ai"]["cloud"]
    _need(cloud["send_private_data"] is False, "ai.cloud.send_private_data must stay false")
    if cloud["enabled"]:
        _need(cloud["privacy_consent"] is True, "ai.cloud.enabled needs ai.cloud.privacy_consent=true")
        _need(str(cloud["endpoint"]).startswith("https://"), "ai.cloud.endpoint must be https://")
        _need(str(cloud["key_file"]).startswith("data/") and ".." not in cloud["key_file"],
              "ai.cloud.key_file must be inside data/")
    llm = cfg["ai"]["local_llm"]["endpoint"]
    _need(llm.startswith(("http://127.0.0.1:", "http://localhost:")), "ai.local_llm.endpoint must be on this Pi")
    net = cfg["network"]
    _need(net["host"] in ("127.0.0.1", "0.0.0.0") and _int(net["port"], 1024, 65535),
          "network.host must be 127.0.0.1 (this Pi only) or 0.0.0.0 (home LAN, token needed)")
    _need(1 <= cfg["power"]["session_max_minutes"] <= 30, "power.session_max_minutes must be 1..30")
    return cfg


def load(root: Path | str = ROOT) -> dict:
    root = Path(root)
    cfg = json.loads((root / "config" / "eve.json").read_text(encoding="utf-8"))
    local = root / "config" / "local.json"
    if local.exists():
        cfg = deep_merge(cfg, json.loads(local.read_text(encoding="utf-8")))
    cfg["_root"] = str(root)
    return validate(cfg)


def missing_flags(cfg: dict, names) -> list[str]:
    return [n for n in names if cfg["commissioning"].get(n) is not True]


def save_local(root: Path | str, patch: dict) -> dict:
    """Merge `patch` into config/local.json atomically after validating the merged result."""
    root = Path(root)
    local = root / "config" / "local.json"
    current = json.loads(local.read_text(encoding="utf-8")) if local.exists() else {}
    merged_local = deep_merge(current, patch)
    base = json.loads((root / "config" / "eve.json").read_text(encoding="utf-8"))
    validate(deep_merge(base, merged_local))
    tmp = local.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(merged_local, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, local)
    return merged_local


def data_path(cfg: dict, relative: str) -> Path:
    """Resolve a path that must stay inside the project folder."""
    root = Path(cfg["_root"]).resolve()
    p = (root / relative).resolve()
    if root != p and root not in p.parents:
        raise ConfigError(f"path escapes project folder: {relative}")
    return p
