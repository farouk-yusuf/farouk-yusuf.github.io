"""Birmingham's finance narrative, built from the existing workbook and source code.

The website build needs only the standard library. The original analytical pipeline
is separate; this renderer reads its committed outputs, not the unavailable raw CSV.
"""
import ast
import csv
from decimal import Decimal
from datetime import datetime
import json
from pathlib import Path
from story_workbook import read_sheet
from story_components import e, p, source_link, disclosure, note, metric
from story_charts import line_chart, paired_dots

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'projects/01_BCC_Payments'


def workbook_rows(name):
    return read_sheet(PROJECT/'outputs/BCC_Spend_and_Payment_Controls_Pack.xlsx', name)


def evidence_data():
    """Read headline evidence from committed outputs and literal mapping definitions."""
    figures = {r['']: r['value'] for r in csv.DictReader((PROJECT/'outputs/key_figures.csv').open())}
    tree = ast.parse((PROJECT/'scripts/01_clean.py').read_text())
    mapping = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'dir_map' for t in node.targets))
    spend = workbook_rows('Spend by directorate')
    totals = next(row for row in spend if row['report_group'] == 'Total')
    years = ('1 Apr - 23 Jul 2025 £m', '1 Apr - 23 Jul 2026 £m')
    groups = sorted([(r['report_group'], Decimal(r[years[1]]) - Decimal(r[years[0]])) for r in spend if r['report_group'] != 'Total'], key=lambda item: item[1], reverse=True)
    with (PROJECT/'outputs/sql_results/03_possible_duplicate_payments.csv').open() as stream:
        initial_pairs = sum(1 for _ in csv.DictReader(stream))
    monthly = [row for row in workbook_rows('Monthly spend £m') if row['month'] < '2026-07']
    return {'figures': figures, 'mapping': mapping, 'groups': groups, 'totals': [Decimal(totals[k]) for k in years], 'initial_pairs': initial_pairs, 'monthly': monthly}


def code_excerpt(filename, start, end=None):
    text = (PROJECT/filename).read_text()
    excerpt = text[text.index(start):]
    if end:
        excerpt = excerpt[:excerpt.index(end)]
    return f'<pre tabindex="0" role="region" aria-label="Code excerpt"><code>{e(excerpt.strip())}</code></pre>'


def movement_bars(groups):
    minimum, maximum = Decimal('-45'), Decimal('90')
    scale = maximum-minimum
    zero = -minimum/scale*100
    rows = []
    for label, value in groups:
        left = min(zero, (value-minimum)/scale*100)
        width = abs(value)/scale*100
        rows.append(f'<li class="finance-bar-row"><div class="finance-bar-label"><span>{e(label)}</span><strong>{"+" if value>0 else "−"}£{abs(value):.2f}m</strong></div><div class="finance-bar-track finance-bar-track--diverging" style="--zero:{float(zero):.3f}%" aria-hidden="true"><span class="finance-bar {"finance-bar--focus" if label=="City Operations" else ""}" style="left:{float(left):.3f}%;width:{float(width):.3f}%"></span></div></li>')
    return f'<p class="finance-axis-note"><span>Lower payments ←</span><span>→ Higher payments</span></p><ul class="finance-bars">{"".join(rows)}</ul>'


def report_gallery(report):
    """Native disclosures keep exported pages usable with keyboard and without JS."""
    pdf = '../'+report['pdf']
    actions = f'<div class="actions report-actions"><a class="button" href="{e(pdf)}" download>Download the Power BI report <span aria-hidden="true">↓</span></a><a class="text-link" href="{e("../"+report["data"])}" download>Download supporting data <span aria-hidden="true">↓</span></a><span class="report-format">PDF · 3 pages</span></div>'
    pages = []
    for index,page in enumerate(report['pages'],1):
        image = '../'+page['image']
        pages.append(f'''<details class="report-page"{' open' if index==1 else ''}>
          <summary><span class="report-page-number" aria-hidden="true">{index:02d}</span><span class="report-page-label"><strong>{e(page['title'])}</strong><span>{e(page['summary'])}</span></span></summary>
          <div class="report-page-body"><figure><img src="{e(image)}" alt="{e(page['alt'])}" width="2214" height="1269" loading="lazy" decoding="async"><figcaption>Power BI · PDF export · Page {index} of 3</figcaption></figure>
          <div class="report-page-links"><a href="{e(image)}" target="_blank" rel="noopener">Open full-size preview<span class="sr-only">: {e(page['title'])}</span> <span aria-hidden="true">↗</span></a><a href="{e(pdf)}#page={index}" target="_blank" rel="noopener">Open PDF page<span class="sr-only">: {e(page['title'])}</span> <span aria-hidden="true">↗</span></a></div></div>
        </details>''')
    return p(report['intro'])+actions+'<div class="report-gallery">'+''.join(pages)+'</div><p class="report-coverage">'+e(report['coverage'])+'</p>'


def render(project, next_project, *, chart, table, organisation, resources):
    copy = json.loads((ROOT/'site/birmingham.json').read_text())
    data = evidence_data()
    figures = data['figures']
    sections = []
    headings = []

    def section(identifier, title, body):
        headings.append((identifier, title))
        number = len(headings)
        sections.append(f'<section class="finance-section" id="{identifier}" aria-labelledby="{identifier}-heading"><div class="finance-section-heading"><span class="finance-step" aria-hidden="true">{number:02d}</span><h2 id="{identifier}-heading">{e(title)}</h2></div>{body}</section>')

    requirements_summary = '<aside class="requirements-card" aria-label="Requirements summary"><span class="practice-label">Requirements summary</span><dl>'+''.join(f'<div><dt>{e(label)}</dt><dd>{e(text)}</dd></div>' for label,text in copy['requirements_summary'])+'</dl></aside>'
    framework = copy['requirements_template']
    framework_items = []
    for item in framework['items']:
        framework_items.append(f'''<li><div class="framework-item-heading"><h3>{e(item['element'])}</h3><span class="framework-status framework-status--{e(item['state'])}">{e(item['status'])}</span></div><dl><div><dt>Framework prompt</dt><dd>{e(item['prompt'])}</dd></div><div><dt>Project application</dt><dd>{e(item['application'])}</dd></div></dl></li>''')
    framework_detail = disclosure('See my requirements elicitation template', p(framework['intro'])+'<ol class="framework-items">'+''.join(framework_items)+'</ol>', css_class='requirements-template')
    section('brief', 'Requirements and scope', '<span class="scenario-label">Simulated workplace brief</span>'+p(copy['brief'])+p(copy['requirements_intro'])+requirements_summary+framework_detail)

    requests = table(['Dataset', 'Data owner', 'Analytical purpose', 'Availability'], copy['data_requests'], 'Data access assessment')
    source = '<p class="inline-source">Actual source: <a href="https://www.cityobservatory.birmingham.gov.uk/explore/dataset/payments-to-suppliers-over-gbp500/" target="_blank" rel="noopener">Birmingham City Observatory · Payments to Suppliers over £500 ↗</a></p>'
    steps = [('Extract','Published payments CSV'),('Transform','Standard names, dates and reporting fields'),('Load','SQLite payment model'),('Report','Excel finance and controls pack')]
    flow = '<ol class="etl-flow" aria-label="ETL and reporting workflow">'+''.join(f'<li><strong>{e(label)}</strong><span>{e(text)}</span></li>' for label,text in steps)+'</ol>'
    schema = '<div class="model-diagram" aria-label="SQL reporting model"><div class="model-fact"><strong>fact_payment</strong><span>One row per published payment line</span></div><ul>'+''.join(f'<li>{label}</li>' for label in ['dim_supplier','dim_directorate','dim_category','dim_date'])+'</ul></div>'
    schema += source_link('projects/01_BCC_Payments/sql/00_schema.sql', 'SQL table definitions')+source_link('projects/01_BCC_Payments/scripts/02_build_database.py','Database build script')
    section('data', 'Data requirements and availability', p(copy['data_intro'])+requests+source+p(copy['etl_intro'])+flow+disclosure('SQL schema and relationships', schema))

    sample = ['Adults Social Care Directorate','Adult Social Care & Health Directorate','Council Managament','Finance Control- Monitoring','Places, Prosperity & Sustainability Directorate']
    rows = [[name,data['mapping'][name]] for name in sample]
    mapping_table = table(['Source department', 'Standardised directorate'], rows, 'Department standardisation sample')
    proof = code_excerpt('scripts/01_clean.py', 'unmapped =', '# 2. Personal data')
    proof += code_excerpt('scripts/01_clean.py', 'assert len(df) ==', 'df.drop(')
    proof += source_link('projects/01_BCC_Payments/scripts/01_clean.py','Cleaning and validation script')
    section('comparison', 'Data preparation and validation', p(copy['mapping_intro'])+mapping_table+p(copy['corporate_note'])+note('Data validation',copy['validation_note'])+disclosure('Mapping logic and reconciliation checks',proof))

    spend_chart = chart('Net payments increased by £118.82m over equivalent dates', '1 April–23 July in each year. Credits are included in the net totals.', paired_dots([('Net payments',*data['totals'],True)],first_label='2025',second_label='2026',maximum=800,prefix='£',suffix='m',places=2)+f'<p class="chart-annotation">2026 was <strong>21.3% higher</strong>. Both periods end on 23 July.</p>', ['Period','Net payments (£m)'],[['1 Apr–23 Jul 2025',f'{data["totals"][0]:.2f}'],['1 Apr–23 Jul 2026',f'{data["totals"][1]:.2f}']], 'Excel finance pack · Spend by directorate · Total row.')
    monthly = data['monthly']
    month_labels = [datetime.strptime(row['month'],'%Y-%m').strftime('%b %y') for row in monthly]
    monthly_values = [Decimal(row['Total']) for row in monthly]
    monthly_chart = chart('Monthly payments fluctuated rather than rising steadily','Published monthly net payments, July 2024–June 2026. The partial July 2026 total is excluded because the extract ends on 23 July.',line_chart(month_labels,monthly_values,ymax=240,yticks=(0,80,160,240),ylabel='Net payments (£m)',tick_indices=(0,6,12,18,len(monthly)-1),optional_ticks=(18,),value_format=lambda v:f'{float(v):g}')+'<p class="chart-annotation"><strong>June 2026: £202.23m.</strong> Payment timing can shift a monthly total; this line does not measure the cost of services delivered in that month.</p>',['Month','Net payments (£m)'],[[row['month'],f'{Decimal(row["Total"]):.2f}'] for row in monthly],'Excel finance pack · Monthly spend £m · Total column. Rounded published-payment aggregates.')
    movement_chart = chart('City Operations and adult social care drove the largest increases', 'Each bar shows a reporting group’s contribution to the £118.82m net increase. Decreases offset part of the growth.', movement_bars(data['groups'])+'<p class="chart-annotation"><strong>City Operations: +£75.62m.</strong> Higher net payments to Birmingham Highways contributed £66.95m within this group.</p>', ['Reporting group','Year-on-year change (£m)'], [[label,f'{value:.2f}'] for label,value in data['groups']], 'Excel finance pack · Spend by directorate and YTD variance drivers. Values rounded to £0.01m.')
    period_proof = code_excerpt('scripts/03_finance_pack.py', 'last =', 'K_period =')+source_link('projects/01_BCC_Payments/scripts/03_finance_pack.py','Matched-period calculations')
    section('spending', 'Spending rose 21.3%', p(copy['spending_intro'])+spend_chart+monthly_chart+p(copy['spending_interpretation'])+movement_chart+note('Management interpretation',copy['highways_note'])+disclosure('Reporting-period calculation',period_proof))

    concentration = f'<div class="supplier-facts">{metric(figures["top10_share_pct"]+"%", "of FY2025/26 payment value went to the top ten suppliers")}{metric("+"+figures["agency_ytd_change_pct"]+"%", "agency-staff payments over the matched year-to-date period")}</div>'
    extra_proof = '<p>These figures are recorded in the finance pack’s Top suppliers FY25-26 and Agency staff monthly sheets. The year-to-date agency comparison uses the same reporting dates as the expenditure analysis.</p>'+source_link('projects/01_BCC_Payments/sql/02_top_suppliers_fy2025_26.sql','Supplier reporting query')+source_link('projects/01_BCC_Payments/sql/05_agency_staff_monthly.sql','Agency-staff reporting query')+source_link('projects/01_BCC_Payments/scripts/03_finance_pack.py','Concentration and agency calculations')
    section('suppliers', 'Supplier and agency-staff expenditure', p(copy['suppliers_intro'])+concentration+p(copy['supplier_note'])+disclosure('Supplier concentration and agency calculations',extra_proof))

    rule_list = '<ol class="rule-list">'+''.join(f'<li><strong>{e(title)}</strong><span>{e(text)}</span></li>' for title,text in copy['duplicate_rules'])+'</ol>'
    initial = data['initial_pairs']
    final = int(figures['dup_pairs'])
    same_day = int(figures['dup_same_day'])
    remaining = final-same_day
    duplicate_visual = f'<div data-viz="process"><ol class="analysis-process"><li><span>Initial SQL screening</span><strong>{initial:,}</strong><small>candidate payment pairs</small></li><li><span>Refined in Python</span><strong>{final:,}</strong><small>candidate pairs · £{e(figures["dup_value_m"])}m</small></li></ol><div class="process-subset"><strong>Within the {final} candidates</strong><span>{same_day} same-day pairs · review first</span><span>{remaining} pairs one to three days apart</span></div></div>'
    duplicate_chart = chart('A more selective rule produced a focused AP review list', 'These are screening stages, not confirmed duplicate payments. The 73 same-day pairs are included within the 281 candidates.', duplicate_visual, ['Screening stage','Payment pairs'],[['Initial SQL rule',initial],['Refined Python rule',final],['Same-day subset of refined pairs',same_day]], 'Initial SQL results CSV; finance pack · Possible duplicates; key_figures.csv.')
    duplicate_proof = '<h3>Stage 1 · SQL candidate generation</h3><p>The SQL self-join compares payment lines for the same supplier and amount within three days. It produces the initial 6,553-pair list.</p>'+source_link('projects/01_BCC_Payments/sql/03_possible_duplicate_payments.sql','Initial SQL matching query')
    duplicate_proof += '<h3>Stage 2 · Python refinement</h3><p>The additional supplier–amount frequency condition is implemented below. It retains combinations appearing exactly twice across the dataset, then checks the gap between those two dates.</p>'+code_excerpt('scripts/03_finance_pack.py','x = df[~df.is_personal_data', 'credits =')+source_link('projects/01_BCC_Payments/scripts/03_finance_pack.py','Refined Python screening')
    section('duplicates', 'Duplicate-payment screening', p(copy['duplicates_intro'])+rule_list+duplicate_chart+p(copy['duplicates_result'])+note('Screening coverage and limitations',copy['duplicates_limit'])+disclosure('Duplicate-screening logic: SQL and Python',duplicate_proof))

    privacy_evidence = '<p>The workbook’s Personal data check sheet records the aggregate publication issue. No supplier identifiers or personal names are displayed on this page. This check concerns the risk of linking records across a publication; it does not establish whether anyone accessed or misused the information.</p>'+source_link('projects/01_BCC_Payments/scripts/03_finance_pack.py','Information-governance calculations')
    section('privacy', 'Publication checks identified a privacy risk', p(copy['privacy_intro'])+p(copy['privacy_action'])+disclosure('Publication risk assessment',privacy_evidence))

    actions = table(['Action owner','Recommended action','Success measure'],copy['actions'],'Action plan and proposed success measures')
    section('actions', 'Recommended actions', actions+p(copy['delivery']))

    section('report', 'Power BI report', report_gallery(copy['report']))

    limitations = '<details class="evidence"><summary>Scope and limitations</summary><div class="evidence-body"><ul><li>The publication covers payments over £500, rather than all council expenditure.</li><li>Cash payments are not budgets, commitments or full service costs.</li><li>Invoice references are absent; exceptions require internal verification.</li><li>35.4% of FY2025/26 payment value uses a generic PO-accrual category, limiting analysis by expenditure type.</li></ul></div></details>'
    supporting = resources(project)
    download = '<div class="actions"><a class="button" href="../projects/01_BCC_Payments/outputs/BCC_Spend_and_Payment_Controls_Pack.xlsx" download>Download the Excel finance pack <span aria-hidden="true">↓</span></a></div>'
    section('files', 'Deliverables and supporting files', '<p>Inspect the completed workbook, management summary, requirements brief and decisions note, or follow the scripts from cleaning to reporting.</p>'+download+supporting+limitations)

    nav = ''.join(f'<a href="#{identifier}"><span aria-hidden="true">{i:02d}</span>{e(title)}</a>' for i,(identifier,title) in enumerate(headings,1))
    tool_icons = ''.join(f'<span><img src="../assets/icons/{icon}" width="22" height="22" alt="">{name}</span>' for name,icon in [('Python','python.svg'),('SQL','sql.svg'),('Excel','excel.svg'),('Power BI','power-bi.svg')])
    metrics = metric('21.3%','increase in net payments over matched dates')+metric('281','potential duplicate payment pairs · £4.45m')+metric('73','same-day pairs to investigate first')
    return f'''<main class="container finance-case" id="main">
      <div class="breadcrumb"><a href="../index.html#projects">Selected projects</a> / Local government</div>
      <header class="finance-hero">{organisation(project,'../')}<span class="eyebrow">Expenditure analysis &amp; payment controls</span><h1>{e(copy['title'])}</h1><p class="lead">{e(copy['summary'])}</p><div class="finance-meta"><span>July 2024–23 July 2026</span><span>My role: independent analyst</span><div class="finance-tools">{tool_icons}</div></div><div class="actions"><a class="button" href="#report">View the Power BI report <span aria-hidden="true">↓</span></a><a class="text-link" href="../{e(copy['report']['pdf'])}" download>Download PDF <span aria-hidden="true">↓</span></a></div></header>
      <aside class="scenario-note" aria-label="About this case study"><strong>About this case study</strong><p>{e(copy['scenario_note'])}</p></aside>
      <div class="finance-metrics" aria-label="Results at a glance">{metrics}</div>
      <div class="finance-layout"><nav class="finance-nav" aria-label="On this page"><strong>Follow the analysis</strong>{nav}</nav><div class="finance-content">{''.join(sections)}</div></div>
      <div class="next-project"><a href="../index.html#projects">← All projects</a><a class="button" href="{e(next_project['slug'])}.html">Next: {e(next_project['organisation'])} <span aria-hidden="true">→</span></a></div>
    </main>'''
