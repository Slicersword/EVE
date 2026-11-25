#!/usr/bin/env python3
"""Check the bundled release using the real HTTP entry points and simulated hardware."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import wave
from zipfile import ZipFile

from _common import ROOT, config
from eve3.__main__ import _SimDevice, simulation_config
from eve3.runtime import Runtime
from eve3.server import serve
from eve3.expressions import CATALOG, WEB


def check_pack():
    names = set(CATALOG["expressions"])
    if len(names) != 90 or names != set(CATALOG["clips"]):
        raise ValueError("Expected the complete 90-expression catalog.")
    with ZipFile(WEB / "expression-sounds.zip") as archive:
        if set(archive.namelist()) != {name + ".wav" for name in names} or len(archive.namelist()) != len(names):
            raise ValueError("Expression ZIP contents do not match the catalog.")
        for name, meta in CATALOG["clips"].items():
            clip = archive.read(name + ".wav")
            if len(clip) != meta["bytes"] or hashlib.sha256(clip).hexdigest() != meta["sha256"]:
                raise ValueError("Wrong expression asset: " + name)
            with wave.open(io.BytesIO(clip)) as wav:
                if not wav.getnframes():
                    raise ValueError("Empty expression audio: " + name)


def check_runtime():
    with tempfile.TemporaryDirectory() as tmp:
        # Supply fake drivers and isolated data. This opens no GPIO, camera, mic or serial.
        cfg = simulation_config(config.load(root=ROOT))
        cfg["_root"] = tmp
        rt = Runtime(cfg, opener=lambda: None, tof=_SimDevice((600.0,) * 3), imu=_SimDevice(1))
        http = serve(rt, "127.0.0.1", 0)
        base = f"http://127.0.0.1:{http.server_port}"

        def fetch(path, body=None, token=False):
            headers = {"X-EVE-Token": rt.token} if token else {}
            request = Request(base + path, json.dumps(body).encode() if body is not None else None, headers)
            with urlopen(request, timeout=4) as result:
                return result.read()

        def command(operation, **args):
            path = "/api/home-command" if operation.startswith("home.") else "/api/command"
            return json.loads(fetch(path, {"name": operation, "args": args}, token=True))

        def rejected(path, expected, body=None):
            try:
                fetch(path, body)
            except HTTPError as exc:
                assert exc.code == expected, (path, exc.code)
            else:
                raise AssertionError("Unexpected access to " + path)

        try:
            for path in ("/", "/control", "/home", "/home.js", "/home.css", "/expressions",
                         "/eva-face-art.js", "/expression-audio.js", "/expression-assets.json"):
                assert fetch(path), path
            assert fetch("/sfx/happy.wav").startswith(b"RIFF")
            rejected("/sfx/%2e%2e/expressions.json", 404)
            rejected("/api/audio-priority", 401)
            rejected("/api/home-command", 401, {"name": "home.view"})
            assert json.loads(fetch("/api/audio-priority", token=True))["home_available"]
            assert command("expression", name="proud_smile")["ok"]
            assert not command("expression", name="unknown_face")["ok"]
            assert not command("drive", left=50, right=50)["ok"]
            assert command("home.game", action="start", kind="riddles", lang="mr", players=["Team 1"])["message"]["game"]["options"]
            assert command("home.story", action="start", hero="Tara", lang="hi")["ok"]
            assert command("home.kitchen", action="start", title="Tea", steps=["Fill kettle", "Pour water"])["ok"]
            assert command("home.kitchen", action="next")["ok"]
            assert command("home.timer", name="Tea", seconds=30)["ok"]
            assert not command("home.messages", action="save", text="test record")["ok"]
            assert command("home.messages", action="save", text="test record", confirm=True)["ok"]
            assert command("home.capsule", action="save", title="Test", text="sample", confirm=True)["ok"]
            view = command("home.view")["message"]
            assert len(view["messages"]) == len(view["memories"]) == 1
            assert (Path(tmp) / "data/sim/home_companion.sqlite3").stat().st_mode & 0o777 == 0o600
            assert command("erase_memory", confirm=True)["ok"]
            assert not command("home.view")["message"]["messages"]
            assert command("sleep")["ok"]
            assert not command("home.view")["ok"]
            assert command("wake")["ok"]
            assert command("estop")["ok"]
            assert json.loads(fetch("/api/audio-priority", token=True))["stop_latched"]
        finally:
            http.shutdown()
            http.server_close()
            rt.stop()


if __name__ == "__main__":
    check_pack()
    check_runtime()
    print("PASS: all 90 original WAVs, face and home routes, private commands, and locked motion defaults")
