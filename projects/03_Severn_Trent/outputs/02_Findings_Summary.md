# Findings: Severn Trent storm overflows, 2020-2025

*Analysis of Environment Agency monitoring returns and Met Office rainfall. Scripts describe the original pipeline; rerunning it requires raw inputs not committed here. See the [evidence review](05_Website_Validation_Notes.md) for qualifications to the preserved workbook and charts.*

## Headline
Severn Trent's recorded spills fell 41% in 2025 (62,085 to 36,471) and spill hours fell 56%. Midlands rainfall was 28% lower than 2024. **The decline cannot be attributed entirely to improvement work.** A five-observation rainfall model and a comparison with the similarly dry year of 2022 provide context, but neither isolates the effect of investment.

## 1. How much of the 2025 fall was the weather?
- Among overflows with monitors working at least 90% of the year, average spills fell from 25.1 (2024) to 15.0 (2025).
- Fitting a line to 2020–2024 annual rainfall and qualifying-overflow averages gives an association of about **1.6 additional average spills per 100 mm**. The line estimates 21.4 at 2025 rainfall, versus 15.0 observed. The slope-based rainfall component is about 46% of the fall in this average; it is an exploratory association, **not a causal share explained by weather**.
- The model is indicative only. It rests on five years and explains under half the year-to-year variation (R² = 0.48), because annual totals miss how intense individual storms were.
- **A second comparison uses similar annual rainfall:** 2022 and 2025 had 721.4 mm and 716.6 mm respectively. Average spills per qualifying overflow fell from 19.4 to 15.0, about **23%**. This is not fully like-for-like: the populations differ (1,737 vs 2,342 qualifying assets), and regional annual totals do not match individual storms.

## 2. Monitoring reliability
- The share of overflows whose monitors worked less than 90% of the year fell from **30% in 2022 to 4% in 2025**.
- Monitoring gaps may miss events. These outputs cannot establish how many events were missed or the net direction of bias in the year-on-year change. The legacy low-operation share also mixes populations in its numerator and denominator; see the evidence review before treating it as a monitoring-completeness measure.

## 3. Investment priorities
- 1,802 overflows had reliable monitoring in all three years 2023-2025.
- **74 sites (4% of the panel) reached 60 model-adjusted spills in every year.** This does not mean each recorded 60 observed spills annually: 36 recorded fewer than 60 in 2025. Their 4,895 observed 2025 spills are **18.9% of spills within the 1,802-site panel**, or **13.4% of all recorded company spills**.
- 33 of the 74 are storm tanks at sewage treatment works (plus one tank classified as having treatment). This supports investigating treatment-work constraints alongside network issues; it does not establish the cause or optimal investment.
- **17 of the 74 reported no improvement action in 2025.** These are candidates for status verification. The observed 2025 high-spill list has a different rule: 76 sites with at least 60 recorded spills, of which 13 report no improvement action. The lists overlap and must not be added.
- A further 65 overflows (with 30+ spills a year) did not improve in 2025 even after allowing for the dry weather.
- Full lists: `priority_overflows_persistent_high.csv`, `overflows_not_improving_2025.csv`.

## 4. Context against other companies
- All ten companies fell in 2025; nationally spills per overflow fell 35% while England rainfall fell 23%.
- Comparing 2022 with 2025 (similar national rainfall), Severn Trent's fall of 18% is among the larger ones, behind United Utilities (24%) and Anglian (21%). Company comparisons use national rainfall, so treat them as context, not a ranking.

## Recommendations
1. Report observed performance alongside rainfall and monitor-coverage context. Label model-adjusted measures exploratory and explain their assumptions.
2. Review the 17 persistent high-spillers with no 2025 improvement action first.
3. Investigate storm-tank capacity and other local constraints before comparing interventions; engineering, environmental and cost evidence is needed.
4. Agree monitor-availability targets and fault-response times with Maintenance. Review the 27 repeat low-operation records among the 87 exported exceptions; no new service target has been agreed in this portfolio exercise.

## Limitations
Annual totals only (no storm intensity); one regional rainfall series for the whole company area; five-year model; 2025 figures as published by the EA in August 2026.
