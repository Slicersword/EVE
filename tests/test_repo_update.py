"""Exercise the owner updater with local Git repositories and private fixture data."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest

from eve3 import config, firmware


@unittest.skipUnless(shutil.which('git'), 'requires Git')
class RepositoryUpdateTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.upstream = root / 'upstream'
        self.owner = root / 'owner'
        self.backups = root / 'backups'
        self.upstream.mkdir()
        self.git(self.upstream, 'init', '--quiet', '-b', 'main')
        self.git(self.upstream, 'config', 'user.name', 'EVE test')
        self.git(self.upstream, 'config', 'user.email', 'eve@example.invalid')

        self.header = Path('firmware/eve_controller/eve_config.h')
        for name in ('.gitignore', 'scripts/update_repo.sh', 'tools/_common.py', 'tools/gen_header.py',
                     'config/eve.json', 'eve3/__init__.py', 'eve3/config.py', 'eve3/firmware.py', self.header):
            destination = self.upstream / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(config.ROOT / name, destination)
        (self.upstream / 'tests').mkdir()
        (self.upstream / 'tests/__init__.py').touch()
        (self.upstream / 'tests/test_check.py').write_text(
            'import unittest\n\nclass Check(unittest.TestCase):\n    def test_checkout(self):\n        pass\n')
        (self.upstream / 'tools/check_repo.py').touch()
        (self.upstream / 'tools/check_clone.py').touch()
        self.base = self.commit('Fixture baseline')
        self.git(root, 'clone', '--quiet', str(self.upstream), str(self.owner))

        self.settings = Path('config/local.json')
        self.owner_settings = json.dumps({'drive': {'max_pwm': 120}})
        (self.owner / self.settings).write_text(self.owner_settings)
        self.owner_header = firmware.header_text(config.load(self.owner))
        (self.owner / self.header).write_text(self.owner_header)
        (self.owner / 'data').mkdir()
        (self.owner / 'data/example.txt').write_text('private fixture')

    @staticmethod
    def git(directory, *args):
        return subprocess.run(['git', *args], cwd=directory, text=True, capture_output=True, check=True).stdout.strip()

    def commit(self, message):
        self.git(self.upstream, 'add', '-A')
        self.git(self.upstream, 'commit', '--quiet', '-m', message)
        return self.git(self.upstream, 'rev-parse', 'HEAD')

    def update(self):
        return subprocess.run(['bash', 'scripts/update_repo.sh'], cwd=self.owner, input='YES\n',
                              env={**os.environ, 'EVE_BACKUP_DIR': str(self.backups)},
                              text=True, capture_output=True, timeout=30)

    def assert_owner_state(self, revision):
        self.assertEqual(self.git(self.owner, 'rev-parse', 'HEAD'), revision)
        self.assertEqual((self.owner / self.settings).read_text(), self.owner_settings)
        self.assertEqual((self.owner / self.header).read_text(), self.owner_header)
        self.assertEqual((self.owner / 'data/example.txt').read_text(), 'private fixture')

    def test_failed_candidate_checks_leave_installed_files_in_place(self):
        (self.upstream / 'tools/check_repo.py').write_text("raise SystemExit('Fixture check failed')\n")
        self.commit('Fail pre-update check')
        result = self.update()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Fixture check failed', result.stderr)
        self.assert_owner_state(self.base)
        self.assertFalse(self.backups.exists())

    def test_incompatible_local_settings_leave_installed_files_in_place(self):
        defaults = self.upstream / 'config/eve.json'
        data = json.loads(defaults.read_text())
        data['drive']['test_pwm'] = 130
        defaults.write_text(json.dumps(data))
        self.commit('Raise the fixture test PWM above the owner limit')
        result = self.update()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('max_pwm/test_pwm out of range', result.stderr)
        self.assert_owner_state(self.base)
        self.assertFalse(self.backups.exists())

    def test_successful_update_keeps_private_backup_and_skips_noop_backup(self):
        sketch = self.upstream / 'firmware/eve_controller/eve_controller.ino'
        sketch.write_text('// Updated fixture sketch\n')
        target = self.commit('Change firmware')
        result = self.update()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Follow M02 to flash', result.stdout)
        self.assert_owner_state(target)
        backups = list(self.backups.glob('*.tar.gz'))
        self.assertEqual(len(backups), 1)
        with tarfile.open(backups[0]) as archive:
            self.assertEqual(archive.extractfile(f'./{self.header}').read().decode(), self.owner_header)
            self.assertEqual(archive.extractfile('./data/example.txt').read(), b'private fixture')

        result = self.update()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('already at the latest revision', result.stdout)
        self.assertEqual(list(self.backups.glob('*.tar.gz')), backups)

    def test_refused_merge_preserves_config_and_restores_the_local_header(self):
        (self.upstream / self.settings).write_text('{}')
        self.git(self.upstream, 'add', '-f', str(self.settings))
        self.commit('Track a path already used by private settings')
        result = self.update()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('original header and backup were retained', result.stdout)
        self.assert_owner_state(self.base)
        self.assertEqual(len(list(self.backups.glob('*.tar.gz'))), 1)
