# Decisions and reasoning (interview prep)

**Why only monitors working 90%+ of the year?** A monitor that was down for half the year records fewer spills because it missed them, not because the overflow behaved better. Including those would mix data gaps with performance. 90% is the EA's own reporting threshold.

**Why average spills per overflow, not totals?** The number of overflows with data changes every year (2,288 to 2,452), so totals partly measure how many monitors were reporting.

**Why a simple straight-line rainfall model?** Five years of data can't support anything more complex. I report it as indicative, and lean on the 2022 vs 2025 comparison, which needs no model at all.

**Why the 60-spill threshold?** It's the high-spill level the EA uses in its own summary tables, so a regulator would recognise it.

**Why rainfall-adjust before ranking overflows?** Otherwise 2025's dry weather makes almost every overflow look improved, and wet-year spikes dominate the ranking. Scaling each year to a typical 1,000 mm year compares overflows on the same footing.

**What surprised me?** I expected improved monitoring to have *inflated* the apparent improvement. It did the opposite: earlier years were under-recorded, so the raw comparison understates progress.

**What would I do with more data?** Monthly or event-level spill data matched to daily rainfall at each catchment, which would separate storm intensity from total rainfall.
