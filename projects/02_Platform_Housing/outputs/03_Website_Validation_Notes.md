# Platform Housing: evidence review and outstanding checks

This review accompanies the website narrative. It checks the committed workbook and scripts; raw regulatory spreadsheets and source PDFs are not committed, so it does not independently verify their contents or rerun the original analysis. The workbook is preserved unchanged.

## Peer groups and survey interpretation

- The primary TSM cohort has **17 housing associations with more than 40,000 homes, including Platform**, not 17 other landlords. All twelve satisfaction measures in the workbook have 17 observations in that cohort.
- The Midlands housing-association median for overall satisfaction is **77.4%**, compared with **64.6%** for the large-landlord cohort. Size was used to choose a relevant comparator; this does not control all differences between organisations.
- Platform's survey sample is recorded as **2,316**, predominantly telephone. The primary cohort is selected by landlord type and size, not restricted to telephone surveys. Checking the predominant method does not establish full comparability.
- Six of the **twelve satisfaction measures** are in the bottom quartile. The key-figures CSV's seven bottom-quartile measures include an operational measure and should not be described as seven of twelve satisfaction measures.
- The correlation calculation uses complete cases across all twelve satisfaction measures for **all landlords**, not just the 17-landlord comparison cohort. Five service measures pass the script's correlation >= 0.80 and negative-gap rule. The three recommendations are a selected starting set, not a causal model, complete ranking or estimated return on investment.

## Repairs and other year-on-year checks

- The workbook records repair timeliness of **91.7% → 62.3%**, a **29.4 percentage-point decline**, and underlying counts of **90,250 → 13,872**. These counts are recorded in the workbook's Year-on-year checks sheet and hardcoded in the original analytical script; they have not been independently re-extracted during the website review.
- Both years are recorded as using a 28-day target. The large population change requires reconciliation of inclusion rules, job types and counts. A recording change is a hypothesis; the data do not exclude genuine service deterioration.
- Anti-social behaviour case counts and stage-one complaint counts also require owner review. Higher recorded volumes do not, on their own, establish worse service or a coding change.

## Ombudsman extraction and rate reconciliation

- The reports are labelled **2025/26**, separate from the **2024/25** TSM return. The 21-landlord Ombudsman sample is not the 17-landlord TSM cohort. The median recorded rate for the **other 20** landlords is **56.5%**, not a pooled findings rate.
- Platform's headline extraction records **137 findings**, **51 adverse findings** and a **38%** rate. Its category table sums to the same 137 and 51 counts. However, **51 / 137 = 37.2%**, which does not reproduce the recorded 38% rate. The source PDF, extraction and applicable rate denominator must be checked before the headline rate or ranking is used in formal reporting. No explanation for the discrepancy is assumed here.
- The repairs category has **43 total findings, of which 23 are adverse**. It is incorrect to describe this as 23 of 43 adverse findings across Platform. There are 51 adverse findings across all extracted categories.
- In this analysis, category “upheld” counts combine service failure, maladministration and severe maladministration. Complaint findings concern escalated cases, not a representative tenant sample; multiple findings can relate to one determination.
- The original decisions note reports small category-extraction differences for four other landlords. The extraction script prints reconciliation differences but does not assert that every landlord passes. These differences remain unresolved without a source-report review.

## Proposed release checks

Before an operational board report: reconcile the repair populations, confirm survey definitions and cohort membership, resolve the rate/count discrepancy against the original Ombudsman report, check all PDF category totals and agree service-owner interpretations. No stakeholder approval, deployed dashboard, delivered savings or measured service improvement is claimed.
