# Platform Housing Group: tenant satisfaction benchmarking

The annual task for a housing association performance or insight analyst: benchmark the Tenant Satisfaction Measures against peers for the board, identify priorities, and sense-check the data first.

**Start here:** `outputs/00_Board_Summary.md` and `outputs/Platform_TSM_Benchmarking_Pack.xlsx`

Data: Regulator of Social Housing TSM full data 2023/24 and 2024/25; Housing Ombudsman landlord performance reports 2025/26 (Open Government Licence).

- `scripts/01_extract_ombudsman.py` extracts headline and category figures from 21 Ombudsman PDF reports
- `scripts/02_tsm_benchmark.py` benchmarks TSMs against peer groups, driver analysis, survey-method check, Excel pack and charts
- `clean/` extracted and combined tables; `outputs/` summary, pack, brief, decisions note, charts

Run: `python3 scripts/01_extract_ombudsman.py && python3 scripts/02_tsm_benchmark.py`
