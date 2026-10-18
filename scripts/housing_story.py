"""Platform Housing's narrative, using committed analytical outputs as evidence."""
import csv
from decimal import Decimal
import json
from pathlib import Path
import re
from statistics import median

from story_components import e, p, source_link, disclosure, note, metric
from story_workbook import read_sheet

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT/'projects/02_Platform_Housing'
WORKBOOK = PROJECT/'outputs/Platform_TSM_Benchmarking_Pack.xlsx'
SOURCE = 'projects/02_Platform_Housing/'
CURRENT = 'Platform 2024/25'
PREVIOUS = 'Platform 2023/24'
MEDIAN = 'Large HA median (>40k homes)'
GAP = 'Gap to large HA median'


def evidence_data():
    benchmark = read_sheet(WORKBOOK, 'Benchmark')
    satisfaction = [r for r in benchmark if r['Measure'].startswith('TP')]
    peers = read_sheet(WORKBOOK, 'Ombudsman peers')
    platform = next(r for r in peers if r['landlord'] == 'Platform Housing Group Limited')
    other_peers = [r for r in peers if r is not platform]
    categories = read_sheet(WORKBOOK, 'Ombudsman categories')
    checks = read_sheet(WORKBOOK, 'Year-on-year checks')
    # Counts are recorded as prose in the existing workbook; retain that lineage.
    repair_counts = [int(n.replace(',', '')) for n in re.findall(r'\d[\d,]*', checks[0]['What the underlying counts show'])[:2]]
    figures = {r['']: r['value'] for r in csv.DictReader((PROJECT/'outputs/key_figures.csv').open())}
    return dict(benchmark=benchmark, satisfaction=satisfaction,
                measures={r['Measure'].split(' ')[0]:r for r in satisfaction},
                drivers=read_sheet(WORKBOOK, 'Satisfaction drivers'),
                methods=read_sheet(WORKBOOK, 'Survey method'), checks=checks,
                repair=next(r for r in benchmark if r['Measure'].startswith('RP02 1 ')),
                repair_counts=repair_counts, platform=platform, peers=peers,
                peer_median=median(Decimal(r['mal_rate_2025_26']) for r in other_peers),
                categories=categories, figures=figures)


def n(value, places=1):
    return f'{Decimal(str(value)):,.{places}f}'


def bars(rows, maximum=100, *, percent=True):
    """Readable HTML bars with a common zero baseline and explicit units."""
    result = []
    for label, value, focus in rows:
        display = n(value)+'%' if percent else n(value, 0)
        result.append(f'<li class="finance-bar-row"><div class="finance-bar-label"><span>{e(label)}</span><strong>{display}</strong></div><div class="finance-bar-track" aria-hidden="true"><span class="finance-bar {"finance-bar--focus" if focus else ""}" style="width:{float(value)/maximum*100:.3f}%"></span></div></li>')
    return '<ul class="finance-bars">'+''.join(result)+'</ul>'


def gap_bars(rows, focus):
    result = []
    # Fixed, shared scale of -10 to +3 percentage points; zero is 10/13 across.
    for row in sorted(rows, key=lambda r:Decimal(r[GAP])):
        value = Decimal(row[GAP])
        code, label = row['Measure'].split(' ', 1)
        left = (10+min(0, value))/13*100
        width = abs(value)/13*100
        display = ('+' if value>0 else '−' if value<0 else '')+n(abs(value))+' pts'
        result.append(f'<li class="finance-bar-row"><div class="finance-bar-label"><span>{e(label.replace("ASB handling", "Anti-social behaviour handling"))}</span><strong>{display}</strong></div><div class="finance-bar-track finance-bar-track--diverging" style="--zero:76.923%" aria-hidden="true"><span class="finance-bar {"finance-bar--focus" if code in focus else ""}" style="left:{float(left):.3f}%;width:{float(width):.3f}%"></span></div></li>')
    return '<p class="finance-axis-note"><span>Below peer median ←</span><span>→ Above peer median</span></p><ul class="finance-bars">'+''.join(result)+'</ul>'


def code_excerpt(filename, start, end=None):
    code = (PROJECT/'scripts'/filename).read_text()
    excerpt = code[code.index(start):]
    if end:
        excerpt = excerpt[:excerpt.index(end)]
    return f'<pre tabindex="0" role="region" aria-label="Code excerpt"><code>{e(excerpt.strip())}</code></pre>'


def render(project, next_project, *, chart, table, organisation, resources):
    copy = json.loads((ROOT/'site/platform.json').read_text())
    data = evidence_data()
    sections, headings = [], []

    def section(identifier, title, body):
        headings.append((identifier,title))
        sections.append(f'<section class="finance-section" id="{identifier}" aria-labelledby="{identifier}-heading"><div class="finance-section-heading"><span class="finance-step" aria-hidden="true">{len(headings):02d}</span><h2 id="{identifier}-heading">{e(title)}</h2></div>{body}</section>')

    summary = '<aside class="requirements-card" aria-label="Requirements summary"><span class="practice-label">Requirements summary</span><dl>'+''.join(f'<div><dt>{e(label)}</dt><dd>{e(text)}</dd></div>' for label,text in copy['requirements_summary'])+'</dl></aside>'
    framework = copy['requirements_template']
    items = ''.join(f'<li><div class="framework-item-heading"><h3>{e(item["element"])}</h3><span class="framework-status framework-status--{e(item["state"])}">{e(item["status"])}</span></div><dl><div><dt>Framework prompt</dt><dd>{e(item["prompt"])}</dd></div><div><dt>Project application</dt><dd>{e(item["application"])}</dd></div></dl></li>' for item in framework['items'])
    template = disclosure('See my requirements elicitation template',p(framework['intro'])+'<ol class="framework-items">'+items+'</ol>',css_class='requirements-template')
    section('brief','Requirements and scope','<span class="scenario-label">Simulated workplace brief</span>'+p(copy['brief'])+p(copy['requirements_intro'])+summary+template)

    access = table(['Dataset','Data owner','Analytical purpose','Availability'],copy['data_requests'],'Data access assessment')
    flow = '<ol class="etl-flow" aria-label="ETL and reporting workflow">'+''.join(f'<li><strong>{e(label)}</strong><span>{e(text)}</span></li>' for label,text in [('Extract','Regulatory spreadsheets and Ombudsman PDFs'),('Transform','Standard fields, numeric values and landlord identifiers'),('Validate','Compare measures, counts and category totals'),('Report','Peer benchmarks and an Excel board pack')])+'</ol>'
    links = '<p class="inline-source">Public sources: <a href="https://www.gov.uk/government/statistics/tenant-satisfaction-measures-202425" target="_blank" rel="noopener">Regulator of Social Housing · TSM 2024/25 ↗</a> and <a href="https://www.housing-ombudsman.org.uk/landlords/" target="_blank" rel="noopener">Housing Ombudsman landlord reports ↗</a>. File-level sources and access dates are in the downloadable source log.</p>'
    extraction = p('The Python pipeline converts spreadsheet fields to numeric values, joins survey and management returns by landlord and extracts headline and category tables from PDF reports. ETL means extract, transform and load: turning the source publications into consistent tables for analysis.')+flow
    extraction += disclosure('Spreadsheet selection and PDF extraction',source_link(SOURCE+'scripts/02_tsm_benchmark.py','TSM preparation and benchmark script')+source_link(SOURCE+'scripts/01_extract_ombudsman.py','Ombudsman PDF extraction script'))
    section('data','Data requirements and preparation',p(copy['data_intro'])+access+links+extraction)

    overall = data['measures']['TP01']
    benchmark_rows = [['Platform · 2023/24',n(overall[PREVIOUS])],['Platform · 2024/25',n(overall[CURRENT])],['Large-landlord median · 2024/25',n(overall[MEDIAN])]]
    overall_chart = chart('Overall satisfaction improved, but only reached the peer median','Percentage satisfied. The primary cohort contains 17 housing associations with more than 40,000 homes, including Platform.',bars([(label,Decimal(value),i==1) for i,(label,value) in enumerate(benchmark_rows)])+'<p class="chart-annotation"><strong>64.6% satisfied</strong>, up from 62.6% a year earlier. Improvement does not mean Platform is ahead of similar landlords.</p>',['Landlord / period','Overall satisfaction (%)'],benchmark_rows,'Benchmark worksheet · TP01. Published landlord-level survey measures, not a matched panel of tenants.')
    cohort_proof = code_excerpt('02_tsm_benchmark.py','cur = tsm[','# ---- benchmark table')+source_link(SOURCE+'scripts/02_tsm_benchmark.py','Peer-cohort definitions')
    method_rows = [[r['Predominant collection method'],r['Landlords'],n(r['Median overall satisfaction'])] for r in data['methods']]
    method_proof = table(['Predominant survey method','Landlords','Median satisfaction (%)'],method_rows,'Survey-method comparison across the full published dataset')
    section('comparison','A relevant peer group changes the interpretation',p('I selected large housing associations as the main comparator rather than treating every Midlands landlord as equivalent. Platform’s 64.6% overall satisfaction matches the large-landlord median; the broader Midlands housing-association median is 77.4%. The choice changes the comparison materially, so the cohort must be visible.')+overall_chart+note('Comparability check',f'Platform reported {int(float(data["figures"]["platform_sample"])):,} survey responses and predominantly used telephone interviews. Telephone was also the most common method across the published dataset. The primary cohort was not restricted to telephone surveys: method, tenant mix and response differences can still affect comparisons.')+disclosure('Peer selection and survey-method checks',cohort_proof+method_proof))

    focus = [r[0] for r in copy['priorities']]
    gap_rows = [[r['Measure'],n(r[CURRENT]),n(r[MEDIAN]),n(r[GAP]),r['Quartile vs large HAs'],r['Large HAs compared']] for r in sorted(data['satisfaction'],key=lambda r:Decimal(r[GAP]))]
    gaps = chart('Communication and neighbourhood scores trail the headline result','Gap to the large-landlord median in percentage points. Green highlights the three recommended starting priorities; grey retains the wider service picture.',gap_bars(data['satisfaction'],focus)+'<p class="chart-annotation">For keeping tenants informed, <strong>61.8% were satisfied versus 69.1% at the peer median</strong>: about seven fewer satisfied tenants in every 100. This is a comparison of survey percentages, not a count of individual tenants.</p>',['Measure','Platform satisfied (%)','Peer median (%)','Gap (percentage points)','Quartile','Landlords compared'],gap_rows,'Benchmark worksheet · TP01–TP12. All 12 measures have 17 landlords in this workbook.')
    section('gaps','The overall score conceals specific service gaps',p('Six of the twelve tenant-satisfaction measures sit in the bottom quarter of the large-landlord cohort. Communal areas show the largest shortfall: 55.4% satisfied against a 64.5% peer median. Communication, listening and neighbourhood services also warrant attention.')+gaps+p('Performance is mixed. Repairs-service satisfaction is above the peer median, as is satisfaction with home safety. Separately, operational returns record 100% completion for five building-safety checks and 98.2% of emergency repairs within target. Compliance and tenant perceptions answer different questions; neither should substitute for the other.'))

    driver_index = {r['Measure'].split(' ')[0]:r for r in data['drivers']}
    priority_rows = [[label,n(data['measures'][code][GAP])+' pts',n(driver_index[code]['Correlation with overall satisfaction'],2),action] for code,label,action in copy['priorities']]
    priorities = table(['Starting priority','Gap to median','Association with overall satisfaction (r)','Proposed service review'],priority_rows,'Recommended priorities and their analytical basis')
    correlations = table(['Satisfaction measure','Correlation with overall satisfaction (r)','Platform gap (percentage points)','Rule-based flag'],[[r['Measure'],n(r['Correlation with overall satisfaction'],2),n(r['Platform gap to large HA median (pts)']),r['Priority'] or 'Not flagged'] for r in data['drivers']],'All service-score associations and screening flags')
    driver_proof = p('The script uses complete landlord rows across all twelve survey measures, calculates Pearson correlations and flags measures with a correlation of at least 0.80 and a negative Platform gap. Five measures meet that screening rule. The three recommendations above are an analyst-selected starting set, not an automatic or cost-optimised ranking.')+code_excerpt('02_tsm_benchmark.py','drv =','# ---- survey method')+correlations+source_link(SOURCE+'scripts/02_tsm_benchmark.py','Association calculations and screening rule')
    section('priorities','Listening, communication and maintenance are starting priorities',p(copy['priorities_intro'])+priorities+note('Statistical interpretation','A correlation near 1 means landlord-level scores tend to move together. It does not show how an individual tenant would respond, establish causation or estimate the benefit of an intervention. Tenant mix and other unmeasured differences may contribute to these associations.')+p('Communal areas still need a local review because the shortfall is the largest. Fair treatment and repair time also meet the screening rule. Final priorities would depend on tenant feedback, urgency, cost and service capacity; those inputs are unavailable here.')+disclosure('Association method and full screening results',driver_proof))

    repair = data['repair']
    repair_rates = [('2023/24',Decimal(repair[PREVIOUS]),False),('2024/25',Decimal(repair[CURRENT]),True)]
    rate_chart = chart('Reported repair timeliness fell from 91.7% to 62.3%','Non-emergency repairs completed within target. The recorded target remained 28 days.',bars(repair_rates),['Year','Within target (%)'],[[label,n(value)] for label,value,_ in repair_rates],'Benchmark worksheet · RP02 1; Year-on-year checks worksheet.')
    counts = data['repair_counts']
    count_chart = chart('The number of repairs counted fell by about 85%','Recorded repair counts underlying the year-on-year check. This population change needs reconciliation alongside the rate.',bars([('2023/24',counts[0],False),('2024/25',counts[1],True)],maximum=100000,percent=False)+'<p class="chart-annotation"><strong>Reconcile the population before explaining the rate.</strong> A stable target does not establish consistent inclusion rules.</p>',['Year','Repairs counted'],[['2023/24',counts[0]],['2024/25',counts[1]]],'Year-on-year checks worksheet · underlying counts recorded in the original analysis.')
    check_rows = [[r['Measure'],r['Platform 2023/24 -> 2024/25'],r['What the underlying counts show']] for r in data['checks']]
    checks_proof = table(['Measure','Published movement (rounded)','Underlying count check'],check_rows,'Year-on-year checks recorded in the workbook')+p('The existing workbook suggests possible recording changes. The evidence does not settle that explanation: genuine service changes remain possible. I would ask owners to reconcile both years rather than remove the decline from the board narrative.')+source_link(SOURCE+'outputs/03_Website_Validation_Notes.md','Validation notes and unresolved checks')
    section('validation','Repair counts need reconciliation before a performance conclusion',p('I checked the underlying counts before interpreting the decline. The rate fell by 29.4 percentage points, while the repairs counted fell from 90,250 to 13,872. This combination raises a comparability question; it does not prove a recording error or rule out a real deterioration.')+rate_chart+count_chart+note('Data validation and escalation','Request job-level totals by year, repair type, completion status and inclusion rule from Repairs. Build a bridge from the earlier population to the later one, confirm the 28-day definition and then quantify any remaining performance change.')+p('The same review identified large increases in recorded anti-social behaviour cases and stage-one complaints. Higher recorded volumes can reflect worsening experience, broader recording or both; the service owners need to establish which explanation fits.')+disclosure('Repair, anti-social behaviour and complaint checks',checks_proof))

    categories = sorted(data['categories'],key=lambda r:Decimal(r['Platform upheld']),reverse=True)
    category_rows = [[r['category'],int(r['Platform findings']),int(r['Platform upheld'])] for r in categories]
    label_map = {'Responsive repairs/activity':'Responsive repairs','Managing Relations':'Managing relations'}
    category_chart = chart('Responsive repairs account for the most adverse findings','Housing Ombudsman reports labelled 2025/26. “Upheld” combines service failure, maladministration and severe maladministration in this analysis.',bars([(label_map.get(r['category'],r['category']),int(r['Platform upheld']),i==0) for i,r in enumerate(categories[:3])],maximum=25,percent=False)+'<p class="chart-annotation"><strong>23 of the 43 repairs findings were adverse.</strong> The 43 is the total for the repairs category, not the total number of adverse findings across Platform.</p>',['Category','Total findings','Adverse findings'],category_rows,'Ombudsman categories worksheet. Bars show the three largest adverse-finding counts; the table includes all categories.')
    om = data['platform']
    extracted_rate = Decimal(om['mal_findings'])/Decimal(om['findings'])*100
    headline_rows = [['Headline rate recorded in extraction',n(om['mal_rate_2025_26'])+'%'],['Median recorded rate for the other 20 landlords',n(data['peer_median'])+'%'],['Platform extracted adverse / total findings',f'{om["mal_findings"]} / {om["findings"]}'],['Rate calculated directly from those counts',n(extracted_rate)+'%'],['Platform category totals',str(sum(int(r['Platform findings']) for r in categories))],['Platform category adverse findings',str(sum(int(r['Platform upheld']) for r in categories))]]
    om_proof = table(['Reconciliation item','Value'],headline_rows,'Ombudsman headline and category reconciliation')+p('Platform’s category counts reconcile to its extracted headline counts. However, 51 divided by 137 gives 37.2%, which does not reproduce the recorded 38% headline rate. The source PDF and rate denominator must be checked. The original decisions note also records small category-extraction differences for four other landlords; these remain unresolved.')+code_excerpt('01_extract_ombudsman.py','# check: category totals reconcile')+source_link(SOURCE+'scripts/01_extract_ombudsman.py','PDF extraction and reconciliation diagnostic')
    section('complaints','Complaint findings reinforce the need to investigate repairs',p('I examined Ombudsman findings as a second source of service evidence. These concern escalated complaints, not a representative sample of tenants, and cover reports labelled 2025/26 rather than the 2024/25 satisfaction return. They provide context, not a direct validation of the survey result.')+category_chart+note('Reconciliation outstanding','The extraction records a 38% headline rate and a 56.5% median for the other 20 landlords. Its counts do not reproduce Platform’s rate, so I would hold the rate and ranking from a formal board conclusion until verified against the original report. The category analysis remains provisional pending that check.')+disclosure('Ombudsman counts, rates and extraction checks',om_proof))

    actions = table(['Action owner','Recommended action','Proposed success measure'],copy['actions'],'Recommended investigations and proposed measures')
    section('actions','Recommendations and proposed measures',p('The completed output is an evidence-backed benchmark and a focused investigation plan. It identifies service gaps and reporting questions; it does not establish delivered savings or a measured improvement in tenant satisfaction.')+actions)

    download = '<div class="actions"><a class="button" href="../projects/02_Platform_Housing/outputs/Platform_TSM_Benchmarking_Pack.xlsx" download>Download the Excel benchmark pack <span aria-hidden="true">↓</span></a></div>'
    limitations = disclosure('Scope and interpretation limits',p('Only published aggregates are available. Survey method and tenant mix are not controlled, year-on-year respondents may differ, and correlation is across landlords. The TSM and Ombudsman cohorts and periods differ. Repair definitions and the Ombudsman rate discrepancy require follow-up. Raw inputs are not committed, so website checks verify existing outputs rather than rerunning or independently verifying the original source analysis.'))
    section('files','Deliverables and supporting files',p('The workbook contains the benchmark, service-score associations, survey-method comparison, Ombudsman tables and year-on-year checks. Review the validation note alongside the original outputs.')+download+resources(project)+source_link(SOURCE+'outputs/03_Website_Validation_Notes.md','Website evidence review and outstanding checks')+limitations+'<h3>Power BI · planned reporting view</h3>'+p(copy['dashboard']))

    nav = ''.join(f'<a href="#{identifier}"><span aria-hidden="true">{i:02d}</span>{e(title)}</a>' for i,(identifier,title) in enumerate(headings,1))
    icons = ''.join(f'<span><img src="../assets/icons/{icon}" width="22" height="22" alt="">{name}</span>' for name,icon in [('Python','python.svg'),('Excel','excel.svg'),('Statistics','statistics.svg')])
    metrics = metric('64.6%','overall satisfaction · level with the large-landlord median')+metric('6 of 12','satisfaction measures in the bottom quarter of the cohort')+metric('7 fewer','satisfied tenants per 100 on communication, compared with the peer median')
    return f'''<main class="container finance-case housing-case" id="main"><div class="breadcrumb"><a href="../index.html#projects">Selected projects</a> / Social housing</div>
    <header class="finance-hero">{organisation(project,'../')}<span class="eyebrow">Tenant experience &amp; service performance</span><h1>{e(copy['title'])}</h1><p class="lead">{e(copy['summary'])}</p><div class="finance-meta"><span>TSM 2023/24–2024/25 · Ombudsman reports 2025/26</span><span>My role: independent analyst</span><div class="finance-tools">{icons}</div></div></header>
    <aside class="scenario-note" aria-label="About this case study"><strong>About this case study</strong>{p(copy['scenario_note'])}</aside><div class="finance-metrics" aria-label="Results at a glance">{metrics}</div>
    <div class="finance-layout"><nav class="finance-nav" aria-label="On this page"><strong>Follow the analysis</strong>{nav}</nav><div class="finance-content">{''.join(sections)}</div></div>
    <div class="next-project"><a href="../index.html#projects">← All projects</a><a class="button" href="{e(next_project['slug'])}.html">Next: {e(next_project['organisation'])} <span aria-hidden="true">→</span></a></div></main>'''
