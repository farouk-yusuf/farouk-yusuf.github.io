#!/usr/bin/env python3
"""Check the finance story's evidence, chart arithmetic and reading interactions."""
from decimal import Decimal
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
from threading import Thread

from playwright.sync_api import sync_playwright
from birmingham_story import evidence_data, workbook_rows

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def check_evidence():
    data = evidence_data()
    figures = data['figures']
    pairs = workbook_rows('Possible duplicates')
    assert data['initial_pairs'] == 6553
    assert len(pairs) == int(figures['dup_pairs']) == 281
    assert sum(row['days_apart'] == '0' for row in pairs) == int(figures['dup_same_day']) == 73
    candidate_value = sum(Decimal(row['amount']) for row in pairs)
    assert (candidate_value/1000000).quantize(Decimal('.01')) == Decimal(figures['dup_value_m']) == Decimal('4.45')
    assert all(Decimal(row['days_apart']) <= 3 and Decimal(row['amount']) >= 1000 for row in pairs)
    change = data['totals'][1]-data['totals'][0]
    assert change == Decimal('118.82')
    assert abs(sum(value for _, value in data['groups'])-change) < Decimal('.01')
    assert (change/data['totals'][0]*100).quantize(Decimal('.1')) == Decimal(figures['ytd_change_pct']) == Decimal('21.3')
    assert len(data['mapping']) == 18 and len(set(data['mapping'].values())) == 9
    assert data['mapping']['Adults Social Care Directorate'] == data['mapping']['Adult Social Care & Health Directorate'] == 'Adult Social Care & Health'
    assert data['mapping']['Council Managament'] == 'Council Management'


def main():
    check_evidence()
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}/'
    errors = []
    try:
        with sync_playwright() as p:
            executable = shutil.which('chromium') or shutil.which('chromium-browser')
            browser = p.chromium.launch(**({'executable_path':executable} if executable else {}), args=['--no-sandbox'])
            page = browser.new_page(viewport={'width':1440,'height':1000})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('response', lambda response: errors.append(f'HTTP {response.status}: {response.url}') if response.status >= 400 else None)
            page.goto(base, wait_until='networkidle')
            page.locator('.project-highlight').first.locator('h3 a').click()
            page.wait_for_url('**/case-studies/birmingham-payments.html')
            assert page.locator('h1').inner_text() == 'Explaining expenses and flagging payments for review'
            assert 'simulated' in page.locator('.scenario-note').inner_text()
            assert page.locator('.question-card dt').all_text_contents() == ['I considered','Why it mattered','I clarified']
            assert page.locator('.etl-flow strong').all_text_contents() == ['Extract','Transform','Load','Report']
            assert page.locator('.chart-panel').count() == 3
            for chart in page.locator('.chart-panel').all():
                assert chart.locator('table').count() == 1
                summary = chart.locator('summary')
                summary.focus()
                page.keyboard.press('Enter')
                assert chart.locator('table').is_visible()
                assert chart.locator('figcaption').inner_text() == chart.locator('caption').inner_text()
            for proof in page.locator('.evidence').all():
                summary = proof.locator('summary').first
                summary.focus()
                page.keyboard.press('Enter')
                assert proof.get_attribute('open') is not None
            assert 'assert len(df) == n0' in page.locator('#comparison pre').first.inner_text() or 'assert len(df) == n0' in page.locator('#comparison pre').last.inner_text()
            assert 'transform("size") == 2' in page.locator('#duplicates pre').inner_text()
            assert 'the sum of both payments or a confirmed loss' in page.locator('#duplicates').inner_text()
            assert page.locator('#comparison tbody tr').count() == 5
            for link in page.locator('.finance-nav a').all():
                target = link.get_attribute('href')
                assert link.inner_text()[2:].strip() == page.locator(target+' h2').inner_text()
                link.click()
                page.wait_for_function("selector=>{const y=document.querySelector(selector+' h2').getBoundingClientRect().top;return y>=64 && y<=180}", arg=target)
                box = page.locator(target+' h2').bounding_box()
                assert 64 <= box['y'] <= 240, (target,box)
            with page.expect_download() as download:
                page.get_by_role('link',name='Download the Excel finance pack').click()
            assert download.value.suggested_filename == 'BCC_Spend_and_Payment_Controls_Pack.xlsx'
            for width in (1440,1024,768,390,320):
                page.set_viewport_size({'width':width,'height':900})
                for identifier in ('brief','data','comparison','spending','duplicates','actions','files'):
                    page.locator('#'+identifier).scroll_into_view_if_needed()
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width,identifier)
                # Charts stay legible at phone widths; only wide evidence tables scroll.
                if width <= 390:
                    assert page.locator('.finance-bar-label').first.evaluate('(el)=>parseFloat(getComputedStyle(el).fontSize)') >= 12
                    assert page.locator('#data .table-scroll').evaluate('(el)=>el.scrollWidth>el.clientWidth')
                    assert page.locator('#comparison .table-scroll').evaluate('(el)=>el.scrollWidth<=el.clientWidth')
            page.get_by_role('button',name='Dark mode',exact=True).click()
            assert page.locator('html').get_attribute('data-theme') == 'dark'
            page.close()
            for options in ({'java_script_enabled':False}, {'reduced_motion':'reduce'}):
                context = browser.new_context(viewport={'width':390,'height':844}, **options)
                tab = context.new_page()
                tab.goto(base+'case-studies/birmingham-payments.html',wait_until='networkidle')
                tab.locator('#duplicates .evidence summary').click()
                assert tab.locator('#duplicates pre').is_visible()
                assert tab.locator('.finance-section').count() == 9
                assert tab.evaluate('document.documentElement.scrollWidth<=innerWidth')
                context.close()
            browser.close()
            assert not errors, errors
    finally:
        server.shutdown()
        server.server_close()
    print('Passed: workbook/CSV arithmetic; exact department mappings; headline-to-chart reconciliation; homepage entry; scenario label; matching navigation; keyboard evidence and chart tables; workbook download; five viewport sizes; readable mobile charts; dark/no-JS/reduced-motion layouts; no overflow or request/script errors.')


if __name__ == '__main__':
    main()
