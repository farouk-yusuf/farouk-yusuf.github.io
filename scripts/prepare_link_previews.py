#!/usr/bin/env python3
"""Render LinkedIn covers from real project screenshots and supplied logos.

Requires Playwright and Chromium. The image composition is an HTML layout;
screenshots retain the actual charts, labels and figures from the portfolio.
No generated illustrations or fabricated dashboard graphics are used.
"""
from functools import partial
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assets/social'


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def layout(body):
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><style>
@font-face{font-family:DM;src:url(/assets/fonts/dm-sans-latin.woff2)}
@font-face{font-family:Manrope;src:url(/assets/fonts/manrope-latin.woff2)}
*{box-sizing:border-box}html,body{margin:0;width:1200px;height:627px;overflow:hidden}
body{background:#f4f6f2;color:#1b302b;font-family:DM,Arial,sans-serif}
.cover{height:627px;padding:32px 40px 24px 44px;border-left:8px solid #21664f;display:flex;flex-direction:column}
.top{display:flex;justify-content:space-between;align-items:center;height:48px;flex-shrink:0;font-size:18px}
.brand{font-weight:700;letter-spacing:.2px}.domain{color:#53665b;font-size:15px}
.content{display:grid;grid-template-columns:350px 1fr;gap:28px;align-items:center;flex:1;min-height:0}
.portfolio .content{grid-template-columns:330px 1fr;gap:28px}
.eyebrow{color:#21664f;font-size:15px;letter-spacing:1.2px;font-weight:700;margin-bottom:14px}
h1{font-family:Manrope,Arial,sans-serif;font-size:48px;line-height:1.12;letter-spacing:-1.8px;margin:0 0 20px;font-weight:750}
.portfolio h1{font-size:55px}
.lead{font-size:20px;line-height:1.5;color:#46574f;margin:0 0 20px}
.toolset{display:grid;grid-template-columns:1fr 1fr;gap:14px 10px;margin-top:24px}
.tool{display:flex;align-items:center;gap:9px;font-size:17px;font-weight:600}
.tool img{height:25px;width:25px;object-fit:contain}
.footer{display:flex;align-items:center;justify-content:space-between;flex-shrink:0;font-size:15px;padding-top:17px;border-top:1px solid #d6dfd8;color:#53665b}
.footer b{color:#21664f;font-weight:650}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.tile{height:208px;border:1px solid #d6dfd8;border-radius:8px;background:white;overflow:hidden}
.tile-top{height:68px;padding:10px 13px;display:flex;align-items:center;gap:12px;border-bottom:1px solid #e7ece8}
.tile-top img{width:112px;height:44px;object-fit:contain;flex-shrink:0}
.tile-top img.nhs-mark{object-fit:cover}
.tile-top span{font-size:15px;line-height:1.2;font-weight:600}
.tile-shot{width:100%;height:136px;object-fit:cover;object-position:top;display:block}
.screen{border:1px solid #ccd8cf;border-radius:9px;overflow:hidden;background:white;box-shadow:0 8px 24px #1b302b0c;max-height:442px}
.screen-label{height:32px;background:#edf2ee;border-bottom:1px solid #d9e2dc;font-size:12px;color:#53665b;padding:8px 12px}
.screen>img{display:block;width:100%;height:auto;max-height:408px;object-fit:contain}
.logo-row{display:flex;flex-direction:column;align-items:flex-start;gap:8px;margin-bottom:16px;font-size:15px;font-weight:650}
.logo-row img{width:164px;height:68px;object-fit:contain;object-position:left center}
.nhs .logo-row img{width:150px;height:58px;object-fit:cover;object-position:center}
.compact h1{font-size:42px}
</style></head><body>'''+body+'</body></html>'


def tools(names):
    return '<div class="toolset">'+''.join(f'<span class="tool"><img src="/assets/icons/{icon}.svg" alt="">{label}</span>' for label,icon in names)+'</div>'


def cover(variant, content, footer):
    return f'<main class="cover {variant}"><header class="top"><span class="brand">Farouk Yusuf</span><span class="domain">farouk-yusuf.github.io</span></header><div class="content">{content}</div><footer class="footer"><span>Independent analysis of public data</span><b>{footer}</b></footer></main>'


def main():
    OUT.mkdir(exist_ok=True)
    evidence = OUT/'evidence'
    evidence.mkdir(exist_ok=True)
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    errors = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=shutil.which('chromium'), args=['--no-sandbox'])
            page = browser.new_page(viewport={'width':1200,'height':1000}, device_scale_factor=1, color_scheme='light')
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('response', lambda r: errors.append(f'HTTP {r.status}: {r.url}') if r.status >= 400 else None)
            projects = [('birmingham-payments','bcc.png','Council payments'),('platform-housing','platform.png','Housing performance'),('severn-trent','severn-trent.png','Storm overflows'),('uhb-waiting-times','nhs.svg','NHS waiting times')]
            for slug,_,_ in projects:
                page.goto(base+'/case-studies/'+slug+'.html', wait_until='networkidle')
                page.evaluate('document.fonts.ready')
                chart_index = {'birmingham-payments':2,'platform-housing':1}.get(slug,0)
                figure = page.locator('.chart-panel').nth(chart_index)
                figure.scroll_into_view_if_needed()
                figure.screenshot(path=str(evidence/(slug+'.png')), animations='disabled', style='.site-header{visibility:hidden!important}')
                if slug == 'platform-housing':
                    page.locator('.chart-panel').first.screenshot(path=str(evidence/'platform-overall.png'), animations='disabled', style='.site-header{visibility:hidden!important}')
            page.set_viewport_size({'width':1440,'height':1010})
            page.goto(base+'/dashboards/birmingham-payments.html', wait_until='networkidle')
            page.evaluate('document.fonts.ready')
            page.wait_for_timeout(200)
            # Start at the real dashboard header; omit the separate portfolio nav.
            top = page.locator('.top').bounding_box()
            bottom = page.locator('[data-chart=months]').bounding_box()['y']
            page.screenshot(path=str(evidence/'interactive-dashboard.png'), clip={'x':24,'y':top['y'],'width':1392,'height':bottom-top['y']-12}, animations='disabled')
            page.set_viewport_size({'width':1200,'height':627})
            tiles = ''.join(f'<article class="tile"><div class="tile-top"><img class="{"nhs-mark" if logo=="nhs.svg" else ""}" src="/assets/logos/{logo}" alt=""><span>{escape(label)}</span></div><img class="tile-shot" src="/assets/social/evidence/{slug}.png" alt="Actual project chart"></article>' for slug,logo,label in projects)
            portfolio = cover('portfolio', '<div><div class="eyebrow">DATA ANALYST</div><h1>Data analysis<br>portfolio</h1><p class="lead">Four UK projects.<br>Explore the analysis<br>and supporting work.</p>'+tools([('SQL','sql'),('Python','python'),('Excel','excel'),('Power BI','power-bi')])+'</div><div class="grid">'+tiles+'</div>', 'SQL · Python · Excel · Power BI')
            views = [('portfolio',portfolio)]
            entries = [
                ('birmingham-dashboard','INTERACTIVE DASHBOARD','Spending,<br>suppliers &amp;<br>payment checks','Filter the data.<br>Explore the full supplier list.','bcc.png','Birmingham City Council','/assets/social/evidence/interactive-dashboard.png','Birmingham payments · Spending overview','Explore the dashboard'),
                ('birmingham-power-bi','POWER BI REPORT','Council spending<br>&amp; payment<br>controls','Trends, supplier movements<br>and potential duplicates.','bcc.png','Birmingham City Council','/assets/bcc-dashboard.png','Power BI · Spending overview','View the three-page report'),
                ('nhs-waiting-times','PERFORMANCE ANALYSIS','NHS waiting<br>times &amp;<br>forecasting','41 monthly datasets.<br>23 specialties.','nhs.svg','University Hospitals Birmingham','/assets/social/evidence/uhb-waiting-times.png','18-week performance · April 2023–August 2026','Read the analysis'),
                ('platform-housing','HOUSING PERFORMANCE','Tenant<br>satisfaction<br>benchmarking','12 measures.<br>17 housing associations.','platform.png','Platform Housing Group','/assets/social/evidence/platform-overall.png','Overall tenant satisfaction · Platform and peer median','Explore the benchmarking'),
                ('severn-trent','WATER SECTOR ANALYSIS','Storm overflow<br>performance<br>&amp; monitoring','Six years of returns.<br>Monitoring gaps and priorities.','severn-trent.png','Severn Trent Water','/assets/social/evidence/severn-trent.png','Recorded storm overflow spills · 2020–2025','Explore the analysis'),
            ]
            for filename,label,title,lead,logo,organisation,image,caption,action in entries:
                text=f'<div><div class="logo-row"><img src="/assets/logos/{logo}" alt=""><span>{escape(organisation)}</span></div><div class="eyebrow">{label}</div><h1>{title}</h1><p class="lead">{lead}</p></div>'
                shot=f'<div class="screen"><div class="screen-label">{caption}</div><img src="{image}" alt="Actual report screenshot"></div>'
                views.append((filename,cover('compact '+('nhs' if logo=='nhs.svg' else ''),text+shot,action)))
            # Route each generated layout under the same local origin for fonts/assets.
            for filename,body in views:
                address=base+'/__link-preview/'+filename
                html=layout(body)
                page.route(address,lambda route,request,html=html: route.fulfill(status=200,content_type='text/html',body=html))
                page.goto(address,wait_until='networkidle')
                page.evaluate('document.fonts.ready')
                assert page.evaluate('Array.from(document.images).every(i=>i.complete&&i.naturalWidth>0)'), filename
                assert page.evaluate('document.documentElement.scrollWidth===1200&&document.documentElement.scrollHeight===627'), filename
                assert page.evaluate('''()=>{const area=document.querySelector('.content').getBoundingClientRect();return [...document.querySelectorAll('.screen,.grid')].every(el=>{const r=el.getBoundingClientRect();return r.top>=area.top-1&&r.bottom<=area.bottom+1;});}'''), filename
                page.screenshot(path=str(OUT/(filename+'.png')), animations='disabled')
            assert not errors,errors
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    print(f'Rendered {len(views)} covers at 1200 × 627 from actual project screenshots and supplied logos.')


if __name__ == '__main__':
    main()
