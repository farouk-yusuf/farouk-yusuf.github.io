# UHB: evidence review and reporting qualifications

This review checks the committed `UHB_RTT_Performance_Report.xlsx`, key-figures CSV and Python scripts. It does not rerun the original pipeline or independently verify the national extracts, which are not committed. The workbook is preserved unchanged.

## Reporting unit and scope

- The series covers **41 months, April 2023–August 2026**, for UHB, with a latest-month benchmark of UHB, six selected Midlands trusts and England.
- The waiting list is **incomplete RTT pathways with known clock-start dates**, not unique people. The same person can have multiple pathways. The 52+ figures use the same pathway reporting unit.
- Clock starts record new pathways. Clock stops include treatment and other qualifying pathway endings; they are not a direct measure of theatre capacity, treatment slots or staff productivity.
- The latest benchmark is descriptive. Similar list sizes do not establish matched specialty mix, complexity, referral patterns or local conditions. England is a national comparator, not an eighth peer trust.

## Extraction and validation

The original analysis found that `Part_2` rows left `Total` blank. The revised extractor sums weekly wait bands into `known_clock_start`, retains unknown starts and `Total All`, and aggregates commissioner rows to provider/specialty level. The reporting script uses the `Total` treatment-function row separately from the component specialties.

The committed workbook records no missing provider-months across the selected organisations and zero latest-month UHB unknown clock starts. All 41 committed UHB trend rows have zero unknown starts. These are aggregate checks, not proof that every source row is complete. In particular, the extractor **does not enforce an assertion that weekly bands plus unknown starts equal `Total All`**. An operational release needs that source-row reconciliation.

The 23 latest specialty rows sum to **96,303 waiting pathways** and **175 pathways at 52+ weeks**, matching the trust totals. This reconciliation was checked against committed outputs during the website review.

## Recovery and current pressure

- March 2026 waiting list: **89,544**; August: **96,303**, an increase of **6,759 (7.5%)**.
- Under-18-week performance: March **68.60%**, June **68.93%**, August **66.60%**. August 2025 was **55.73%**. Percentages in the trend workbook are rounded to two decimals; headline figures use one decimal.
- 52+ week pathways fell from **397 in March** to **175 in August**. A larger total list can coexist with fewer very long waits.
- The original pack carries March planning references from a secondary Shelford Group dashboard. This review does not independently confirm current official NHS planning requirements or certify compliance. A list-size scenario cannot establish future performance against an under-18-week percentage target.

## April–August stock-flow reconciliation

| Component | Pathways |
|---|---:|
| Opening waiting list, March 2026 | 89,544 |
| Add clock starts, April–August | +133,091 |
| Subtract clock stops, April–August | −104,806 |
| Unclassified net residual | −21,526 |
| Closing waiting list, August 2026 | 96,303 |

Starts minus stops is **28,285**, while the actual list increase is **6,759**. The **−21,526 residual** reconciles the arithmetic but does not identify specific removals or prove that any adjustment was valid. Obtain coded removals, transfers, corrections and reporting adjustments from the data owners before assigning causes.

Against the same months in 2025, starts increased from **115,481 to 133,091 (+15.2%)**, while stops increased from **103,997 to 104,806 (+0.8%)**. This supports investigating pressure from additions. It does not establish “demand, not capacity” as a complete explanation, or demonstrate unchanged operational capacity.

## Specialty review priorities

- ENT has **57** and Ophthalmology **53** pathways at 52+ weeks: **110 of 175 (62.9%)**. Their under-18-week percentages also improved over the year. Concentration and direction of change answer different questions.
- Gynaecology's list grew **6,379 → 8,831 (+38.4%)**, while its under-18-week percentage fell **56.8% → 45.9%**. It has just one 52+ pathway, so ranking services on longest waits alone would miss its wider pressure.
- These are operational review priorities, not individual clinical triage decisions. Further interpretation needs pathway stage, appointment supply, cancellations, referral patterns and clinical priority.

## Model validation and scenario precision

- The held-out test is **March–August 2026**; training ends in February 2026. The no-change baseline holds February's waiting list at **91,407** for all six months.
- Mean absolute percentage errors in the workbook are **2.50% baseline**, **6.07% trend**, **8.40% demand/capacity**. Recalculating them from the rounded six-month predictions reproduces the reported two-decimal results. These errors are not confidence levels.
- Both models continued the earlier decline. In August, the actual list is **96,303**, the demand/capacity model **80,236**, and the trend **84,715**. The simple baseline is closer over the test period. One holdout is limited evidence; further rolling tests would be appropriate before operational adoption.
- The original continuation model repeats seasonal starts/stops, scales them by recent year-on-year ratios and carries forward the average historical stock-flow residual. It does not independently explain or validate that residual.
- The workbook's March 2027 scenario is **107,190**, rounded from the unrounded model. The key-figures CSV truncates the same estimate to **107,189**. The website uses the workbook's rounded series consistently.
- The workbook has **seven** future months, September 2026–March 2027. Its implied increase is **10,887** pathways. Dividing by seven gives approximately **1,555 additional clock stops a month** to hold the modelled list flat if all other assumptions remain unchanged. This is a scenario calculation, not a feasible capacity target or a count of additional treatments.
- No forecast interval, intervention benefit or probability of missing a future waiting-time standard is established.

## Operational use

Before release, reconcile source-row totals and the stock-flow residual, confirm policy references, obtain service-owner explanations and validate any capacity assumptions. Deliverables here are the Excel report and analysis; no stakeholder approval, deployed dashboard, extra clinical capacity or recovery benefit is claimed.
