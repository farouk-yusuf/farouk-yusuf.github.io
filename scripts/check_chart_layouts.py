#!/usr/bin/env python3
"""Check plotted coordinates against evidence and readable responsive chart labels."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
from threading import Thread

from playwright.sync_api import sync_playwright
from birmingham_story import evidence_data as finance_data
from housing_story import evidence_data as housing_data, GAP, MEDIAN, CURRENT, PREVIOUS
from water_story import evidence_data as water_data

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):
        pass


def close(actual,expected):
    assert abs(float(actual)-float(expected))<0.0002,(actual,expected)


def check_series(plot,values,minimum,maximum):
    points = plot.locator('.plot-dot')
    assert points.count() == len(values)
    geometry = plot.locator('polyline').get_attribute('points').split()
    for i,(point,value,coordinate) in enumerate(zip(points.all(),values,geometry)):
        x,y = map(float,coordinate.split(','))
        expected_x = i/(len(values)-1)*100
        expected_y = (float(value)-minimum)/(maximum-minimum)*100
        close(point.get_attribute('data-value'),value)
        close(point.evaluate('el=>parseFloat(el.style.left)'),expected_x)
        close(point.evaluate('el=>parseFloat(el.style.bottom)'),expected_y)
        close(x,expected_x)
        close(y,100-expected_y)


def main():
    finance,housing,water = finance_data(),housing_data(),water_data()
    server = ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}/case-studies/'
    try:
        with sync_playwright() as p:
            executable = shutil.which('chromium') or shutil.which('chromium-browser')
            browser = p.chromium.launch(**({'executable_path':executable} if executable else {}),args=['--no-sandbox'])
            page = browser.new_page()
            page.goto(base+'birmingham-payments.html',wait_until='networkidle')
            check_series(page.locator('[data-viz="line"]'),[r['Total'] for r in finance['monthly']],0,240)
            page.goto(base+'platform-housing.html',wait_until='networkidle')
            check_series(page.locator('[data-viz="slope"]'),[housing['repair'][PREVIOUS],housing['repair'][CURRENT]],0,100)
            rows = sorted(housing['satisfaction'],key=lambda r:float(r[GAP]))
            for pair,row in zip(page.locator('#gaps .pair-row').all(),rows):
                for selector,key in [('.pair-dot--open',MEDIAN),('.pair-dot:not(.pair-dot--open)',CURRENT)]:
                    point = pair.locator(selector)
                    close(point.get_attribute('data-value'),row[key])
                    close(point.evaluate('el=>parseFloat(el.style.left)'),row[key])
            page.goto(base+'severn-trent.html',wait_until='networkidle')
            for index,key,maximum in [(0,'total_spills',70000),(1,'midlands_rain_mm',1200)]:
                check_series(page.locator('#annual [data-viz="line"]').nth(index),[r[key] for r in water['yearly']],0,maximum)
            scatter = page.locator('[data-viz="scatter"]')
            for point,row in zip(scatter.locator('.plot-dot').all(),water['yearly']):
                close(point.get_attribute('data-x'),row['midlands_rain_mm'])
                close(point.get_attribute('data-value'),row['avg_spills_reliable'])
                close(point.evaluate('el=>parseFloat(el.style.left)'),(float(row['midlands_rain_mm'])-650)/450*100)
                close(point.evaluate('el=>parseFloat(el.style.bottom)'),(float(row['avg_spills_reliable'])-10)/20*100)
            for slug in ('birmingham-payments','platform-housing','severn-trent'):
                page.goto(base+slug+'.html',wait_until='networkidle')
                for width in (1440,768,390,320):
                    page.set_viewport_size({'width':width,'height':900})
                    for chart in page.locator('.chart-panel').all():
                        chart.scroll_into_view_if_needed()
                        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(slug,width)
                        box = chart.bounding_box()
                        for label in chart.locator('.plot-x-labels > span:visible,.scatter-label,.pair-heading strong,.plot-y-labels span').all():
                            rect = label.bounding_box()
                            assert rect['x']>=box['x']-1 and rect['x']+rect['width']<=box['x']+box['width']+1,(slug,width,label.inner_text())
                            assert label.evaluate('el=>parseFloat(getComputedStyle(el).fontSize)')>=12
                        ticks = [el.bounding_box() for el in chart.locator('.plot-x-labels > span:visible').all()]
                        assert all(a['x']+a['width']<=b['x']+1 for a,b in zip(ticks,ticks[1:])),(slug,width,'x-axis label collision')
                        years = [el.bounding_box() for el in chart.locator('.scatter-label').all()]
                        for i,a in enumerate(years):
                            for b in years[i+1:]:
                                assert a['x']+a['width']<=b['x'] or b['x']+b['width']<=a['x'] or a['y']+a['height']<=b['y'] or b['y']+b['height']<=a['y'],(width,'scatter year collision')
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print('Passed: line/slope geometry and benchmark/scatter positions agree with workbook/CSV values; labels stay readable, within the figures and collision-free at four widths across three projects.')


if __name__ == '__main__':
    main()
