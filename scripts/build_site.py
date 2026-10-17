#!/usr/bin/env python3
"""Build the GitHub Pages site with the Python standard library.

Run from any directory: python3 scripts/build_site.py
HTML is committed so serving and deployment never require this script.
"""
import argparse
import csv
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = json.loads((ROOT / 'site/projects.json').read_text())
RESOURCES = json.loads((ROOT / 'site/resources.json').read_text())
OUTPUTS = {}
EXTERNAL_ARROW = '<svg class="arrow-icon" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 13 13 3M3 3h10v10"/></svg>'


def emit(path, content):
    OUTPUTS[ROOT / path] = content


def e(value):
    return escape(str(value), quote=True)


def paragraph(text):
    return f'<p>{e(text)}</p>'


def list_html(items, ordered=False):
    tag = 'ol' if ordered else 'ul'
    return f'<{tag}>' + ''.join(f'<li>{e(item)}</li>' for item in items) + f'</{tag}>'


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


def line(labels, values, unit='', low=0, high=None, reference=None):
    left, right, top, bottom = 52, 555, 28, 205
    high = high if high is not None else max(values) * 1.15
    def y(v):
        return bottom - (v-low)/(high-low)*(bottom-top)
    def x(i):
        return left+i*(right-left)/max(1,len(values)-1)
    body = ''
    for i in range(4):
        v = low + (high-low)*i/3
        yy = y(v)
        body += f'<line class="axis" x1="{left}" x2="{right}" y1="{yy:.2f}" y2="{yy:.2f}"/><text x="{left-10}" y="{yy+4:.2f}" text-anchor="end">{v:.0f}</text>'
    if reference:
        value, label = reference
        body += f'<line class="threshold" x1="{left}" x2="{right}" y1="{y(value):.2f}" y2="{y(value):.2f}"/><text x="{right}" y="{y(value)-8:.2f}" text-anchor="end">{e(label)}</text>'
    points = ' '.join(f'{x(i):.2f},{y(v):.2f}' for i,v in enumerate(values))
    body += f'<polyline class="series" points="{points}"/>'
    stride = max(1, (len(values)+4)//5)
    for i,(label,v) in enumerate(zip(labels, values)):
        body += f'<circle class="point" cx="{x(i):.2f}" cy="{y(v):.2f}" r="3"><title>{e(label)}: {e(v)}{e(unit)}</title></circle>'
        if i % stride == 0 or i == len(values)-1:
            body += f'<text x="{x(i):.2f}" y="230" text-anchor="middle">{e(label)}</text>'
    body += f'<text x="{right+10}" y="{y(values[-1])+4:.2f}">{e(values[-1])}</text>'
    return svg_wrap(body)


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


def charts(project):
    slug = project['slug']
    source = project['source']
    if slug == 'birmingham-payments':
        a = chart('Agency payments rose alongside overall spending.', 'Matched period: 1 April–23 July, £m. These categories overlap and must not be added together.',
          bars(['Total · 2025', 'Total · 2026', 'Agency · 2025', 'Agency · 2026'], [559,677,34,43], maximum=800),
          ['Payment group','2025 (£m)','2026 (£m)'], [['All payments',559,677],['Agency staff',34,43]], source)
        b = chart('The tighter rule produces a more selective review list.', 'Candidate payment pairs; the 73 same-day pairs are a subset of the 281 refined matches.',
          bars(['Initial matches','Refined matches','Same-day subset'], [6553,281,73], maximum=8000),
          ['Rule','Candidate pairs'], [['Initial matching rule',6553],['One-off-amount condition',281],['Same-day subset',73]], source)
        return a,b
    if slug == 'platform-housing':
        pairs = [('Communal areas',-9.1),('Kept informed',-7.3),('Neighbourhood',-6.0),('Listen and act',-4.9),('ASB handling',-4.2),('Well maintained',-2.0),('Time taken to repair',-1.5),('Fair treatment',-1.4),('Overall',0.0),('Repairs',1.3),('Safe home',1.4),('Complaints',2.0)]
        a = chart('Overall satisfaction masks gaps in communication and neighbourhood services.', 'Percentage-point gap to the median of 17 large housing associations. Zero means at the median.',
          bars([x[0] for x in pairs],[x[1] for x in pairs],unit=' pts',maximum=5),
          ['Satisfaction measure','Gap to median (percentage points)'],pairs,source)
        b = chart('The recorded repairs population changed sharply.', 'Counts and rates answer different questions. The target remained 28 days; comparability needs confirmation.',
          bars(['Earlier year','Later year'],[90250,13872],maximum=120000),
          ['Measure','Earlier year','Later year'],[['Repairs counted',90250,13872],['Within target (rounded)','92%','62%']],source)
        return a,b
    if slug == 'severn-trent':
        rows = list(csv.DictReader((ROOT/'projects/03_Severn_Trent/outputs/st_yearly_summary.csv').open()))
        years = [r['year'] for r in rows]
        spills = [round(float(r['total_spills'])/1000,1) for r in rows]
        rainfall = [round(float(r['midlands_rain_mm']),1) for r in rows]
        a = chart('Spills fell in 2025; rainfall fell too.', 'Total reported spills, thousands. The separate rainfall chart supplies context without a dual axis.',
          line(years,spills,low=0,high=75),['Year','Reported spills (thousands)'],list(zip(years,spills)),source)
        b = chart('2022 and 2025 had similar annual rainfall.', 'Midlands rainfall, mm. Similar annual totals do not guarantee comparable storm intensity or local conditions.',
          line(years,rainfall,low=0,high=1200),['Year','Rainfall (mm)','Average spills per reliable overflow'],
          [[r['year'],round(float(r['midlands_rain_mm']),1),round(float(r['avg_spills_reliable']),2)] for r in rows],source)
        c = chart('The reliable-monitor comparison also shows improvement.', 'Average spills per overflow with at least 90% monitor operation. The two groups can differ in composition.',
          bars(['2022','2025'],[19.42,15.01],maximum=25),['Year','Average spills per reliable overflow'],[[2022,19.42],[2025,15.01]],source)
        return a+b,c
    labels=['Jul 25','Aug 25','Sep 25','Oct 25','Nov 25','Dec 25','Jan 26','Feb 26','Mar 26','Apr 26','May 26','Jun 26','Jul 26','Aug 26']
    values=[53.6,55.7,59.0,60.6,61.5,61.5,61.2,62.5,68.6,68.4,68.6,68.9,67.3,66.6]
    a = chart('18-week performance improved, then eased after June.', 'UHB incomplete RTT pathways within 18 weeks, %. The March 2026 milestone is shown for context.',
      line(labels,values,low=40,high=80,reference=(65,'Mar 2026 milestone: 65%')),
      ['Month','Within 18 weeks (%)'],list(zip(labels,values)),source)
    b = chart('Referrals increased while clock stops stayed broadly flat.', 'April–August totals. These flows alone do not fully reconcile the change in the waiting-list stock.',
      bars(['Starts · 2025','Starts · 2026','Stops · 2025','Stops · 2026'],[115481,133091,103997,104806],maximum=180000),
      ['Flow','Apr–Aug 2025','Apr–Aug 2026'],[['Clock starts',115481,133091],['Clock stops',103997,104806]],source)
    c = chart('A no-change baseline beat both forecast models.', 'Back-test mean absolute percentage error, %. Lower is better; the models missed the turning point.',
      bars(['No-change baseline','Trend model','Demand/capacity'],[2.5,6.07,8.4],unit='%',maximum=11),
      ['Model','Back-test error (%)'],[['No change',2.5],['Trend',6.07],['Demand and capacity',8.4]],source)
    return a+b,c


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
      <nav class="nav-links" aria-label="Main navigation"><a href="{prefix}index.html#projects">Selected work</a><a href="{prefix}index.html#research">Research</a><a href="{prefix}index.html#about">About</a><a href="{prefix}index.html#contact">Contact ↗</a><button class="theme-button" data-theme-toggle aria-pressed="false" hidden>Dark mode</button></nav>
    </div></header>'''


def footer(prefix=''):
    return f'''<footer class="container site-footer"><p>© 2026 Farouk Yusuf · Birmingham, UK<br>Independent portfolio analyses of published data. Organisation names and marks identify the subjects of the analysis; no affiliation or endorsement is implied.</p><a href="https://github.com/farouk-yusuf/farouk-yusuf.github.io" target="_blank" rel="noopener">Source code ↗</a></footer>'''


def document(title, description, content, prefix=''):
    return f'''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} | Farouk Yusuf</title><meta name="description" content="{e(description)}">
<meta name="theme-color" content="#1b302b"><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{prefix}assets/css/site.css"><script src="{prefix}assets/js/site.js" defer></script></head>
<body>{header(prefix)}{content}{footer(prefix)}</body></html>\n'''.replace('↗', EXTERNAL_ARROW)


def project_card(project, index):
    previews = [
        bars(['2025 YTD','2026 YTD'],[559,677],unit='m',maximum=850,compact=True),
        bars(['Communal areas','Kept informed','Listen and act'],[-9.1,-7.3,-4.9],unit=' pts',maximum=3,compact=True),
        line(['2020','2021','2022','2023','2024','2025'],[61.0,59.7,44.8,60.3,62.1,36.5],high=75),
        bars(['Mar 2026','Aug 2026'],[89544,96303],maximum=125000,compact=True),
    ]
    labels=['Matched-period payments · £m','Gap to large-landlord median · percentage points','Reported spills · thousands','Incomplete RTT pathways · waiting-list size']
    tags=''.join(f'<span class="tag">{e(t)}</span>' for t in project['tools'])
    # A single real anchor makes the entire card accessible by mouse and keyboard.
    return f'''<a class="project-card" data-sector="{e(project['sector'])}" href="case-studies/{project['slug']}.html">
      <div class="card-visual" aria-hidden="true"><p class="card-chart-label">{e(labels[index])}</p>{previews[index]}</div>
      <div class="card-body">{organisation(project)}<h3>{e(project['title'])}</h3><p>{e(project['summary'])}</p><div class="card-bottom"><div class="tags">{tags}</div><span>Read case study <span class="card-arrow" aria-hidden="true">↗</span></span></div></div></a>'''


def home():
    filters=''.join(f'<button type="button" data-filter="{e(s)}" aria-pressed="false">{e(s)}</button>' for s in ['Local government','Housing','Utilities','NHS'])
    cards=''.join(project_card(p,i) for i,p in enumerate(PROJECTS))
    hero_chart=bars(['March 2026','August 2026'],[89544,96303],maximum=125000,compact=True)
    content=f'''<main id="main">
    <section class="hero container"><div class="hero-grid"><div>
      <div class="availability">Birmingham, UK · Open to analyst opportunities</div>
      <h1>Good analysis starts with <em>a closer look.</em></h1>
      <p class="intro">I’m Farouk, a researcher moving into data and performance analysis. I work with messy public data to explain what changed, check what can be trusted, and give teams a useful next step.</p>
      <div class="actions"><a class="button" href="#projects">Explore my work <span aria-hidden="true">↗</span></a><a class="text-link" href="#about">A little about me →</a></div>
      <p class="hero-note">SQL · Python · Excel · Power BI · A research background that makes me question the first answer.</p>
    </div><aside class="evidence-card" aria-label="A finding from my NHS analysis"><div class="paper"><div class="paper-top"><span>A closer look / 04</span><span>NHS performance</span></div><h2>A recovery worth protecting.</h2>{hero_chart}<p class="paper-note">UHB’s waiting list grew 7.5% after March. I looked at referrals and completed pathways to understand the pressure.</p><a class="text-link" href="case-studies/uhb-waiting-times.html">Read the analysis →</a></div><div class="evidence-footer"><span>Public data. Independent analysis.</span><span>Apr 2023–Aug 2026</span></div></aside></div></section>
    <div class="container skills-row"><strong>Evidence before conclusions</strong><span>Local government</span><span>Social housing</span><span>Regulated utilities</span><span>NHS performance</span></div>
    <section class="section container" id="projects"><div class="section-heading"><div><span class="eyebrow">01 / Selected work</span><h2>Behind the headline number.</h2></div><p>Four independent projects on UK public data. Each follows a question through to a practical recommendation.</p></div>
    <div class="filter-row" data-project-filters role="group" aria-label="Filter projects by sector" hidden><button type="button" data-filter="all" aria-pressed="true">All projects</button>{filters}</div><p class="sr-only" data-filter-status role="status" aria-live="polite">4 projects shown</p><div class="project-grid">{cards}</div><p class="project-caption">Each case study includes methods, limitations and the original analysis files. Power BI dashboards are being developed separately.</p></section>
    <section class="section container" id="research"><div class="research-feature"><div><span class="eyebrow">02 / Research that shaped my approach</span><h2>The disagreement changed my research.</h2><p>During my PhD, I tested human and AI coding before applying it to a corpus of 29,182 cleaned social media posts about leaving Nigeria.</p><p class="quote">The average looked reassuring. The question-level breakdown told a more complicated story.</p><p>I investigated disagreements, revised the coding rules and set aside a finer scheme when the pilot proved unstable.</p><div class="actions"><a class="button" href="case-studies/research-validation.html">Explore the research <span aria-hidden="true">↗</span></a></div></div><div class="research-proof"><div class="proof-line"><strong>Test the measurement.</strong><span>A question had drifted from the theory it was meant to capture.</span></div><div class="proof-line"><strong>Make the workflow usable.</strong><span>I built a coding app with saved progress and CSV export.</span></div><div class="proof-line"><strong>Keep the uncertainty visible.</strong><span>Some questions performed poorly despite strong overall agreement.</span></div></div></div></section>
    <section class="section container" id="about"><div class="about-grid"><div class="about-copy"><span class="eyebrow">03 / A little about me</span><h2>Curiosity, fieldwork<br>and a habit of checking.</h2><p>I’m completing a PhD in International Development at the University of Birmingham, with my viva pending. My research examines why skilled Nigerians migrate to the UK.</p><p>I taught myself Python during the PhD and learned SQL for the council payments project. I enjoy the point where a technical check changes the explanation you would give someone.</p><p>I’m interested in analyst roles in performance reporting, data quality and public-service insight. My toolkit includes SQL, Python, Excel and Power BI, alongside research design and communicating with different audiences.</p><div class="actions"><a class="text-link" href="https://www.linkedin.com/in/farouk-yusuf-fy" target="_blank" rel="noopener">Experience on LinkedIn ↗</a></div></div><ul class="experience-list"><li><small>Communication / NatCen</small><strong>English Housing Survey interviewer</strong><p>Achieved a 67% response rate against a 30% programme benchmark, September 2024–January 2025.</p></li><li><small>Learning / Research and technical training</small><strong>From social research to analytical tools</strong><p>MA Social Research, MSc with Distinction, Oxford’s ESRC-funded LLM Spring School, and a Data and AI Skills Bootcamp.</p></li><li><small>Building / uHired</small><strong>Co-founded a job-search platform</strong><p>1,025 users since its April 2026 launch, with no paid marketing. I tracked usage with Google Analytics and Google Sheets.</p></li><li><small>Evaluation / Outlier</small><strong>Testing language-model responses</strong><p>Since March 2026, I have written prompts designed to expose errors and assessed responses against guidelines.</p></li></ul></div></section>
    <section class="section container" id="contact"><div class="contact"><div><span class="eyebrow">Let’s talk</span><h2>Bring a closer look to your team.</h2><p>I’m open to data analyst, performance and insight opportunities.</p></div><div><p><a href="mailto:faroukyusuf.code@gmail.com">faroukyusuf.code@gmail.com</a></p><div class="actions"><a class="button" href="https://www.linkedin.com/in/farouk-yusuf-fy" target="_blank" rel="noopener">Connect on LinkedIn <span aria-hidden="true">↗</span></a></div></div></div></section>
    </main>'''
    emit('index.html', document('Data & performance analyst portfolio','Farouk Yusuf, Birmingham-based researcher moving into data analysis. Explore independent SQL, Python and Excel projects in NHS performance, housing, utilities and council finance.',content))


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
    first_chart,second_chart=charts(project)
    metrics=''.join(f'<div class="metric"><strong>{e(v)}</strong><span>{e(label)}</span></div>' for v,label in project['metrics'])
    actions=''.join(f'<h3>{e(owner)}</h3>{paragraph(action)}' for owner,action in project['actions'])
    dashboard=''
    if project['dashboard'] and (ROOT/'assets'/project['dashboard']).exists():
        # Keep the existing image paths and hide-if-missing behaviour. Do not invent dashboards.
        dashboard=f'<figure class="dashboard-preview" data-image-container><img data-optional-image src="../assets/{e(project["dashboard"])}" alt="{e(project["organisation"])} Power BI dashboard" loading="lazy"><figcaption>Power BI dashboard preview</figcaption></figure>'
    body=section('brief','The decision this analysis supports.',paragraph(project['brief']))
    body+=section('findings','What a closer look revealed.',paragraph(project['finding'])+first_chart+f'<div class="callout"><h3>My recommendation</h3>{paragraph(project["decision"])}</div>')
    body+=section('detail',project['secondary_title'],paragraph(project['secondary'])+second_chart)
    body+=section('method','How I built and checked it.',list_html(project['methods'],ordered=True))
    body+=section('actions','What I would ask the team to do next.',actions)
    body+=section('limitations','Where the evidence stops.',list_html(project['limitations'])+f'<div class="callout"><h3>What I learned</h3>{paragraph(project["reflection"])}</div>')
    body+=section('files','Explore the work behind the story.',paragraph('These are the original write-ups, scripts and workbook. Their links are preserved from the previous site. The analysis is presented as a portfolio exercise; recommendations have not been implemented or evaluated by these organisations.')+resources(project)+f'<h3>Power BI dashboard</h3>{paragraph(project["dashboard_plan"])}'+dashboard)
    nav=''.join(f'<a href="#{id_}">{title}</a>' for id_,title in [('brief','The brief'),('findings','Key findings'),('detail','A deeper look'),('method','Method and checks'),('actions','Recommendations'),('limitations','Limitations'),('files','Files and dashboard')])
    next_project=PROJECTS[(index+1)%len(PROJECTS)]
    content=f'''<main class="container" id="main"><div class="breadcrumb"><a href="../index.html#projects">Selected work</a> / {e(project['sector'])}</div><div class="case-hero">{organisation(project,'../')}<span class="eyebrow">Independent public-data case study</span><h1>{e(project['title'])}</h1><p class="lead">{e(project['summary'])}</p><div class="case-meta"><span><strong>For:</strong> {e(project['audience'])}</span><span>{e(project['period'])}</span><span>{e(' · '.join(project['tools']))}</span></div></div><div class="metric-grid">{metrics}</div><div class="case-layout"><nav class="case-nav" aria-label="On this page"><strong>Inside the analysis</strong>{nav}</nav><div class="case-content">{body}</div></div><div class="next-project"><a class="text-link" href="../index.html#projects">← All projects</a><a class="button" href="{next_project['slug']}.html">Next: {e(next_project['organisation'])} <span aria-hidden="true">→</span></a></div></main>'''
    emit(f'case-studies/{project["slug"]}.html', document(project['organisation']+' analysis',project['summary'],content,'../'))


def research():
    chart_html=chart('Overall reliability passed the target; individual questions did not.', 'Selected Krippendorff’s alpha results from the 500-post validation sample. These are different comparisons, rather than a complete question-level series.',
      bars(['Human–human overall','AI–human overall','Human–human Q7','AI–human Q9'],[0.758,0.807,0.484,0.445],maximum=1.05,reference=.70),
      ['Comparison','Krippendorff’s alpha'],[['Human–human overall',.758],['AI–human overall',.807],['Human–human Q7',.484],['AI–human Q9',.445]],
      'Author’s unpublished thesis validation results, as provided in the portfolio handoff. Exact figures remain subject to supervisor sign-off.')
    body=section('question','Could AI help code research data reliably?',paragraph('My PhD investigates why skilled Nigerians migrate to the UK. To analyse a corpus of 29,182 cleaned social media posts about leaving Nigeria, I needed ten yes/no coding questions grounded in my theoretical framework. Before scaling up, I tested whether humans and AI interpreted those questions consistently.'))
    body+=section('validation','The breakdown changed the next step.',paragraph('Two human coders worked through a 100-post pilot and 400 further posts. ChatGPT and Gemini were tested as proxy coders. Overall agreement was 88.5% for the human–human comparison and 90.8% for AI–human, while overall alpha cleared the 0.70 target. The weaker question-level results meant that the average was insufficient grounds to trust every part of the scheme.')+chart_html)
    body+=section('revision','I had to revisit what the questions measured.',paragraph('Human disagreements concentrated on Q1, Q3, Q7 and Q8. Q3, the spatial-horizon question, had drifted from the theoretical concept it was meant to capture. I corrected it and refined the codebook across versions v1.1 to v3.3.')+paragraph('Q3 also illustrated a measurement trap: 99.7% raw agreement coexisted with alpha of 0.000 because nearly every answer was “no”. A high agreement percentage was therefore a poor standalone guide to reliability.')+paragraph('I built a coding app that presented one question at a time, saved progress and exported CSV files. A finer instance-level scheme was piloted on 40 posts and set aside when it proved unstable.'))
    body+=section('learning','What I take into analyst work.',paragraph('I learned to treat disagreement as evidence about the measurement process. Before trusting a KPI or classifier, I want to know whether its definition is clear, whether important groups fail, and whether the headline metric disguises a weak component.')+f'<div class="callout"><h3>Publication status</h3>{paragraph("These are unpublished thesis results. Exact figures shown here were already included in the portfolio revision and remain subject to supervisor sign-off before formal publication. The page does not publish raw posts or participant-level data.")}</div>')
    content=f'''<main class="container" id="main"><div class="breadcrumb"><a href="../index.html#research">Research</a> / Coding validation</div><div class="case-hero"><span class="eyebrow">Doctoral research / University of Birmingham</span><h1>The coders disagreed.<br>That was a finding worth following.</h1><p class="lead">A validation study taught me why a reassuring average can hide a measurement problem, and why revising the question can matter more than changing the model.</p><div class="case-meta"><span>International Development PhD · Viva pending</span><span>Python · Research design · Reliability testing</span></div></div><div class="case-layout"><nav class="case-nav" aria-label="On this page"><strong>Inside the research</strong><a href="#question">The question</a><a href="#validation">Validation</a><a href="#revision">Revising the scheme</a><a href="#learning">Lessons and limitations</a></nav><div class="case-content">{body}</div></div><div class="next-project"><a href="../index.html#research">← Back to portfolio</a><a class="button" href="birmingham-payments.html">Explore the public-data projects →</a></div></main>'''
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
