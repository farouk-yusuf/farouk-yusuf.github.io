# Farouk Yusuf: data analyst portfolio

Live site: https://farouk-yusuf.github.io

Four projects on UK public data, each written up as the task an analyst in that organisation would be given:

| Project | Task | Start here |
|---|---|---|
| Birmingham City Council | Spend reporting and payment controls (SQL star schema) | [Management summary](projects/01_BCC_Payments/outputs/00_Management_Summary.md) |
| Platform Housing Group | Tenant satisfaction benchmarking for the board | [Board summary](projects/02_Platform_Housing/outputs/00_Board_Summary.md) |
| Severn Trent Water | Storm overflow return checks and performance pack | [Management summary](projects/03_Severn_Trent/outputs/00_Management_Summary_2025.md) |
| University Hospitals Birmingham | Monthly elective waiting times report | [Performance summary](projects/04_UHB_Waiting_Times/outputs/00_Performance_Summary.md) |

Each project folder has a README, the scripts to rerun the analysis, and an `outputs` folder with the summary, Excel pack, requirements brief and decisions note. Raw data is not stored here; each `source_log.csv` lists where it was downloaded from. All data is published under the Open Government Licence.

## Website development

The website is static HTML, CSS and JavaScript. It runs on GitHub Pages with no Node packages, framework or deployment build step. Charts use responsive HTML or generated SVGs with captions, source notes and expandable data tables; they work without JavaScript or an external chart service. Fonts are served locally.

From the repository root:

```sh
python3 -m http.server 5500 --bind 127.0.0.1
```

Use the existing checkout. Cloud tasks are already isolated; do not create a Git worktree unless explicitly requested.

### Editing and rebuilding

- `site/birmingham.json`: Birmingham’s agreed finance narrative, simulated brief, data request and recommendations.
- `site/platform.json`: Platform Housing’s tailored brief, requirements framework, data-access assessment and proposed service actions.
- `scripts/housing_story.py`: Platform Housing story and responsive HTML charts, populated from the committed benchmarking workbook.
- `site/severn-trent.json` and `scripts/water_story.py`: Severn Trent’s requirements, performance analysis and operational recommendations; figures and examples come from committed CSVs and the Excel pack.
- `scripts/story_workbook.py` and `scripts/story_components.py`: shared standard-library workbook reader and evidence markup for the Birmingham and Platform stories.
- `scripts/birmingham_story.py`: Birmingham page renderer; reads the committed Excel workbook, key-figures CSV, SQL results and department mapping code using the Python standard library.
- `assets/css/finance.css`: shared evidence-led case-study layout, responsive HTML charts, requirements frameworks and disclosures for Birmingham, Platform Housing and Severn Trent.
- `site/projects.json`: project copy, facts, limitations, dashboard plans and approved homepage STAR highlights.
- `site/about.json`: the agreed homepage introduction and the personal/professional timeline, dated employment events and milestone labels. The MSc dissertation mark is 82; the MA quantitative-module mark is 75%.
- `site/skills.json`: tool-slide names, icons and four business-focused capabilities per slide.
- `site/templates/home.html`: homepage structure; edit this rather than generated HTML.
- `site/templates/journey.html`: accessible HTML structure for the walking journey and ending panel.
- `site/resources.json`: the original GitHub write-up and download links.
- `scripts/build_site.py`: shared HTML components, homepage/research copy and chart definitions. Uses only the Python standard library.
- `assets/css/site.css`: shared layout, responsive styles, dark mode and print rules.
- `assets/css/home.css`: compact homepage layout, tool slides and detailed project highlights.
- `assets/css/journey.css` and `assets/js/journey.js`: the walking timeline, continuous scroll-driven poses, chapter controls and static reading layouts.
- `assets/js/site.js`: progressive enhancements for theme choice, the tool carousel and optional dashboard images.
- `index.html` and `case-studies/*.html`: generated pages committed for GitHub Pages. Update their source and rebuild rather than editing these files directly.

```sh
python3 scripts/build_site.py
python3 scripts/check_site.py
node --check assets/js/site.js
```

`build_site.py --check` checks freshness without changing files. `check_site.py` also checks local assets and fragment links, unique IDs, one main heading per page, data tables for charts and preservation of the 20 original project resource links. The original analytical scripts under `projects/` are separate and are not run by the website build.

For browser review, check all pages at desktop and narrow phone widths, keyboard navigation, tool selection, theme persistence and the chart data disclosures. The tool carousel advances every six seconds with a smooth crossfade. Visitors can also use the circular arrow controls, left/right keyboard arrows or tool icons. Autoplay stops while hovered or focused, while off-screen or in a hidden tab, and when reduced motion is requested. There are no playback buttons. Without JavaScript all tools remain visible. Do not treat build/link checks as validation of the original analytical calculations.

With Playwright and Chromium installed, run `python3 scripts/check_homepage_browser.py` for automated homepage interaction checks. It starts a temporary local server and does not require a manually started development server.

### Power BI and organisation logos

The About journey uses a six-screen scroll section on desktop, with a sticky scene and a native scroll handler. It does not intercept wheel or touch input and needs no external animation library. The walker stays at 35% of the viewport, uses continuous limb movement only while scrolling, reverses with scroll direction and accumulates six milestone patches on an illustrated backpack. Graduation dates add a cap and gown; the 2023 marriage pin adds a wedding suit and an illustrated partner in a wedding dress, strictly after the 2023 tick. Hearts and sparkles stay visible at that stop, and a finite confetti burst replays on each return. The final chapter switches to business attire. HTML callouts, year ticks from 2019 to 2026, employment start/end pins and the ending panel remain readable in document order. Chapter dots support native links and keyboard activation, including direct URL fragments.

Below 768px, on short viewports, with reduced motion, without JavaScript or when printing, the route becomes a static list. Desktop visitors can also choose **Read as a list**. Chapter copy follows the user-supplied script, with grammatical corrections only; wider desktop cards accommodate it in full. `python3 scripts/check_journey_browser.py` validates movement, reversal, patches, date-driven outfits, the repeatable post-2023 wedding celebration and persistent sparkles, CV employment markers, chapter jumps and reading fallbacks with Playwright.

Employment dates come from the supplied CV: University of Birmingham Research Associate (September 2021–January 2022), Charis Care Solutions Support Worker (February–December 2022), and freelance NatCen interviewer (September 2024–January 2025). Outlier is described as freelance but remains undated because it is absent from that CV. The CV itself is not published. Chevening is described without an applicant count or acceptance-rate claim; its official programme background is linked.

The user-supplied portrait is at `assets/images/headshot-3.png`, copied unchanged from `assets.zip`; the three supplied organisation logos are in `assets/logos/`. The build also supports a replacement portrait named `headshot-3.jpg`, `.jpeg` or `.webp`. Do not substitute a generated portrait.

The dashboards are planned work. When ready, add `assets/bcc-dashboard.png` and `assets/uhb-dashboard.png`, then rebuild. The original paths are preserved. Missing previews are omitted at build time; if a published image subsequently fails, JavaScript hides its container. No dashboard or deployment is implied by a placeholder.

Logo provenance is documented in [assets/logos/README.md](assets/logos/README.md). Organisation names and marks identify the subjects of independent analysis and do not imply employment, affiliation or endorsement.

### Before external publication

The research page retains the existing unpublished thesis figures and the supervisor-sign-off caveat. Confirm clearance for exact results. The Severn Trent page distinguishes 90 low-operation flags from 87 maintenance exceptions after excluding records labelled “No longer operational”; its model-dependent screening and remaining reporting checks are explained alongside the findings. The UHB scenario remains labelled as a scenario because the baseline outperformed both forecast models.

### Birmingham finance story

The Birmingham case study presents the simulated finance brief separately from actual analysis and results. The opening requirements summary links the business problem, core questions, relevance and scope. An expandable requirements elicitation template covers decision, stakeholders, scope, measures, data access, validation, delivery, acceptance and service-level targets. Its project applications explicitly distinguish completed analysis, scenario assumptions, items needing stakeholder confirmation and elements outside scope. Dataset and data-owner fields are separate columns. Evidence disclosures use content-specific titles. Each section links to relevant source code or workbook evidence. Its navigation uses the same titles as the sections. Three responsive HTML charts show matched-period payments, directorate contributions to the change, and the duplicate-screening stages, with data tables for all three.

The initial SQL query produces 6,553 candidate pairs. The refinement in `03_finance_pack.py` keeps supplier–amount combinations occurring exactly twice, then checks the three-day gap. The final list has 281 pairs, including 73 same-day pairs. Its £4.45m value counts one potentially repeated amount per pair; it is not a confirmed loss or a delivered saving.

Run `python3 scripts/check_finance_browser.py` with Playwright and Chromium installed to check the figures against existing workbook/CSV outputs, department mappings, matching navigation, evidence disclosures, downloads and responsive reading layouts. The raw payment CSV is not committed, so these website checks do not rerun the original analysis or independently validate the source publication. The workbook and other original resource links remain available.

### Platform Housing service story

The Platform page separates its simulated board brief from the actual published-data analysis. It explains the 17-landlord TSM cohort (including Platform), uses five accessible HTML charts with data tables, and links recommendations to peer gaps, landlord-level associations and complaint categories. The requirements framework identifies outstanding internal access, definition checks, acceptance criteria and service-owner decisions. All original resource links remain available.

Read [the evidence review](projects/02_Platform_Housing/outputs/03_Website_Validation_Notes.md) alongside the preserved workbook. It qualifies survey comparability, treats possible recording changes as hypotheses, and flags the unresolved Ombudsman rate/count discrepancy: 51/137 gives 37.2%, while the extraction records 38%. The repairs category contains 43 findings, of which 23 are adverse. The website holds the rate/ranking from a formal conclusion pending source verification.

Run `python3 scripts/check_housing_browser.py` with Playwright and Chromium to verify workbook arithmetic, cohort definitions, evidence disclosures, downloads, navigation and responsive reading. These checks use committed outputs; they do not rerun the original pipeline without its raw files.

### Severn Trent performance analysis

The Severn Trent page separates a simulated internal brief from the actual public-data analysis. Six HTML charts explain the annual spill/rainfall changes, the dry-year comparison, maintenance reasons, basin workloads and a longer-term model-adjusted screen. Each chart has a data table; evidence disclosures link source code and actual asset examples. The requirements framework distinguishes analytical thresholds from operational SLAs and investment approval.

The observed 2025 list has 76 sites with at least 60 recorded spills, 13 reporting no improvement action. The separate model-adjusted three-year list has 74 sites, 17 reporting no action; the lists overlap. Persistent sites account for 13.4% of all recorded 2025 spills, or 18.9% within the linked panel. Rainfall comparisons do not establish causation. The original summaries now carry those qualifications; the workbook is preserved unchanged. Read [the evidence review](projects/03_Severn_Trent/outputs/05_Website_Validation_Notes.md) alongside it.

Run `python3 scripts/check_water_browser.py` with Playwright and Chromium to check output reconciliation, model arithmetic, screening rules, downloads, evidence interactions and responsive layouts. It uses committed outputs, not unavailable raw files. The existing site and housing checks also cover the shared workbook reader and presentation helpers.
