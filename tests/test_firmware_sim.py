"""Compiles the real Mega sketch against a fake Arduino core and tests its safety behaviour on the PC.
This checks logic only; it is not an AVR compile and closes no physical gate."""
import copy, re, shutil, subprocess, tempfile, unittest
from pathlib import Path
from eve3 import config, firmware

ROOT = config.ROOT
GXX = shutil.which("g++")


def build(tmp: Path, mutate) -> Path:
    cfg = copy.deepcopy(config.load())
    mutate(cfg)
    (tmp / "eve_config.h").write_text(firmware.header_text(cfg), "ascii")
    exe = tmp / "sim"
    subprocess.run([GXX, "-std=c++11", "-Wall", "-Werror", "-Wno-unused-function", "-include", str(tmp / "eve_config.h"),
                    "-I", str(ROOT / "firmware" / "host_check"), str(ROOT / "firmware" / "host_check" / "harness.cpp"),
                    "-o", str(exe)], check=True, capture_output=True, text=True)
    return exe


def enabled(cfg):
    cfg["firmware"].update(drive_enabled=True, head_enabled=True)
    cfg["sensors"]["cliff_calibration"].update(calibrated=True, edge_level=[0, 0, 0])


SAFE_PINS = "in 39 1\nin 40 1\nin 41 1\n"
ARM = SAFE_PINS + "rx SYNC\nrx HB\nrx CLEAR\n"


@unittest.skipUnless(GXX, "g++ not installed; firmware logic test needs a C++ compiler")
class FirmwareSim(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        for name, mut in (("on", enabled), ("off", lambda c: None),
                          ("nocal", lambda c: c["firmware"].update(drive_enabled=True, head_enabled=True))):
            (root / name).mkdir()
        cls.on = build(root / "on", enabled)
        cls.off = build(root / "off", lambda c: c["sensors"]["cliff_calibration"].update(calibrated=True))
        cls.nocal = build(root / "nocal", lambda c: c["firmware"].update(drive_enabled=True, head_enabled=True))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_sim(self, exe, script):
        out = subprocess.run([str(exe)], input=script, capture_output=True, text=True, timeout=20, check=True).stdout
        return out.strip().splitlines()

    @staticmethod
    def pwm(line):
        return [int(x) for x in re.search(r"pwm=([\d,]+)", line)[1].split(",")]

    def hb_drive(self, n, payload="DRIVE,100,100"):
        return "".join(f"rx HB\nrx {payload}\nms 80\n" for _ in range(n))

    def test_sync_reports_fingerprint_and_starts_latched(self):
        cfg = copy.deepcopy(config.load()); enabled(cfg)
        out = self.run_sim(self.on, SAFE_PINS + "rx SYNC\nrx HB\nrx DRIVE,100,100\nms 100\ndump\ntel\n")
        self.assertEqual(out[0], "TX ACK," + firmware.firmware_id(cfg))
        self.assertEqual(out[2], "TX ERR,UNSAFE")                  # latched until CLEAR
        self.assertEqual(self.pwm(out[3]), [0, 0, 0, 0])
        self.assertTrue(out[4].endswith(",1"))                      # telemetry says latched

    def test_drive_ramps_then_lease_expiry_stops(self):
        out = self.run_sim(self.on, ARM + self.hb_drive(6) + "dump\nrx HB\nms 200\nrx HB\nms 200\ndump\n")
        dumps = [l for l in out if l.startswith("D ")]
        self.assertEqual(self.pwm(dumps[0]), [100, 100, 100, 100])
        self.assertIn("stby=1,1", dumps[0])
        self.assertIn("fwd=1,1,1,1", dumps[0])
        self.assertEqual(self.pwm(dumps[1]), [0, 0, 0, 0])          # heartbeats alone did not keep it moving
        self.assertIn("stby=0,0", dumps[1])

    def test_heartbeat_loss_stops_and_latches(self):
        out = self.run_sim(self.on, ARM + self.hb_drive(4) + "rx DRIVE,100,100\nms 100\nrx DRIVE,100,100\nms 100\n"
                           "rx DRIVE,100,100\nms 100\nrx DRIVE,100,100\nms 100\ndump\nrx HB\nrx DRIVE,100,100\n")
        self.assertEqual(self.pwm([l for l in out if l.startswith("D ")][0]), [0, 0, 0, 0])
        self.assertEqual(out[-1], "TX ERR,UNSAFE")                  # stays latched after heartbeat returns

    def test_each_cliff_channel_stops_and_latches(self):
        for pin in (39, 40, 41):
            out = self.run_sim(self.on, ARM + self.hb_drive(4) + f"in {pin} 0\nms 2\ndump\nin {pin} 1\nrx HB\n"
                               "rx DRIVE,100,100\nrx CLEAR\nrx DRIVE,100,100\n")
            self.assertEqual(self.pwm([l for l in out if l.startswith("D ")][0]), [0, 0, 0, 0], pin)
            self.assertEqual(out[-3:], ["TX ERR,UNSAFE", "TX ACK", "TX ACK"], pin)

    def test_clear_refused_while_cliff_unsafe(self):
        out = self.run_sim(self.on, "in 39 0\nin 40 1\nin 41 1\nrx SYNC\nrx HB\nrx CLEAR\n")
        self.assertEqual(out[-1], "TX ERR,UNSAFE")

    def test_uncalibrated_cliff_never_arms(self):
        out = self.run_sim(self.nocal, ARM + "rx DRIVE,100,100\n")
        self.assertEqual(out[-2:], ["TX ERR,UNSAFE", "TX ERR,UNSAFE"])

    def test_disabled_firmware_never_moves(self):
        out = self.run_sim(self.off, ARM + "rx DRIVE,100,100\nrx HOMESET\nrx HEAD,10,0\nms 100\ndump\n")
        self.assertEqual(out[-4:-1], ["TX ERR,UNSAFE"] * 3)
        self.assertEqual(self.pwm(out[-1]), [0, 0, 0, 0])
        self.assertIn("coils=00000000", out[-1])

    def test_reverse_pivot_and_range_refused(self):
        out = self.run_sim(self.on, ARM + "rx DRIVE,-50,-50\nrx DRIVE,50,-50\nrx DRIVE,50,0\nrx DRIVE,999,10\n"
                           "rx DRIVE,10\nrx DRIVE,1e2,5\nrx NOPE\ndump\n")
        self.assertEqual(out[-8:-1], ["TX ERR,RANGE"] * 3 + ["TX ERR,CMD"] * 4)
        self.assertEqual(self.pwm(out[-1]), [0, 0, 0, 0])

    def test_stop_command_latches(self):
        out = self.run_sim(self.on, ARM + self.hb_drive(3) + "rx STOP\ndump\nrx HB\nrx DRIVE,100,100\n")
        self.assertEqual(self.pwm([l for l in out if l.startswith("D ")][0]), [0, 0, 0, 0])
        self.assertEqual(out[-1], "TX ERR,UNSAFE")

    def test_replayed_and_corrupt_frames_ignored(self):
        out = self.run_sim(self.on, ARM + "seq 1\nrx DRIVE,100,100\nraw E1:900:DRIVE,100,100*0000\nraw junk\nms 50\ndump\n")
        self.assertEqual(out[-1].split()[0], "D")
        self.assertEqual(self.pwm(out[-1]), [0, 0, 0, 0])
        self.assertEqual(len([l for l in out if l.startswith("TX")]), 3)   # only SYNC, HB, CLEAR were answered

    def test_head_needs_home_moves_inside_lease_and_releases_coils(self):
        script = ARM + "rx HEAD,20,0\nrx HOMESET\n" + "".join("rx HB\nrx HEAD,20,5\nms 60\n" for _ in range(4)) + "tel\ndump\n"
        script += "rx HB\nms 150\nrx HB\nms 150\ndump\n"
        out = self.run_sim(self.on, script)
        self.assertEqual(out[3], "TX ERR,UNSAFE")                   # HEAD before HOMESET
        tel = [l for l in out if l.startswith("TEL")][0].split(",")
        self.assertEqual(tel[5:8], ["1", "20", "5"])                # homed, pan=20, tilt=5
        self.assertIn("coils=00000000", out[-1])                    # released after reaching the target

    def test_head_lease_expiry_holds_position(self):
        out = self.run_sim(self.on, ARM + "rx HOMESET\nrx HEAD,600,0\nms 100\nrx HB\nms 200\nrx HB\nms 200\nrx HB\nms 300\ntel\ndump\n")
        tel = [l for l in out if l.startswith("TEL")][0].split(",")
        self.assertLess(int(tel[6]), 300)                           # stopped long before 600
        self.assertEqual(tel[8], "0")                               # not busy
        self.assertIn("coils=00000000", out[-1])

    def test_head_and_drive_are_mutually_exclusive(self):
        out = self.run_sim(self.on, ARM + "rx HOMESET\nrx HEAD,600,0\nms 20\nrx DRIVE,100,100\n")
        self.assertEqual(out[-1], "TX ERR,UNSAFE")
        out = self.run_sim(self.on, ARM + "rx HOMESET\nrx DRIVE,100,100\nms 20\nrx HEAD,50,0\n")
        self.assertEqual(out[-1], "TX ERR,UNSAFE")


if __name__ == "__main__":
    unittest.main()
