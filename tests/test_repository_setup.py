"""Regression coverage for real setup acceptance errors and IO/privacy boundaries."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from eve3 import config, voice
from eve3.__main__ import simulation_config

TOOLS = Path(__file__).resolve().parent.parent / 'tools'
sys.path.insert(0, str(TOOLS))
import stage


class StageAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.cfg = config.load()

    def test_level_tilt_accepts_zero_but_rejects_missing_and_invalid(self):
        for value, expected in ((0, True), (2.5, True), (-2.5, True), (None, False),
                                (True, False), (10, False), (-25, False), (float('nan'), False)):
            with self.subTest(value=value), patch.object(stage, 'st', return_value={'sensors': {'tilt_deg': value}}):
                self.assertEqual(stage.level_tilt(self.cfg), expected)

    def test_zero_age_is_fresh_and_all_three_channels_are_required(self):
        keys = ('tof_age_s', 'imu_age_s', 'mega_age_s')
        readings = dict.fromkeys(keys, 0.0)
        with patch.object(stage, 'st', return_value={'sensors': readings}):
            self.assertTrue(stage.fresh_sensors(self.cfg))
        for key in keys:
            for bad in (None, -0.1, 0.5, float('inf'), True):
                with self.subTest(key=key, bad=bad):
                    values = {**readings, key: bad}
                    with patch.object(stage, 'st', return_value={'sensors': values}):
                        self.assertFalse(stage.fresh_sensors(self.cfg))

    def test_power_check_requires_actual_zero_flags(self):
        for flags, expected in ((0, True), (1, False), (0x50000, False), (None, False)):
            with self.subTest(flags=flags), patch('eve3.power.read_throttled', return_value=flags):
                self.assertEqual(stage.healthy_supply(self.cfg), expected)

    def test_generated_guide_has_no_window_labels_inside_shell_blocks(self):
        inside = False
        for line in stage.guide().splitlines():
            if line.startswith('```'):
                inside = not inside
            elif inside:
                self.assertFalse(line.startswith(('[PuTTY', '[Windows', '[you]')))


class IsolationTests(unittest.TestCase):
    def test_missing_ram_directory_cannot_create_disk_audio(self):
        with patch('eve3.voice.os.path.isdir', return_value=False), patch('eve3.voice.tempfile.mkstemp') as create:
            with self.assertRaisesRegex(RuntimeError, 'refusing'):
                voice.transcribe(config.load(), b'\x00\x00')
            create.assert_not_called()

    def test_simulation_never_starts_enabled_physical_or_cloud_features(self):
        source = config.load()
        source['camera'].update(enabled=True, allow_tracking=True)
        source['voice'].update(tts_enabled=True, capture_enabled=True)
        source['ai']['cloud'].update(enabled=True, privacy_consent=True)
        source['ai']['local_llm']['enabled'] = True
        source['integrations']['web_tools_enabled'] = True
        before = copy.deepcopy(source)
        sim = simulation_config(source)
        self.assertEqual(source, before)
        for section, key in (('touch','enabled'), ('camera','enabled'), ('camera','allow_tracking'),
                             ('voice','tts_enabled'), ('voice','capture_enabled'),
                             ('integrations','web_tools_enabled')):
            self.assertIs(sim[section][key], False)
        self.assertIs(sim['ai']['cloud']['enabled'], False)
        self.assertIs(sim['ai']['local_llm']['enabled'], False)
        self.assertEqual(sim['storage']['data_dir'], 'data/sim')
        self.assertEqual(sim['memory']['db'], 'data/sim/eve.db')
        self.assertEqual(sim['commissioning'], source['commissioning'])


if __name__ == '__main__':
    unittest.main()
