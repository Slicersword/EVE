import math, time, unittest
from eve3 import sensors
from eve3.mega_link import MegaLink
from eve3.motion import Drive, Head
from eve3.power import PowerSession, read_throttled
from eve3.safety import SafetyGate
from eve3.sim import FakeMega
from tests.helpers import Clock, FakeHub, FakeLink, cfg_with, good_frame


def rig(clock=None, throttled=lambda: 0, **flags):
    clock = clock or Clock()
    cfg = cfg_with(**(flags or {"all": True}))
    session = PowerSession(cfg, throttled=throttled, clock=clock)
    gate = SafetyGate(cfg, session, clock=clock)
    link = FakeLink()
    hub = FakeHub(good_frame(clock))
    return cfg, clock, session, gate, link, hub


class PowerTests(unittest.TestCase):
    def test_read_throttled_parses_and_fails_closed(self):
        class R:
            def __init__(self, out): self.stdout = out
        self.assertEqual(read_throttled(lambda *a, **k: R("throttled=0x50005\n")), 0x50005)
        self.assertIsNone(read_throttled(lambda *a, **k: R("VCHI error")))
        def boom(*a, **k): raise FileNotFoundError()
        self.assertIsNone(read_throttled(boom))

    def test_session_needs_power_flags_and_healthy_supply(self):
        cfg, clock, session, *_ = rig(power_a_verified=True)
        self.assertEqual(session.start(5)[0], False)                       # bank B + motor current missing
        for bad in (0, 31, 2.5, "5", True):
            self.assertFalse(rig()[2].start(bad)[0])
        self.assertFalse(rig(throttled=lambda: None)[2].start(5)[0])
        self.assertFalse(rig(throttled=lambda: 0x50005)[2].start(5)[0])
        self.assertTrue(rig(throttled=lambda: 0x50000)[2].start(5)[0])       # history only: allowed, shown in status

    def test_session_expires_and_ends_on_undervoltage(self):
        flags = [0]
        cfg, clock, session, *_ = rig(throttled=lambda: flags[0])
        self.assertTrue(session.start(1)[0] and session.active())
        clock.advance(61)
        self.assertFalse(session.active())
        session.start(5)
        flags[0] = 0x50005
        self.assertEqual(session.check(), "Pi under-voltage")
        self.assertFalse(session.active())
        session.start.__self__.until = 0
        flags[0] = None
        self.assertEqual(session.check(), "")                               # inactive: nothing to do
        self.assertIsNone(session.status()["battery_percent"])


class SensorTests(unittest.TestCase):
    def test_default_frame_is_unsafe(self):
        f = sensors.Frame()
        self.assertEqual(f.cliff, (True, True, True))
        self.assertEqual(f.tof_mm, (None, None, None))
        self.assertIsNone(f.tilt_deg)

    def test_valid_tof(self):
        for bad in (None, float("nan"), float("inf"), 29.9, 1000.1, "100", True, -5):
            self.assertFalse(sensors.valid_tof_mm(bad), bad)
        self.assertTrue(sensors.valid_tof_mm(30) and sensors.valid_tof_mm(1000.0))

    def test_decode_cliff(self):
        self.assertEqual(sensors.decode_cliff((1, 1, 1), (0, 0, 0), True), (False, False, False))
        self.assertEqual(sensors.decode_cliff((0, 1, 1), (0, 0, 0), True), (True, False, False))
        self.assertEqual(sensors.decode_cliff((1, 1, 0), (0, 0, 1), True), (False, False, False))
        self.assertEqual(sensors.decode_cliff((1, 1, 1), (0, 0, 0), False), (True, True, True))
        self.assertEqual(sensors.decode_cliff((1, None, 2), (0, 0, 0), True), (False, True, True))
        self.assertEqual(sensors.decode_cliff((1, 1), (0, 0, 0), True), (True, True, True))

    def test_calibrate_cliff(self):
        cal = sensors.calibrate_cliff([(1, 1, 0)] * 10, [(0, 0, 1)] * 10)
        self.assertEqual(cal, {"calibrated": True, "edge_level": [0, 0, 1]})
        with self.assertRaises(ValueError):
            sensors.calibrate_cliff([(1, 1, 1)] * 9, [(0, 0, 0)] * 10)       # too few
        with self.assertRaises(ValueError):
            sensors.calibrate_cliff([(1, 1, 1)] * 10, [(0, 1, 0)] * 10)      # centre did not change
        with self.assertRaises(ValueError):
            sensors.calibrate_cliff([(1, 1, 1)] * 9 + [(0, 1, 1)], [(0, 0, 0)] * 10)   # flicker

    def test_hub_and_mega_update(self):
        hub = sensors.SensorHub({"calibrated": True, "edge_level": [0, 0, 0]})
        hub.update_mega({"cliff_raw": (1, 0, 1), "pir": True}, at=5.0)
        hub.update_tof((100.0, None, 300.0), at=6.0)
        f = hub.snapshot()
        self.assertEqual((f.cliff, f.cliff_at, f.pir, f.tof_mm, f.tof_at), ((False, True, False), 5.0, True, (100.0, None, 300.0), 6.0))

    def test_mpu6050_tilt_and_rejects_bad_reads(self):
        class Bus:
            def __init__(self, raw): self.raw = raw
            def read_byte_data(self, a, r): return 0x68
            def write_byte_data(self, a, r, v): pass
            def read_i2c_block_data(self, a, r, n): return self.raw
            def close(self): pass
        def raw(ax, ay, az):
            out = []
            for g in (ax, ay, az):
                v = int(g * 16384) & 0xFFFF
                out += [v >> 8, v & 0xFF]
            return out
        imu = sensors.MPU6050(lambda: Bus(raw(0, 0, 1))); imu.start()
        self.assertAlmostEqual(imu.sample(), 0.0, places=1)
        imu = sensors.MPU6050(lambda: Bus(raw(0.5, 0, 0.866))); imu.start()
        self.assertAlmostEqual(imu.sample(), 30.0, delta=0.5)
        imu = sensors.MPU6050(lambda: Bus(raw(0, 0, -1))); imu.start()
        self.assertGreater(imu.sample(), 170)                                # upside down is NOT level
        imu = sensors.MPU6050(lambda: Bus([0] * 6)); imu.start()
        with self.assertRaises(ValueError):
            imu.sample()                                                     # all zeros = dead bus, not "level"

    def test_reader_restarts_failed_device_and_never_publishes_garbage(self):
        clock = Clock()
        hub = sensors.SensorHub()

        class Dev:
            def __init__(self, values): self.values, self.starts, self.fail_start = list(values), 0, False
            def start(self):
                self.starts += 1
                if self.fail_start: raise OSError("no device")
            def sample(self):
                v = self.values.pop(0)
                if isinstance(v, Exception): raise v
                return v
            def close(self): pass
        tof = Dev([(100.0, 200.0, 300.0), OSError("bus"), (1.0, 2.0, 3.0)])
        imu = Dev([1.0, ValueError("not 1 g"), 2.0])
        reader = sensors.SensorReader(hub, tof, imu, retry_s=5, clock=clock)
        reader.poll()
        first = hub.snapshot()
        self.assertEqual((first.tof_mm, first.tilt_deg), ((100.0, 200.0, 300.0), 1.0))
        reader.poll()                                                        # tof bus error, imu implausible
        failed = hub.snapshot()
        self.assertEqual((failed.tof_mm, failed.tilt_deg), ((None, None, None), None))
        self.assertEqual((failed.tof_at, failed.imu_at), (0, 0))
        self.assertFalse(reader.status()["tof"]["ok"])
        reader.poll()
        self.assertEqual(tof.starts, 1)                                      # waits retry_s before restarting
        clock.advance(6)
        reader.poll()
        self.assertEqual(tof.starts, 2)
        self.assertTrue(reader.status()["tof"]["ok"])


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.cfg, self.clock, self.session, self.gate, self.link, self.hub = rig()
        self.session.start(5)

    def ok(self, **over):
        return self.gate.drive_verdict(good_frame(self.clock, **over), self.link)

    def test_all_good_passes(self):
        self.assertTrue(self.ok().ok)

    def test_every_missing_or_bad_sensor_value_refuses(self):
        now = self.clock()
        cases = {
            "tof none": dict(tof_mm=(None, 500.0, 500.0)), "tof nan": dict(tof_mm=(float("nan"), 500.0, 500.0)),
            "tof rear none": dict(tof_mm=(500.0, 500.0, None)), "tof short tuple": dict(tof_mm=(500.0, 500.0)),
            "tof stale": dict(tof_at=now - 0.6), "tof never": dict(tof_at=0.0), "tof future": dict(tof_at=now + 5),
            "imu stale": dict(imu_at=now - 0.6), "tilt none": dict(tilt_deg=None), "tilt nan": dict(tilt_deg=float("nan")),
            "tilt big": dict(tilt_deg=29.0), "cliff stale": dict(cliff_at=now - 0.6), "cliff one": dict(cliff=(False, True, False)),
            "cliff none": dict(cliff=(False, None, False)), "cliff short": dict(cliff=()),
            "obstacle left": dict(tof_mm=(149.0, 500.0, 500.0)),
            "obstacle right": dict(tof_mm=(500.0, 100.0, 500.0)),
        }
        for name, over in cases.items():
            gate = SafetyGate(self.cfg, self.session, clock=self.clock)
            self.assertFalse(gate.drive_verdict(good_frame(self.clock, **over), self.link).ok, name)
        self.assertFalse(SafetyGate(self.cfg, self.session, clock=self.clock).drive_verdict(sensors.Frame(), self.link).ok)

    def test_cliff_and_tilt_latch_until_cleared(self):
        self.assertEqual(self.ok(cliff=(True, False, False)).reason, "cliff")
        self.assertIn("latched", self.ok().reason)                           # good frame is not enough any more
        self.assertFalse(self.gate.clear(good_frame(self.clock, cliff=(True, False, False)), self.link).ok)
        self.link.fail = RuntimeError("ERR,UNSAFE")
        self.assertFalse(self.gate.clear(good_frame(self.clock), self.link).ok)   # Mega disagrees -> stay latched
        self.link.fail = None
        self.assertTrue(self.gate.clear(good_frame(self.clock), self.link).ok)
        self.assertTrue(self.ok().ok)

    def test_uncalibrated_cliff_refuses_without_latching(self):
        self.cfg["sensors"]["cliff_calibration"]["calibrated"] = False
        self.assertIn("not calibrated", self.ok().reason)
        self.assertEqual(self.gate.latched, "")

    def test_obstacle_does_not_latch(self):
        self.assertEqual(self.ok(tof_mm=(100.0, 500.0, 500.0)).reason, "obstacle")
        self.assertTrue(self.ok().ok)

    def test_link_session_firmware_and_mega_latch_gates(self):
        self.link.is_online = False
        self.assertIn("offline", self.ok().reason)
        self.link.is_online, self.link.firmware_ok = True, False
        self.assertIn("firmware", self.ok().reason)
        self.link.firmware_ok = True
        self.link.telemetry["latched"] = True
        self.assertIn("Mega is latched", self.ok().reason)
        del self.link.telemetry["latched"]
        self.assertFalse(self.ok().ok)                                       # unknown latch state = unsafe
        self.link.telemetry["latched"] = False
        self.session.end()
        self.assertIn("attended", self.ok().reason)

    def test_each_commissioning_flag_is_required(self):
        for flag in ("power_a_verified", "power_b_verified", "motor_current_verified", "contained_ground_area", "drive_verified"):
            cfg, clock, session, gate, link, hub = rig()
            session.start(5)
            cfg["commissioning"][flag] = False
            v = gate.drive_verdict(good_frame(clock), link)
            self.assertFalse(v.ok, flag)
            self.assertIn(flag, v.reason)
        cfg, clock, session, gate, link, hub = rig()
        session.start(5)
        cfg["commissioning"]["drive_verified"] = False
        self.assertTrue(gate.drive_verdict(good_frame(clock), link, test=True).ok)   # M07 test mode only
        cfg["firmware"]["drive_enabled"] = False
        self.assertFalse(gate.drive_verdict(good_frame(clock), link, test=True).ok)

    def test_shipped_config_refuses_everything(self):
        cfg, clock, session, gate, link, hub = rig(power_a_verified=False)
        self.assertFalse(gate.drive_verdict(good_frame(clock), link).ok)
        self.assertFalse(gate.drive_verdict(good_frame(clock), link, test=True).ok)
        self.assertFalse(gate.head_verdict(good_frame(clock), link, test=True).ok)

    def test_head_gate(self):
        frame = good_frame(self.clock, tof_mm=(60.0, 60.0, 60.0))            # someone close: fine for the head
        self.assertTrue(self.gate.head_verdict(frame, self.link).ok)
        self.link.telemetry["drive_active"] = True
        self.assertFalse(self.gate.head_verdict(frame, self.link).ok)
        self.link.telemetry["drive_active"] = False
        self.cfg["commissioning"]["head_verified"] = False
        self.assertFalse(self.gate.head_verdict(frame, self.link).ok)
        self.assertTrue(self.gate.head_verdict(frame, self.link, test=True).ok)
        self.assertFalse(self.gate.head_verdict(good_frame(self.clock, tilt_deg=None), self.link, test=True).ok)

    def test_manual_latch(self):
        self.gate.latch("owner stop")
        self.assertIn("owner stop", self.ok().reason)


class MotionTests(unittest.TestCase):
    def setUp(self):
        self.cfg, self.clock, self.session, self.gate, self.link, self.hub = rig()
        self.session.start(5)
        self.drive = Drive(self.cfg, self.link, self.gate, self.hub, clock=self.clock)
        self.head = Head(self.cfg, self.link, self.gate, self.hub, clock=self.clock)

    def refresh(self, **over):
        self.hub.frame = good_frame(self.clock, **over)

    def test_drive_limits(self):
        for args in ((151, 100, 1), (100, 100, 0), (100, 100, 2.5), (-50, -50, 1), (50, -50, 1), (50, 0, 1),
                     (50.0, 50, 1), ("50", 50, 1), (True, 50, 1)):
            self.assertFalse(self.drive.move(*args)[0], args)
        self.assertNotIn(("DRIVE", 151, 100), self.link.sent)
        self.assertFalse(self.drive.move(100, 100, 0.5, test=True)[0])       # above test speed
        self.assertFalse(self.drive.move(60, 60, 1.5, test=True)[0])         # longer than a test move

    def test_drive_moves_renews_and_finishes(self):
        self.assertEqual(self.drive.move(100, 80, 1.0), (True, "moving"))
        self.assertEqual(self.link.sent[-1], ("DRIVE", 100, 80))
        for _ in range(9):
            self.clock.advance(0.1); self.refresh(); self.drive.tick()
        self.assertGreaterEqual(self.link.sent.count(("DRIVE", 100, 80)), 8)
        self.clock.advance(0.2); self.refresh(); self.drive.tick()
        self.assertEqual(self.link.sent[-1], ("DRIVE", 0, 0))
        self.assertIsNone(self.drive.active)

    def test_drive_stops_when_anything_goes_bad_mid_move(self):
        for breaker in (lambda: self.refresh(tof_mm=(100.0, 500.0, 500.0)), lambda: self.refresh(cliff=(False, False, True)),
                        lambda: None,                                       # frame simply goes stale
                        lambda: (self.refresh(), setattr(self.link, "is_online", False)),
                        lambda: (self.refresh(), self.session.end())):
            self.setUp()
            self.drive.move(100, 100, 2.0)
            self.clock.advance(0.1); self.refresh(); self.drive.tick()
            self.assertIsNotNone(self.drive.active)
            self.clock.advance(0.6); breaker(); self.drive.tick()
            self.assertIsNone(self.drive.active)
            self.assertEqual(self.link.sent[-1], ("DRIVE", 0, 0))

    def test_drive_refused_when_gate_closed(self):
        self.session.end()
        ok, why = self.drive.move(100, 100, 1.0)
        self.assertFalse(ok)
        self.assertNotIn(("DRIVE", 100, 100), self.link.sent)

    def test_stop_always_works_even_with_dead_link(self):
        self.link.stop_motion = lambda: (_ for _ in ()).throw(IOError("gone"))
        self.drive.move(0, 0, 0)
        self.assertIsNone(self.drive.active)

    def test_failed_motion_send_is_reported(self):
        def drop(*args):
            raise OSError("unplugged")
        self.link.drive = self.link.head = drop
        self.assertFalse(self.drive.move(60, 60, 1)[0])
        self.assertIsNone(self.drive.active)
        self.head.home(True)
        self.assertFalse(self.head.jog(4, 0, True)[0])
        self.assertFalse(self.head.homed)

    def test_head_home_needs_owner_confirmation(self):
        self.assertFalse(self.head.home(False)[0])
        self.assertFalse(self.head.home("yes")[0])
        self.assertTrue(self.head.home(True)[0])
        self.assertTrue(self.head.homed)

    def test_head_jog_rules(self):
        self.assertFalse(self.head.jog(4, 0, True)[0])                       # not homed
        self.head.home(True)
        for args in ((4, 0, False), (4, 4, True), (0, 0, True), (9, 0, True), (4.0, 0, True)):
            self.assertFalse(self.head.jog(*args)[0], args)
        self.assertTrue(self.head.jog(-8, 0, True)[0])
        self.assertEqual(self.link.sent[-1], ("HEAD", -8, 0))
        self.assertFalse(self.head.jog(1, 0, True)[0])                       # still moving
        self.link.telemetry.update(pan=-8)
        self.head.tick()
        self.assertTrue(self.head.jog(0, 3, True)[0])
        self.assertEqual(self.link.sent[-1], ("HEAD", -8, 3))

    def test_head_goto_needs_verified_limits_and_stays_inside(self):
        self.head.home(True)
        self.assertFalse(self.head.goto(10, 0)[0])                           # limits not verified
        self.head.limits_verified = True
        self.assertFalse(self.head.goto(651, 0)[0])
        self.assertFalse(self.head.goto(0, -261)[0])
        self.assertTrue(self.head.goto(100, -50)[0])
        self.clock.advance(0.15); self.refresh(); self.head.tick()
        self.assertEqual(self.link.sent.count(("HEAD", 100, -50)), 2)        # lease renewed
        self.session.end(); self.clock.advance(0.15); self.refresh(); self.head.tick()
        self.assertIsNone(self.head.target)                                  # stops renewing when unsafe

    def test_head_refused_when_gate_closed(self):
        self.gate.latch("cliff")
        self.assertFalse(self.head.home(True)[0])
        self.assertNotIn("HOMESET", self.link.sent)


class MegaLinkTests(unittest.TestCase):
    def make(self, mega=None, expected="sim000000000"):
        mega = mega or FakeMega()
        got = []
        link = MegaLink(lambda: mega, expected_id=expected, on_telemetry=lambda t, at: got.append(t))
        link.open(settle_s=0)
        self.addCleanup(link.close)
        return mega, link, got

    def pump(self, link, seconds=0.3):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            link.heartbeat()
            time.sleep(0.05)

    def test_sync_heartbeat_telemetry_online(self):
        mega, link, got = self.make()
        self.assertTrue(link.synced and link.firmware_ok)
        self.assertFalse(link.online())                                      # no heartbeat ACK yet
        self.pump(link)
        self.assertTrue(link.online())
        self.assertTrue(got and got[-1]["latched"] is True)
        self.assertEqual(link.clear_stop(), "ACK")

    def test_firmware_mismatch_is_reported(self):
        mega, link, _ = self.make(expected="somethingelse")
        self.assertTrue(link.synced)
        self.assertFalse(link.firmware_ok)

    def test_goes_offline_when_mega_falls_silent(self):
        mega, link, _ = self.make()
        self.pump(link)
        self.assertTrue(link.online())
        mega.silent = True
        self.pump(link, 0.6)
        self.assertFalse(link.online())

    def test_err_reply_raises_and_timeout_raises(self):
        mega, link, _ = self.make()
        with self.assertRaises(RuntimeError):
            link.clear_stop()                                                # no heartbeat yet -> ERR,UNSAFE
        mega.silent = True
        with self.assertRaises(TimeoutError):
            link.request("CLEAR", timeout_s=0.1)

    def test_open_fails_cleanly_without_mega(self):
        mega = FakeMega(); mega.silent = True
        link = MegaLink(lambda: mega)
        with self.assertRaises(TimeoutError):
            link.open(settle_s=0)
        self.assertFalse(link.synced)
        self.assertIsNone(link.ser)
        self.assertFalse(link.online())

    def test_close_sends_stop(self):
        mega, link, _ = self.make()
        link.close()
        self.assertEqual(mega.log[-1], "STOP")
        with self.assertRaises(RuntimeError):
            link.drive(10, 10)

    def test_corrupt_bytes_are_ignored(self):
        mega, link, _ = self.make()
        mega.rx.put(b"E1:5:T,1,1,1,0,0,0,0,0,0,0*0000\n")                    # bad CRC
        mega.rx.put(b"\xff\xfe garbage\n")
        mega.rx.put(b"x" * 400 + b"\n")
        self.pump(link)
        self.assertTrue(link.online())


if __name__ == "__main__":
    unittest.main()
