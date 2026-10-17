# Severn Trent storm overflows: 2025 performance pack

The task an analyst at a water company would be given: check the annual monitoring return, produce the year-end performance pack, and send exception lists to the teams who act on them.

**Start here:** `outputs/00_Management_Summary_2025.md` and `outputs/Severn_Trent_Overflow_Performance_Pack_2025.xlsx`

Public data: Environment Agency Event Duration Monitoring annual returns 2020-2025; Met Office HadUK-Grid regional rainfall (Open Government Licence).

- `scripts/01_build_clean_data.py` combines six years of returns (four different formats) into one clean overflow-year table
- `scripts/03_performance_pack.py` QA checks, KPIs by river basin and asset type, maintenance and high-spill exception lists (Excel)
- `scripts/02_analysis.py` supporting analysis: rainfall context and three-year persistent high-spillers
- `outputs/` summary, workbook, brief, data-quality log, decisions note, charts
- `raw/` untouched downloads (`source_log.csv`); `clean/` cleaned data

Run: `python3 scripts/01_build_clean_data.py && python3 scripts/02_analysis.py && python3 scripts/03_performance_pack.py`
