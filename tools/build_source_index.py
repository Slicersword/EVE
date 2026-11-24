#!/usr/bin/env python3
"""Generate the self-contained public source snapshot consumed by Jekyll.

Only selected public build-source folders/files are included. Never walk data,
local overrides, downloaded models or the generated snapshot itself.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / '_data/source_files.json'


def source_files():
    files = ['eve', 'requirements.txt', '.gitignore', 'config/eve.json', 'config/local.example.json',
             'config/alsa-inmp441.conf', 'config/eve-inmp441-overlay.dts', '_config.yml',
             '_layouts/manual.html', 'index.html', 'search-data.js', 'progress-data.js', 'source-data.js',
             'code.html', '_data/navigation.json', '_data/build_progress.json']
    allowed = {'.py', '.ino', '.h', '.cpp', '.mjs', '.js', '.css', '.svg', '.sh', '.json', '.html', '.yml', '.yaml', '.service', '.dts', '.conf'}
    for folder in ('eve3', 'firmware', 'tools', 'scripts', 'systemd', 'tests', '.github', 'site/assets'):
        for path in (ROOT / folder).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and 'vendor' not in path.parts and path.suffix in allowed:
                files.append(path.relative_to(ROOT).as_posix())
    return {name: (ROOT / name).read_text() for name in sorted(set(files))}


def render():
    return json.dumps(source_files(), ensure_ascii=False, indent=1) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            parser.exit(1, 'Source viewer is stale: run python3 tools/build_source_index.py\n')
        print('PASS: public source viewer matches the build source')
    else:
        OUTPUT.parent.mkdir(exist_ok=True)
        OUTPUT.write_text(text)
        print(f'Generated {len(source_files())} public source files')


if __name__ == '__main__':
    main()
