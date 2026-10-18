# Severn Trent: evidence checks and interpretation

The website review uses the committed workbook, CSV outputs and source code. It does not rerun the pipeline or independently verify the original Environment Agency spreadsheets and Met Office downloads, which are not committed. The analytical workbook is preserved unchanged; the qualifications below apply to its figures and interpretation.

## Annual figures and measures

- Recorded spills: **62,085 in 2024 → 36,471 in 2025**, down **41.3%**. These figures agree between the yearly CSV and workbook KPIs.
- Annual Midlands rainfall: **1,000.2 mm → 716.6 mm**, down **28.4%**. Rainfall is context, not a proportional adjustment to observed spills.
- Spills use the EA 12/24-hour counting method. Counted spills and duration do not measure discharge volume or environmental harm.
- The workbook's basin groups come from waterbody-ID prefixes. The largest grouping also contains the most assets; raw counts are operational workload, not a risk-adjusted performance ranking.

## Maintenance: 90 flagged records versus 87 exported exceptions

The QA sheet and yearly CSV record **90** low-operation flags in 2025. The maintenance script explicitly excludes records whose reason begins **“No longer operational”**. The maintenance sheet contains **87** records after that filter, including **27** repeat low-operation records from 2024. The three-record difference is consistent with the documented export rule; it is not a second estimate of the same operational list. Raw excluded records are unavailable for independent reinspection.

Reported primary reasons for the 87 exported records sum to 87: installation/design 29, sensor faults 21, communications faults 18, telemetry/archiving 11, works affecting operation 5, power faults 2 and logger access 1. These are published reasons, not independently verified fault diagnoses. Current status must be checked before raising maintenance work.

## Return checks are not complete sign-off

The QA sheet contains **five Pass**, **five Review** and **one Info** entries. Review items include **21 missing spill counts**, **90 low-operation flags**, **11 new IDs**, **18 removed IDs** and **two increases of at least 50 spills**. Zero duplicate IDs or missing low-operation reasons does not resolve these review items. The original cleaning flag for operation above 100% uses a **100.5% tolerance**. The duration limit used by the performance-pack check is 8,760 hours for 2025.

The original data-quality log records an eight-spill/seven-hour reconciliation difference in 2021 and agreement in other years. Those source-level reconciliations cannot be independently repeated from committed outputs alone.

## Rainfall comparisons and model

- The dry-year comparison uses **1,737** qualifying overflows in 2022 and **2,342** in 2025. Each has spill data and monitor operation ≥90% of the year. Mean recorded spills fall **19.415 → 15.011**, or **22.7%**, while annual regional rainfall is similar (**721.4 mm vs 716.6 mm**).
- This is **not a fixed-cohort or fully controlled comparison**. Qualifying assets differ, some monitoring time is still missing, and similar annual rainfall totals do not match local storm patterns. The comparison does not identify the effect of investment.
- The original model fits a line to **five annual observations, 2020–2024**. Its slope is about 1.62 additional average spills per 100 mm, with training R² about 0.48. It estimates 21.45 spills per qualifying overflow at 2025 rainfall, versus 15.01 observed.
- Multiplying the fitted slope by the rainfall change gives about **45.5%** of the observed decline in the qualifying-overflow average. This is an **exploratory model-associated component**, not a causal claim that weather explains exactly half the change. No causal share is assigned to improvement work.
- The legacy low-operation share divides all low-operation flags by records with spill data. Its numerator and denominator do not necessarily describe identical populations. It should not be treated as an exact complement of the qualifying-monitor share. The website explains populations explicitly instead of using that share to correct spill totals.
- Monitoring gaps can miss events, but these outputs do not establish the size or direction of the net bias in year-on-year change. Earlier claims that raw totals necessarily understate improvement are not supported.

## Separate observed and model-adjusted review lists

| List | Rule and population | Sites | No improvement action reported |
|---|---|---:|---:|
| Observed 2025 high spills | Full return; recorded spills ≥60 | 76 | 13 |
| Persistent model-adjusted high spills | Linked 2023–2025 panel, monitor operation ≥90% in every year; adjusted spills ≥60 in all three years | 74 | 17 |

These lists overlap and must not be added. **36 of the 74** model-adjusted sites recorded fewer than 60 observed spills in 2025. “No improvement action” is the published reporting-period description; it does not imply no investigation, no planned investment or a current lack of action.

The panel construction retains **2,382** sites with linked spill counts, then **1,802** with qualifying operation in all three years. The 74 persistent sites recorded **4,895** spills in 2025: **13.4% of all 36,471 recorded company spills**, or **18.9% within the narrower 1,802-site panel**. The previously reported 19% must retain that panel denominator.

The separate 65-site “not improving” CSV also depends on the rainfall model: its adjusted 2025 count is at least the adjusted 2023–2024 mean, from an earlier mean of at least 30. It is a screening flag, not an independently established engineering outcome.

## Operational use

The deliverables are an Excel pack and investigation lists. Internal owners would need to confirm asset and programme status, local rainfall, environmental risk, costs, response targets and reporting acceptance before action or investment. No regulatory approval, completed maintenance, cost saving or reduction caused by this portfolio analysis is claimed.
