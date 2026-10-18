# Birmingham Power BI: spending and payment review

This pack contains the complete prepared data for the scoped report, DAX and build instructions. It is not a PBIX: use Power BI Desktop to assemble and save the report. The supplier comparison now includes **all suppliers paid in either matched period**, replacing the previous 18-row selection. Existing reports can retain their tables, relationships and visuals: follow [UPDATE_EXISTING_REPORT.md](UPDATE_EXISTING_REPORT.md).

## 1. Import the tables

1. Extract the ZIP into a folder you will keep, such as Documents/BCC Power BI.
2. Open Power BI Desktop → **Blank report** → **Get data → Excel workbook**.
3. Open `BCC_PowerBI_Starter.xlsx`. Select these **six named tables**, then Load:
   - `DimDirectorate`
   - `DimMonth`
   - `FactMatchedSpend`
   - `FactMonthlySpend`
   - `FactSupplierDrivers`
   - `FactDuplicatePairs`
4. Import `bcc-theme.json` through **Design → Import theme**, or **View → Themes → Browse for themes** in versions with the older ribbon.

Use the named tables rather than the similarly named worksheet entries. Keep the table names unchanged so the supplied DAX works.

## 2. Set five relationships

Open **Model view**. Keep only these relationships; remove any automatically created fact-to-fact relationships. All five should be **active, one-to-many (1:*), with Single cross-filter direction** from the dimension to the fact.

| One side | Many side |
|---|---|
| DimDirectorate[ReportGroup] | FactMatchedSpend[ReportGroup] |
| DimDirectorate[ReportGroup] | FactMonthlySpend[ReportGroup] |
| DimDirectorate[ReportGroup] | FactSupplierDrivers[ReportGroup] |
| DimDirectorate[ReportGroup] | FactDuplicatePairs[ReportGroup] |
| DimMonth[MonthStart] | FactMonthlySpend[MonthStart] |

In Table view, set `DimMonth[MonthLabel]` to **Sort by column → YearMonthSort**. Set both `MonthStart` columns and both duplicate-pair date columns to **Date**, and monetary `GBP` columns to **Fixed decimal number**. Do not relate the duplicate dates to DimMonth: the exception list has a different reporting scope.

## 3. Add the measures together

Open **DAX Query view**, paste the complete contents of `create-measures.dax`, and select **Run**. Its results should match the checks below. Then select **Update model with changes** to save the defined measures in the model. Button wording can differ by Desktop version.

If your version does not offer that command, use **Modeling → New measure** for each definition, omitting `DEFINE`, `MEASURE`, the table prefix and the final `EVALUATE` statement. Add one measure at a time.

| Check, with all filters cleared | Expected |
|---|---:|
| Matched current payments | £677,461,112.00 |
| Matched prior payments | £558,638,892.64 |
| Matched payment change | £118,822,219.36 |
| Matched payment change % | 21.27% → display as 21.3% |
| Payment lines | 247,785 |
| Candidate pairs | 281 |
| Candidate value | £4,448,515.38 |
| Same-day candidate pairs | 73 |

Format currency measures as GBP; use **Millions and two decimal places** in spending cards, and full pounds in the exception table. In the current Card visual, use **General → Data format → Apply settings to → Format options → Custom**, with `£0.00` while the card automatically abbreviates millions. Do not add scaling commas or a literal `m` to this visual-level code. Earlier versions expose Display units in Callout value settings. Format `Matched payment change %` as **Percentage, one decimal place**. The query returns the percentage as a ratio; approximately 0.2127 is correct before percentage formatting. The old workbook rounded totals to £10,000; the new model retains exact source amounts. The displayed main cards remain £558.64M, £677.46M and £118.82M.

## 4. Build page 1: Spending overview

Set the page to **16:9**. Add the title **“Net payments rose £118.82m over equivalent dates”** and the subtitle **“Birmingham City Council · 1 April–23 July 2025 versus 2026 · 21.3% increase · Payments include credits”**.

| Position | Visual | Fields |
|---|---|---|
| Top left | Card | Matched prior payments |
| Top middle | Card | Matched current payments |
| Top right | Card | Matched payment change |
| Below cards, left | Line chart | X: DimMonth[MonthStart], use the date field itself; Y: Monthly net payments |
| Below cards, right | Horizontal bar chart | Y: DimDirectorate[ReportGroup]; X: Matched payment change |

For the **line chart only**, set a visual-level filter `DimMonth[IsCompleteMonth] = TRUE`. Title it **“June 2026 recorded the highest monthly payments in this period”**, with the subtitle **“July 2024–June 2026 · Complete months only”**. Use straight line segments rather than smoothing. The cards and variance chart use the fixed matched dates in the subtitle. Do not add a date slicer to page 1: it would filter the line without changing the fixed-period cards.

Use green for the variance of interest and neutral grey for context. Title the department chart **“City Operations recorded the largest payment increase”** and label its axis **“Change in net payments (£m)”**. Keep negative department movements visible, with zero between increases and decreases. These are changes in cash payments, not budget overspends or savings. Keep this page as the whole-council summary. Before adding a department slicer, replace the fixed whole-council heading with a wide **Card** using `Spending overview title`, and make chart headings filter-aware too. Alternatively disable visual interactions through **Format → Edit interactions** so selecting a chart does not contradict the fixed narrative. Page 2 provides the department exploration.

Save as `BCC_Spending_and_Payment_Review.pbix`.

## Page 2: Spending drivers

Use a single-select `DimDirectorate[ReportGroup]` dropdown and a table containing the supplier-driver fields `ReportGroup`, `Supplier`, `PriorGBP`, `CurrentGBP` and `ReportedMovementGBP`. Sort by the absolute movement, or start with City Operations.

Title the page **“Explore the suppliers behind each department’s change”**. Subtitle: **“1 April–23 July · 2025 versus 2026 · All supplier payments in the matched periods”**. Add a card using `Matched payment change` and label it **“Department’s total payment change”**.

The supplier table includes every supplier display name/reporting group present in either matched window, with private accounts pooled by group. There is **no Top N truncation**. Its exact prior, current and change amounts reconcile to each department to the penny. Zero-net suppliers are retained. Supplier names are standardised using the most frequent public spelling per account across the source, then combined by display name within each reporting group; account IDs are not published.

Rename the columns to **Supplier**, **Payments · 2025**, **Payments · 2026** and **Change in payments**. Format monetary cells as `£#,##0` for whole pounds (or `£#,##0.00` when pennies matter). Use light data bars in the change column with values still visible, readable 12-point text and faint horizontal rules. Totals can now be enabled because the table is complete; a subsequently filtered Top N display would need its subtotal clearly distinguished from the department total. Retain the department card from FactMatchedSpend.

Add a small note: **“All suppliers paid in either comparison period are included. Names are standardised; accounts linked to redacted individuals are pooled by department. Payment changes alone do not explain contract changes, service volumes or invoice timing.”**

## Page 3: Potential duplicate payments

Title: **“Potential duplicate payments for AP review”**. Subtitle: **“Full publication coverage: July 2024–23 July 2026 · screening candidates, not confirmed duplicates”**.

- Cards: Candidate pairs, Candidate value and Same-day candidate pairs.
- Slicers: `DimDirectorate[ReportGroup]` and `FactDuplicatePairs[ReviewPriority]`. Keep page-specific selections; do not sync the priority slicer to spending pages.
- Table: PairID, Supplier, ReportGroup, AmountGBP, FirstDate, SecondDate and DaysApart. Sort AmountGBP descending.
- Note: **“Value counts one potentially repeated amount per pair. Confirm invoice references and the underlying transaction before recording a loss or recovery.”**

The review list was produced by the refined Python rule, not the initial 6,553-pair SQL screen. Supplier–amount combinations occur exactly twice in the qualifying dataset, amount is at least £1,000 and the gap is at most three days. Original supplier numbers are omitted from this pack; PairID is a report identifier.

## Data scope and refresh

- All 247,785 original CSV records contribute to the exact monthly/group totals, independently reconciled to the previous SQL output.
- All supplier accounts present in either fixed matched window contribute to the supplier comparison and matched-period department totals. Supplier sums reconcile to each group to the penny. These are period aggregates, not a transaction-level ledger, and cannot support arbitrary new date ranges.
- Redacted accounts, including names elsewhere linked to their IDs, are pooled by reporting group. Original supplier IDs, personal pseudonyms and payment descriptions are omitted. Public supplier names and their aggregated amounts remain available.
- The duplicate list spans the full publication period, independently of the matched-period comparison. Department filtering works through the shared dimension; date filtering does not apply across these facts.
- The workbook's `Read me` sheet records table grains and sources; `data-checks.json` records the source CSV checksum, counts, coverage and exact totals. Refreshing this prepared file does not fetch a new council publication. Rebuild with `python3 scripts/build_bcc_powerbi.py --source-csv /path/to/payments-to-suppliers-over-gbp500.csv` (requires openpyxl). Keep the original CSV outside the public repository. A changed source snapshot requires scope and validation review; the builder stops rather than silently changing the reporting dates or coverage.
- Public-source context and original analysis: https://farouk-yusuf.github.io/case-studies/birmingham-payments.html

## Publishing comes after the first report check

After page 1 works, publish from Desktop to your Power BI workspace. We will then check whether **File → Embed report → Publish to web (public)** is available in Power BI Service. Do not choose an authenticated embed expecting anonymous access. Publish to web makes the report and included model data public. The next website step is to embed the actual published report URL, with a screenshot/PDF fallback; this starter pack does not create an embed URL or change the live case study.
