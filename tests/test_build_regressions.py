"""Configuration and installer contracts that must work before physical commissioning."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from eve3 import config
from eve3.mega_link import find_port

ROOT = config.ROOT
sys.path.insert(0, str(ROOT / 'tools'))
import _common
import i2c_diag


class ConfigurationRegressionTests(unittest.TestCase):
    def reject(self, section, key, value):
        cfg = copy.deepcopy(config.load())
        cfg[section][key] = value
        with self.assertRaises(config.ConfigError):
            config.validate(cfg)

    def test_wrong_types_and_nonfinite_values_fail_before_hardware(self):
        for section, key, value in (
            ('safety', 'max_tilt_deg', True), ('safety', 'mega_watchdog_ms', 350.5),
            ('head', 'pan_max_steps', float('inf')), ('drive', 'ramp_per_second', -1),
            ('drive', 'reverse_deadtime_ms', float('nan')), ('serial', 'baud', 9600),
            ('serial', 'settle_s', -1), ('camera', 'tracking_pan_sign', 0),
            ('voice', 'sample_rate', 0), ('storage', 'data_dir', 'published'),
            ('memory', 'db', 'data/../../private.db')):
            with self.subTest(section=section, key=key, value=value):
                self.reject(section, key, value)

    def test_invalid_structure_and_unknown_fields_report_config_error(self):
        for cfg in ([], {'drive': {}}, {**config.load(), 'sensors': []},
                    {**config.load(), 'typo': True}):
            with self.subTest(cfg=type(cfg)), self.assertRaises(config.ConfigError):
                config.validate(cfg)
        with self.assertRaises(config.ConfigError):
            config.deep_merge({}, [])

    def test_pin_collisions_and_non_pwm_outputs_are_rejected(self):
        self.reject('sensors', 'tof_xshut', [5, 5, 13])
        self.reject('touch', 'head_gpio', 2)
        self.reject('touch', 'head_gpio', 5)
        cfg = copy.deepcopy(config.load())
        cfg['pins']['mega']['left'][3] = 42  # D42 has no hardware PWM
        with self.assertRaises(config.ConfigError):
            config.validate(cfg)
        cfg['pins']['mega']['left'][3] = 9   # already assigned to right STBY
        with self.assertRaises(config.ConfigError):
            config.validate(cfg)

    def test_tof_addresses_must_be_distinct_and_not_the_imu_or_poweron_address(self):
        for addresses in ([48, 48, 50], [0x29, 49, 50], [0x68, 49, 50], [48, 49]):
            with self.subTest(addresses=addresses):
                self.reject('sensors', 'tof_addresses', addresses)

    def test_example_overrides_are_valid_and_do_not_unlock_actuators(self):
        example = json.loads((ROOT / 'config/local.example.json').read_text())
        cfg = config.validate(config.deep_merge(config.load(), example))
        self.assertFalse(any(cfg['commissioning'].values()))
        self.assertFalse(cfg['firmware']['drive_enabled'])
        self.assertFalse(cfg['firmware']['head_enabled'])

    def test_local_settings_are_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / 'config').mkdir()
            shutil.copy(ROOT / 'config/eve.json', root / 'config/eve.json')
            config.save_local(root, {'robot': {'language': 'hi'}})
            self.assertEqual((root / 'config/local.json').stat().st_mode & 0o777, 0o600)


class DeviceSelectionRegressionTests(unittest.TestCase):
    def test_explicit_serial_port_wins_over_other_ch340_devices(self):
        with patch('eve3.mega_link.glob.glob', return_value=['/dev/serial/by-id/other-board']):
            self.assertEqual(find_port('/dev/ttyACM1'), '/dev/ttyACM1')
            self.assertEqual(find_port(None), '/dev/serial/by-id/other-board')
        with patch('eve3.mega_link.glob.glob', return_value=['one', 'two']):
            with self.assertRaises(ValueError):
                find_port(None)

    def test_runtime_lock_uses_configured_private_data_directory(self):
        import fcntl
        with tempfile.TemporaryDirectory() as tmp:
            cfg = copy.deepcopy(config.load()); cfg['_root'] = tmp
            cfg['storage']['data_dir'] = 'data/custom'
            lock = Path(tmp) / 'data/custom/eve.lock'; lock.parent.mkdir(parents=True)
            with lock.open('w') as handle, patch.object(_common.config, 'load', return_value=cfg):
                self.assertFalse(_common.eve_running())
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.assertTrue(_common.eve_running())

    def test_i2c_advice_includes_configured_shutdown_pin(self):
        advice = i2c_diag.advice([0x68], [False, True, True], True, [17, 6, 13], [11, 31, 33])
        self.assertIn('BCM17, pin 11', advice[0])


class FlashScriptRegressionTests(unittest.TestCase):
    def run_flash(self, upload_result):
        # A fake arduino-cli and a PTY verify selection/failure behavior without a Mega.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for directory in ('eve3', 'scripts', 'tools', 'config', 'firmware'):
                shutil.copytree(ROOT / directory, root / directory, ignore=shutil.ignore_patterns('__pycache__'))
            master, slave = os.openpty()
            self.addCleanup(os.close, master); self.addCleanup(os.close, slave)
            port = os.ttyname(slave)
            (root / 'config/local.json').write_text(json.dumps({'serial': {'port': port}}))
            bindir = root / 'bin'; bindir.mkdir()
            fake = bindir / 'arduino-cli'
            fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$EVE_TEST_CLI_LOG"\n'
                            f'[ "$1" != upload ] || exit {upload_result}\n')
            fake.chmod(0o755)
            log = root / 'cli.log'
            env = {**os.environ, 'PATH': str(bindir)+os.pathsep+os.environ['PATH'], 'EVE_TEST_CLI_LOG': str(log)}
            result = subprocess.run(['bash', 'scripts/flash_mega.sh', '--yes'], cwd=root, env=env,
                                    text=True, capture_output=True, timeout=20)
            self.assertIn(f'-p {port}', log.read_text())
            self.assertEqual(result.returncode, upload_result, result.stdout + result.stderr)
            self.assertEqual((root / 'data/eve_config.last_flashed.h').is_file(), upload_result == 0)

    def test_flasher_uses_selected_port_and_records_only_successful_upload(self):
        self.run_flash(0)
        self.run_flash(42)


if __name__ == '__main__':
    unittest.main()
