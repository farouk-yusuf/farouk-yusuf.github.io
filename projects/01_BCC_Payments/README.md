# Birmingham City Council: spend and payment controls

The tasks a council finance or accounts-payable analyst would be given: monthly spend reporting, year-to-date variance, supplier and agency spend, payment-control exceptions, and a personal-data check on published data.

**Start here:** `outputs/00_Management_Summary.md` and `outputs/BCC_Spend_and_Payment_Controls_Pack.xlsx`

Data: Birmingham City Council "Payments to Suppliers over £500", City Observatory (Open Government Licence), Jul 2024 to Jul 2026.

- `scripts/01_clean.py` standardises directorates, suppliers and categories; pseudonymises individuals
- `scripts/02_build_database.py` builds a SQLite star schema (`clean/bcc_payments.sqlite`) and runs the queries in `sql/`
- `sql/` schema plus five reporting and control queries (CTEs, window functions, self-join)
- `scripts/03_finance_pack.py` builds the Excel pack and charts
- `outputs/` summary, workbook, brief, decisions note, SQL results, charts

Run: `python3 scripts/01_clean.py && python3 scripts/02_build_database.py && python3 scripts/03_finance_pack.py`
