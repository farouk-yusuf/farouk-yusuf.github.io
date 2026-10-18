# Update your existing Birmingham report

This replaces the earlier 18-row supplier selection with the **complete supplier
comparison for 1 April–23 July in 2025 and 2026**. The six table names, all existing
column names and the five relationships are unchanged. Keep your PBIX, measures,
visuals, colours and formatting.

## Replace the workbook and refresh

1. Open your existing PBIX. Choose **File → Save As** to save a backup copy, then
   continue in the report you want to update.
2. Extract the updated `BCC_PowerBI_Starter.zip` into a separate folder.
3. Copy its `BCC_PowerBI_Starter.xlsx` into the folder containing the workbook
   your report already uses. Agree to replace the old file. Keep the exact same
   filename; do not leave the replacement as `BCC_PowerBI_Starter (1).xlsx`.
4. In Power BI Desktop, click **Home → Refresh** and wait for completion.
5. If you cannot replace the original file, use **Home → Transform data → Data
   source settings**, select the Excel source, choose **Change Source → Browse**
   and select the new workbook. Confirm, close the settings and refresh. In some
   versions this is under **File → Options and settings → Data source settings**.
6. Do not delete the tables, reimport them under new names, or recreate the
   relationships. Refresh updates the existing tables.

## Update the scope wording on Spending drivers

Replace the subtitle mentioning three suppliers with:

> 1 April–23 July · 2025 versus 2026 · All supplier payments in the matched periods

Replace the note beneath the table with:

> All suppliers paid in either comparison period are included. Names are
> standardised; accounts linked to redacted individuals are pooled by department.
> Payment changes alone do not explain contract changes, service volumes or
> invoice timing.

The previous table was not filtered to three rows: the source itself contained
three rows. After refresh, every matched-period supplier/group row is available.
If you have since added a Top N filter, clear it to see the complete list.

You may now enable the supplier table's totals: its prior, current and change
columns reconcile to the department card. Sorting, scrolling or an optional
visual Top N selection does not remove records from the model. A Top N view's
visible rows should not be labelled as the full department total.

## Check before continuing

With **City Operations** selected, the table should have more than three rows.
The department card should still display **£75.62M**. Birmingham Highways should
show **£20,625,624.12 → £87,575,989.53**, an increase of **£66,950,365.41**.

These exact supplier amounts are taken from the CSV. Check `data-checks.json`
for the authoritative figures; the old supplier workbook rounded amounts to
£10,000 before they were imported.

The main cards still display **£558.64M**, **£677.46M** and **£118.82M**. Their
underlying exact values are now **£558,638,892.64**, **£677,461,112.00** and
**£118,822,219.36**. The increase still rounds to **21.3%**.

The monthly source still covers **247,785 payment lines**. The exception list is
unchanged: **281 candidate pairs**, **£4,448,515.38**, including **73 same-day
pairs**. Each candidate's supplier, amount and dates were checked against the CSV.

Save the PBIX after refresh. This updates your local report; any already
published Power BI report must subsequently be republished.

## What the complete comparison supports

- Every supplier paid in either fixed comparison window, including suppliers
  appearing in only one year and suppliers with a zero net balance.
- Department selection, exact supplier movements and reconciliation to the
  department totals, with credits retained.
- Monthly department trends over the complete source publication.
- The full refined payment-review candidate list.

The model preserves these separate grains. Supplier amounts are period totals,
not a transaction ledger, and a month filter does not redefine the fixed-period
supplier comparison. The published data contains no invoice references or
budgets. Private supplier account identifiers and payment descriptions are not
included in the public workbook.
