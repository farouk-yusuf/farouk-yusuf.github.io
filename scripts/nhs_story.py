"""UHB's performance brief, built from the committed RTT report and source code."""
import csv
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path
import re

from story_components import e, p, source_link, disclosure, note, metric, requirements_panels, horizontal_bars
from story_workbook import read_sheet
from story_charts import line_chart, paired_dots, balance_waterfall, comparison_lines

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT/'projects/04_UHB_Waiting_Times'
SOURCE = 'projects/04_UHB_Waiting_Times/'
WORKBOOK = PROJECT/'outputs/UHB_RTT_Performance_Report.xlsx'


def d(value):
    return Decimal(str(value))


def n(value, places=0):
    return f'{d(value):,.{places}f}'


def evidence_data():
    trend = read_sheet(WORKBOOK,'Trust trend',index_header='month')
    months = {r['month']:r for r in trend}
    specialties = read_sheet(WORKBOOK,'Specialties',index_header='specialty')
    mixed = read_sheet(WORKBOOK,'Forecast back-test')
    backtest = [r for r in mixed if re.fullmatch(r'\d{4}-\d{2}',r['Month'])]
    errors = {r['Month']:d(r['Actual']) for r in mixed if r['Month'] not in ('Model',) and r not in backtest}
    period = [r for r in trend if '2026-04'<=r['month']<='2026-08']
    opening,closing = d(months['2026-03']['waiting_list']),d(months['2026-08']['waiting_list'])
    starts,stops = [sum(d(r[field]) for r in period) for field in ('clock_starts','clock_stops')]
    with (PROJECT/'outputs/key_figures.csv').open() as stream:
        figures = {r['']:r['value'] for r in csv.DictReader(stream)}
    return dict(trend=trend,months=months,specialties=specialties,
                specialty={r['specialty']:r for r in specialties},
                benchmark=read_sheet(WORKBOOK,'Benchmark'),backtest=backtest,errors=errors,
                scenario=read_sheet(WORKBOOK,'Forecast',index_header='month'),
                checks=read_sheet(WORKBOOK,'Data checks'),figures=figures,
                opening=opening,closing=closing,starts=starts,stops=stops,
                residual=closing-opening-starts+stops,period=period)


def code_excerpt(filename,start,end=None):
    text = (PROJECT/'scripts'/filename).read_text()
    excerpt = text[text.index(start):]
    if end:
        excerpt = excerpt[:excerpt.index(end)]
    return f'<pre tabindex="0" role="region" aria-label="Code excerpt"><code>{e(excerpt.strip())}</code></pre>'


def month_label(value):
    return datetime.strptime(value,'%Y-%m').strftime('%b %y')


def render(project,next_project,*,chart,table,organisation,resources):
    copy = json.loads((ROOT/'site/uhb.json').read_text())
    data = evidence_data()
    months,latest = data['months'],data['trend'][-1]
    sections,headings = [],[]

    def section(identifier,title,body):
        headings.append((identifier,title))
        sections.append(f'<section class="finance-section" id="{identifier}" aria-labelledby="{identifier}-heading"><div class="finance-section-heading"><span class="finance-step" aria-hidden="true">{len(headings):02d}</span><h2 id="{identifier}-heading">{e(title)}</h2></div>{body}</section>')

    section('brief','Requirements and reporting scope','<span class="scenario-label">Simulated workplace brief</span>'+p(copy['brief'])+p(copy['requirements_intro'])+requirements_panels(copy))

    requests = table(['Dataset','Data owner','Analytical purpose','Availability'],copy['data_requests'],'Data access assessment')
    flow = '<ol class="etl-flow" aria-label="Data preparation workflow">'+''.join(f'<li><strong>{e(label)}</strong><span>{e(text)}</span></li>' for label,text in [('Extract','Read 41 monthly national files in chunks'),('Aggregate','Sum commissioner rows to provider and specialty'),('Validate','Review totals, missing months and clock starts'),('Report','Trends, specialty priorities and model checks')])+'</ol>'
    sources = '<p class="inline-source">Sources: <a href="https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/rtt-data-2026-27/" target="_blank" rel="noopener">NHS England RTT monthly data ↗</a> and <a href="https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/rtt-statistics-user-guidance/" target="_blank" rel="noopener">RTT definitions and guidance ↗</a>. Earlier monthly releases and file versions are recorded in the source log.</p>'
    schema = table(['Source field / row','Handling in the extraction','Reporting implication'],[
        ['Part_2 · Total','The original analysis found this field blank; sum the weekly wait bands instead.','Known-clock-start incomplete pathways form the denominator.'],
        ['Total All and unknown clock starts','Retain both source fields for validation.','A source-row reconciliation is still required before operational release.'],
        ['Commissioner and specialty rows','Aggregate across commissioners; use the Total treatment-function row separately.','Avoid adding the trust-total row to its component specialties.']
    ],'Source-schema decisions behind the waiting-list measure')
    extraction_proof = code_excerpt('01_extract.py','            wk =','        res =')+source_link(SOURCE+'scripts/01_extract.py','Chunked extraction and weekly-band aggregation')
    checks = table(['Recorded check','Result'],[[r['Check'],r['Result']] for r in data['checks']],'Checks retained in the Excel report')
    validation = p('The committed trend contains 41 UHB observations and zero unknown clock starts. The report records no missing provider-months across the selected trusts and England. These checks do not establish that every source row is complete. I also reconciled the latest specialty totals to the trust total when preparing this page.')+checks+p('The corrected extractor computes weekly-band totals but does not enforce a row-level assertion against Total All. That reconciliation, and the reasons behind the stock-flow residual, remain operational release checks.')+source_link(SOURCE+'outputs/03_Website_Validation_Notes.md','Evidence review and remaining validation requirements')
    section('data','Data preparation and validation',p('Referral to Treatment (RTT) tracks consultant-led elective pathways. One person may have more than one pathway, so the counts below are not unique patients. A clock start records a new pathway; a clock stop can reflect treatment or another qualifying end to the wait.')+p('Inside the trust, I would request the patient tracking list and operational records through their owners. Here, I used public provider/specialty aggregates, preserving the distinction between reporting pressure and explaining its causes.')+requests+sources+flow+schema+disclosure('Weekly-band extraction and aggregation logic',extraction_proof)+disclosure('Recorded data checks and release requirements',validation))

    trend = data['trend']
    labels = [month_label(r['month']) for r in trend]
    performance = [d(r['pct_within_18']) for r in trend]
    waiting = [d(r['waiting_list']) for r in trend]
    perf_chart = chart('18-week performance recovered, then eased to 66.6%','Share of incomplete pathways with known clock starts waiting under 18 weeks, April 2023–August 2026. This is a snapshot of those still waiting.',line_chart(labels,performance,ymax=100,yticks=(0,25,50,75,100),ylabel='Waiting under 18 weeks (%)',tick_indices=(0,12,24,40))+'<p class="chart-annotation"><strong>68.9% in June → 66.6% in August 2026.</strong> The latest score remains well above August 2025’s 55.7%, but the recent easing warrants review.</p>',['Month','Waiting under 18 weeks (%)'],[[r['month'],n(r['pct_within_18'],2)] for r in trend],'Excel report · Trust trend. Percentages retained to two decimal places in the workbook.')
    stock_chart = chart('The waiting list grew by 6,759 pathways after March','Incomplete pathways with known clock starts. The long view shows the earlier recovery as well as the recent increase.',line_chart(labels,waiting,ymax=160000,yticks=(0,40000,80000,120000,160000),ylabel='Waiting pathways',tick_indices=(0,12,24,40),value_format=lambda v:f'{float(v)/1000:g}k')+'<p class="chart-annotation"><strong>89,544 in March → 96,303 in August: up 7.5%.</strong> Over the same period, 52+ week pathways fell from 397 to 175. List size and the oldest waits can move in different directions.</p>',['Month','Waiting pathways','52+ week pathways'],[[r['month'],n(r['waiting_list']),n(r['over_52'])] for r in trend],'Excel report · Trust trend. Counts are pathways, not unique people.')
    milestones = table(['Reference carried in the original pack','Recorded result','Use in this case study'],[
        ['March 2026 · 65% under 18 weeks','68.6%','Historical comparison only; confirm the applicable official planning requirement.'],
        ['March 2026 · under 1% waiting 52+ weeks','0.44%','Historical comparison only; do not treat it as the sole current standard.'],
        ['March 2027 · 70% under 18 weeks','No percentage projection built','Requires current policy confirmation and a plan by wait band; list-size forecasts cannot establish achievement.']
    ],'Planning references and their limits')+p('The original summary sourced these references from the Shelford Group dashboard. This page does not independently certify compliance with current NHS planning guidance.')
    section('recovery','Recovery and renewed waiting-list pressure',p('I assessed the percentage waiting under 18 weeks alongside list size and the longest waits. A single headline could give an incomplete account: UHB had fewer very long waits while its total list was growing again.')+perf_chart+stock_chart+disclosure('Planning references carried in the source pack',milestones))

    flow_rows = []
    for field,label in [('clock_starts','Clock starts'),('clock_stops','Clock stops')]:
        a,b = [sum(d(r[field]) for r in trend if f'{year}-04'<=r['month']<=f'{year}-08') for year in ('2025','2026')]
        flow_rows.append([label,n(a),n(b),n((b/a-1)*100,1)+'%'])
    comparison = table(['Measure','Apr–Aug 2025','Apr–Aug 2026','Change'],flow_rows,'Matched-period additions and completed pathways')
    start,add,stop,residual,end = data['opening'],data['starts'],data['stops'],data['residual'],data['closing']
    rows = [('Mar 26',0,start,f'{start/1000:.1f}k','total'),('Starts',start,start+add,f'+{add/1000:.1f}k','flow'),('Stops',start+add,start+add-stop,f'−{stop/1000:.1f}k','flow'),('Residual',start+add-stop,end,f'−{abs(residual)/1000:.1f}k','residual'),('Aug 26',0,end,f'{end/1000:.1f}k','end')]
    balance_rows = [['Opening list · March 2026',n(start),n(start)],['Clock starts',f'+{n(add)}',n(start+add)],['Clock stops',f'−{n(stop)}',n(start+add-stop)],['Unclassified net residual',f'−{n(abs(residual))}',n(end)],['Closing list · August 2026',n(end),n(end)]]
    balance_chart = chart('Starts and stops leave a 21,526-pathway reconciliation gap','April–August 2026 stock-flow bridge. Solid bars show recorded totals and flows; the dashed bar is the calculated residual, not an identified removal category.',balance_waterfall(rows)+'<p class="chart-annotation"><strong>89,544 + 133,091 − 104,806 − 21,526 = 96,303.</strong> The residual reconciles the arithmetic; the public aggregates do not explain its causes.</p>',['Balance component','Pathways / signed change','Running balance'],balance_rows,'Derived from Excel report · Trust trend, March–August 2026. Rounded k labels in the drawing; exact counts in the table.')
    residual_rows = []
    for row in data['period']:
        previous = trend[trend.index(row)-1]
        change = d(row['waiting_list'])-d(previous['waiting_list'])
        net = d(row['clock_starts'])-d(row['clock_stops'])
        residual_rows.append([row['month'],n(change),n(net),n(change-net)])
    balance_proof = table(['Month','Actual list change','Starts minus stops','Unclassified residual'],residual_rows,'Monthly stock-flow reconciliation')+code_excerpt('02_performance_report.py','recon =','checks =')+source_link(SOURCE+'scripts/02_performance_report.py','Stock-flow check and KPI definitions')
    section('balance','Starts, stops and the unexplained balance',p('I compared April–August with the same months a year earlier. Clock starts rose 15.2%, while clock stops rose 0.8%. That points to greater pressure from additions, but does not establish that clinical capacity was unchanged or explain the entire change in the list.')+comparison+balance_chart+note('Requirement for operational use','Ask the validation and informatics teams for coded removals, transfers, corrections and reporting adjustments. Reconcile them to the residual before attributing list growth or setting an activity target. Clock stops are not a direct measure of theatre capacity.')+disclosure('Monthly balance and reconciliation calculation',balance_proof))

    ent = data['specialty']['Ear Nose and Throat Service']
    eye = data['specialty']['Ophthalmology Service']
    long_total = d(latest['over_52'])
    remaining = long_total-d(ent['52+ week waiters'])-d(eye['52+ week waiters'])
    long_rows = [('ENT',d(ent['52+ week waiters']),True),('Ophthalmology',d(eye['52+ week waiters']),True),('All other specialties',remaining,False)]
    long_chart = chart('ENT and Ophthalmology hold 110 of the 175 longest waits','Pathways waiting 52+ weeks in August 2026. “All other specialties” combines the remaining 21 specialty rows.',horizontal_bars(long_rows,70,lambda v:n(v))+'<p class="chart-annotation"><strong>62.9% of 52+ week pathways sit in two services.</strong> Both services improved their 18-week percentages over the year; remaining long waits still need a targeted review.</p>',['Specialty grouping','52+ week pathways'],[[label,n(value)] for label,value,_ in long_rows],'Excel report · Specialties. The component counts reconcile to the trust total of 175.')
    selected = [data['specialty'][name] for name in ['Gynaecology Service','Oral Surgery Service','Ear Nose and Throat Service','Ophthalmology Service']]
    short_names = ['Gynaecology','Oral surgery','ENT','Ophthalmology']
    pairs = [(label,d(row['% within 18 weeks 12 months ago']),d(row['% within 18 weeks']),i==0) for i,(label,row) in enumerate(zip(short_names,selected))]
    detail_rows = [[label,n(row['Waiting list']),n(row['List change %'],1)+'%',n(row['% within 18 weeks 12 months ago'],1)+'%',n(row['% within 18 weeks'],1)+'%',n(row['52+ week waiters'])] for label,row in zip(short_names,selected)]
    specialty_chart = chart('Gynaecology deteriorated while ENT and Ophthalmology improved','Selected services, August 2025 versus August 2026. The same percentage scale shows the direction and size of each change.',paired_dots(pairs,first_label='Aug 2025',second_label='Aug 2026')+'<p class="chart-annotation"><strong>Gynaecology: 56.8% → 45.9% under 18 weeks.</strong> Its list grew from 6,379 to 8,831 pathways, up 38.4%. Only one pathway was at 52+ weeks, so the long-wait ranking alone would miss this emerging pressure.</p>',['Specialty','Latest waiting list','Annual list change','Under 18 weeks · Aug 2025','Under 18 weeks · Aug 2026','52+ week pathways'],detail_rows,'Excel report · Specialties. These four services illustrate different review needs; they are not a complete ranking.')
    full_specialties = table(['Specialty','Waiting list','Annual list change (%)','Under 18 weeks (%)','52+ week pathways'],[[r['specialty'],n(r['Waiting list']),n(r['List change %'],1),n(r['% within 18 weeks'],1),n(r['52+ week waiters'])] for r in data['specialties']],'All 23 specialty rows retained in the workbook')
    section('specialties','Specialty priorities need more than one measure',p('I separated two review needs: the services holding the longest waits and services showing wider deterioration. The resulting priorities differ, so I retained both views rather than ranking specialties on a single percentage.')+long_chart+specialty_chart+note('Service review','Combine the aggregate figures with pathway stage, clinical priority, cancellations and appointment supply. This analysis identifies questions for service leaders; it does not determine individual treatment priority or prove the cause of a specialty’s performance.')+disclosure('Full specialty comparison and reporting logic',full_specialties+source_link(SOURCE+'scripts/02_performance_report.py','Specialty calculations and year-on-year comparison')))

    benchmarks = table(['Trust / comparator','Under 18 weeks (%)','52+ week share (%)','Waiting pathways'],[[r['Trust'],n(r['% within 18 weeks'],1),n(r['% waiting 52+ weeks'],2),n(r['Waiting list'])] for r in data['benchmark']],'August 2026 comparison: UHB, six selected trusts and England')
    section('benchmark','Selected peers provide context, not a performance explanation',p('UHB’s 66.6% under-18-week result is highest among the seven trusts selected for this analysis, including UHB, and above England’s 65.2%. That relative position does not remove the need to investigate its own recent list growth.')+benchmarks+note('Comparator selection','The six other trusts are large Midlands acute trusts, not a statistically matched control group. Specialty mix, complexity, referral patterns and local conditions may differ. England is a separate national comparator, not an eighth peer trust.')+disclosure('Provider selection and benchmark calculation',source_link(SOURCE+'scripts/01_extract.py','Selected provider codes')+source_link(SOURCE+'scripts/02_performance_report.py','Latest-month benchmark calculation')))

    bt = data['backtest']
    series = [('Actual',[d(r['Actual']) for r in bt],'actual'),('Demand/capacity model',[d(r['Demand-capacity model']) for r in bt],'model'),('No-change baseline',[d(r['No change (naive)']) for r in bt],'baseline')]
    backtest_chart = chart('The model projected a decline while the actual list grew','Six held-out months, March–August 2026. Models use data through February 2026; the baseline holds February’s list at 91,407 pathways.',comparison_lines([month_label(r['Month']) for r in bt],series,ymin=70000,ymax=110000,yticks=(70000,80000,90000,100000,110000),tick_indices=(0,2,5),ylabel='Waiting pathways · axis 70k–110k')+'<p class="chart-annotation"><strong>August: 96,303 actual versus 80,236 modelled.</strong> The no-change baseline was closer across the six-month test. The zoomed axis makes the paths visible; it does not start at zero.</p>',['Month','Actual waiting list','Demand/capacity model','Trend model','No-change baseline'],[[r['Month'],n(r['Actual']),n(r['Demand-capacity model']),n(r['Trend model']),n(r['No change (naive)'])] for r in bt],'Excel report · Forecast back-test. The trend model is included in the table and error comparison below, not plotted.')
    errors = table(['Method','Mean absolute percentage error','Interpretation'],[
        ['No-change baseline',n(data['errors']['No change (naive)'],2)+'%','Most accurate of the three methods on this test.'],
        ['Six-month trend',n(data['errors']['Trend (6-month average change)'],2)+'%','Continued the earlier decline and missed the turn.'],
        ['Demand/capacity model',n(data['errors']['Demand-capacity'],2)+'%','Seasonal starts/stops and an average residual did not capture the turn.']
    ],'Back-test accuracy: lower average absolute percentage error is better')
    scenario = data['scenario']
    additional = (d(scenario[-1]['Forecast waiting list'])-d(latest['waiting_list']))/len(scenario)
    scenario_proof = p('The original continuation model reuses last year’s seasonal starts and stops, scales each by the latest three-month year-on-year ratio and carries forward the recent average residual. It gives 107,190 waiting pathways in March 2027 in the rounded workbook. It has no prediction interval and failed to outperform the baseline in the held-out test.')
    scenario_proof += table(['Month','Scenario starts','Scenario stops','Scenario waiting list'],[[r['month'],n(r['Forecast clock starts']),n(r['Forecast clock stops']),n(r['Forecast waiting list'])] for r in scenario],'Original continuation scenario · not a validated prediction')
    scenario_proof += p(f'Within this model, holding the list flat would require roughly {n(additional)} additional clock stops per month, with every other assumption unchanged. This is arithmetic from the scenario, not a feasible capacity plan or a count of treatment slots. It also depends on an unclassified residual continuing. The key-figures CSV truncates the final unrounded estimate to 107,189; the workbook rounds it to 107,190.')+code_excerpt('02_performance_report.py','def dc_forecast(hist, h):','wl = u.waiting_list')+source_link(SOURCE+'scripts/02_performance_report.py','Forecast method and back-test calculations')
    section('planning','Model validation limits the planning outlook',p('I held out the final six observed months before evaluating the models, rather than assessing them only on the data used to build them. I compared them with a simple no-change baseline so additional complexity had to demonstrate value.')+backtest_chart+errors+p('Mean absolute percentage error averages the size of each monthly miss relative to the actual list. It measures accuracy on these six months, not a confidence level. A single holdout is limited evidence, but it gives a clear reason to avoid using the more complex model as a committed recovery forecast.')+disclosure('Continuation scenario, assumptions and model code',scenario_proof))

    section('actions','Recommended actions and measures',p('The delivered output is a performance report with reconciled specialty totals, an explicit stock-flow gap and a tested planning model. The recommendations below describe the operational work needed to turn those findings into an agreed response.')+table(['Action owner','Recommended action','Proposed success measure'],copy['actions'],'Recommended investigations and follow-up measures'))

    download = '<div class="actions"><a class="button" href="../projects/04_UHB_Waiting_Times/outputs/UHB_RTT_Performance_Report.xlsx" download>Download the Excel performance report <span aria-hidden="true">↓</span></a></div>'
    limits = disclosure('Scope, definitions and remaining checks',p('The report covers published aggregate consultant-led RTT pathways, not unique people, patient-level clinical priority or a complete capacity model. Missing-month checks do not prove complete source coverage. The stock-flow residual and source-row totals require operational reconciliation. Peer selection does not control case mix. Planning references need policy confirmation, and the March scenario is not a validated prediction. Website checks use committed outputs; they do not rerun unavailable raw files.')+source_link(SOURCE+'outputs/03_Website_Validation_Notes.md','Detailed evidence review and qualifications'))
    dashboard = '<h3>Power BI · planned reporting view</h3>'+p(copy['dashboard'])
    if project['dashboard'] and (ROOT/'assets'/project['dashboard']).exists():
        dashboard += f'<figure class="dashboard-preview" data-image-container><img data-optional-image src="../assets/{e(project["dashboard"])}" alt="UHB Power BI dashboard" loading="lazy"><figcaption>Power BI dashboard preview</figcaption></figure>'
    section('files','Deliverables and supporting files',p('The workbook contains the 41-month trust trend, all 23 specialties, the eight-row benchmark, the seven-month continuation scenario, back-test results and data checks. Review the definitions and validation note alongside the original outputs.')+download+resources(project)+source_link(SOURCE+'scripts/01_extract.py','Python extraction script')+source_link(SOURCE+'scripts/02_performance_report.py','Performance reporting and forecast script')+limits+dashboard)

    nav = ''.join(f'<a href="#{identifier}"><span aria-hidden="true">{i:02d}</span>{e(title)}</a>' for i,(identifier,title) in enumerate(headings,1))
    icons = ''.join(f'<span><img src="../assets/icons/{icon}" width="22" height="22" alt="">{name}</span>' for name,icon in [('Python','python.svg'),('Excel','excel.svg'),('Statistics','statistics.svg')])
    metrics = metric(n(latest['pct_within_18'],1)+'%','of waiting pathways under 18 weeks · August 2026')+metric('+7.5%','waiting-list growth since March · 6,759 additional pathways')+metric('62.9%','of 52+ week pathways in ENT and Ophthalmology · 110 of 175')
    return f'''<main class="container finance-case nhs-case" id="main"><div class="breadcrumb"><a href="../index.html#projects">Selected projects</a> / NHS performance</div>
    <header class="finance-hero">{organisation(project,'../')}<span class="eyebrow">Elective performance &amp; planning analysis</span><h1>{e(copy['title'])}</h1><p class="lead">{e(copy['summary'])}</p><div class="finance-meta"><span>April 2023–August 2026 · provider RRK</span><span>My role: independent analyst</span><div class="finance-tools">{icons}</div></div></header>
    <aside class="scenario-note" aria-label="About this case study"><strong>About this case study</strong>{p(copy['scenario_note'])}</aside><div class="finance-metrics" aria-label="Results at a glance">{metrics}</div>
    <div class="finance-layout"><nav class="finance-nav" aria-label="On this page"><strong>Follow the analysis</strong>{nav}</nav><div class="finance-content">{''.join(sections)}</div></div>
    <div class="next-project"><a href="../index.html#projects">← All projects</a><a class="button" href="{e(next_project['slug'])}.html">Next: {e(next_project['organisation'])} <span aria-hidden="true">→</span></a></div></main>'''
