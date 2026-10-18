#!/usr/bin/env python3
"""Check NHS report evidence, model arithmetic and accessible reading interactions."""
from decimal import Decimal
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
from threading import Thread

from playwright.sync_api import sync_playwright
from nhs_story import evidence_data, d

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass


def serial(month):
    year,number = map(int,month.split('-'))
    return year*12+number-1


def model_from_history(history,horizon):
    """Recalculate the documented seasonal model without the original pandas pipeline."""
    by_month = {serial(r['month']):r for r in history}
    last = serial(history[-1]['month'])
    ratios = {}
    for field in ('clock_starts','clock_stops'):
        ratios[field] = sum(d(by_month[m][field]) for m in range(last-2,last+1))/sum(d(by_month[m-12][field]) for m in range(last-2,last+1))
    residual = sum(d(by_month[m]['waiting_list'])-d(by_month[m-1]['waiting_list'])-d(by_month[m]['clock_starts'])+d(by_month[m]['clock_stops']) for m in range(last-5,last+1))/6
    current,values = d(history[-1]['waiting_list']),[]
    for month in range(last+1,last+horizon+1):
        starts = d(by_month[month-12]['clock_starts'])*ratios['clock_starts']
        stops = d(by_month[month-12]['clock_stops'])*ratios['clock_stops']
        current += starts-stops+residual
        values.append(current)
    return values


def check_evidence():
    data = evidence_data()
    assert len(data['trend']) == len(data['months']) == 41
    assert data['trend'][0]['month']=='2023-04' and data['trend'][-1]['month']=='2026-08'
    assert sum(d(r['unknown_clock_start']) for r in data['trend'])==0
    assert len(data['specialties']) == 23
    assert sum(d(r['Waiting list']) for r in data['specialties']) == data['closing'] == 96303
    assert sum(d(r['52+ week waiters']) for r in data['specialties']) == 175
    assert data['opening'] == 89544 and data['starts'] == 133091 and data['stops'] == 104806
    assert data['residual'] == -21526
    assert data['opening']+data['starts']-data['stops']+data['residual']==data['closing']
    assert ((data['closing']/data['opening']-1)*100).quantize(Decimal('.1'))==Decimal('7.5')
    assert d(data['specialty']['Ear Nose and Throat Service']['52+ week waiters'])+d(data['specialty']['Ophthalmology Service']['52+ week waiters'])==110
    assert len(data['benchmark'])==8
    assert data['benchmark'][0]['Trust']=='University Hospitals Birmingham'
    assert sum(r['Trust']=='England' for r in data['benchmark'])==1
    assert len(data['backtest'])==6
    actual = [d(r['Actual']) for r in data['backtest']]
    predicted = model_from_history(data['trend'][:-6],6)
    for value,row in zip(predicted,data['backtest']):
        assert abs(value-d(row['Demand-capacity model']))<=Decimal('.5')
    for name,key in [('Demand-capacity','Demand-capacity model'),('Trend (6-month average change)','Trend model'),('No change (naive)','No change (naive)')]:
        error = sum(abs(d(r[key])-a)/a for r,a in zip(data['backtest'],actual))/6*100
        assert error.quantize(Decimal('.01')) == data['errors'][name]
    assert data['errors']['No change (naive)'] < data['errors']['Trend (6-month average change)'] < data['errors']['Demand-capacity']
    forecast = model_from_history(data['trend'],7)
    assert len(data['scenario'])==7
    for value,row in zip(forecast,data['scenario']):
        assert abs(value-d(row['Forecast waiting list']))<=Decimal('.5')
    assert data['scenario'][-1]['Forecast waiting list']=='107190'
    assert int(forecast[-1]) == int(data['figures']['forecast_list_mar27']) == 107189


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
            page.locator('a[href="case-studies/uhb-waiting-times.html"]').first.click()
            page.wait_for_url('**/case-studies/uhb-waiting-times.html')
            assert page.locator('h1').inner_text()=='Explaining waiting-list growth and targeting specialty reviews'
            assert 'simulated' in page.locator('.scenario-note').inner_text()
            assert page.locator('.requirements-card dt').all_text_contents()==['Business problem','Core questions','Business relevance','Defined scope']
            template = page.locator('.requirements-template')
            template.locator('summary').focus()
            page.keyboard.press('Enter')
            assert template.get_attribute('open') is not None
            assert template.locator('.framework-items > li').count()==7
            assert template.locator('.framework-status--pending').count()==4
            assert page.locator('#data table').first.locator('th').all_text_contents()==['Dataset','Data owner','Analytical purpose','Availability']
            assert page.locator('.chart-panel').count()==6
            assert page.locator('[data-viz="line"] .plot-dot').count()==82
            assert page.locator('[data-viz="waterfall"] .waterfall-bar').count()==5
            assert page.locator('[data-viz="comparison-lines"] polyline').count()==3
            for chart in page.locator('.chart-panel').all():
                assert chart.locator('table').count()==1
                chart.locator('summary').focus()
                page.keyboard.press('Enter')
                assert chart.locator('table').is_visible()
                assert chart.locator('caption').inner_text()==chart.locator('figcaption').inner_text()
            for details in page.locator('.evidence').all():
                if details.get_attribute('open') is None:
                    details.locator('summary').first.focus()
                    page.keyboard.press('Enter')
                assert details.get_attribute('open') is not None
            assert 'known_clock_start' in page.locator('#data pre').inner_text()
            assert 'does not enforce a row-level assertion' in page.locator('#data').inner_text()
            assert '21,526' in page.locator('#balance').inner_text()
            assert 'No-change baseline' in page.locator('#planning').inner_text()
            assert '107,190' in page.locator('#planning').inner_text()
            assert 'not a feasible capacity plan' in page.locator('#planning').inner_text()
            assert page.locator('#benchmark table tbody tr').count()==8
            assert page.locator('#specialties .evidence tbody tr').count()==23
            assert 'not unique patients' in page.locator('#data').inner_text()
            for link in page.locator('.finance-nav a').all():
                target = link.get_attribute('href')
                assert link.inner_text()[2:].strip()==page.locator(target+' h2').inner_text()
                link.click()
                page.wait_for_function("selector=>{const y=document.querySelector(selector+' h2').getBoundingClientRect().top;return y>=64 && y<=180}",arg=target)
            with page.expect_download() as download:
                page.get_by_role('link',name='Download the Excel performance report').click()
            assert download.value.suggested_filename=='UHB_RTT_Performance_Report.xlsx'
            for width in (1440,1024,768,390,320):
                page.set_viewport_size({'width':width,'height':900})
                for identifier in ('brief','data','recovery','balance','specialties','benchmark','planning','actions','files'):
                    page.locator('#'+identifier).scroll_into_view_if_needed()
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,identifier)
            page.get_by_role('button',name='Dark mode',exact=True).click()
            assert page.locator('html').get_attribute('data-theme')=='dark'
            page.close()
            for options in ({'java_script_enabled':False},{'reduced_motion':'reduce'}):
                context = browser.new_context(viewport={'width':390,'height':844},**options)
                tab = context.new_page()
                tab.goto(base+'case-studies/uhb-waiting-times.html',wait_until='networkidle')
                tab.locator('.requirements-template summary').click()
                assert tab.locator('.framework-items').is_visible()
                tab.locator('#planning .evidence summary').click()
                assert tab.locator('#planning pre').is_visible()
                assert tab.locator('.finance-section').count()==9
                assert tab.evaluate('document.documentElement.scrollWidth<=innerWidth')
                context.close()
            browser.close()
            assert not errors,errors
    finally:
        server.shutdown()
        server.server_close()
    print('Passed: pathway/specialty totals, residual, independent back-test and scenario calculations; six chart tables; tailored requirements; keyboard evidence and matching navigation; workbook download; five widths; dark/no-JS/reduced-motion layouts; no overflow or request/script errors.')


if __name__=='__main__':
    main()
