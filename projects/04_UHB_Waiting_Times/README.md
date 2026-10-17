# University Hospitals Birmingham: elective waiting times report

The monthly report an NHS trust performance analyst produces: progress against national waiting-time milestones, why the list is moving, specialty hotspots, peer benchmarking and a forecast.

**Start here:** `outputs/00_Performance_Summary.md` and `outputs/UHB_RTT_Performance_Report.xlsx`

Data: NHS England Referral to Treatment full monthly CSV extracts, April 2023 to August 2026 (Open Government Licence).

- `scripts/01_extract.py` reads 41 monthly extracts (80 MB each) and keeps UHB, six Midlands peers and an England total at trust-specialty level
- `scripts/02_performance_report.py` KPIs, demand vs capacity, specialties, benchmark, back-tested forecast, Excel report and charts
- `clean/monthly_v2/` extracted data (`clean/monthly/` is the superseded first run); `outputs/` summary, report, brief, decisions note, charts

Run: `python3 scripts/01_extract.py && python3 scripts/02_performance_report.py`
