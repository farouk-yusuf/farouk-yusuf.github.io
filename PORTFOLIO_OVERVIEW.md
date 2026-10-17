# Data analyst portfolio: four projects on real UK public data

Each project is written as a task an analyst would be given in that organisation, using the data the organisation or its regulator publishes. Every figure is reproducible from the project's `scripts/` folder.

| Project | The task | Tools | Start here |
|---|---|---|---|
| Birmingham City Council | Monthly spend report, year-to-date variance, payment-control exceptions, personal-data check | SQL (SQLite star schema), Python, Excel | `01_BCC_Payments/outputs/00_Management_Summary.md` |
| Platform Housing Group | Annual Tenant Satisfaction Measures benchmarking for the board, with Ombudsman complaint outcomes | Python (PDF extraction), Excel | `02_Platform_Housing/outputs/00_Board_Summary.md` |
| Severn Trent Water | Check the annual storm overflow return, build the year-end performance pack, send exception lists | Python, Excel | `03_Severn_Trent/outputs/00_Management_Summary_2025.md` |
| University Hospitals Birmingham | Monthly elective waiting-times report with demand vs capacity and a back-tested forecast | Python, Excel | `04_UHB_Waiting_Times/outputs/00_Performance_Summary.md` |

## CV bullets (all figures from the analysis)

**Spend and payment controls: Birmingham City Council** | SQL, Python, Excel
- Built a SQL star schema from 247,785 council payments (£3.9bn, 2024-26) and produced the monthly spend and year-to-date variance report by directorate.
- Flagged 281 possible duplicate payments worth £4.45m and 260 duplicate supplier records for accounts-payable review.
- Found that 213 payments to individuals could be re-identified despite name redaction; pseudonymised them and set out the issue for information governance.

**Tenant satisfaction benchmarking: Platform Housing Group** | Python, Excel
- Benchmarked Platform's 22 Tenant Satisfaction Measures against 17 large housing associations and identified the three priorities most linked to overall satisfaction.
- Extracted Housing Ombudsman figures from 21 PDF reports; showed Platform has the lowest maladministration rate of 21 Midlands landlords (38% vs 57%).
- Caught a reported 29-point fall in repairs performance that the underlying counts showed was a recording change, before it reached the board.

**Storm overflow performance pack: Severn Trent Water** | Python, Excel
- Validated the 2025 Environment Agency return for 2,452 overflows and combined six years of returns in four different formats into one dataset.
- Built the year-end performance pack; flagged 27 repeat monitor failures for maintenance and 13 high-spilling overflows with no improvement action for investment review.
- Showed that roughly half of the 41% fall in 2025 spills was explained by drier weather.

**Elective waiting times: University Hospitals Birmingham** | Python, Excel
- Processed 41 monthly NHS England extracts (3.3 GB) to report UHB against waiting-time milestones, six Midlands trusts and England.
- Showed the waiting list's 7.5% growth since March 2026 was driven by a 15% rise in referrals, not falling activity, and estimated the extra activity needed to hold it flat.
- Back-tested two forecasting models, reported that both missed the turning point, and presented the outlook as a scenario.
