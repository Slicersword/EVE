"""Check hosted subpaths without weakening the offline export's relative-path rules."""
from pathlib import Path
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from check_site import check


class HostedDocumentationTests(unittest.TestCase):
    def fixture(self, root, href='/EVE/docs/guide.html#setup'):
        (root / 'docs').mkdir()
        (root / 'index.html').write_text(f'<a href="{href}">Setup</a>')
        (root / 'docs/guide.html').write_text('<h2 id="setup">Setup</h2><a href="/EVE/">Home</a>')
        (root / 'search-data.js').write_text('window.EVE_SEARCH=[{"url":"docs/guide.html","title":"Guide","text":"Setup"}];\n')

    def test_hosted_root_and_subpath_links_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            failures, checked = check(root, '/EVE/', 'search-data.js')
            self.assertEqual(failures, [])
            self.assertEqual(checked, 2)

    def test_bad_fragments_and_paths_outside_site_are_rejected(self):
        for href in ('/EVE/docs/guide.html#absent', '/another-site/index.html'):
            with self.subTest(href=href), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); self.fixture(root, href)
                failures, _ = check(root, '/EVE/', 'search-data.js')
                self.assertTrue(failures)

    def test_offline_checks_continue_to_reject_absolute_site_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            failures, _ = check(root, search_file='search-data.js')
            self.assertTrue(any('path escapes' in failure for failure in failures))

    def test_preview_frame_must_point_to_a_packaged_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            (root / 'docs/guide.html').write_text('<h2 id="setup">Setup</h2><iframe sandbox src="preview.html"></iframe>')
            self.assertTrue(any('missing file preview.html' in issue for issue in check(root, '/EVE/', 'search-data.js')[0]))
            (root / 'docs/preview.html').write_text('<fieldset disabled>Sample controls</fieldset>')
            self.assertEqual(check(root, '/EVE/', 'search-data.js')[0], [])

    def test_dynamic_progress_instruction_links_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.fixture(root)
            (root / 'docs/PROGRESS.html').write_text('<div id="build-progress"></div>')
            manifest = {'groups': [{'tasks': [{'id': 'test', 'href': 'docs/guide.html#setup'}]}]}
            data = root / 'progress-data.js'
            data.write_text('window.EVE_BUILD_PROGRESS=' + json.dumps(manifest) + ';\n')
            self.assertEqual(check(root, '/EVE/', 'search-data.js')[0], [])
            manifest['groups'][0]['tasks'][0]['href'] = 'docs/guide.html#missing'
            data.write_text('window.EVE_BUILD_PROGRESS=' + json.dumps(manifest) + ';\n')
            self.assertTrue(any('missing fragment' in issue for issue in check(root, '/EVE/', 'search-data.js')[0]))


if __name__ == '__main__':
    unittest.main()
