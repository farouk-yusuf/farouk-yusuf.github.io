# Data-quality log

| # | Issue | Impact | Resolution |
|---|---|---|---|
| 1 | Column formats change between years: EDM operation stored as a fraction (2020-22) and as a percentage (2023-25); spill duration as decimal hours (2020-23), hh:mm:ss durations (2024) and time-of-day values for spills under 24 hours (2025) | Mis-scaled values would corrupt every comparison | Converted all to percentage and decimal hours in `to_hours()` / scale factors; totals reconciled to EA summaries |
| 2 | Header row position and sheet names differ by year (row 2 vs row 6; "Severn Trent 2024" vs "Severn Trent Water") | Wrong rows read as data | Header row and sheet set explicitly per year |
| 3 | Two columns both called "Site Name" (EA name and company name) | Column clash on load | De-duplicated headers; EA consent name used as the primary name |
| 4 | 2021: 25 overflows have Excel `#N/A` errors for spills and duration; 246 listed without spill data, many with permit "TBC" | Missing spill counts | Treated as missing, flagged `dq_no_spill_data`; excluded from averages |
| 5 | 2021 totals differ from the EA summary by 8 spills and 7 hours (0.01%) | Negligible | Logged; overflow-level file used as-is |
| 6 | Overflow IDs changed in 2024 (SVE to SVT format) | Overflows couldn't be tracked across years | Linked via the "old format Unique ID" column: 2,382 of 2,452 2025 overflows linked to 2023 |
| 7 | The original low-operation share falls from about 30% in 2022 to 4% in 2025; its numerator and denominator have different inclusion rules | Monitoring gaps may miss events; the net bias in the trend is not quantified | Compare qualifying-monitor averages with explicit populations; do not infer a causal improvement from coverage alone |
| 8 | Character encoding error in source text (e.g. "PAUPER¿S DRAIN") | Cosmetic | Replaced with apostrophe |
| 9 | 2025 file re-issued by EA in August 2026 (Anglian Water resubmission) | None for Severn Trent | Used the latest version; noted |

All other 2020-2025 Severn Trent totals reconcile exactly with the EA's published summary tables.

These are the original pipeline's recorded source checks, not a new independent verification of raw files. The website reads committed outputs only. For the maintenance filter (90 flagged versus 87 exported), review statuses, model assumptions and denominator corrections, see [the website validation notes](05_Website_Validation_Notes.md).
