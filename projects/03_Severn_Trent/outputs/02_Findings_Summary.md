# Findings: Severn Trent storm overflows, 2020-2025

*Analysis of Environment Agency monitoring returns and Met Office rainfall. All figures reproducible from `scripts/`.*

## Headline
Severn Trent's recorded spills fell 41% in 2025 (62,085 to 36,471) and spill hours fell 56%. But Midlands rainfall was 28% lower than 2024. **Roughly half of the fall is explained by the drier year. The rest is consistent with real improvement**, and the clearest evidence is a like-for-like comparison with 2022, an equally dry year.

## 1. How much of the 2025 fall was the weather?
- Among overflows with monitors working at least 90% of the year, average spills fell from 25.1 (2024) to 15.0 (2025).
- Fitting spills against rainfall for 2020-2024 gives about **1.6 extra spills per overflow for every 100 mm of extra rain**. On that basis, 2025's rainfall alone predicts about 21.4 spills per overflow. The actual figure was 15.0, about **30% below expectation**. Rainfall accounts for about 46% of the 2024-25 fall.
- The model is indicative only. It rests on five years and explains under half the year-to-year variation (R² = 0.48), because annual totals miss how intense individual storms were.
- **The stronger evidence is the like-for-like comparison:** 2022 and 2025 had almost identical rainfall (721 mm vs 717 mm). Average spills per reliably monitored overflow fell from 19.4 to 15.0, a **23% reduction at the same rainfall**.

## 2. Monitoring reliability
- The share of overflows whose monitors worked less than 90% of the year fell from **30% in 2022 to 4% in 2025**.
- That means earlier years under-recorded spills. A simple year-on-year comparison of totals therefore *understates*, not overstates, Severn Trent's improvement. (My starting hypothesis was the reverse; the data showed otherwise.)

## 3. Investment priorities
- 1,802 overflows had reliable monitoring in all three years 2023-2025.
- **74 overflows (4% of them) spilled 60 or more times a year in every year, even after adjusting for rainfall. Together they produced 19% of 2025 spills.**
- 33 of the 74 are storm tanks at sewage treatment works, so capacity at treatment works is a bigger issue than the network alone.
- **17 of the 74 reported no improvement action in 2025.** These are the first candidates for review.
- A further 65 overflows (with 30+ spills a year) did not improve in 2025 even after allowing for the dry weather.
- Full lists: `priority_overflows_persistent_high.csv`, `overflows_not_improving_2025.csv`.

## 4. Context against other companies
- All ten companies fell in 2025; nationally spills per overflow fell 35% while England rainfall fell 23%.
- Comparing 2022 with 2025 (similar national rainfall), Severn Trent's fall of 18% is among the larger ones, behind United Utilities (24%) and Anglian (21%). Company comparisons use national rainfall, so treat them as context, not a ranking.

## Recommendations
1. Report 2025 performance alongside a rainfall-adjusted measure, so a dry year isn't presented as the full improvement and a wet 2026 doesn't look like a reversal.
2. Review the 17 persistent high-spillers with no 2025 improvement action first.
3. Prioritise storm tank capacity at treatment works, which account for almost half the persistent cases.
4. Keep monitor reliability above 95%; the gains since 2022 are what make these comparisons trustworthy.

## Limitations
Annual totals only (no storm intensity); one regional rainfall series for the whole company area; five-year model; 2025 figures as published by the EA in August 2026.
