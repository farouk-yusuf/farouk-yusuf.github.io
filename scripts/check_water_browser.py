#!/usr/bin/env python3
"""Check spill-analysis arithmetic, distinct screening populations and reading access."""
from collections import Counter
from decimal import Decimal
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
from threading import Thread

from playwright.sync_api import sync_playwright
from water_story import evidence_data

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass


def check_evidence():
    data = evidence_data()
    years, figures = data['years'], data['figures']
    for year in ('2024','2025'):
        assert Decimal(years[year]['total_spills']) == Decimal(data['kpis']['Total spills'][year])
        assert Decimal(years[year]['midlands_rain_mm']) == Decimal(data['kpis']['Midlands rainfall (mm)'][year])
    assert sum(Decimal(r['Spills 2025']) for r in data['basins']) == 36471
    assert sum(Decimal(r['Spills 2025']) for r in data['assets']) == 36471
    assert Counter(r['Status'] for r in data['qa']) == {'Info':1,'Pass':5,'Review':5}
    assert len(data['maintenance']) == 87
    assert all(Decimal(r['edm_op_pct'])<90 and not r['low_op_reason'].startswith('No longer operational') for r in data['maintenance'])
    assert sum(r['Repeat (<90% in 2024 too)']=='1' for r in data['maintenance']) == 27
    assert all((r['Repeat (<90% in 2024 too)']=='1') == (Decimal(r['op_2024'])<90 if r['op_2024'] else False) for r in data['maintenance'])
    assert len(data['high']) == sum(int(r['Overflows 60+ spills 2025']) for r in data['basins']) == 76
    assert all(Decimal(r['spills_2025'])>=60 for r in data['high'])
    assert sum(r['No improvement action 2025']=='1' for r in data['high']) == 13
    assert all((r['No improvement action 2025']=='1') == r['improvement_activity'].startswith('No improvement') for r in data['high'])
    assert len(data['persistent']) == 74
    assert sum(r['improvement_2025'].startswith('No improvement') for r in data['persistent']) == 17
    assert sum(Decimal(r['spills_2025'])<60 for r in data['persistent']) == 36
    assert sum(Decimal(r['spills_2025']) for r in data['persistent']) == 4895
    assert (Decimal(4895)/36471*100).quantize(Decimal('.1')) == Decimal('13.4')
    assert len(data['not_improving']) == 65
    # Independently refit the exploratory model using the five committed annual rows.
    training = [r for r in data['yearly'] if int(r['year'])<=2024]
    xs = [float(r['midlands_rain_mm']) for r in training]
    ys = [float(r['avg_spills_reliable']) for r in training]
    xbar,ybar = sum(xs)/len(xs),sum(ys)/len(ys)
    slope = sum((x-xbar)*(y-ybar) for x,y in zip(xs,ys))/sum((x-xbar)**2 for x in xs)
    intercept = ybar-slope*xbar
    assert abs(slope*100-float(figures['slope_spills_per_100mm']))<1e-9
    assert abs(intercept-float(figures['intercept']))<1e-9
    expected = intercept+slope*float(years['2025']['midlands_rain_mm'])
    assert abs(expected-float(figures['expected_2025']))<1e-9
    for row in data['persistent']:
        for year in ('2023','2024','2025'):
            adjusted = float(row['spills_'+year])*(intercept+slope*1000)/(intercept+slope*float(years[year]['midlands_rain_mm']))
            assert abs(adjusted-float(row['adj_'+year]))<=0.051
            assert adjusted>=60
    for row in data['not_improving']:
        earlier = (float(row['adj_2023'])+float(row['adj_2024']))/2
        assert earlier>=29.95 and float(row['adj_2025'])>=earlier-0.1


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
            page.on('pageerror',lambda err:errors.append(str(err)))
            page.on('response',lambda r:errors.append(f'HTTP {r.status}: {r.url}') if r.status>=400 else None)
            page.goto(base,wait_until='networkidle')
            page.locator('a[href="case-studies/severn-trent.html"]').first.click()
            page.wait_for_url('**/case-studies/severn-trent.html')
            assert page.locator('h1').inner_text() == 'Checking spill reductions and prioritising overflow investigations'
            assert 'simulated' in page.locator('.scenario-note').inner_text()
            assert page.locator('.requirements-card dt').all_text_contents() == ['Business problem','Core questions','Business relevance','Defined scope']
            template = page.locator('.requirements-template')
            template.locator('summary').focus()
            page.keyboard.press('Enter')
            assert template.get_attribute('open') is not None
            assert template.locator('.framework-items > li').count() == 7
            assert template.locator('.framework-status--pending').count() == 3
            assert 'service-level agreements (SLAs)' in template.inner_text()
            assert page.locator('#data table').first.locator('th').all_text_contents() == ['Dataset','Data owner','Analytical purpose','Availability']
            assert page.locator('.chart-panel').count() == 6
            assert page.locator('#annual [data-viz="line"]').count() == 2
            assert page.locator('#annual [data-viz="line"] .plot-dot').count() == 12
            assert page.locator('#rainfall [data-viz="scatter"] .plot-dot').count() == 6
            assert page.locator('#rainfall [data-viz="paired-dot"]').count() == 1
            assert page.locator('#operations > .table-scroll tbody tr').count() == 3
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
            assert 'def to_hours(v)' in page.locator('#data pre').first.inner_text()
            assert 'No longer operational' in page.locator('#maintenance pre').inner_text()
            assert '13.4%' in page.locator('#persistent').inner_text()
            assert '18.9%' in page.locator('#persistent').inner_text()
            assert 'not observed annual spill counts' in page.locator('#persistent').inner_text()
            assert 'not causal attribution' in page.locator('#rainfall').inner_text()
            assert '1,737' in page.locator('#rainfall').inner_text() and '2,342' in page.locator('#rainfall').inner_text()
            assert 'SVT00656' in page.locator('#maintenance').inner_text()
            assert 'SVT00291' in page.locator('#operations').inner_text()
            for link in page.locator('.finance-nav a').all():
                target = link.get_attribute('href')
                assert link.inner_text()[2:].strip() == page.locator(target+' h2').inner_text()
                link.click()
                page.wait_for_function("selector=>{const y=document.querySelector(selector+' h2').getBoundingClientRect().top;return y>=64 && y<=180}",arg=target)
            for name,filename in [('Download the Excel performance pack','Severn_Trent_Overflow_Performance_Pack_2025.xlsx'),('Persistent high-spill investigation list','priority_overflows_persistent_high.csv'),('Sites flagged as not improving by the model','overflows_not_improving_2025.csv')]:
                with page.expect_download() as download:
                    page.get_by_role('link',name=name).click()
                assert download.value.suggested_filename == filename
            for width in (1440,1024,768,390,320):
                page.set_viewport_size({'width':width,'height':900})
                for identifier in ('brief','data','annual','rainfall','maintenance','operations','persistent','actions','files'):
                    page.locator('#'+identifier).scroll_into_view_if_needed()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,identifier)
                if width<=390:
                    assert page.locator('.finance-bar-label').first.evaluate('el=>parseFloat(getComputedStyle(el).fontSize)')>=12
                    assert page.locator('#data .table-scroll').first.evaluate('el=>el.scrollWidth>el.clientWidth')
            page.get_by_role('button',name='Dark mode',exact=True).click()
            assert page.locator('html').get_attribute('data-theme') == 'dark'
            page.close()
            for options in ({'java_script_enabled':False},{'reduced_motion':'reduce'}):
                context = browser.new_context(viewport={'width':390,'height':844},**options)
                tab = context.new_page()
                tab.goto(base+'case-studies/severn-trent.html',wait_until='networkidle')
                tab.locator('.requirements-template summary').click()
                assert tab.locator('.framework-items').is_visible()
                tab.locator('#maintenance .evidence summary').click()
                assert tab.locator('#maintenance pre').is_visible()
                assert tab.locator('.finance-section').count() == 9
                assert tab.evaluate('document.documentElement.scrollWidth<=innerWidth')
                context.close()
            browser.close()
            assert not errors,errors
    finally:
        server.shutdown()
        server.server_close()
    print('Passed: annual totals, distinct exception populations, maintenance filters, independent rainfall-model arithmetic and adjusted CSVs; six chart tables; tailored requirements; keyboard evidence; matching navigation; three downloads; five widths; dark/no-JS/reduced-motion layouts; no overflow or request/script errors.')


if __name__ == '__main__':
    main()
