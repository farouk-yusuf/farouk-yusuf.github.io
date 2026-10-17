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

The website is static HTML, CSS and JavaScript. It runs on GitHub Pages with no Node packages, framework or deployment build step. Charts are generated SVGs with captions, source notes and expandable data tables; they work without JavaScript or an external chart service. Fonts are served locally.

From the repository root:

```sh
python3 -m http.server 5500 --bind 127.0.0.1
```

Use the existing checkout. Cloud tasks are already isolated; do not create a Git worktree unless explicitly requested.

### Editing and rebuilding

- `site/projects.json`: project copy, facts, limitations and dashboard plans.
- `site/resources.json`: the original GitHub write-up and download links.
- `scripts/build_site.py`: shared HTML components, homepage/research copy and chart definitions. Uses only the Python standard library.
- `assets/css/site.css`: shared layout, responsive styles, dark mode and print rules.
- `assets/js/site.js`: progressive enhancements for theme choice, sector filters and optional dashboard images.
- `index.html` and `case-studies/*.html`: generated pages committed for GitHub Pages. Update their source and rebuild rather than editing these files directly.

```sh
python3 scripts/build_site.py
python3 scripts/check_site.py
node --check assets/js/site.js
```

`build_site.py --check` checks freshness without changing files. `check_site.py` also checks local assets and fragment links, unique IDs, one main heading per page, data tables for charts and preservation of the 20 original project resource links. The original analytical scripts under `projects/` are separate and are not run by the website build.

For browser review, check all pages at desktop and narrow phone widths, keyboard navigation, the sector filters, theme persistence and the chart data disclosures. Also check the pages with JavaScript disabled. Do not treat build/link checks as validation of the original analytical calculations.

### Power BI and organisation logos

The dashboards are planned work. When ready, add `assets/bcc-dashboard.png` and `assets/uhb-dashboard.png`, then rebuild. The original paths are preserved. Missing previews are omitted at build time; if a published image subsequently fails, JavaScript hides its container. No dashboard or deployment is implied by a placeholder.

Logo provenance and the remaining official-logo download limitation are documented in [assets/logos/README.md](assets/logos/README.md). Organisation names and marks identify the subjects of independent analysis and do not imply employment, affiliation or endorsement.

### Before external publication

The research page retains the existing unpublished thesis figures and the supervisor-sign-off caveat. Confirm clearance for exact results. The Severn Trent case study explicitly flags an unreconciled low-uptime monitor count (87 in the narrative versus 90 in the yearly CSV). Resolve the denominator before reporting one total. The UHB scenario remains labelled as a scenario because the baseline outperformed both forecast models.
