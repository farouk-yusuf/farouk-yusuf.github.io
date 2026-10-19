#!/usr/bin/env python3
"""Build the GitHub Pages site with the Python standard library.

Run from any directory: python3 scripts/build_site.py
HTML is committed so serving and deployment never require this script.
"""
import argparse
import json
from html import escape
from pathlib import Path
from string import Template

from birmingham_story import render as render_birmingham
from housing_story import render as render_housing
from water_story import render as render_water
from nhs_story import render as render_nhs

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = json.loads((ROOT / 'site/projects.json').read_text())
RESOURCES = json.loads((ROOT / 'site/resources.json').read_text())
ABOUT = json.loads((ROOT / 'site/about.json').read_text())
SKILLS = json.loads((ROOT / 'site/skills.json').read_text())
OUTPUTS = {}
EXTERNAL_ARROW = '<svg class="arrow-icon" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 13 13 3M3 3h10v10"/></svg>'


def emit(path, content):
    OUTPUTS[ROOT / path] = content


def e(value):
    return escape(str(value), quote=True)


def paragraph(text):
    return f'<p>{e(text)}</p>'


def svg_wrap(body, height=250):
    # The figure caption names the chart; the adjacent table supplies its data.
    return f'<svg class="chart" viewBox="0 0 620 {height}" role="img" aria-label="Chart; values are also available in the data table"><title>Values are available in the accompanying data table</title>{body}</svg>'


def bars(labels, values, unit='', maximum=None, reference=None, compact=False):
    left, right = (205, 555) if not compact else (170, 555)
    row = 37 if not compact else 32
    top = 25
    height = top + row * len(values) + 35
    minimum = min(0, min(values))
    maximum = maximum if maximum is not None else max(0, max(values)) * 1.2
    if maximum == minimum:
        maximum += 1
    def x(v):
        return left + (v - minimum) / (maximum - minimum) * (right - left)
    body = f'<line class="axis" x1="{x(0):.2f}" y1="10" x2="{x(0):.2f}" y2="{height-30}"/>'
    for i, (label, value) in enumerate(zip(labels, values)):
        y = top + i * row
        color = 'warm-bar' if value < 0 else 'bar'
        start, end = sorted([x(0), x(value)])
        body += f'<text x="{left-15}" y="{y+15}" text-anchor="end">{e(label)}</text>'
        body += f'<rect class="{color}" x="{start:.2f}" y="{y}" width="{max(0,end-start):.2f}" height="21" rx="2"><title>{e(label)}: {e(value)}{e(unit)}</title></rect>'
        label_x = end + 8
        display_value = f'{value:,}' if isinstance(value, int) else str(value)
        body += f'<text x="{label_x:.2f}" y="{y+15}">{e(display_value)}{e(unit)}</text>'
    if reference is not None:
        body += f'<line class="threshold" x1="{x(reference):.2f}" x2="{x(reference):.2f}" y1="9" y2="{height-30}"/>'
        body += f'<text x="{x(reference):.2f}" y="{height-8}" text-anchor="middle">Target {e(reference)}</text>'
    return svg_wrap(body, height)


def table(headers, rows, title):
    head = ''.join(f'<th scope="col">{e(h)}</th>' for h in headers)
    cells = ''.join('<tr>'+''.join(f'<td>{e(v)}</td>' for v in row)+'</tr>' for row in rows)
    return f'<div class="table-scroll" tabindex="0" role="region" aria-label="{e(title)}"><table><caption>{e(title)}</caption><thead><tr>{head}</tr></thead><tbody>{cells}</tbody></table></div>'


def chart(title, subtitle, drawing, headers, rows, source):
    drawing = drawing.replace('aria-label="Chart; values are also available in the data table"', f'aria-label="{e(title)}"')
    return f'''<figure class="chart-panel"><figcaption>{e(title)}</figcaption>
    <p class="chart-subtitle">{e(subtitle)}</p>{drawing}
    <details><summary>View the chart data</summary>{table(headers, rows, title)}</details>
    <p class="chart-source">Source: {e(source)}</p></figure>'''


def organisation(project, prefix=''):
    logo = project['logo']
    if (ROOT/'assets/logos'/logo).exists():
        extra = ' nhs' if logo == 'nhs.svg' else ''
        # NHS is an NHS mark, not the UHB trust's own logo.
        alt = 'NHS' if logo == 'nhs.svg' else project['organisation']
        image = f'<img class="org-logo{extra}" src="{prefix}assets/logos/{e(logo)}" alt="{e(alt)}" width="100" height="45">'
    else:
        image = f'<span class="org-symbol" aria-hidden="true">{e(project["initials"])}</span>'
    return f'<div class="organisation">{image}<span>{e(project["organisation"])}</span></div>'


def header(prefix=''):
    return f'''<a class="skip-link" href="#main">Skip to content</a>
    <header class="site-header"><div class="container nav">
      <a class="brand" href="{prefix}index.html"><span class="brand-mark" aria-hidden="true">FY</span>Farouk Yusuf<span class="sr-only">, home</span></a>
      <button class="theme-button" data-theme-toggle aria-pressed="false" hidden>Dark mode</button>
    </div></header>'''


def footer(prefix=''):
    return f'''<footer class="container site-footer"><p>© 2026 Farouk Yusuf · Birmingham, UK<br>Independent portfolio analyses of published data. Organisation names and marks identify the subjects of the analysis; no affiliation or endorsement is implied.</p><a href="https://github.com/farouk-yusuf" target="_blank" rel="noopener">GitHub ↗</a></footer>'''


def document(title, description, content, prefix='', styles=()):
    home_styles = '<link rel="stylesheet" href="assets/css/home.css"><link rel="stylesheet" href="assets/css/journey.css"><script src="assets/js/journey.js" defer></script>' if not prefix else ''
    extra_styles = ''.join(f'<link rel="stylesheet" href="{prefix}assets/css/{e(style)}">' for style in styles)
    return f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} | Farouk Yusuf</title><meta name="description" content="{e(description)}">
<meta name="theme-color" content="#1b302b"><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/css/site.css">{home_styles}{extra_styles}<script src="{prefix}assets/js/site.js" defer></script></head>
<body>{header(prefix)}{content}{footer(prefix)}</body></html>\n'''.replace('↗', EXTERNAL_ARROW)


def project_highlight(project, index):
    highlight = project['highlight']
    steps = []
    for label in ('Situation', 'Task', 'Action', 'Results', 'Implications'):
        copy = highlight[label.lower()]
        if project['slug'] == 'severn-trent' and label == 'Situation':
            copy = 'Storm overflows can release sewage into rivers when the sewer system is overwhelmed. ' + copy
        steps.append(f'<div class="star-step star-step--{label.lower()}"><dt>{label}</dt><dd>{e(copy)}</dd></div>')
    tags = ''.join(f'<span class="tag">{e(tool)}</span>' for tool in project['tools'])
    report_link = f'<a class="project-report-link" href="{e(project["report_url"])}">View Power BI report <span aria-hidden="true">↗</span></a>' if project.get('report_url') else ''
    return f'''<article class="project-highlight" aria-labelledby="project-{index}-title">
      <div class="project-art"><img class="sector-image" src="assets/illustrations/{e(highlight['image'])}" alt="{e(highlight['image_alt'])}" width="640" height="400" loading="lazy">
      <div class="project-art-footer"><span class="eyebrow">{e(project['sector'])}</span><div class="project-key">{('<span class="project-key-prefix">' + e(highlight['key_prefix']) + '</span>') if highlight.get('key_prefix') else ''}<strong>{e(highlight['key_figure'])}</strong><span>{e(highlight['key_label'])}</span></div><div class="tags">{tags}</div></div></div>
      <div class="project-narrative">{organisation(project)}<h3 id="project-{index}-title"><a href="case-studies/{project['slug']}.html">{e(highlight['headline'])}</a></h3>
      <dl class="star-list">{''.join(steps)}</dl><a class="project-detail-link" href="case-studies/{project['slug']}.html">View analysis and supporting files <span aria-hidden="true">↗</span><span class="sr-only">: {e(project['organisation'])}</span></a>{report_link}</div>
    </article>'''


def skills_carousel():
    slides = []
    for index, tool in enumerate(SKILLS):
        items = ''.join(f'<li><strong>{e(name)}</strong><span>{e(description)}</span></li>' for name, description in tool['items'])
        slides.append(f'''<section class="tool-slide" data-tool-slide role="group" aria-roledescription="slide" aria-label="{index+1} of {len(SKILLS)}: {e(tool['name'])}">
        <div class="tool-identity"><img src="assets/icons/{e(tool['icon'])}" alt="" width="42" height="42"><h3>{e(tool['name'])}</h3></div><div class="tool-details"><ul>{items}</ul></div></section>''')
    choices = ''.join(f'<button type="button" data-tool-select="{index}" aria-label="Show {e(tool["name"])}" title="{e(tool["name"])}" aria-pressed="{str(index==0).lower()}"><img src="assets/icons/{e(tool["icon"])}" width="20" height="20" alt=""></button>' for index,tool in enumerate(SKILLS))
    return f'''<section class="tool-carousel" data-tool-carousel role="region" aria-roledescription="carousel" aria-label="Tools and capabilities">
      <div class="tool-carousel-top"><h2>Tools &amp; capabilities</h2><div class="tool-controls" data-tool-controls hidden><button type="button" data-tool-previous aria-label="Previous tool"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m14 6-6 6 6 6"/></svg></button><button type="button" data-tool-next aria-label="Next tool"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m10 6 6 6-6 6"/></svg></button></div></div>
      <div data-tool-track>{''.join(slides)}</div><div class="tool-choices" data-tool-choices role="group" aria-label="Choose a tool" hidden>{choices}</div><p class="sr-only" data-tool-announcement role="status" aria-live="polite"></p>
    </section>'''


def profile_picture():
    portraits = [('assets/images/headshot.jpeg',400,400)]
    portraits += [(f'assets/images/headshot-3.{extension}',400,500) for extension in ('jpg','jpeg','png','webp')]
    for filename,width,height in portraits:
        if (ROOT / filename).is_file():
            return f'<figure class="profile-picture"><img src="{filename}" alt="Farouk Yusuf" width="{width}" height="{height}" fetchpriority="high"><figcaption>Farouk Yusuf · Birmingham, UK</figcaption></figure>'
    return '<div class="profile-placeholder" role="img" aria-label="Placeholder for Farouk Yusuf’s profile photograph"><span class="profile-initials" aria-hidden="true">FY</span><p>Farouk Yusuf</p><span>Birmingham, UK</span></div>'



def toolkit_icon(name, css_class=''):
    return f'<svg class="{css_class}" viewBox="0 0 32 32" aria-hidden="true"><use href="#kit-{e(name)}"/></svg>'


def about_section():
    cards, links, stops, toolkit, events = [], [], [], [], []
    for event in ABOUT['events']:
        events.append(f'<div class="route-event route-event--{e(event["kind"])}" data-route-event="{e(event["kind"])}" data-position="{event["position"]}" style="--event:{event["position"]};--lane:{event["lane"]};--event-width:{event.get("label_width",164)}px"><span class="route-event-dot">{"♡" if event["kind"] == "wedding" else ""}</span><p><span>{e(event["date"])}</span><strong>{e(event["label"])}</strong>{e(event["organisation"])}</p></div>')
    for index, milestone in enumerate(ABOUT['milestones']):
        chapter_id = f'journey-{index+1:02d}'
        related_events = [event for event in ABOUT['events'] if event['after'] == index]
        life = '<ul class="route-life-static" aria-label="Along the way">' + ''.join(f'<li class="route-life-entry route-life-entry--{e(event["kind"])}"><span class="route-event-symbol" aria-hidden="true">{"♡" if event["kind"] == "wedding" else "·"}</span><div><span>{e(event["date"])}</span><strong>{e(event["label"])}</strong><span>{e(event["organisation"])}</span></div></li>' for event in related_events) + '</ul>' if related_events else ''
        body = paragraph(milestone['text'])
        note = f'<p class="route-note">{e(milestone["note"])}</p>' if milestone['note'] else ''
        if milestone['item'] == 'scholarship':
            for phrase in ('Chevening scholarship', 'Chevening Scholarship'):
                link = f'<a href="{e(ABOUT["chevening_source"])}" target="_blank" rel="noopener">{e(phrase)}</a>'
                body = body.replace(e(phrase), link)
                note = note.replace(e(phrase), link)
        cards.append(f'''<li class="route-chapter" id="{chapter_id}" data-route-chapter data-stop="{milestone['position']}">
          <article class="route-card"><div class="route-card-top"><span class="route-date">{e(milestone['date'])}</span><span class="route-pickup">{toolkit_icon(milestone['item'])}<span>{e(milestone['item_label'])}</span></span></div>
          <h3>{e(milestone['title'])}</h3>{body}{note}</article>{life}</li>''')
        links.append(f'<a href="#{chapter_id}" data-route-jump="{index}" aria-label="Jump to {e(milestone["date"])}: {e(milestone["tag"])}" title="{e(milestone["date"])} · {e(milestone["tag"])}"><span aria-hidden="true"></span></a>')
        stops.append(f'<div class="route-stop" data-route-stop style="--stop:{milestone["position"]}"><span class="route-stop-dot"></span><span class="route-tag">{e(milestone["tag"])}</span></div>')
        toolkit.append(f'<span class="route-tool" data-route-tool>{toolkit_icon(milestone["item"])}<span>{e(milestone["item_label"])}</span></span>')
    # Small milestone patches accumulate on the backpack, then travel with the analyst.
    carry = ''.join(f'<g class="walker-item" data-walker-item="{index}" transform="translate({22+(index%2)*9} {59+(index//2)*10})"><use href="#kit-{e(m["item"])}" width="9" height="9"/></g>' for index,m in enumerate(ABOUT['milestones']))
    walker_svg = Template((ROOT/'assets/illustrations/journey-walker.svg').read_text()).substitute(carry=carry)
    partner_svg = (ROOT/'assets/illustrations/journey-partner.svg').read_text()
    walker = f'<div class="route-walker" data-route-walker data-frame="0" data-outfit="graduate" aria-hidden="true">{partner_svg}{walker_svg}</div>'
    confetti = ''.join(f'<i style="--piece:{index};--drift:{(index%7-3)*31}px;--rise:{70+(index%5)*20}px"></i>' for index in range(18))
    celebration = f'<div class="route-celebration" data-route-celebration aria-hidden="true"><div class="route-confetti">{confetti}</div><span class="route-love">♡ ✧ ♡</span></div>'
    template = Template((ROOT/'site/templates/journey.html').read_text())
    ending = ABOUT['ending']
    return template.substitute(
        symbols=(ROOT/'assets/illustrations/journey-toolkit.svg').read_text(),
        opening=e(ABOUT['opening']), cards=''.join(cards), chapter_links=''.join(links),
        year_ticks=''.join(f'<span class="route-year" style="--year:{(year-2019)/7}">{year}</span>' for year in range(2019,2027)),
        axis_stops=''.join(stops), events=''.join(events), walker=walker, celebration=celebration, toolkit=''.join(toolkit),
        additional_experience=e(ABOUT['additional_experience']),
        ending_heading=e(ending['heading']), ending_lead=e(ending['lead']),
        ending_points=''.join(f'<li>{e(point)}</li>' for point in ending['points']),
    )


def home():
    template = Template((ROOT/'site/templates/home.html').read_text())
    content = template.substitute(
        introduction=''.join(paragraph(text) for text in ABOUT['introduction']),
        portrait=profile_picture(),
        skills=skills_carousel(),
        projects=''.join(project_highlight(project, index) for index,project in enumerate(PROJECTS,1)),
        about=about_section(),
    )
    emit('index.html', document('Data analyst portfolio', 'Farouk Yusuf: six years in academic and applied research, transitioning into commercial data analysis. Explore independent SQL, Python and Excel projects using UK public data.', content))


def resources(project):
    links=[r for r in RESOURCES if '/'+project['folder']+'/' in r['url']]
    rows=[]
    for r in links:
        kind='Excel workbook' if '.xlsx' in r['url'] else 'GitHub'
        rows.append(f'<a href="{e(r["url"])}" target="_blank" rel="noopener"><span>{e(r["label"])} ↗</span><small>{kind}</small></a>')
    rows.append(f'<a href="../projects/{e(project["folder"])}/source_log.csv" download><span>Source log ↓</span><small>CSV</small></a>')
    return '<div class="resource-list">'+''.join(rows)+'</div>'


def section(id_, title, content):
    return f'<section class="story-section" id="{id_}"><h2>{e(title)}</h2>{content}</section>'


def project_page(project,index):
    renderers = {
        'birmingham-payments': (render_birmingham, 'birmingham.json'),
        'platform-housing': (render_housing, 'platform.json'),
        'severn-trent': (render_water, 'severn-trent.json'),
        'uhb-waiting-times': (render_nhs, 'uhb.json'),
    }
    renderer, filename = renderers[project['slug']]
    copy = json.loads((ROOT/'site'/filename).read_text())
    content = renderer(project,PROJECTS[(index+1)%len(PROJECTS)],chart=chart,table=table,organisation=organisation,resources=resources)
    emit(f"case-studies/{project['slug']}.html",document(copy['title'],copy['summary'],content,'../',styles=('finance.css','story-charts.css')))


def research():
    chart_html=chart('Overall reliability passed the target; individual questions did not.', 'Selected Krippendorff’s alpha results from the 500-post validation sample. These are different comparisons, rather than a complete question-level series.',
      bars(['Human–human overall','AI–human overall','Human–human Q7','AI–human Q9'],[0.758,0.807,0.484,0.445],maximum=1.05,reference=.70),
      ['Comparison','Krippendorff’s alpha'],[['Human–human overall',.758],['AI–human overall',.807],['Human–human Q7',.484],['AI–human Q9',.445]],
      'Author’s unpublished thesis validation results, as provided in the portfolio handoff. Exact figures remain subject to supervisor sign-off.')
    body=section('question','Could AI help code research data reliably?',paragraph('My PhD investigates why skilled Nigerians migrate to the UK. To analyse a corpus of 29,182 cleaned social media posts about leaving Nigeria, I needed ten yes/no coding questions grounded in my theoretical framework. Before scaling up, I tested whether humans and AI interpreted those questions consistently.'))
    body+=section('validation','The breakdown changed the next step.',paragraph('Two human coders worked through a 100-post pilot and 400 further posts. ChatGPT and Gemini were tested as proxy coders. Overall agreement was 88.5% for the human–human comparison and 90.8% for AI–human, while overall alpha cleared the 0.70 target. The weaker question-level results meant that the average was insufficient grounds to trust every part of the scheme.')+chart_html)
    body+=section('revision','I had to revisit what the questions measured.',paragraph('Human disagreements concentrated on Q1, Q3, Q7 and Q8. Q3, the spatial-horizon question, had drifted from the theoretical concept it was meant to capture. I corrected it and refined the codebook across versions v1.1 to v3.3.')+paragraph('Q3 also illustrated a measurement trap: 99.7% raw agreement coexisted with alpha of 0.000 because nearly every answer was “no”. A high agreement percentage was therefore a poor standalone guide to reliability.')+paragraph('I built a coding app that presented one question at a time, saved progress and exported CSV files. A finer instance-level scheme was piloted on 40 posts and set aside when it proved unstable.'))
    body+=section('learning','What I take into analyst work.',paragraph('I learned to treat disagreement as evidence about the measurement process. Before trusting a KPI or classifier, I want to know whether its definition is clear, whether important groups fail, and whether the headline metric disguises a weak component.')+f'<div class="callout"><h3>Publication status</h3>{paragraph("These are unpublished thesis results. Exact figures shown here were already included in the portfolio revision and remain subject to supervisor sign-off before formal publication. The page does not publish raw posts or participant-level data.")}</div>')
    content=f'''<main class="container" id="main"><div class="breadcrumb"><a href="../index.html#about">Research</a> / Coding validation</div><div class="case-hero"><span class="eyebrow">Doctoral research / University of Birmingham</span><h1>The coders disagreed.<br>That was a finding worth following.</h1><p class="lead">A validation study taught me why a reassuring average can hide a measurement problem, and why revising the question can matter more than changing the model.</p><div class="case-meta"><span>International Development PhD · Viva pending</span><span>Python · Research design · Reliability testing</span></div></div><div class="case-layout"><nav class="case-nav" aria-label="On this page"><strong>Inside the research</strong><a href="#question">The question</a><a href="#validation">Validation</a><a href="#revision">Revising the scheme</a><a href="#learning">Lessons and limitations</a></nav><div class="case-content">{body}</div></div><div class="next-project"><a href="../index.html#about">← Back to portfolio</a><a class="button" href="birmingham-payments.html">Explore the public-data projects →</a></div></main>'''
    emit('case-studies/research-validation.html', document('Research coding validation','How Farouk Yusuf tested human and AI coding reliability, investigated disagreement and revised a research coding scheme.',content,'../'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check committed HTML is up to date without writing files')
    args = parser.parse_args()
    home()
    for i,project in enumerate(PROJECTS):
        project_page(project,i)
    research()
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, content in OUTPUTS.items() if not path.exists() or path.read_text() != content]
        if stale:
            parser.exit(1, 'Generated HTML is out of date: ' + ', '.join(stale) + '\nRun python3 scripts/build_site.py\n')
        print('All 6 generated HTML pages are up to date.')
    else:
        for path, content in OUTPUTS.items():
            path.write_text(content)
        print('Built homepage and 5 case-study pages.')


if __name__ == '__main__':
    main()
