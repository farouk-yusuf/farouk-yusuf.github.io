# Published Power BI report

The report was built in Power BI Desktop and supplied by Farouk Yusuf as a
three-page PDF. The public portfolio provides that report as static page previews
and a downloadable PDF. It does not represent a live Power BI embed.

## Preparation of the public export

The supplied PDF's SHA-256 is
`f80cc1c6989ff673e54985df5ce23a864e7936315a0f68372417b9e18e10be4b`.

Before publication, the following document corrections were applied:

- Pages 2 and 3 use the same report identity as page 1:
  **Birmingham City Council Payments**. Their page names are **Supplier movements**
  and **Payment review**.
- Page 3 incorrectly repeated the matched spending-period subtitle. It now states
  **1 July 2024–23 July 2026 · Potential duplicates for invoice checks**. Its 281
  candidates cover the full publication, not only the two matched spending windows.
- PDF bookmarks and descriptive document metadata were added.

The figures, charts, visible table rows and saved filter selections were preserved.
The source PDF remains unchanged in the uploaded attachments. The corrected copy is
`Birmingham_Payments_PowerBI_Report.pdf`.

The same caption and title corrections should be made in the originating Power BI
report before its next export or Service publication. Document preparation does not
modify the user's PBIX or their Power BI Service report.

## Coverage of the captured views

1. **Spending overview:** whole-council payment cards compare 1 April–23 July 2025
   against the same dates in 2026. The monthly chart separately covers complete
   months July 2024–June 2026.
2. **Supplier movements:** Adult Social Care & Health is selected, with a department
   increase of £68.46m. The visible table is sorted by payment increase. The complete
   underlying matched-period comparison includes all supplier accounts, with private
   accounts pooled by reporting group, not just the rows visible in the export.
3. **Payment review:** all departments and payment timings are included. The 281
   candidate pairs have a potential repeated amount of £4,448,515.38, including 73
   same-day pairs. Invoice references are absent, so these are not confirmed errors
   or losses. The PDF captures the table's visible rows, not a scrollable list.

The portfolio links the full supporting data workbook next to the report download.
It includes the 3,947 matched-period supplier/group rows and all 281 candidate pairs.
See `../power-bi/data-checks.json` for source provenance and exact reconciliation.

## Rebuild previews from the supplied PDF

Asset preparation requires PyMuPDF; the static website build does not.

```sh
python3 scripts/prepare_bcc_report.py --source-pdf /path/to/Birmingham\ Payments.pdf
python3 scripts/build_site.py
python3 scripts/check_site.py
python3 scripts/check_finance_browser.py
```

The preparation script corrects the known headings/scope caption, preserves the
source's embedded Segoe UI fonts, and renders 2214 × 1269 PNG previews. Review a
new source export before rerunning: the script is specific to this report layout.
