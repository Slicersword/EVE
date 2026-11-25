"""M00 - configuration. config/eve.json = shipped defaults; config/local.json = owner's own values.

Updates replace eve.json only, so calibration and commissioning flags in local.json survive.
Validation fails closed: a bad value stops start-up instead of being guessed.
"""
from __future__ import annotations
import copy, json, math, os
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent.parent
COMMISSIONING_FLAGS = ("power_a_verified", "power_b_verified", "motor_current_verified",
                       "contained_ground_area", "drive_verified", "head_verified")
POWER_FLAGS = ("power_a_verified", "power_b_verified", "motor_current_verified")
_SECRET_WORDS = ("api_key", "apikey", "password", "passwd", "secret", "token")


class ConfigError(ValueError):
    pass


def deep_merge(base: dict, extra: dict) -> dict:
    if not isinstance(base, dict) or not isinstance(extra, dict):
        raise ConfigError("Configuration and local overrides must be JSON objects")
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


def local_model_endpoint(url: str) -> str:
    try:
        parsed = urlsplit(url)
        port = parsed.port
        if (parsed.scheme == "http" and parsed.hostname in ("127.0.0.1", "localhost")
                and parsed.username is None and port and not parsed.fragment):
            return urlunsplit(parsed._replace(netloc=f"127.0.0.1:{port}"))
    except ValueError:
        pass
    raise ConfigError("ai.local_llm.endpoint must be a loopback HTTP URL with a port")


def _no_secrets(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}" if path else key
            if any(w in key.lower() for w in _SECRET_WORDS) and isinstance(value, str) and value:
                raise ConfigError(f"{here}: secrets do not belong in config; put the key in a data/*.key file")
            _no_secrets(value, here)


def validate(cfg: dict) -> dict:
    """Reject malformed values before opening GPIO, serial or generating a firmware header."""
    try:
        _need(isinstance(cfg, dict), "Configuration must be a JSON object")
        _check_values(cfg)
        return _validate(cfg)
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ConfigError(f"Missing or malformed configuration field: {exc}") from exc


def _check_values(cfg):
    # Validate types against the public defaults, including disabled optional features.
    # bool is deliberately not a number here; NaN/Infinity are never valid JSON settings.
    defaults = json.loads((ROOT / "config/eve.json").read_text(encoding="utf-8"))

    def walk(value, expected, path):
        if isinstance(expected, dict):
            _need(isinstance(value, dict), f"{path}: expected object")
            _need(not (set(value) - set(expected) - ({"_root"} if not path else set())),
                  f"{path or 'config'}: unknown setting")
            for key, template in expected.items():
                walk(value[key], template, f"{path}.{key}" if path else key)
        elif isinstance(expected, list):
            _need(isinstance(value, list), f"{path}: expected list")
            for item in value:
                walk(item, expected[0], path)
        elif type(expected) is bool:
            _need(type(value) is bool, f"{path}: expected true/false")
        elif type(expected) in (int, float):
            _need(type(value) in (int, float) and math.isfinite(value), f"{path}: expected finite number")
            if type(expected) is int:
                _need(type(value) is int, f"{path}: expected whole number")
        else:
            _need(isinstance(value, str), f"{path}: expected text")
    walk(cfg, defaults, "")
    _need(cfg["serial"]["baud"] == 115200, "serial.baud must be 115200 (fixed in Mega firmware)")
    _need(bool(cfg["serial"]["port"]), "serial.port: set the actual Mega device path")
    _need(0 <= cfg["serial"]["settle_s"] <= 10 and 0 < cfg["serial"]["ack_timeout_s"] <= 2,
          "serial settle/ACK timing out of range")
    _need(1 <= cfg["drive"]["ramp_per_second"] <= 10000 and 0 <= cfg["drive"]["reverse_deadtime_ms"] <= 2000,
          "drive ramp/deadtime out of range")
    sensors = cfg["sensors"]
    _need(sensors["imu_address"] in (0x68, 0x69), "sensors.imu_address must be 104 or 105")
    addresses = sensors["tof_addresses"]
    _need(len(addresses) == 3 and len(set(addresses)) == 3
          and all(0x08 <= a <= 0x77 and a not in (0x29, sensors["imu_address"]) for a in addresses),
          "sensors.tof_addresses: need three distinct usable addresses, excluding 0x29 and the IMU")
    _need(sensors["tof_range_mm"] == [30, 1000], "sensors.tof_range_mm is fixed at [30, 1000]")
    gpio = sensors["tof_xshut"] + [cfg["touch"]["head_gpio"], cfg["touch"]["back_gpio"], cfg["camera"]["led_gpio"]]
    _need(len(sensors["tof_xshut"]) == 3 and len(set(gpio)) == len(gpio)
          and all(4 <= p <= 27 for p in gpio), "Pi GPIO assignments must be distinct BCM4..27 (I2C pins reserved)")
    pins = cfg["pins"]["mega"]
    for key, length in (("left", 7), ("right", 7), ("pan", 4), ("tilt", 4), ("cliff", 3)):
        _need(len(pins[key]) == length, f"pins.mega.{key}: need {length} pins")
    all_pins = sum((pins[k] for k in ("left", "right", "pan", "tilt", "cliff")), []) + [pins["pir"]]
    _need(len(all_pins) == len(set(all_pins)) and all(2 <= p <= 53 for p in all_pins),
          "Mega pins must be distinct D2..D53 (USB serial pins reserved)")
    _need(all(pins[k][i] in (*range(2, 14), 44, 45, 46) for k in ("left", "right") for i in (3, 6)),
          "Wheel PWM pins must support analogWrite on Mega 2560")
    _need(cfg["robot"]["language"] in ("en", "hi", "mr"), "robot.language: choose en, hi or mr")
    _need(-720 <= cfg["behavior"]["utc_offset_minutes"] <= 840, "behavior.utc_offset_minutes out of range")
    _need(all(cfg["camera"][k] in (-1, 1) for k in ("tracking_pan_sign", "tracking_tilt_sign")),
          "camera tracking signs must be -1 or 1")
    for value in (cfg["storage"]["data_dir"], cfg["memory"]["db"], cfg["ai"]["cloud"]["key_file"]):
        _need((value == "data" or value.startswith("data/")) and ".." not in Path(value).parts,
              "Runtime data, memory and key paths must stay under ignored data/")
    v = cfg["voice"]
    _need(v["sample_rate"] == 16000 and 0 < v["silence_s"] <= 5 and 0 < v["max_utterance_s"] <= 30
          and 0 <= v["vad_rms"] <= 32768 and 1 <= v["stt_timeout_s"] <= 120,
          "voice capture timing/rate/threshold invalid (sample_rate must be 16000)")
    c = cfg["camera"]
    _need(16 <= c["width"] <= 1920 and 16 <= c["height"] <= 1080 and 1 <= c["process_fps"] <= 30,
          "camera dimensions/frame rate out of range")
    _need(0 < cfg["touch"]["hold_stop_s"] <= 5 and 1 <= cfg["sleep"]["idle_minutes"] <= 1440,
          "touch/sleep timing out of range")


def _validate(cfg: dict) -> dict:
    _no_secrets(cfg)
    voice = cfg["voice"]
    _need(not voice["echo_cancel_enabled"] or (voice["capture_enabled"] and voice["tts_enabled"]),
          "voice.echo_cancel_enabled needs both microphone capture and TTS enabled")
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
    local_model_endpoint(cfg["ai"]["local_llm"]["endpoint"])
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
    tmp.chmod(0o600)
    os.replace(tmp, local)
    return merged_local


def data_path(cfg: dict, relative: str) -> Path:
    """Resolve a path that must stay inside the project folder."""
    root = Path(cfg["_root"]).resolve()
    p = (root / relative).resolve()
    if root != p and root not in p.parents:
        raise ConfigError(f"path escapes project folder: {relative}")
    return p
