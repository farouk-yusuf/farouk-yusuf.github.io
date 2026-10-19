# Birmingham interactive dashboard

[Open the published dashboard](https://farouk-yusuf.github.io/dashboards/birmingham-payments.html)
or return to the [case study and Power BI report](../case-studies/birmingham-payments.html#report).

Adapted from `birmingham-payments-dashboard.html`, supplied by Farouk and created
with Claude. This is a standalone HTML/CSS/JavaScript dashboard hosted on GitHub
Pages, not an embedded Power BI report. It uses local portfolio fonts and an
embedded council logo. It loads no external scripts, analytics or services and
requires no account. All filtering runs in the visitor's browser.

## Data and reconciliation

The snapshot covers 247,785 published payment lines from 1 July 2024 to 23 July
2026. It includes credits; net payments total £3,873,852,012.19. The monthly line
excludes the incomplete July 2026. Spending comparisons use 1 April–23 July in
2025 and 2026: £558,638,892.64 versus £677,461,112.00.

- The supplier table includes all 3,325 standardised display names in either
  comparison period. Its underlying 3,947 department/name combinations reconcile
  to `FactSupplierDrivers` in the complete Power BI workbook, to the penny.
- The embedded monthly/category rows reconcile to all 150 month/department rows
  in `FactMonthlySpend`, including payment-line counts.
- The finer category, matched-month and agency-category aggregates were also
  independently reconciled to the original council CSV. Categories outside the
  fifteen named buckets are pooled as “All other categories”. Agency totals
  include support staff and teachers within that bucket.
- All 281 review records, IDs, labels and dates now match `FactDuplicatePairs` in
  the delivered workbook. The supplied HTML had different ID ordering for some
  tied amounts and different category labels for some otherwise identical pairs;
  these were aligned for consistent cross-referencing. The candidate identities,
  £4,448,515.38 screening value and 73 same-day pairs are unchanged.
- Amounts flagged for review are not confirmed losses, savings or recoveries.
  A pair can span two categories; its category filter follows the AP workbook's
  reporting label and does not replace checking both invoices.
- All accounts linked to any redacted individual are pooled. No supplier account
  identifiers, raw descriptions or linkable pseudonyms are embedded. Counts refer
  to standardised display names rather than supplier accounts.

The public workbook retains its six-table model; the HTML additionally embeds
category-level aggregates. The original CSV is not included in the repository.
Neither the HTML nor PDF refreshes automatically when the council publishes new
data. Validate any future snapshot against its source before replacing this one.

## Integration and review

The homepage and Birmingham case study open this dashboard as a full page, so its
tables have room on desktop and scroll within their containers on phones. The
Power BI PDF previews and supporting workbook remain in the case study. Links
back to both are provided in the dashboard.

Integration corrections include input validation for shared filter links,
consistent reset/search behaviour, keyboard tab and sort controls, chart data
tables, clearer empty states, colour contrast and reduced-motion support.
Supplier concentration uses positive net payments in both numerator and
denominator, excluding credits and zero balances. “Only in 2026” means absent
from the equivalent 2025 window, not a newly appointed supplier.

From the repository root, with openpyxl, Playwright and Chromium installed:

```sh
python3 scripts/check_site.py
python3 scripts/check_bcc_dashboard.py
python3 scripts/check_bcc_dashboard.py --source-csv /path/to/payments-to-suppliers-over-gbp500.csv
```

The dashboard check reconciles every supplier/monthly/review row and exercises
filter combinations, searches, pagination, keyboard sorting and tab navigation,
shared links, chart/table switching and layouts at 1440, 768, 390 and 320 pixels.
PDF and workbook links provide a fallback when JavaScript is disabled.
