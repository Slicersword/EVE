"""Fakes shared by the tests: a fake clock, a fake Mega link and helpers for a fully-commissioned config."""
import copy
from eve3 import config
from eve3.sensors import Frame


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


class FakeLink:
    def __init__(self):
        self.is_online, self.firmware_ok = True, True
        self.telemetry = {"latched": False, "drive_active": False, "homed": False, "pan": 0, "tilt": 0}
        self.sent = []
        self.fail = None                 # exception to raise on the next request-style call

    def online(self, now=None):
        return self.is_online

    def _req(self, name):
        if self.fail:
            raise self.fail
        self.sent.append(name)
        return "ACK"

    def drive(self, l, r): self.sent.append(("DRIVE", l, r))
    def stop_motion(self): self.sent.append(("DRIVE", 0, 0))
    def emergency_stop(self): self.sent.append("STOP")
    def head(self, p, t): self.sent.append(("HEAD", p, t))
    def clear_stop(self): return self._req("CLEAR")
    def release_head(self): return self._req("HEADSTOP")

    def set_manual_home(self):
        self._req("HOMESET")
        self.telemetry.update(homed=True, pan=0, tilt=0)


def cfg_with(**flags):
    """Shipped config with selected commissioning flags true. all=True unlocks everything."""
    cfg = copy.deepcopy(config.load())
    if flags.pop("all", False):
        for k in cfg["commissioning"]:
            cfg["commissioning"][k] = True
        cfg["firmware"].update(drive_enabled=True, head_enabled=True)
        cfg["sensors"]["cliff_calibration"].update(calibrated=True)
    cfg["commissioning"].update(flags)
    return cfg


def good_frame(clock, **over):
    base = dict(tof_mm=(500.0, 500.0, 500.0), tof_at=clock(), tilt_deg=2.0, imu_at=clock(),
                cliff=(False, False, False), cliff_raw=(1, 1, 1), cliff_at=clock(), pir=False)
    base.update(over)
    return Frame(**base)


class FakeHub:
    def __init__(self, frame):
        self.frame = frame

    def snapshot(self):
        return self.frame
