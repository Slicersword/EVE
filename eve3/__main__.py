"""Start EVE:  .venv/bin/python -m eve3      (Ctrl+C = safe stop)
   --sim   run on a PC with a pretend Mega and pretend sensors (nothing real moves)
   --check load and validate the config, print the firmware id, exit"""
from __future__ import annotations
import argparse, copy, os, signal, sys, threading
from . import config, firmware
from .runtime import Runtime, log
from .server import serve


class _SimDevice:
    def __init__(self, value): self.value = value
    def start(self): pass
    def sample(self): return self.value
    def close(self): pass


def simulation_config(cfg):
    """Simulation must never start real GPIO, camera, sound or external AI IO."""
    cfg = copy.deepcopy(cfg)
    cfg["touch"]["enabled"] = False
    cfg["camera"].update(enabled=False, allow_tracking=False)
    cfg["voice"].update(tts_enabled=False, capture_enabled=False)
    cfg["ai"]["local_llm"]["enabled"] = False
    cfg["ai"]["cloud"].update(enabled=False, privacy_consent=False)
    cfg["integrations"]["web_tools_enabled"] = False
    cfg["storage"]["data_dir"] = "data/sim"
    cfg["memory"]["db"] = "data/sim/eve.db"
    return cfg


def _lock(cfg):
    path = config.data_path(cfg, os.path.join(cfg["storage"]["data_dir"], "eve.lock"))
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    handle = open(path, "w")
    try:
        import fcntl
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except ImportError:
        pass                                             # Windows (--sim only)
    except OSError:
        sys.exit("EVE is already running (another PuTTY window or the service). Stop that one first.")
    return handle


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="eve3")
    parser.add_argument("--sim", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        cfg = config.load()
    except (config.ConfigError, ValueError, OSError) as exc:
        sys.exit(f"Config problem: {exc}")
    if args.check:
        print(f"Config OK. Firmware id for this config: {firmware.firmware_id(cfg)}")
        return 0
    if args.sim:
        cfg = simulation_config(cfg)
    lock = _lock(cfg)
    if args.sim:
        from .sim import FakeMega
        mega = FakeMega(firmware_id=firmware.firmware_id(cfg), drive_enabled=cfg["firmware"]["drive_enabled"],
                        head_enabled=cfg["firmware"]["head_enabled"])
        mega.edge_level = list(cfg["sensors"]["cliff_calibration"]["edge_level"])
        mega.cliff = [1 - e for e in mega.edge_level]
        runtime = Runtime(cfg, opener=lambda: mega, tof=_SimDevice((600.0, 600.0, 600.0)), imu=_SimDevice(1.0),
                          throttled=lambda: 0)
        runtime.settle_s = 0
        log("SIMULATION: pretend Mega and sensors. Nothing real is connected.")
    else:
        runtime = Runtime(cfg)
    runtime.write_token()
    net = cfg["network"]
    server = serve(runtime, net["host"], net["port"])
    runtime.start()
    log(f"Face:    http://127.0.0.1:{net['port']}/")
    where = "<this-pi-ip>" if net["host"] == "0.0.0.0" else "127.0.0.1"
    log(f"Control: http://{where}:{net['port']}/control   (token: run  python3 tools/evectl.py token)")
    done = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: done.set())
    try:
        while not done.wait(0.5):
            pass
    finally:
        server.shutdown()
        runtime.stop()
        lock.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
