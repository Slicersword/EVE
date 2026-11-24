import tempfile
from pathlib import Path
import unittest

from tools import setup_i2s_mic as mic


class MicrophoneSetupTests(unittest.TestCase):
    def test_boot_edit_is_repeatable_and_preserves_existing_settings(self):
        original = '# existing\ndtparam=audio=on\n[pi4]\nmax_framebuffers=2\n'
        configured = mic.boot_config(original)
        self.assertTrue(configured.startswith(original))
        self.assertEqual(mic.boot_config(configured), configured)
        self.assertIn('[all]\ndtparam=i2s=on\ndtoverlay=eve-inmp441', configured)
        later = configured + '# later user setting\n[pi4]\narm_boost=1\n'
        self.assertEqual(mic.boot_config(later), later)

    def test_conflicting_or_malformed_profiles_stop_before_editing(self):
        for text in ('dtoverlay=googlevoicehat-soundcard\n', 'dtoverlay=adau7002-simple\n',
                     mic.START + '\nmissing end', mic.END + '\n' + mic.START):
            with self.subTest(text=text), self.assertRaises(ValueError):
                mic.boot_config(text)

    def test_capture_profile_keeps_playback_and_forces_stereo_32bit_frames(self):
        original = 'pcm.!default { type pulse }\n'
        configured = mic.audio_config(original)
        self.assertTrue(configured.startswith(original))
        self.assertEqual(mic.audio_config(configured), configured)
        for value in ('format S32_LE', 'channels 2', 'rate 48000', 'route_policy average',
                      'hw:CARD=EVEINMP441,DEV=0'):
            self.assertIn(value, configured)
        with self.assertRaises(ValueError):
            mic.audio_config('pcm.eve_mic { type hw }')

    def test_backups_preserve_original_and_noop_does_not_make_another(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'config.txt'
            target.write_text('original\n')
            mic.backup_write(target, 'changed\n')
            backup = list(Path(temp).glob('*.eve-backup-*'))
            self.assertEqual(len(backup), 1)
            self.assertEqual(backup[0].read_text(), 'original\n')
            mic.backup_write(target, 'changed\n')
            self.assertEqual(list(Path(temp).glob('*.eve-backup-*')), backup)


if __name__ == '__main__':
    unittest.main()
