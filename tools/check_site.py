#!/usr/bin/env python3
"""Validate the built documentation without network access or robot hardware."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
import sys

ROOT = Path(__file__).resolve().parent.parent


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links, self.assets, self.duplicates = set(), [], [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                self.duplicates.append(attrs['id'])
            self.ids.add(attrs['id'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag in ('script', 'img') and attrs.get('src'):
            self.assets.append(attrs['src'])
        if tag == 'link' and attrs.get('href'):
            self.assets.append(attrs['href'])


def check(directory):
    directory = Path(directory).resolve()
    failures, checked = [], 0
    pages = {p.resolve(): Page(p.read_text(encoding='utf-8')) for p in directory.rglob('*.html')}
    if not (directory / 'index.html').is_file():
        return ['No index.html; run node tools/build_docs.mjs first'], 0
    for path, page in pages.items():
        failures.extend(f'{path.relative_to(directory)}: duplicate id {i}' for i in page.duplicates)
        for value in page.links + page.assets:
            url = urlsplit(value)
            if url.scheme or url.netloc:
                if value in page.assets:
                    failures.append(f'{path.name}: external asset {value}')
                continue
            if url.path.startswith('/'):
                failures.append(f'{path.name}: absolute path breaks offline/subpath hosting: {value}')
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            if not target.is_relative_to(directory) or not target.is_file():
                failures.append(f'{path.relative_to(directory)}: missing file {value}')
            elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
                failures.append(f'{path.relative_to(directory)}: missing fragment {value}')
            checked += 1
    for name in ('config/local.json', 'data/token', 'data/eve.db'):
        if (directory / 'raw' / name).exists():
            failures.append(f'Private runtime file published: {name}')
    search = directory / 'assets/search-data.js'
    if not search.is_file() or not search.read_text().startswith('window.EVE_SEARCH='):
        failures.append('Offline search data missing')
    else:
        entries = json.loads(search.read_text().removeprefix('window.EVE_SEARCH=').rstrip(';\n'))
        for entry in entries:
            if not (directory / entry['url']).is_file():
                failures.append(f'Search points to missing page: {entry["url"]}')
    # The raw listings must exactly match the repository, including their line endings.
    for path in (directory / 'raw').rglob('*'):
        if path.is_file():
            source = ROOT / path.relative_to(directory / 'raw')
            if not source.is_file() or source.read_bytes() != path.read_bytes():
                failures.append(f'Source listing differs: {source}')
    return failures, checked


def main():
    failures, checked = check(ROOT / 'dist')
    for failure in failures:
        print('FAIL:', failure)
    if failures:
        return 1
    print(f'PASS: {checked} local links/assets/fragments, source listings and offline search')
    return 0


if __name__ == '__main__':
    sys.exit(main())
