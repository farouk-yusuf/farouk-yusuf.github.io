#!/usr/bin/env python3
"""Exercise the walking route, chapter controls, supplied images and static fallbacks."""
import json
import shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def settle(page):
    page.wait_for_timeout(320)


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}/'
    about = json.loads((ROOT/'site/about.json').read_text())
    errors = []
    try:
        with sync_playwright() as p:
            executable = shutil.which('chromium') or shutil.which('chromium-browser')
            browser = p.chromium.launch(**({'executable_path':executable} if executable else {}), args=['--no-sandbox'])
            page = browser.new_page(viewport={'width':1440,'height':900})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('response', lambda response: errors.append(f'HTTP {response.status}: {response.url}') if response.status >= 400 else None)
            page.goto(base, wait_until='networkidle')
            assert page.locator('.profile-picture img').evaluate('(img) => img.complete && img.naturalWidth > 0')
            assert page.locator('.project-highlight .org-logo').count() == 4
            assert page.locator('.project-highlight .org-logo').evaluate_all('(imgs) => imgs.every(i=>i.complete && i.naturalWidth > 0)')
            assert page.locator('.route-enhanced').count() == 1
            assert page.locator('.route-year').all_text_contents() == list(map(str,range(2016,2027)))
            assert page.locator('[data-route-scroll]').evaluate('(el)=>el.offsetHeight / innerHeight') == 6
            for index, chapter in enumerate(about['milestones']):
                link = page.locator(f'[data-route-jump="{index}"]')
                link.focus()
                page.keyboard.press('Enter')
                settle(page)
                assert page.locator('.route-section').get_attribute('data-route-current') == str(index+1)
                assert page.locator('.route-chapter.is-active').count() == 1
                assert page.locator('.route-chapter.is-active h3').inner_text() == chapter['title']
                assert page.locator('.walker-item.is-collected').count() == index+1
                assert page.locator('.route-tool.is-collected').count() == index+1
                assert link.get_attribute('aria-current') == 'step'
                assert page.locator('[data-route-walker]').get_attribute('data-frame') == '0'
                box = page.locator('[data-route-walker]').bounding_box()
                assert abs(box['x']+box['width']/2 - 1440*.35) < 2

            # Real incremental scroll must drive multiple poses, then stop at rest.
            page.locator('[data-route-jump="1"]').click()
            settle(page)
            poses = set()
            for _ in range(8):
                page.evaluate('scrollBy({top:19,behavior:"instant"})')
                page.wait_for_timeout(35)
                poses.add(page.locator('[data-route-walker]').get_attribute('data-frame'))
            assert len(poses) >= 3, poses
            page.wait_for_timeout(220)
            assert page.locator('[data-route-walker]').get_attribute('data-frame') == '0'
            page.evaluate('scrollBy({top:-40,behavior:"instant"})')
            page.wait_for_timeout(50)
            assert page.locator('[data-route-walker]').evaluate('(el)=>el.style.getPropertyValue("--facing")') == '-1'

            page.locator('[data-route-jump="ending"]').click()
            settle(page)
            assert page.locator('.route-at-end').count() == 1
            assert page.locator('.walker-item.is-collected').count() == 6
            assert page.locator('.route-ending a').evaluate_all('(links)=>links.every(a=>a.tabIndex===0)')
            page.keyboard.press('Tab')
            assert page.locator(':focus').get_attribute('href') == '#projects'
            page.locator('[data-route-view]').click()
            assert page.locator('.route-enhanced').count() == 0
            assert page.locator('.route-chapter').evaluate_all('(cards)=>cards.every(c=>getComputedStyle(c).opacity==="1")')
            page.locator('[data-route-view]').click()
            settle(page)
            assert page.locator('.route-enhanced').count() == 1

            # Pinning must not place any active card under the sticky controls.
            for width,height in ((1440,900),(1280,800),(768,800),(1024,760)):
                page.set_viewport_size({'width':width,'height':height})
                for index in range(6):
                    page.locator(f'[data-route-jump="{index}"]').click()
                    settle(page)
                    box = page.locator('.route-chapter.is-active').bounding_box()
                    assert box['y'] >= 126, (width,height,index,box)
                    assert box['y']+box['height'] < height, (width,height,index)
                page.locator('[data-route-jump="ending"]').click()
                settle(page)
                assert page.locator('.route-ending').bounding_box()['y'] >= 126, (width,height)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.close()

            for settings in ({'viewport':{'width':390,'height':844}}, {'viewport':{'width':320,'height':800}}, {'viewport':{'width':1440,'height':600}}, {'viewport':{'width':1440,'height':900},'reduced_motion':'reduce'}, {'viewport':{'width':1440,'height':900},'java_script_enabled':False}):
                context = browser.new_context(**settings)
                tab = context.new_page()
                tab.goto(base,wait_until='networkidle')
                assert tab.locator('.route-enhanced').count() == 0, settings
                assert tab.locator('[data-route-chapter]').count() == 6
                assert tab.locator('.route-chapter').evaluate_all('(cards)=>cards.every(c=>getComputedStyle(c).opacity==="1")')
                assert tab.locator('.route-ending').evaluate('(el)=>getComputedStyle(el).opacity') == '1'
                assert tab.evaluate('document.documentElement.scrollWidth <= innerWidth'), settings
                context.close()
            context = browser.new_context(viewport={'width':1440,'height':900})
            direct = context.new_page()
            direct.goto(base+'#journey-05',wait_until='networkidle')
            assert direct.locator('.route-section').get_attribute('data-route-current') == '5'
            direct.emulate_media(reduced_motion='reduce')
            direct.locator('.route-enhanced').wait_for(state='detached')
            assert direct.locator('.route-enhanced').count() == 0
            context.close()
            browser.close()
            assert not errors, errors
    finally:
        server.shutdown()
        server.server_close()
    print('Passed: supplied portrait/logos; six-screen route; six keyboard chapter jumps; accumulated tools; scroll poses and reversal; idle stop; ending actions; list toggle; four desktop sizes; mobile/short-screen/reduced-motion/no-JS fallbacks; deep link; no overflow or script/request failures.')


if __name__ == '__main__':
    main()
