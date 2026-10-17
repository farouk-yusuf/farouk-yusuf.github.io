# Decisions and reasoning (interview prep)

**Why sum commissioner rows?** The NHS England file has one row per trust, commissioner and specialty. Trust performance is the sum across commissioners.

**A data issue that nearly went wrong:** for waiting-list rows (Part 2) the 'Total' column is blank and only 'Total All' is filled, so my first run showed a waiting list of zero. The fix was to total the weekly bands directly. I now check every new extract for this.

**Why starts versus stops?** A waiting list only grows if more people join than leave. Splitting the change into referrals and treatments tells managers whether to look at demand management or at theatre and clinic capacity. Here it was demand.

**Why report a forecast that failed its back-test?** Because hiding it would be worse. Both models missed the March 2026 turning point; I report the error, show that 'no change' did better, and present March 2027 as a scenario.

**Why these peer trusts?** They are the large acute and teaching trusts in the Midlands, with waiting lists of 65,000 to 115,000, so similar scale and case mix.
