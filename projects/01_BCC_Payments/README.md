# Birmingham City Council: spend and payment controls

The tasks a council finance or accounts-payable analyst would be given: monthly spend reporting, year-to-date variance, supplier and agency spend, payment-control exceptions, and a personal-data check on published data.

**Start here:** `outputs/00_Management_Summary.md` and `outputs/BCC_Spend_and_Payment_Controls_Pack.xlsx`

The completed three-page [Power BI report PDF](outputs/Birmingham_Payments_PowerBI_Report.pdf)
is also available as page previews in the [portfolio case study](https://farouk-yusuf.github.io/case-studies/birmingham-payments.html#report).
Read [the export notes](outputs/Birmingham_Payments_Report_Notes.md) for the corrected
review-page caption, selected supplier view and static PDF coverage. The public
export does not provide live Power BI filters; the complete data workbook is linked
alongside it.

The [interactive web dashboard](https://farouk-yusuf.github.io/dashboards/birmingham-payments.html)
offers browser filters, charts, the full searchable supplier comparison and all 281
candidate pairs without a Microsoft sign-in. It uses the same publication snapshot
as the Power BI pack. It is a separate HTML implementation; the Power BI PDF remains
available. [Implementation and reconciliation notes](../../dashboards/README.md)
explain its additional category detail and privacy handling.

Data: Birmingham City Council "Payments to Suppliers over £500", City Observatory (Open Government Licence), Jul 2024 to Jul 2026.

- `scripts/01_clean.py` standardises directorates, suppliers and categories; pseudonymises individuals
- `scripts/02_build_database.py` builds a SQLite star schema (`clean/bcc_payments.sqlite`) and runs the queries in `sql/`
- `sql/` schema plus five reporting and control queries (CTEs, window functions, self-join)
- `scripts/03_finance_pack.py` builds the Excel pack and charts
- `outputs/` summary, workbook, brief, decisions note, SQL results, charts

Run: `python3 scripts/01_clean.py && python3 scripts/02_build_database.py && python3 scripts/03_finance_pack.py`

For the Power BI build, use [the prepared data pack](power-bi/BCC_PowerBI_Starter.zip) and [Desktop instructions](power-bi/START_HERE.md). It contains six named Excel tables, DAX definitions and a theme, not a PBIX. The supplier comparison now includes **every supplier paid in either matched window**, replacing the initial 18-row selection. All supplier amounts reconcile to their department totals to the penny. The monthly, fixed matched-period and candidate-pair tables retain their distinct scopes. Follow [the existing-report update guide](power-bi/UPDATE_EXISTING_REPORT.md) to refresh without recreating visuals or relationships.

Rebuild from the repository root with `python3 scripts/build_bcc_powerbi.py --source-csv /path/to/payments-to-suppliers-over-gbp500.csv` (requires openpyxl). This reads the original council CSV, applies the documented department/name mappings, pools accounts linked to redacted individuals, reconciles the monthly and matched-period aggregates and independently checks all 281 candidate signatures. Source IDs and payment descriptions are not exported. Keep the original CSV outside this public repository. `power-bi/data-checks.json` records the source checksum, counts and exact totals. Power BI/DAX execution still takes place in Desktop.
