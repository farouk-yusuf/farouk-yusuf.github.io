#!/usr/bin/env python3
"""Check responsive homepage content and carousel behaviour with Playwright."""
import json
import shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def assert_viewport(page, label):
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Horizontal overflow: {label}'


def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}/'
    skills = json.loads((ROOT/'site/skills.json').read_text())
    about = json.loads((ROOT/'site/about.json').read_text())
    try:
        with sync_playwright() as p:
            executable = shutil.which('chromium') or shutil.which('chromium-browser')
            browser = p.chromium.launch(**({'executable_path': executable} if executable else {}), args=['--no-sandbox'])
            errors = []
            page = browser.new_page(viewport={'width':1440, 'height':1000})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('response', lambda response: errors.append(f'HTTP {response.status}: {response.url}') if response.status >= 400 else None)
            for width in (320,390,768,1440):
                page.set_viewport_size({'width':width,'height':1000})
                page.goto(base, wait_until='networkidle')
                assert page.locator('h1').inner_text() == 'Farouk Yusuf'
                assert page.locator('.profile-introduction p').all_text_contents() == about['introduction']
                assert page.locator('.project-highlight').count() == 4
                assert page.locator('.star-step dt').all_text_contents() == ['Situation','Task','Action','Results','Implications'] * 4
                assert page.locator('.site-header nav, [data-project-filters], .evidence-card, .skills-row').count() == 0
                assert page.locator('img').evaluate_all('(imgs) => imgs.filter(i=>i.complete).every(i=>i.naturalWidth > 0)')
                for tool in skills:
                    page.get_by_role('button', name='Show '+tool['name'], exact=True).click()
                    assert page.locator('[data-tool-slide]:visible h3').inner_text() == tool['name']
                    assert_viewport(page, (width,tool['name']))
                assert page.locator('[data-tool-play], [data-tool-count], .tool-status').count() == 0
                assert page.locator('[data-tool-slide]:visible li').count() == 4
                for project in page.locator('.project-highlight').all():
                    project.scroll_into_view_if_needed()
                    assert_viewport(page, (width,'project'))

            # Desktop should expose the complete skills panel in the opening view.
            page.set_viewport_size({'width':1440,'height':900})
            page.goto(base,wait_until='networkidle')
            assert page.locator('[data-tool-carousel]').bounding_box()['y'] + page.locator('[data-tool-carousel]').bounding_box()['height'] < 900
            page.get_by_role('button',name='Previous tool',exact=True).click()
            assert page.locator('[data-tool-slide]:visible h3').inner_text() == skills[-1]['name']
            page.get_by_role('button',name='Next tool',exact=True).click()
            assert page.locator('[data-tool-slide]:visible h3').inner_text() == skills[0]['name']
            page.keyboard.press('ArrowRight')
            assert page.locator('[data-tool-slide]:visible h3').inner_text() == 'SQL'
            page.keyboard.press('ArrowLeft')
            assert page.locator('[data-tool-slide]:visible h3').inner_text() == 'Microsoft Excel'
            page.get_by_role('button',name='Show R',exact=True).focus()
            page.keyboard.press('Enter')
            assert page.locator('[data-tool-slide]:visible h3').inner_text() == 'R'
            page.wait_for_timeout(7000)
            assert page.locator('[data-tool-slide]:visible h3').inner_text() == 'R', 'Focus did not hold the selected slide'

            # The existing project pages remain reachable and retain their charts.
            for link in page.locator('.project-detail-link').all():
                target = link.get_attribute('href')
                detail = browser.new_page()
                detail.goto(base+target, wait_until='networkidle')
                assert detail.locator('h1').count() == 1
                assert detail.locator('.chart-panel').count() >= 2
                detail.close()
            page.get_by_role('button',name='Dark mode',exact=True).click()
            page.reload()
            assert page.locator('html').get_attribute('data-theme') == 'dark'
            assert_viewport(page,'dark')
            page.close()

            for settings in ({'java_script_enabled':False}, {'reduced_motion':'reduce'}):
                context = browser.new_context(viewport={'width':390,'height':844},**settings)
                tab = context.new_page()
                tab.goto(base,wait_until='networkidle')
                if settings.get('java_script_enabled') is False:
                    assert tab.locator('[data-tool-slide]:visible').count() == len(skills)
                else:
                    assert tab.locator('[data-tool-slide]:visible').count() == 1
                    assert tab.get_by_role('button',name='Next tool',exact=True).is_visible()
                assert tab.locator('[data-route-chapter]').count() == 6
                assert tab.locator('.route-card').evaluate_all('(cards) => cards.every(c=>getComputedStyle(c).opacity === "1")')
                assert_viewport(tab,str(settings))
                context.close()
            # Advance the browser clock to exercise real rotation and transition logic.
            rotation = browser.new_context(viewport={'width':1440,'height':900})
            auto = rotation.new_page()
            auto.clock.install()
            auto.goto(base, wait_until='networkidle')
            auto.locator('[data-tool-carousel]').scroll_into_view_if_needed()
            auto.mouse.move(0,0)
            auto.wait_for_timeout(100)
            active_name = lambda: auto.locator('[data-tool-slide]:visible h3').inner_text()
            height = auto.locator('[data-tool-track]').bounding_box()['height']
            auto.clock.run_for(6500)
            assert active_name() == 'SQL', active_name()
            assert auto.locator('[data-tool-announcement]').inner_text() == ''
            assert auto.locator('[data-tool-track]').bounding_box()['height'] == height
            auto.locator('[data-tool-carousel]').hover()
            auto.clock.run_for(7000)
            assert active_name() == 'SQL', 'Hover did not hold the selected slide'
            auto.mouse.move(0,0)
            auto.clock.run_for(6500)
            assert active_name() == 'Python', active_name()
            auto.get_by_role('button',name='Show R',exact=True).focus()
            auto.keyboard.press('Enter')
            assert auto.locator('.tool-transition').get_attribute('aria-hidden') == 'true'
            assert auto.locator('.tool-transition').evaluate('(el)=>el.inert')
            assert auto.locator('[data-tool-slide]:visible').evaluate('(el)=>el.getAnimations().some(a=>a.effect.getTiming().duration===420)')
            auto.clock.run_for(7000)
            assert active_name() == 'R', 'Focus did not hold the selected slide'
            # Browser-clock jumps do not advance the native Web Animations timeline.
            auto.locator('.tool-transition').wait_for(state='detached', timeout=2000)
            auto.evaluate('document.activeElement.blur()')
            auto.clock.run_for(6500)
            assert active_name() == 'Statistics', active_name()
            auto.locator('#contact').scroll_into_view_if_needed()
            auto.locator('[data-tool-carousel][data-rotation="paused"]').wait_for()
            selected = active_name()
            auto.clock.run_for(6500)
            assert active_name() == selected, 'Off-screen carousel continued rotating'
            auto.locator('[data-tool-carousel]').scroll_into_view_if_needed()
            auto.locator('[data-tool-carousel][data-rotation="playing"]').wait_for()
            auto.clock.run_for(6500)
            assert active_name() != selected, 'Visible carousel did not resume'
            auto.emulate_media(reduced_motion='reduce')
            auto.locator('[data-tool-carousel][data-rotation="paused"]').wait_for()
            selected = active_name()
            auto.clock.run_for(6500)
            assert active_name() == selected, 'Reduced motion did not stop rotation'
            auto.get_by_role('button',name='Next tool',exact=True).click()
            assert active_name() != selected
            assert auto.locator('.tool-transition').count() == 0
            rotation.close()
            browser.close()
            assert not errors, errors
    finally:
        server.shutdown()
        server.server_close()
    print(f'Passed: exact introduction; 4 STAR summaries; {len(skills)} slides with four capabilities at 4 widths; smooth autoplay; hover/focus/off-screen/reduced-motion holds; manual arrows and keyboard selection; stable slide height; project links; dark mode; no-JS/reduced-motion support; no overflow or request/script errors.')


if __name__ == '__main__':
    main()
