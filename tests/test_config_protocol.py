import copy, json, tempfile, unittest
from pathlib import Path
from eve3 import config, protocol


def base():
    return config.load()


class ConfigTests(unittest.TestCase):
    def test_shipped_config_is_valid_and_everything_is_locked(self):
        cfg = base()
        self.assertTrue(all(v is False for v in cfg["commissioning"].values()))
        self.assertFalse(cfg["firmware"]["drive_enabled"] or cfg["firmware"]["head_enabled"])
        self.assertFalse(cfg["drive"]["reverse_allowed"] or cfg["drive"]["pivot_allowed"])
        self.assertFalse(cfg["camera"]["enabled"] or cfg["voice"]["capture_enabled"])
        self.assertFalse(cfg["ai"]["cloud"]["enabled"] or cfg["integrations"]["web_tools_enabled"])
        self.assertEqual(cfg["network"]["host"], "127.0.0.1")
        self.assertFalse(cfg["sensors"]["cliff_calibration"]["calibrated"])

    def bad(self, mutate):
        cfg = copy.deepcopy(base())
        mutate(cfg)
        with self.assertRaises(config.ConfigError):
            config.validate(cfg)

    def test_rejects_unsafe_values(self):
        self.bad(lambda c: c["hardware"].update(ina219_enabled=True))
        self.bad(lambda c: c["commissioning"].update(drive_verified="yes"))
        self.bad(lambda c: c["commissioning"].update(extra=True))
        self.bad(lambda c: c["firmware"].update(drive_enabled=True))            # power flags still false
        self.bad(lambda c: c["commissioning"].update(drive_verified=True))      # firmware drive off
        self.bad(lambda c: c["drive"].update(max_pwm=300))
        self.bad(lambda c: c["drive"].update(command_lease_ms=5000))
        self.bad(lambda c: c["safety"].update(mega_watchdog_ms=150))
        self.bad(lambda c: c["ai"]["cloud"].update(send_private_data=True))
        self.bad(lambda c: c["ai"]["cloud"].update(enabled=True))               # no consent
        self.bad(lambda c: c["ai"]["cloud"].update(enabled=True, privacy_consent=True, endpoint="http://x"))
        self.bad(lambda c: c["ai"]["local_llm"].update(endpoint="http://example.com/v1"))
        self.bad(lambda c: c["network"].update(host="192.168.1.5"))
        self.bad(lambda c: c["sensors"]["cliff_calibration"].update(edge_level=[0, 2, 0]))
        self.bad(lambda c: c["ai"].update(api_key="abc123"))

    def test_local_overlay_merge_save_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config" / "eve.json").write_text((config.ROOT / "config" / "eve.json").read_text("utf-8"), "utf-8")
            config.save_local(root, {"commissioning": {"power_a_verified": True}})
            config.save_local(root, {"drive": {"max_pwm": 120}})
            cfg = config.load(root)
            self.assertTrue(cfg["commissioning"]["power_a_verified"])
            self.assertEqual(cfg["drive"]["max_pwm"], 120)
            self.assertEqual(cfg["drive"]["test_pwm"], 80)                      # untouched default kept
            with self.assertRaises(config.ConfigError):
                config.save_local(root, {"firmware": {"drive_enabled": True}})
            self.assertNotIn("firmware", json.loads((root / "config" / "local.json").read_text("utf-8")))

    def test_data_path_cannot_escape(self):
        cfg = base()
        self.assertTrue(str(config.data_path(cfg, "data/eve.db")).endswith("eve.db"))
        with self.assertRaises(config.ConfigError):
            config.data_path(cfg, "../outside.key")

    def test_missing_flags(self):
        self.assertEqual(config.missing_flags(base(), config.POWER_FLAGS), list(config.POWER_FLAGS))


class ProtocolTests(unittest.TestCase):
    def test_crc_known_vector(self):
        self.assertEqual(protocol.crc16_ccitt(b"123456789"), 0x29B1)

    def test_round_trip(self):
        self.assertEqual(protocol.decode(protocol.encode(7, "DRIVE,10,-10")), (7, "DRIVE,10,-10"))

    def test_encode_rejects_bad_input(self):
        for seq, payload in ((0, "HB"), (65536, "HB"), (True, "HB"), (1, ""), (1, "A*B"), (1, "A:B"),
                             (1, "A\nB"), (1, "x" * 300)):
            with self.assertRaises(ValueError):
                protocol.encode(seq, payload)

    def test_decode_rejects_corruption(self):
        good = protocol.encode(5, "HB")
        for bad in (good[:-1], good.replace(b"HB", b"HC"), b"E1:0:HB*0000\n", b"E2" + good[2:],
                    b"garbage\n", good + good, b"E1:5:" + b"x" * 300 + b"*0000\n"):
            with self.assertRaises(ValueError):
                protocol.decode(bad)

    def test_telemetry(self):
        t = protocol.parse_telemetry("T,1,0,1,1,0,-12,30,0,1,1")
        self.assertEqual(t["cliff_raw"], (1, 0, 1))
        self.assertTrue(t["pir"] and t["drive_active"] and t["latched"])
        self.assertEqual((t["pan"], t["tilt"]), (-12, 30))
        for bad in ("T,1,0,1", "X,1,0,1,1,0,0,0,0,1,1", "T,2,0,1,1,0,0,0,0,1,1", "T,1,0,1,1,0,9999,0,0,1,1",
                    "T,1,0,1,1,0,a,0,0,1,1", "T,1,0,1,1,0, 1,0,0,1,1", "T,1,0,1,1,0,1e2,0,0,1,1"):
            with self.assertRaises(ValueError):
                protocol.parse_telemetry(bad)


if __name__ == "__main__":
    unittest.main()
