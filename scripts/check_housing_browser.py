#!/usr/bin/env python3
"""Verify housing evidence and the reader's path from findings to supporting files."""
from decimal import Decimal
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
from threading import Thread

from playwright.sync_api import sync_playwright
from housing_story import evidence_data, CURRENT, PREVIOUS, MEDIAN, GAP

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def check_evidence():
    data = evidence_data()
    satisfaction = data['satisfaction']
    assert len(satisfaction) == 12
    assert all(r['Large HAs compared'] == '17' for r in satisfaction)
    assert sum(r['Quartile vs large HAs'] == 'Bottom' for r in satisfaction) == 6
    overall = data['measures']['TP01']
    assert round(float(overall[CURRENT]),1) == round(float(overall[MEDIAN]),1) == 64.6
    for row in satisfaction:
        assert abs(Decimal(row[CURRENT])-Decimal(row[MEDIAN])-Decimal(row[GAP])) < Decimal('0.000001')
    assert Decimal(data['repair'][PREVIOUS])-Decimal(data['repair'][CURRENT]) == Decimal('29.4')
    assert data['repair_counts'] == [90250,13872]
    assert round((1-13872/90250)*100) == 85
    assert len(data['peers']) == 21 and data['peer_median'] == Decimal('56.5')
    platform = data['platform']
    assert sum(int(r['Platform findings']) for r in data['categories']) == int(platform['findings']) == 137
    assert sum(int(r['Platform upheld']) for r in data['categories']) == int(platform['mal_findings']) == 51
    assert (Decimal(51)/137*100).quantize(Decimal('.1')) == Decimal('37.2')
    assert Decimal(platform['mal_rate_2025_26']) == 38  # Deliberately not reconciled.
    repairs = next(r for r in data['categories'] if r['category']=='Responsive repairs/activity')
    assert [int(repairs[k]) for k in ('Platform findings','Platform upheld')] == [43,23]
    assert sum(r['Priority']=='Improve' for r in data['drivers']) == 5
    assert all(Decimal(r['Correlation with overall satisfaction'])>=Decimal('.8') for r in data['drivers'] if r['Priority']=='Improve')


def main():
    check_evidence()
    server = ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}/'
    errors = []
    try:
        with sync_playwright() as p:
            executable = shutil.which('chromium') or shutil.which('chromium-browser')
            browser = p.chromium.launch(**({'executable_path':executable} if executable else {}),args=['--no-sandbox'])
            page = browser.new_page(viewport={'width':1440,'height':1000})
            page.on('pageerror',lambda error: errors.append(str(error)))
            page.on('response',lambda r: errors.append(f'HTTP {r.status}: {r.url}') if r.status>=400 else None)
            page.goto(base,wait_until='networkidle')
            page.locator('a[href="case-studies/platform-housing.html"]').first.click()
            page.wait_for_url('**/case-studies/platform-housing.html')
            assert page.locator('h1').inner_text() == 'Finding the service gaps behind tenant satisfaction'
            assert 'simulated' in page.locator('.scenario-note').inner_text()
            assert page.locator('.requirements-card dt').all_text_contents() == ['Business problem','Core questions','Business relevance','Defined scope']
            template = page.locator('.requirements-template')
            template.locator('summary').focus()
            page.keyboard.press('Enter')
            assert template.get_attribute('open') is not None
            assert template.locator('.framework-items > li').count() == 7
            assert template.locator('.framework-status--pending').count() == 4
            assert '28-day' in template.inner_text()
            assert page.locator('#data th').all_text_contents() == ['Dataset','Data owner','Analytical purpose','Availability']
            assert page.locator('#data tbody tr').first.locator('td').all_text_contents()[:2] == ['Tenant survey responses','Customer insight']
            assert page.locator('.chart-panel').count() == 5
            for chart in page.locator('.chart-panel').all():
                assert chart.locator('table').count() == 1
                chart.locator('summary').focus()
                page.keyboard.press('Enter')
                assert chart.locator('table').is_visible()
                assert chart.locator('caption').inner_text() == chart.locator('figcaption').inner_text()
            for details in page.locator('.evidence').all():
                if details.get_attribute('open') is None:
                    details.locator('summary').first.focus()
                    page.keyboard.press('Enter')
                assert details.get_attribute('open') is not None
            assert page.locator('#gaps tbody tr').count() == 12
            assert page.locator('#priorities .evidence tbody tr').count() == 11
            assert '37.2%' in page.locator('#complaints').inner_text()
            assert '51 / 137' in page.locator('#complaints').inner_text()
            assert '23 of the 43 repairs findings' in page.locator('#complaints').inner_text()
            assert 'not restricted to telephone surveys' in page.locator('#comparison').inner_text()
            assert 'does not prove a recording error' in page.locator('#validation').inner_text()
            assert 'not an automatic or cost-optimised ranking' in page.locator('#priorities').inner_text()
            for link in page.locator('.finance-nav a').all():
                target = link.get_attribute('href')
                assert link.inner_text()[2:].strip() == page.locator(target+' h2').inner_text()
                link.click()
                page.wait_for_function("selector=>{const y=document.querySelector(selector+' h2').getBoundingClientRect().top;return y>=64 && y<=180}",arg=target)
            with page.expect_download() as download:
                page.get_by_role('link',name='Download the Excel benchmark pack').click()
            assert download.value.suggested_filename == 'Platform_TSM_Benchmarking_Pack.xlsx'
            for width in (1440,1024,768,390,320):
                page.set_viewport_size({'width':width,'height':900})
                for identifier in ('brief','data','comparison','gaps','priorities','validation','complaints','actions','files'):
                    page.locator('#'+identifier).scroll_into_view_if_needed()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,identifier)
                if width<=390:
                    assert page.locator('.finance-bar-label').first.evaluate('el=>parseFloat(getComputedStyle(el).fontSize)')>=12
                    assert page.locator('#data .table-scroll').evaluate('el=>el.scrollWidth>el.clientWidth')
            page.get_by_role('button',name='Dark mode',exact=True).click()
            assert page.locator('html').get_attribute('data-theme') == 'dark'
            page.close()
            for options in ({'java_script_enabled':False},{'reduced_motion':'reduce'}):
                context = browser.new_context(viewport={'width':390,'height':844},**options)
                tab = context.new_page()
                tab.goto(base+'case-studies/platform-housing.html',wait_until='networkidle')
                tab.locator('.requirements-template summary').click()
                assert tab.locator('.framework-items').is_visible()
                tab.locator('#complaints .evidence summary').click()
                assert tab.locator('#complaints pre').is_visible()
                assert tab.locator('.finance-section').count() == 9
                assert tab.evaluate('document.documentElement.scrollWidth<=innerWidth')
                context.close()
            browser.close()
            assert not errors,errors
    finally:
        server.shutdown()
        server.server_close()
    print('Passed: workbook arithmetic, cohorts, screening flags, repair counts and explicit rate discrepancy; homepage entry; tailored requirements; five chart tables; keyboard evidence; matching navigation; workbook download; five widths; mobile legibility; dark/no-JS/reduced-motion layouts; no overflow or request/script errors.')


if __name__ == '__main__':
    main()
