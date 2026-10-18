# Decisions and reasoning (interview prep)

**Why only monitors working 90%+ of the year?** A monitor that was down for half the year records fewer spills because it missed them, not because the overflow behaved better. Including those would mix data gaps with performance. 90% is the EA's own reporting threshold.

**Why average spills per overflow, not totals?** Reporting populations change. The listed count is 2,288 in 2020 and 2,452 in 2025, while the count with spill data is 2,288 and 2,431. Averages reduce the influence of population size, but changing asset composition still affects interpretation.

**Why a simple straight-line rainfall model?** Five years of data can't support anything more complex. I report it as indicative, and lean on the 2022 vs 2025 comparison, which needs no model at all.

**Why the 60-spill threshold?** It's the high-spill level the EA uses in its own summary tables, so a regulator would recognise it.

**Why use a rainfall-adjusted screen?** It provides a supplementary way to examine repeated high counts when annual rainfall differs. The common 1,000 mm reference uses the fitted regional model; it does not control local storm patterns or put every site on a fully equivalent footing. Keep this model-dependent list separate from observed 2025 high spills.

**How did the review change the interpretation?** Monitoring coverage improved, but these annual outputs cannot quantify missed spills or establish the net direction of bias in the trend. The website avoids attributing the remaining reduction to investment or presenting the five-observation rainfall model as causal evidence.

**Why 90 in QA and 87 in maintenance?** The export removes records whose low-operation reason begins “No longer operational”. The QA and yearly CSV count 90 low-operation flags; the maintenance sheet contains 87 records, including 27 repeat low-operation records from 2024. Confirm current status before raising work.

**Which denominator applies to persistent sites?** The 74 model-adjusted sites recorded 4,895 spills in 2025: 18.9% within the 1,802-site linked panel, but 13.4% of all company spills. The 74-site list and observed 76-site list overlap; their no-action counts (17 and 13) answer different questions. See [the evidence review](05_Website_Validation_Notes.md).

**What would I do with more data?** Monthly or event-level spill data matched to daily rainfall at each catchment, which would separate storm intensity from total rainfall.
