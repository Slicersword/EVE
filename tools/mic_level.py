#!/usr/bin/env python3
"""M13 - measure the microphone so the speech threshold (voice.vad_rms) can be set. EVE must be STOPPED.
  python3 tools/mic_level.py       stay silent for 3 s, then talk normally for 3 s.
Nothing is saved; the sound is only measured."""
import subprocess, sys
from _common import config, eve_running
from eve3.voice import rms


def measure(cfg, seconds=3):
    v = cfg["voice"]
    rate = int(v["sample_rate"])
    proc = subprocess.run(["arecord", "-q", "-D", str(v["capture_device"]), "-f", "S16_LE", "-r", str(rate), "-c", "1",
                           "-t", "raw", "-d", str(seconds)], capture_output=True, timeout=seconds + 5)
    if proc.returncode or not proc.stdout:
        sys.exit("Microphone did not record: " + proc.stderr.decode(errors="replace").strip()[:300]
                 + "\nList devices with:  arecord -L   then  python3 tools/evecfg.py set voice.capture_device <name>")
    chunk = rate // 10 * 2
    levels = sorted(rms(proc.stdout[i:i + chunk]) for i in range(0, len(proc.stdout) - chunk + 1, chunk))
    return levels[len(levels) // 2], levels[int(len(levels) * 0.9)]


def main():
    if eve_running():
        sys.exit("Stop EVE first (Ctrl+C in PuTTY 1).")
    cfg = config.load()
    input("Keep the room quiet, then press Enter ...")
    quiet, _ = measure(cfg)
    input("Now press Enter and talk normally from 1 metre for 3 seconds ...")
    _, loud = measure(cfg)
    print(f"quiet level ~ {quiet:.0f}   speech level ~ {loud:.0f}")
    if loud < quiet * 2.5 or loud < 100:
        print("Speech is not clearly louder than the room. Check the microphone wiring/device or raise its gain.")
        return 1
    suggestion = int((quiet * 2 + loud) / 3)
    print(f"Suggested threshold: {suggestion}\nSet it with:  python3 tools/evecfg.py set voice.vad_rms {suggestion}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
