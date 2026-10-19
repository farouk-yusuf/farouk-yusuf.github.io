"""Severn Trent performance analysis, rendered from committed workbook/CSV outputs."""
from collections import Counter
import csv
from decimal import Decimal
import json
from pathlib import Path

from story_components import e, p, source_link, disclosure, note, metric, requirements_panels, horizontal_bars
from story_workbook import read_sheet
from story_charts import line_chart, paired_dots, rainfall_scatter

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT/'projects/03_Severn_Trent'
SOURCE = 'projects/03_Severn_Trent/'
WORKBOOK = PROJECT/'outputs/Severn_Trent_Overflow_Performance_Pack_2025.xlsx'


def csv_rows(name):
    with (PROJECT/'outputs'/name).open() as stream:
        return list(csv.DictReader(stream))


def evidence_data():
    yearly = csv_rows('st_yearly_summary.csv')
    figures = {r['']:r['value'] for r in csv_rows('key_figures.csv')}
    sheets = {key:read_sheet(WORKBOOK,name) for key,name in [
        ('qa','QA checks'),('rises','QA - large rises'),('maintenance','Maintenance exceptions'),
        ('high','High-spill exceptions'),('basins','By river basin'),('assets','By asset type')]}
    return dict(yearly=yearly,years={r['year']:r for r in yearly},figures=figures,
                kpis={r['Measure']:r for r in read_sheet(WORKBOOK,'KPIs',index_header='Measure')},
                persistent=csv_rows('priority_overflows_persistent_high.csv'),
                not_improving=csv_rows('overflows_not_improving_2025.csv'),**sheets)


def n(value, places=0):
    return f'{Decimal(str(value)):,.{places}f}'


def bars(rows, maximum, places=0, suffix=''):
    return horizontal_bars(rows,maximum,lambda value:n(value,places)+suffix)


def code_excerpt(filename, start, end=None):
    code = (PROJECT/'scripts'/filename).read_text()
    excerpt = code[code.index(start):]
    if end:
        excerpt = excerpt[:excerpt.index(end)]
    return f'<pre tabindex="0" role="region" aria-label="Code excerpt"><code>{e(excerpt.strip())}</code></pre>'


def render(project, next_project, *, chart, table, organisation, resources):
    copy = json.loads((ROOT/'site/severn-trent.json').read_text())
    data = evidence_data()
    years, figures = data['years'], data['figures']
    sections, headings = [], []

    def section(identifier,title,body):
        headings.append((identifier,title))
        sections.append(f'<section class="finance-section" id="{identifier}" aria-labelledby="{identifier}-heading"><div class="finance-section-heading"><span class="finance-step" aria-hidden="true">{len(headings):02d}</span><h2 id="{identifier}-heading">{e(title)}</h2></div>{body}</section>')

    section('brief','Requirements and reporting scope','<span class="scenario-label">Simulated workplace brief</span>'+p(copy['brief'])+p(copy['requirements_intro'])+requirements_panels(copy))

    access = table(['Dataset','Data owner','Analytical purpose','Availability'],copy['data_requests'],'Data access assessment')
    links = '<p class="inline-source">Public sources: <a href="https://www.data.gov.uk/dataset/19f6064d-7356-466f-844e-d20ea10ae9fd/event-duration-monitoring-storm-overflows-annual-returns" target="_blank" rel="noopener">Environment Agency annual returns ↗</a> and <a href="https://www.metoffice.gov.uk/research/climate/maps-and-data/uk-and-regional-series" target="_blank" rel="noopener">Met Office regional rainfall ↗</a>. File versions and access dates appear in the source log.</p>'
    flow = '<ol class="etl-flow" aria-label="ETL and reporting workflow">'+''.join(f'<li><strong>{e(label)}</strong><span>{e(text)}</span></li>' for label,text in [('Extract','Six years of annual returns and regional rainfall'),('Standardise','Hours, operation percentages, headers and asset IDs'),('Check','Missing data, value ranges and annual exceptions'),('Report','Performance pack and separate operational lists')])+'</ol>'
    conversions = table(['Measure','Source representation','Standard reporting field'],[
        ['Monitor operation','2020–2022: fraction; 2023–2025: percentage','edm_op_pct · earlier fractions multiplied by 100'],
        ['Spill duration','Decimal hours, durations or Excel time values','duration_hrs · converted to decimal hours'],
        ['Asset identifier','SVE / SVT formats across reporting years','unique_id / old_id · supplied old-ID link used for the panel']
    ],'Standardisation rules used by the cleaning script')
    conversion_proof = code_excerpt('01_build_clean_data.py','def to_hours(v):','def to_num(v):')+source_link(SOURCE+'scripts/01_build_clean_data.py','Full cleaning and field-mapping script')
    qa_rows = [[r['Check'],n(r['Result']),r['Status'],r['Note']] for r in data['qa']]
    qa_proof = table(['Check','Result','Status','Purpose / follow-up'],qa_rows,'2025 return checks recorded in the workbook')+code_excerpt('03_performance_pack.py','checks = [','qa = pd.DataFrame')+source_link(SOURCE+'scripts/03_performance_pack.py','Return checks and performance-pack script')
    section('data','Data preparation and return checks',p(copy['data_intro'])+access+links+p('The files changed format across years. I built one overflow-year table and standardised the fields before calculating trends. This extract, transform and load process—ETL—prevents a fraction, a time value or a changed asset ID from being interpreted as a performance change.')+flow+conversions+disclosure('Duration conversion and field-mapping logic',conversion_proof)+note('Validation results','The workbook records five passing checks, five items requiring review and one information count. It reports zero duplicate IDs, 21 missing spill counts, 11 new IDs, 18 removed IDs and two sites with increases of at least 50 spills. A passing structural check does not resolve these review items.')+disclosure('Annual-return checks and outstanding review items',qa_proof))

    labels = [r['year'] for r in data['yearly']]
    spills = [Decimal(r['total_spills']) for r in data['yearly']]
    rain = [Decimal(r['midlands_rain_mm']) for r in data['yearly']]
    spill_chart = chart('The 2025 fall follows two years of higher recorded spills','Annual counted spills, 2020–2025, using the Environment Agency’s 12/24-hour counting method. The aligned rainfall chart below uses the same years.',line_chart(labels,spills,ymax=70000,yticks=(0,20000,40000,60000),ylabel='Recorded spills',value_format=lambda v:f'{float(v)/1000:g}k')+'<p class="chart-annotation"><strong>62,085 → 36,471 in 2025: a 41.3% fall.</strong> The six-year view also shows the earlier low in 2022. These are recorded counts; they do not isolate improvement work.</p>',['Year','Recorded spills'],[[year,n(value)] for year,value in zip(labels,spills)],'st_yearly_summary.csv · 2024 and 2025 reconcile to the workbook KPIs sheet.')
    rain_chart = chart('Both 2022 and 2025 were drier than the surrounding wet years','Annual Midlands rainfall, 2020–2025, on a separate scale. Matching year positions make the patterns comparable without combining units on a dual axis.',line_chart(labels,rain,ymax=1200,yticks=(0,400,800,1200),ylabel='Annual rainfall (mm)',value_format=lambda v:f'{float(v):g}')+'<p class="chart-annotation"><strong>1,000.2 mm → 716.6 mm in 2025: a 28.4% fall.</strong> Regional annual totals cannot show individual storm intensity.</p>',['Year','Midlands rainfall (mm)'],[[year,n(value,1)] for year,value in zip(labels,rain)],'Met Office Midlands series, recorded in st_yearly_summary.csv.')
    section('annual','Recorded spills fell as rainfall fell',p('A storm overflow can release sewage when the sewer system is overwhelmed. Event Duration Monitoring records when a discharge occurs and how long it lasts; it does not measure the volume released. The annual count uses a defined 12/24-hour grouping rule, so it is not a simple count of every discharge start.')+spill_chart+rain_chart+p('The drier year is relevant context, but a 28.4% fall in rain does not mean spills should fall by the same percentage. Local storm intensity, network conditions, monitor availability and improvement work can all affect the recorded result. I therefore used a second comparison before interpreting the reduction.'))

    dry_rows = [(year,Decimal(years[year]['avg_spills_reliable']),year=='2025') for year in ('2022','2025')]
    dry_table = [[year,n(value,2),n(years[year]['midlands_rain_mm'],1),n(years[year]['reliable_overflows'])] for year,value,_ in dry_rows]
    dry_chart = chart('Average recorded spills were 22.7% lower than in 2022','Only overflows with spill data and monitors operating at least 90% of the year. The qualifying assets differ between years.',paired_dots([('Average spills per qualifying overflow',dry_rows[0][1],dry_rows[1][1],True)],first_label='2022',second_label='2025',maximum=25,suffix='',places=2)+'<p class="chart-annotation">2022 had <strong>721.4 mm</strong> of rain; 2025 had <strong>716.6 mm</strong>. Similar annual totals strengthen the comparison, but do not match the individual storms or the asset populations.</p>',['Year','Average spills per qualifying overflow','Rainfall (mm)','Qualifying overflows'],dry_table,'st_yearly_summary.csv · averages use 1,737 qualifying overflows in 2022 and 2,342 in 2025.')
    slope,intercept = float(figures['slope_spills_per_100mm'])/100,float(figures['intercept'])
    scatter_rows = [[r['year'],n(r['midlands_rain_mm'],1),n(r['avg_spills_reliable'],2),n(intercept+slope*float(r['midlands_rain_mm']),2),n(r['reliable_overflows'])] for r in data['yearly']]
    scatter_chart = chart('2025 lies below the rainfall model’s fitted relationship','Each point is one year, not one overflow. The dashed line was fitted to just five years (2020–2024). The vertical axis spans 10–30 average spills to show the annual positions clearly.',rainfall_scatter(data['yearly'],slope=slope,intercept=intercept)+'<p class="chart-annotation"><strong>2025: 15.01 observed versus 21.45 estimated by the line.</strong> The separation is descriptive; this model does not attribute the difference to investment.</p>',['Year','Midlands rainfall (mm)','Observed average spills','Fitted-line estimate','Qualifying overflows'],scatter_rows,'st_yearly_summary.csv and key_figures.csv · exploratory regional model. No uncertainty interval or causal effect is estimated.')
    regression_rows = [['Training observations','5 annual observations · 2020–2024'],['Slope',n(figures['slope_spills_per_100mm'],2)+' additional average spills per 100 mm'],['Training fit (R²)',n(figures['r2_2020_24'],2)],['Model estimate at 2025 rainfall',n(figures['expected_2025'],2)+' spills per qualifying overflow'],['Observed 2025 average',n(figures['actual_2025'],2)+' spills per qualifying overflow'],['Model-associated share of the 2024–2025 decline',n(Decimal(figures['share_explained_by_rain'])*100,1)+'% · exploratory, not causal attribution']]
    regression = p('I fitted a straight line to annual rainfall and average spills for 2020–2024, then evaluated 2025 against that line. The fitted slope associates the rainfall change with about 46% of the observed fall in the qualifying-overflow average. Five annual observations, changing cohorts and regional totals are insufficient to attribute a causal share to weather or calculate the effect of investment.')+table(['Model item','Value / interpretation'],regression_rows,'Exploratory rainfall model and its limits')+code_excerpt('02_analysis.py','fit = yearly[','# Like-for-like dry years')+source_link(SOURCE+'scripts/02_analysis.py','Rainfall comparison and regression calculations')
    section('rainfall','Similar annual rainfall provides a second comparison',p('I compared 2022 and 2025 because their annual Midlands rainfall totals were close. I also restricted each year’s average to monitors operating at least 90% of the year, reducing the influence of missing monitoring time.')+dry_chart+note('Comparison limits','The 90% threshold reduces one source of bias; it does not recover missed events or create a fixed set of assets. Similar annual rainfall can conceal very different storm patterns. The result is consistent with improved performance, but cannot quantify improvement caused by Severn Trent’s work.')+scatter_chart+disclosure('Rainfall-model calculations and assumptions',regression))

    maintenance = data['maintenance']
    repeats = sum(r['Repeat (<90% in 2024 too)']=='1' for r in maintenance)
    low = next(r for r in data['qa'] if r['Check']=='Monitors working <90% of year')
    reasons = Counter(r['low_op_reason'] for r in maintenance)
    reason_labels = {'Installation set-up/design issue':'Installation or design','Sensor failure / issue':'Sensor faults','Comms failure / issue':'Communications faults','Telemetry or data archiving failure / issue':'Telemetry or archiving','Capital / maintenance works affect EDM operation':'Works affecting the monitor','Power failure / issue':'Power faults','Access - Unable to retrieve data from non-telemetry data logger':'Unable to retrieve logger data'}
    reason_chart = chart('Installation, sensor and communications issues dominate the maintenance list','Published primary low-operation reasons across the 87 maintenance exceptions. These are reported categories, not verified root causes.',bars([(reason_labels[reason],count,i==0) for i,(reason,count) in enumerate(reasons.most_common())],35),['Reported primary reason','Maintenance exceptions'],[[reason,count] for reason,count in reasons.most_common()],'Performance pack · Maintenance exceptions. Each exported record has one primary reason.')
    bridge = table(['Stage','Records','Interpretation'],[['Low-operation flag in the annual return',low['Result'],'All records flagged below 90% operation'],['Excluded from the maintenance export',int(low['Result'])-len(maintenance),'Records labelled “No longer operational”'],['Maintenance review list',len(maintenance),'Remaining records for operational review'],['Repeat low operation in 2024',repeats,'Subset of the 87 maintenance records, not an additional list']],'From 90 flagged records to 87 maintenance exceptions')
    maintenance_samples = table(['Asset ID','Site','2024 operation (%)','2025 operation (%)','Reported reason'],[[r['unique_id'],r['site_name'],n(r['op_2024'],2),n(r['edm_op_pct'],2),r['low_op_reason']] for r in maintenance[:3]],'Sample of repeat maintenance exceptions')
    maintenance_proof = maintenance_samples+code_excerpt('03_performance_pack.py','prev_op =','prev_sp =')+source_link(SOURCE+'scripts/03_performance_pack.py','Maintenance filter and repeat-failure flag')
    section('maintenance','The maintenance list excludes non-operational assets',p(f'The annual return flags {low["Result"]} records below 90% monitor operation. The export removes records whose reason begins “No longer operational”, leaving {len(maintenance)} maintenance exceptions. Of these, {repeats} also fell below 90% in 2024. Those repeat records provide a practical starting point for fault review.')+bridge+reason_chart+note('Operational handover','Check current asset and fault status before raising work orders. A published reason identifies an investigation route; it does not establish whether the fault remains open or whether the proposed repair will reduce spills.')+disclosure('Repeat-failure records and maintenance filtering',maintenance_proof))

    basins = data['basins']
    basin_table = table(['Basin grouping','Listed overflows','Sites with 60+ spills','Share of listed sites'],[[r['river_basin'],n(r['Overflows']),n(r['Overflows 60+ spills 2025']),n(Decimal(r['Overflows 60+ spills 2025'])/Decimal(r['Overflows'])*100,1)+'%'] for r in basins],'The Trent grouping contains 58 of 76 high-spill sites, alongside the largest asset population')
    basin_table += '<p class="inline-source">Source: performance pack · By river basin. Groupings use waterbody-ID prefixes. Counts indicate review workload; the shares use all listed sites, including sites with missing spill counts. The small 27-site “Estuary / other” group warrants caution. Neither measure adjusts for environmental risk.</p>'
    annual_no_action = [r for r in data['high'] if r['No improvement action 2025']=='1']
    high_samples = table(['Asset ID','Site','2025 spills','Reported improvement activity'],[[r['unique_id'],r['site_name'],n(r['spills_2025']),r['improvement_activity']] for r in annual_no_action[:3]],'Sample of observed high-spill sites reporting no improvement action')
    high_proof = high_samples+code_excerpt('03_performance_pack.py','prev_sp =','# ---------- write workbook')+source_link(SOURCE+'scripts/03_performance_pack.py','Observed high-spill exception rules')
    section('operations','76 high-spill overflows need operational review',p(f'I screened the full 2025 return for sites with at least 60 recorded spills. The export contains {len(data["high"])} sites; {len(annual_no_action)} report “No improvement action in reporting period”. I would review those {len(annual_no_action)} records with Operations and Asset Planning first, then confirm the current programme and local environmental context.')+basin_table+note('Action status and interpretation','“No improvement action” is the published reporting-period description. It does not establish whether a site has been neglected, has no planned investment or has no investigation underway. The 60-spill threshold is a screening choice, not a legal compliance verdict.')+disclosure('Observed high-spill records and action-status rule',high_proof))

    persistent = data['persistent']
    persistent_no_action = sum(r['improvement_2025'].startswith('No improvement') for r in persistent)
    top = persistent[:5]
    persistent_chart = chart('A longer-term screen identifies sites for further investigation','Top five of 74 sites meeting the model-adjusted threshold in all three years. Values are three-year averages scaled to the model’s 1,000 mm reference; they are not observed annual spill counts.',bars([(r['site_name'],Decimal(r['adj_mean']),i==0) for i,r in enumerate(top)],210,1),['Asset ID','Site','Observed 2025 spills','Model-adjusted three-year average','Reported improvement activity'],[[r['unique_id'],r['site_name'],n(r['spills_2025']),n(r['adj_mean'],1),r['improvement_2025']] for r in top],'priority_overflows_persistent_high.csv · first five rows. This screen depends on the exploratory rainfall model.')
    cohort_table = table(['Screen','Population and rule','Flagged','No improvement action reported'],[
        ['Observed 2025 high spills','Full 2025 return; recorded spills ≥60',len(data['high']),len(annual_no_action)],
        ['Persistent model-adjusted high spills','1,802 linked sites with ≥90% operation in all three years; adjusted spills ≥60 each year',len(persistent),persistent_no_action]
    ],'Two review lists with different rules; they overlap and must not be added')
    panel_proof = p('The script links 2025 assets through 2024 IDs and the supplied old-ID field for 2023. It retains 1,802 sites with spill counts and monitor operation of at least 90% in all three years, then scales each year’s count using the exploratory regional rainfall model. All three adjusted values must reach 60. This is a screening model, not an engineering design assessment.')+code_excerpt('02_analysis.py','linked = panel.dropna','pr = reliable3[')+source_link(SOURCE+'scripts/02_analysis.py','Three-year linkage and adjusted screening rules')
    spills_persistent = sum(Decimal(r['spills_2025']) for r in persistent)
    share_all = spills_persistent/Decimal(years['2025']['total_spills'])*100
    section('persistent','Persistent high-spill screening adds a longer view',p(f'To look beyond a single year, I linked assets across 2023–2025 and retained sites with at least 90% monitor operation in every year. A separate, model-adjusted screen identifies {len(persistent)} persistent high-spill sites; {persistent_no_action} report no improvement action in 2025. This is a supplementary investigation list, distinct from the 76 observed high-spill sites.')+cohort_table+p(f'The 74 sites recorded {n(spills_persistent)} spills in 2025: {n(share_all,1)}% of all recorded Severn Trent spills, or 18.9% within the narrower 1,802-site panel. The denominator changes the interpretation. Some sites qualify after adjustment despite recording fewer than 60 spills in 2025.')+persistent_chart+note('Investment decision','Use this screen to select sites for evidence gathering. Local rainfall, hydraulic constraints, environmental sensitivity, existing work and cost would be needed to compare investment options. The list does not demonstrate an optimal allocation of capital.')+disclosure('Linked-panel construction and model-adjusted thresholds',panel_proof))

    section('actions','Recommended actions and measures',p('I produced a repeatable performance pack and separate lists for monitor maintenance, observed high spills and longer-term investigation. The proposed actions below describe how teams could use those outputs. No maintenance completion, approved investment or measured reduction from this analysis is claimed.')+table(['Action owner','Recommended action','Proposed success measure'],copy['actions'],'Recommended actions and proposed follow-up measures'))

    downloads = '<div class="actions"><a class="button" href="../projects/03_Severn_Trent/outputs/Severn_Trent_Overflow_Performance_Pack_2025.xlsx" download>Download the Excel performance pack <span aria-hidden="true">↓</span></a></div>'
    lists = '<div class="resource-list"><a href="../projects/03_Severn_Trent/outputs/priority_overflows_persistent_high.csv" download><span>Persistent high-spill investigation list ↓</span><small>CSV · 74 sites</small></a><a href="../projects/03_Severn_Trent/outputs/overflows_not_improving_2025.csv" download><span>Sites flagged as not improving by the model ↓</span><small>CSV · 65 sites</small></a></div>'
    limits = disclosure('Analytical limits and review notes',p('Annual spill counts do not measure discharge volume or environmental harm. Regional annual rainfall cannot describe individual storms. Qualifying monitor cohorts change between years; the five-observation rainfall model does not establish causation. Source reconciliation and exception resolution require the original files and service-owner input. The website reads committed outputs rather than rerunning the pipeline without its raw inputs.')+source_link(SOURCE+'outputs/05_Website_Validation_Notes.md','Evidence checks, reconciled counts and model limitations'))
    section('files','Deliverables and analytical limitations',p('The workbook includes annual KPIs, basin and asset summaries, return checks, large increases, maintenance exceptions and the observed high-spill list. The separate CSVs contain model-dependent longer-term screens. Inspect the rules alongside each list before using it.')+downloads+resources(project)+source_link(SOURCE+'scripts/01_build_clean_data.py','Python cleaning pipeline')+source_link(SOURCE+'scripts/02_analysis.py','Rainfall and longer-term screening analysis')+source_link(SOURCE+'scripts/03_performance_pack.py','Validation and performance-pack generation')+lists+limits)

    nav = ''.join(f'<a href="#{identifier}"><span aria-hidden="true">{i:02d}</span>{e(title)}</a>' for i,(identifier,title) in enumerate(headings,1))
    icons = ''.join(f'<span><img src="../assets/icons/{icon}" width="22" height="22" alt="">{name}</span>' for name,icon in [('Python','python.svg'),('Excel','excel.svg'),('Statistics','statistics.svg')])
    metrics = metric('41.3%','fewer recorded spills in 2025 · rainfall also fell')+metric('87','maintenance exceptions · 27 repeat low-operation records')+metric('13','observed high-spill sites reporting no improvement action')
    return f'''<main class="container finance-case water-case" id="main"><div class="breadcrumb"><a href="../index.html#projects">Selected projects</a> / Regulated utilities</div>
    <header class="finance-hero">{organisation(project,'../')}<span class="eyebrow">Performance reporting &amp; operational prioritisation</span><h1>{e(copy['title'])}</h1><p class="lead">{e(copy['summary'])}</p><div class="finance-meta"><span>Annual returns 2020–2025 · performance pack 2025</span><span>My role: independent analyst</span><div class="finance-tools">{icons}</div></div></header>
    <aside class="scenario-note" aria-label="About this case study"><strong>About this case study</strong>{p(copy['scenario_note'])}</aside><div class="finance-metrics" aria-label="Results at a glance">{metrics}</div>
    <div class="finance-layout"><nav class="finance-nav" aria-label="On this page"><strong>Follow the analysis</strong>{nav}</nav><div class="finance-content">{''.join(sections)}</div></div>
    <div class="next-project"><a href="../index.html#projects">← All projects</a><a class="button" href="{e(next_project['slug'])}.html">Next: {e(next_project['organisation'])} <span aria-hidden="true">→</span></a></div></main>'''
