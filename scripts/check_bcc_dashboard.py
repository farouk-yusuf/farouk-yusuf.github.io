#!/usr/bin/env python3
"""Reconcile the browser dashboard to delivered data, then exercise its controls.

Requires openpyxl, Playwright and Chromium, like the existing model/browser checks.
An optional original CSV checks the additional category and monthly detail too.
"""
import argparse
from collections import defaultdict
import csv
from decimal import Decimal
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import shutil
from threading import Thread

from openpyxl import load_workbook
from playwright.sync_api import sync_playwright, expect
from bcc_source import literal_assignment

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT/'projects/01_BCC_Payments'
DASHBOARD = ROOT/'dashboards/birmingham-payments.html'


def pence(value):
    return int((Decimal(str(value))*100).quantize(Decimal(1)))


def check_data(source=None):
    html = DASHBOARD.read_text()
    data = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)[1])
    book = load_workbook(PROJECT/'power-bi/BCC_PowerBI_Starter.xlsx', data_only=True, read_only=True)
    sheets = {s.title: list(s.values)[1:] for s in book.worksheets}
    actual = defaultdict(lambda: [0, 0])
    for name, group, category, year, amount, count in data['sup']:
        actual[data['groups'][group], data['names'][name]][year] += pence(amount)
    expected = {(g, n): [pence(a), pence(b)] for g, n, a, b, _ in sheets['FactSupplierDrivers']}
    assert dict(actual) == expected, 'Supplier comparison differs from the complete workbook'
    assert len(actual) == 3947 and len(data['names']) == 3325
    monthly = defaultdict(lambda: [0, 0])
    for month, group, category, amount, count in data['monthly']:
        row = monthly[data['months'][month], data['groups'][group]]
        row[0] += pence(amount)
        row[1] += count
    assert dict(monthly) == {(day.strftime('%Y-%m'), g): [pence(v), n]
                             for day, g, v, n in sheets['FactMonthlySpend']}
    pairs = [[pid, name, data['groups'].index(group), cat, amount,
              first.strftime('%Y-%m-%d'), second.strftime('%Y-%m-%d'), gap]
             for pid, name, group, cat, amount, first, second, gap, _ in sheets['FactDuplicatePairs']]
    assert data['pairs'] == pairs, 'Review IDs, labels, dates or amounts differ'
    assert len(pairs) == 281 and sum(p[7] == 0 for p in pairs) == 73
    assert sum(pence(p[4]) for p in pairs) == 444851538
    assert sum(row[1] for row in monthly.values()) == data['meta']['rows'] == 247785
    assert sum(row[0] for row in monthly.values()) == pence(data['meta']['total']) == 387385201219
    assert sum(pence(r[4]) for r in data['sup'] if r[3] == 0) == 55863889264
    assert sum(pence(r[4]) for r in data['sup'] if r[3] == 1) == 67746111200
    if source:
        mapping = literal_assignment(PROJECT/'scripts/01_clean.py', 'dir_map')
        corporate = literal_assignment(PROJECT/'scripts/03_finance_pack.py', 'CORP')
        category_monthly, matched, agency = defaultdict(lambda: [0, 0]), defaultdict(int), defaultdict(int)
        credits = []
        with source.open(encoding='utf-8-sig', newline='') as stream:
            for row in csv.DictReader(stream, delimiter=';'):
                day = row['date']
                group = mapping[row['department']]
                group = data['groups'].index('Corporate services (combined)' if group in corporate else group)
                category = re.sub(r'\s+', ' ', row['merchant_category']).strip()
                index = data['cats'].index(category) if category in data['cats'] else len(data['cats'])-1
                value = pence(row['amount'])
                entry = category_monthly[data['months'].index(day[:7]), group, index]
                entry[0] += value
                entry[1] += 1
                if value < 0:
                    credits.append(value)
                for year_index, year in enumerate((2025, 2026)):
                    if f'{year}-04-01' <= day <= f'{year}-07-23':
                        matched[int(day[5:7])-4, group, index, year_index] += value
                        if category.startswith('Agency '):
                            agency[group, index, year_index] += value
        assert dict(category_monthly) == {(m, g, c): [pence(v), n] for m, g, c, v, n in data['monthly']}
        assert dict(matched) == {(m, g, c, y): pence(v) for m, g, c, y, v in data['mtd']}
        assert dict(agency) == {(g, c, y): pence(v) for g, c, y, v in data['agencyByCategory']}
        assert len(credits) == data['meta']['credits_n'] == 422
        assert sum(credits) == pence(data['meta']['credits_v'])
    book.close()
    return data


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def check_browser(data):
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    url = base+'/dashboards/birmingham-payments.html'
    errors = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
            page = browser.new_page(viewport={'width':1440, 'height':1000})
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('response', lambda r: errors.append(f'HTTP {r.status}: {r.url}') if r.status >= 400 else None)
            page.on('request', lambda r: errors.append(f'External dependency: {r.url}') if not r.url.startswith(base) else None)
            page.goto(base+'/index.html', wait_until='networkidle')
            page.get_by_role('link', name='Explore interactive dashboard', exact=False).click()
            page.wait_for_url(url+'*')
            expect(page.locator('#k-overview')).to_contain_text('£118.82m')
            expect(page.locator('#k-overview')).to_contain_text('+21.3%')
            # Tabs work with keyboard and keep only the selected panel exposed.
            page.locator('#tab-overview').focus()
            page.keyboard.press('ArrowRight')
            expect(page.locator('#tab-drivers')).to_be_focused()
            expect(page.locator('#supCount')).to_have_text('3,325 suppliers')
            page.locator('#fDept').select_option('0')
            expect(page.locator('#supCount')).to_have_text('738 suppliers')
            expect(page.locator('#k-drivers')).to_contain_text('+£75.62m')
            page.locator('#supSearch').fill('Birmingham Highways')
            expect(page.locator('#supCount')).to_have_text('1 supplier')
            expect(page.locator('#supTable')).to_contain_text('£66,950,365')
            page.locator('#reset').click()
            expect(page.locator('#supSearch')).to_have_value('')
            expect(page.locator('#supCount')).to_have_text('3,325 suppliers')
            page.locator('#supPager button').last.click()
            expect(page.locator('#supPager')).to_contain_text('Page 2 of')
            heading = page.locator('#supTable th').first
            heading.focus()
            page.keyboard.press('Space')
            expect(page.locator('#supTable th').first).to_be_focused()
            # Agency categories pooled outside the top 15 still have valid totals.
            page.locator('#fCat').select_option(str(len(data['cats'])-1))
            expect(page.locator('#k-drivers .kpi').last).not_to_contain_text('No agency payments')
            page.locator('#reset').click()
            share = page.locator('[data-chart=conc] .tablev tbody tr').evaluate_all(
                "rows=>rows.reduce((sum,r)=>sum+parseFloat(r.cells[2].textContent),0)")
            assert 0 < share <= 100
            # Payment review reconciles to the AP workbook, including filters.
            page.locator('#tab-review').click()
            expect(page.locator('#k-review .v').first).to_have_text('281')
            expect(page.locator('#k-review')).to_contain_text('£4.45m')
            page.locator('#fGap').select_option('0')
            expect(page.locator('#k-review .v').first).to_have_text('73')
            page.locator('#fMin').select_option('100000')
            expected = sum(p[7] == 0 and p[4] >= 100000 for p in data['pairs'])
            expect(page.locator('#k-review .v').first).to_have_text(str(expected))
            page.locator('#reset').click()
            page.locator('#pairSearch').fill('PAIR-001')
            expect(page.locator('#pairCount')).to_contain_text('1 pair ·')
            expect(page.locator('#pairTable')).to_contain_text('Veolia Es Birmingham Ltd')
            page.locator('#pairSearch').fill('no-such-supplier')
            expect(page.locator('#pairTable')).to_contain_text('Nothing matches')
            page.locator('#reset').click()
            expect(page.locator('#pairSearch')).to_have_value('')
            expect(page.locator('#pairCount')).to_contain_text('281 pairs')
            page.locator('#fCat').select_option('7')
            expect(page.locator('#k-review .v').first).to_have_text('0')
            assert page.locator('[data-chart=pdept] .extra').count() == 0
            page.locator('#reset').click()
            # Shared links restore filters; malformed values recover safely.
            page.goto(url+'#tab=review&dept=0&gap=0&min=100000')
            expect(page.locator('#fDept')).to_have_value('0')
            expect(page.locator('#k-review .v').first).to_have_text(str(sum(p[2] == 0 and p[7] == 0 and p[4] >= 100000 for p in data['pairs'])))
            page.goto(url+'#tab=bad&dept=NaN&cat=0.5&gap=bad&min=-20')
            expect(page.locator('#tab-overview')).to_have_attribute('aria-selected', 'true')
            expect(page.locator('#fDept')).to_have_value('-1')
            expect(page.locator('#fCat')).to_have_value('-1')
            # Every chart exposes its underlying HTML table at all target widths.
            for width in (1440, 768, 390, 320):
                page.set_viewport_size({'width':width, 'height':900})
                page.wait_for_timeout(180)
                for tab in ('overview', 'drivers', 'review', 'about'):
                    page.locator('#tab-'+tab).click()
                    assert page.locator('.page:visible').count() == 1
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, tab)
                    for button in page.locator('.page:visible .tbtn').all():
                        button.click()
                        expect(button).to_have_attribute('aria-pressed', 'true')
                        assert button.locator('xpath=ancestor::div[contains(@class,"card")]').locator('.tablev table').is_visible()
                        button.click()
            page.goto(base+'/case-studies/birmingham-payments.html')
            expect(page.locator('.finance-hero').get_by_role('link', name='Open interactive dashboard', exact=False)).to_have_attribute('href', '../dashboards/birmingham-payments.html')
            assert page.locator('#report .report-page').count() == 3
            assert not errors, errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-csv', type=Path)
    args = parser.parse_args()
    data = check_data(args.source_csv)
    check_browser(data)
    print('Passed: full supplier and monthly reconciliation, all 281 review records, filters, search, pagination, keyboard controls, chart tables and four viewport widths.')


if __name__ == '__main__':
    main()
