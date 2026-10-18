# Birmingham Power BI: first working report

This pack contains prepared **data and build instructions**, not a finished PBIX report. Use Power BI Desktop to build and save the report. Start with page 1; the other two pages follow once its figures and filters work.

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
4. Import `bcc-theme.json` through **View → Themes → Browse for themes**.

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
| Matched current payments | £677,460,000 |
| Matched prior payments | £558,640,000 |
| Matched payment change | £118,820,000 |
| Matched payment change % | 21.27% → display as 21.3% |
| Payment lines | 247,785 |
| Candidate pairs | 281 |
| Candidate value | £4,448,515.38 |
| Same-day candidate pairs | 73 |

Format currency measures as GBP; use **Millions and two decimal places** in spending cards, and full pounds in the exception table. Format `Matched payment change %` as **Percentage, one decimal place**. The query returns the percentage as a ratio; 0.2127 is correct before percentage formatting.

## 4. Build page 1: Spending overview

Set the page to **16:9**. Add the title **“Net payments rose 21.3% over equivalent dates”** and the subtitle **“1 April–23 July in both years · 2025 versus 2026 · net of credits”**.

| Position | Visual | Fields |
|---|---|---|
| Top left | Card | Matched current payments |
| Top middle | Card | Matched prior payments |
| Top right | Card | Matched payment change % |
| Below cards, left | Line chart | X: DimMonth[MonthStart], use the date field itself; Y: Monthly net payments |
| Below cards, right | Horizontal bar chart | Y: DimDirectorate[ReportGroup]; X: Matched payment change |
| Top/right margin | Dropdown slicer | DimDirectorate[ReportGroup] |

For the **line chart only**, set a visual-level filter `DimMonth[IsCompleteMonth] = TRUE`. Title it **“Monthly payments fluctuate; July 2026 is excluded because it is partial”**. The line covers July 2024–June 2026; the cards and variance chart use the fixed matched dates in the subtitle. Do not add a date slicer to page 1: it would filter the line without changing the fixed-period cards.

Use green for the variance of interest and neutral grey for context. Keep negative department movements visible. These are changes in cash payments, not budget overspends or savings. For a filter-aware heading, replace the fixed headline with a wide **Card** using `Spending overview title`, turn its category label off and use a smaller text size. Keep the reporting-period subtitle as a text box. This prevents a whole-council headline remaining above department-filtered results.

Save as `BCC_Spending_and_Payment_Review.pbix`.

## Page 2: Spending drivers

Use a single-select `DimDirectorate[ReportGroup]` dropdown and a table containing the supplier-driver fields `ReportGroup`, `Supplier`, `PriorGBP`, `CurrentGBP` and `ReportedMovementGBP`. Sort by the absolute movement, or start with City Operations.

Label the table **“Selected supplier movements · three largest absolute movements per reporting group”**. It is an **18-row selected list**, not all suppliers. Disable the table's total row. The reported movement was rounded separately from its prior/current amounts, so a £0.01m apparent difference can arise. Do not use this table to calculate the total department change; use FactMatchedSpend instead.

## Page 3: Potential duplicate payments

Title: **“Potential duplicate payments for AP review”**. Subtitle: **“Full publication coverage: July 2024–23 July 2026 · screening candidates, not confirmed duplicates”**.

- Cards: Candidate pairs, Candidate value and Same-day candidate pairs.
- Slicers: `DimDirectorate[ReportGroup]` and `FactDuplicatePairs[ReviewPriority]`. Keep page-specific selections; do not sync the priority slicer to spending pages.
- Table: PairID, Supplier, ReportGroup, AmountGBP, FirstDate, SecondDate and DaysApart. Sort AmountGBP descending.
- Note: **“Value counts one potentially repeated amount per pair. Confirm invoice references and the underlying transaction before recording a loss or recovery.”**

The review list was produced by the refined Python rule, not the initial 6,553-pair SQL screen. Supplier–amount combinations occur exactly twice in the qualifying dataset, amount is at least £1,000 and the gap is at most three days. Original supplier numbers are omitted from this pack; PairID is a report identifier.

## Data scope and refresh

- Monthly data comes from the committed SQL output, with corporate directorates combined into the same six reporting groups as the workbook.
- Matched-period data comes from the workbook's already rounded group totals. It is **not a transaction-level ledger** and cannot support arbitrary new date ranges or counts of matched-period payments.
- The duplicate list spans the full publication period, independently of the matched-period comparison. Department filtering works through the shared dimension; date filtering does not apply across these facts.
- The workbook's `Read me` sheet records table grains and sources. Refreshing this prepared file does not fetch a new council publication. A full refresh needs the upstream analysis and a rebuilt starter file.
- Public-source context and original analysis: https://farouk-yusuf.github.io/case-studies/birmingham-payments.html

## Publishing comes after the first report check

After page 1 works, publish from Desktop to your Power BI workspace. We will then check whether **File → Embed report → Publish to web (public)** is available in Power BI Service. Do not choose an authenticated embed expecting anonymous access. Publish to web makes the report and included model data public. The next website step is to embed the actual published report URL, with a screenshot/PDF fallback; this starter pack does not create an embed URL or change the live case study.
