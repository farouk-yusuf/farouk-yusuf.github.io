# Decisions and reasoning (interview prep)

**Why sum commissioner rows?** The NHS England file has one row per trust, commissioner and specialty. Trust performance is the sum across commissioners.

**A data issue that nearly went wrong:** for waiting-list rows (Part 2), the original analysis found 'Total' blank while 'Total All' was populated. The revised extractor totals the weekly bands into known-clock-start pathways and retains unknown starts and Total All. It does not yet enforce a source-row reconciliation assertion; that remains an operational release requirement. The website checks the committed outputs, not the unavailable raw extracts.

**Why starts versus stops?** The comparison identifies pressure from additions relative to recorded pathway endings. Here, April–August starts rose 15.2% year on year while stops rose 0.8%. However, the actual list change also includes an unclassified net residual of −21,526 pathways. Request the underlying coded adjustments before assigning causes. Starts and stops count pathways, not unique people, and stops are not a direct capacity measure.

**Why report a forecast that failed its back-test?** Because hiding it would be worse. Both models missed the March 2026 turning point; I report the error, show that 'no change' did better, and present March 2027 as a scenario.

**Why these peer trusts?** They are six selected large Midlands acute trusts, with latest waiting lists of roughly 67,000–115,000. That gives scale and regional context; it does not establish equivalent case mix, complexity or referral patterns. UHB's ranking is descriptive within this selection.

**How should the scenario be used?** The seven-month workbook outlook ends at 107,190 pathways in March 2027. The headline CSV truncates the unrounded estimate to 107,189, a one-pathway precision difference. Approximately 1,555 extra clock stops per month would hold the scenario flat only if all other assumptions, including the residual, continued unchanged. It is not a validated capacity plan or an estimate of treatment slots. See the [evidence review](03_Website_Validation_Notes.md).
