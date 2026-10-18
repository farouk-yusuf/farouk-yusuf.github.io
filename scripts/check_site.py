#!/usr/bin/env python3
"""Check static-site links, anchors, accessible chart tables and build freshness."""
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.ids = set()
        self.duplicates = []
        self.refs = []
        self.headings = 0
        self.figures = 0
        self.tables = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            if a['id'] in self.ids:
                self.duplicates.append(a['id'])
            self.ids.add(a['id'])
        for key in ('href', 'src'):
            if key in a:
                self.refs.append(a[key])
        if tag == 'img' and 'alt' not in a:
            raise AssertionError(f'Missing image alt: {self.path}')
        if tag == 'h1':
            self.headings += 1
        if tag == 'figure' and 'chart-panel' in a.get('class', ''):
            self.figures += 1
        if tag == 'table':
            self.tables += 1


def main():
    subprocess.run([sys.executable, str(ROOT/'scripts/build_site.py'), '--check'], check=True)
    skills = json.loads((ROOT/'site/skills.json').read_text())
    for tool in skills:
        assert len(tool['items']) == 4, f'Expected four capabilities: {tool["name"]}'
        assert (ROOT/'assets/icons'/tool['icon']).is_file(), f'Missing tool icon: {tool["name"]}'
    about = json.loads((ROOT/'site/about.json').read_text())
    assert len(about['milestones']) == 6, 'The journey should have six chapters'
    for chapter in about['milestones']:
        assert len(chapter['text'].split()) <= 45, f'Chapter exceeds 45 words: {chapter["date"]}'
    paths = [ROOT/'index.html', *sorted((ROOT/'case-studies').glob('*.html'))]
    pages = {}
    for path in paths:
        page = Page(path)
        page.feed(path.read_text())
        assert page.headings == 1, f'Expected exactly one h1: {path}'
        assert not page.duplicates, f'Duplicate IDs in {path}: {page.duplicates}'
        assert page.figures == page.tables, f'Chart missing its data table: {path}'
        pages[path] = page
    checked = 0
    for path, page in pages.items():
        for ref in page.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc:
                continue
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            assert target.is_relative_to(ROOT), f'Link escapes site: {ref}'
            assert target.exists(), f'Missing target in {path.name}: {ref}'
            if url.fragment and target in pages:
                assert unquote(url.fragment) in pages[target].ids, f'Broken anchor in {path.name}: {ref}'
            checked += 1
    originals = json.loads((ROOT/'site/resources.json').read_text())
    published = {ref for page in pages.values() for ref in page.refs}
    for resource in originals:
        assert resource['url'] in published, f'Original resource link lost: {resource["url"]}'
    for stylesheet in (ROOT/'assets/css').glob('*.css'):
        for ref in re.findall(r'url\([\'\"]?([^\)\'\"]+)', stylesheet.read_text()):
            if not urlsplit(ref).scheme:
                assert (stylesheet.parent / ref).resolve().exists(), f'Missing CSS resource: {ref}'
    print(f'Passed: {len(paths)} pages, {checked} local references, {len(originals)} preserved resource links, chart tables and CSS resources.')


if __name__ == '__main__':
    main()
