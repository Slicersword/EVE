"""Shared helpers for the owner tools (run on the Pi through PuTTY)."""
from __future__ import annotations
import json, os, sys, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from eve3 import config  # noqa: E402


def eve_running() -> bool:
    lock = ROOT / "data" / "eve.lock"
    if not lock.exists():
        return False
    try:
        import fcntl
        with open(lock, "a") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(handle, fcntl.LOCK_UN)
                return False
            except OSError:
                return True
    except ImportError:
        return False


def _base(cfg) -> str:
    return f"http://127.0.0.1:{cfg['network']['port']}"


def owner_config():
    cfg = config.load()
    if os.environ.get("EVE_SIM") == "1":
        from eve3.__main__ import simulation_config
        cfg = simulation_config(cfg)
    return cfg


def token() -> str:
    try:
        cfg = owner_config()
        return config.data_path(cfg, os.path.join(cfg["storage"]["data_dir"], "token")).read_text(encoding="utf-8").strip()
    except OSError:
        sys.exit("EVE is not running (no token yet). Start it in PuTTY 1:  bash scripts/run_eve.sh")


def status(cfg=None) -> dict:
    cfg = cfg or owner_config()
    try:
        with urllib.request.urlopen(_base(cfg) + "/api/status", timeout=5) as response:
            return json.loads(response.read())
    except (urllib.error.URLError, OSError):
        sys.exit("EVE is not running. Start it in PuTTY 1:  bash scripts/run_eve.sh")


def command(name: str, args: dict | None = None, cfg=None, timeout=60) -> dict:
    cfg = cfg or owner_config()
    request = urllib.request.Request(_base(cfg) + "/api/command", method="POST",
                                     data=json.dumps({"name": name, "args": args or {}}).encode("utf-8"),
                                     headers={"Content-Type": "application/json", "X-EVE-Token": token()})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return json.loads(exc.read() or b'{"ok": false, "message": "request refused"}')
    except (urllib.error.URLError, OSError):
        sys.exit("EVE is not running. Start it in PuTTY 1:  bash scripts/run_eve.sh")
