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


def scroll_to_year_position(page, position):
    page.evaluate("""position => {
        const area = document.querySelector('[data-route-scroll]');
        const scene = document.querySelector('[data-route-scene]');
        const start = area.getBoundingClientRect().top + scrollY - 64;
        scrollTo({top:start + (area.offsetHeight-scene.offsetHeight)*position*.84, behavior:'instant'});
    }""", position)
    page.wait_for_timeout(80)


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
            assert page.locator('.route-year').all_text_contents() == list(map(str,range(2019,2027)))
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

            assert page.locator('.route-chapter h3').all_text_contents() == [
                'Spatial Analyst and Real-World Impact', 'Academic Excellence & Media Analysis',
                'Expert in mixed-methods research design and analysis.', 'Doctoral Research',
                'Skilled in Machine Learning', 'Transitioning to the Commercial or Public Sector',
            ]
            for chapter, approved in zip(page.locator('.route-card > p:first-of-type').all(), about['milestones']):
                assert chapter.inner_text() == approved['text']
            for card in page.locator('.route-card').all():
                note = card.locator('.route-note')
                assert note.count() == 1
                assert card.evaluate("""card => {
                    const body = getComputedStyle(card.querySelector('p'));
                    const note = getComputedStyle(card.querySelector('.route-note'));
                    return ['fontFamily','fontSize','fontWeight','fontStyle','lineHeight'].every(key=>body[key]===note[key]);
                }""")
            assert 'structured spreadsheets and databases' in page.locator('#journey-03 .route-note').inner_text()
            first_natcen = page.locator('.route-life-entry').filter(has_text='Sep 2024')
            assert 'National Centre for Social Research (NatCen)' in first_natcen.inner_text()
            assert page.get_by_role('link', name='Connect on LinkedIn').count() == 1
            assert page.get_by_text('Illustrative sector image', exact=True).count() == 0
            assert 'Congratulations' not in page.locator('.route-section').inner_text()

            # The research teaser is removed; Chevening links work by mouse and keyboard.
            assert page.locator('.home-research, #research').count() == 0
            assert page.get_by_role('link', name='Explore the research').count() == 0
            assert page.get_by_role('link', name='About the Chevening programme').count() == 0
            page.context.route('https://www.chevening.org/**', lambda route: route.fulfill(status=200, content_type='text/html', body='<title>Chevening link check</title>'))
            page.locator('[data-route-jump="1"]').click()
            settle(page)
            scholarship_links = page.locator('#journey-02 .route-card a')
            assert scholarship_links.count() == 2
            for index, link in enumerate(scholarship_links.all()):
                assert link.get_attribute('href') == about['chevening_source']
                assert link.evaluate('(el)=>el.tabIndex') == 0
                with page.expect_popup() as popup:
                    if index == 0:
                        link.click()
                    else:
                        link.focus()
                        page.keyboard.press('Enter')
                target = popup.value
                target.wait_for_load_state()
                assert target.url == about['chevening_source']
                target.close()
            page.locator('[data-route-jump="0"]').click()
            settle(page)
            assert scholarship_links.evaluate_all('(links)=>links.every(a=>a.tabIndex===-1)')

            # Dated employment entries stay in HTML reading order alongside study.
            entries = page.locator('.route-life-entry').all_text_contents()
            for date, role, organisation in (
                ('Sep 2021','Started · Research Associate','University of Birmingham'),
                ('Jan 2022','Finished · Research Associate','University of Birmingham'),
                ('Feb 2022','Started · Support Worker','Charis Care Solutions'),
                ('Dec 2022','Finished · Support Worker','Charis Care Solutions'),
                ('2023','Got married','Love and a new chapter'),
                ('Sep 2024','Started · Freelance Interviewer','NatCen'),
                ('Jan 2025','Finished · Freelance Interviewer','NatCen'),
            ):
                assert any(all(value in entry for value in (date,role,organisation)) for entry in entries)
            assert 'freelance' in page.locator('.route-footnote').inner_text().lower()
            assert 'Outlier' in page.locator('.route-footnote').inner_text()
            assert page.locator('.route-tool').all_text_contents() == ['Geography','Chevening','Research design','PhD research','AI evaluation','Business analysis']

            # Wedding partner/effects must never appear before the tick, even on return.
            scroll_to_year_position(page, 0)
            assert page.locator('[data-route-walker]').get_attribute('data-outfit') == 'graduate'
            assert page.locator('[data-route-walker]').evaluate('(el)=>el.style.getPropertyValue("--facing")') == '1'
            scroll_to_year_position(page, .16)
            assert page.locator('[data-route-walker]').get_attribute('data-outfit') == 'explorer'
            scroll_to_year_position(page, 2/7)
            assert page.locator('[data-route-walker]').get_attribute('data-outfit') == 'graduate'
            for position in (4/7-.015, 4/7-.0005):
                scroll_to_year_position(page, position)
                assert page.locator('[data-route-walker]').get_attribute('data-outfit') != 'wedding'
                assert not page.locator('.route-partner').is_visible()
                assert page.locator('.route-event--wedding .route-event-dot').evaluate('(el)=>getComputedStyle(el).fontSize') == '0px'
                assert page.locator('.route-celebration.is-celebrating').count() == 0
            scroll_to_year_position(page, 4/7+.004)
            assert page.locator('[data-route-walker]').get_attribute('data-outfit') == 'wedding'
            assert page.locator('.route-partner').is_visible()
            assert page.locator('.route-celebration.is-celebrating.is-bursting').count() == 1
            assert page.locator('.route-confetti i').count() == 18
            page.wait_for_function("!document.querySelector('.route-celebration').classList.contains('is-bursting')", timeout=4000)
            assert page.locator('.route-celebration.is-celebrating').count() == 1
            assert page.locator('.route-love').is_visible()
            scroll_to_year_position(page, .65)
            assert page.locator('[data-route-walker]').get_attribute('data-outfit') == 'explorer'
            assert not page.locator('.route-partner').is_visible()
            scroll_to_year_position(page, 4/7+.004)
            assert page.locator('.route-celebration.is-celebrating.is-bursting').count() == 1
            scroll_to_year_position(page, 4/7-.015)
            assert page.locator('.route-celebration.is-celebrating').count() == 0
            assert not page.locator('.route-partner').is_visible()
            scroll_to_year_position(page, 4/7+.004)
            assert page.locator('.route-celebration.is-celebrating.is-bursting').count() == 1

            # Real incremental scroll must drive multiple poses, then stop at rest.
            page.locator('[data-route-jump="1"]').click()
            settle(page)
            poses = set()
            angles = []
            for _ in range(8):
                page.evaluate('scrollBy({top:19,behavior:"instant"})')
                page.wait_for_timeout(35)
                poses.add(page.locator('[data-route-walker]').get_attribute('data-frame'))
                angles.append(float(page.locator('[data-route-walker]').evaluate('(el)=>el.style.getPropertyValue("--leg-swing")').removesuffix('deg')))
            assert len(poses) >= 2, poses
            assert len(set(angles)) >= 6, angles
            assert all(abs(a-b) < 14 for a,b in zip(angles,angles[1:])), angles
            page.wait_for_timeout(220)
            assert page.locator('[data-route-walker]').get_attribute('data-frame') == '0'
            page.evaluate('scrollBy({top:-40,behavior:"instant"})')
            page.wait_for_timeout(50)
            assert page.locator('[data-route-walker]').evaluate('(el)=>el.style.getPropertyValue("--facing")') == '-1'
            page.locator('[data-route-jump="0"]').click()
            settle(page)
            assert page.locator('[data-route-walker]').evaluate('(el)=>el.style.getPropertyValue("--facing")') == '1'

            page.locator('[data-route-jump="ending"]').click()
            settle(page)
            assert page.locator('.route-at-end').count() == 1
            assert page.locator('[data-route-walker]').get_attribute('data-outfit') == 'business'
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
                    # Work labels must leave room for the milestone legend below.
                    legend_top = page.locator('.route-toolkit').bounding_box()['y']
                    for label in page.locator('.route-event p').all():
                        event_box = label.bounding_box()
                        if event_box['x'] >= 0 and event_box['x']+event_box['width'] <= width:
                            assert event_box['y']+event_box['height'] < legend_top-4, (width,height,index,event_box,legend_top)
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
                assert tab.locator('.route-life-entry').count() == 7
                assert tab.locator('#journey-02 .route-card a').evaluate_all('(links)=>links.every(a=>a.tabIndex===0)')
                assert not tab.locator('.route-celebration').is_visible()
                assert not tab.locator('.route-partner').is_visible()
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
    print('Passed: supplied portrait/logos; six-screen route; six keyboard chapter jumps; milestone patches; CV employment dates; graduation/wedding/business outfits; repeatable post-2023 celebration and persistent sparkles; continuous scroll poses and reversal; idle stop; ending actions; list toggle; four desktop sizes; mobile/short-screen/reduced-motion/no-JS fallbacks; deep link; no overflow or script/request failures.')


if __name__ == '__main__':
    main()
