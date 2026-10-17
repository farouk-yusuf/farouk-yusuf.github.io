"""
Step 3: the deliverables a council finance / AP analyst would produce.
  - Monthly spend report: FY2025/26 outturn and FY2026/27 year-to-date vs last year, by directorate
  - Supplier concentration and agency staff spend
  - Accounts-payable control exceptions: possible duplicate payments, credits, large payments, duplicate supplier records
  - Information-governance check on published personal data
Output: outputs/BCC_Spend_and_Payment_Controls_Pack.xlsx + charts
"""
import os, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = os.path.join(BASE, "outputs"); R = os.path.join(O, "sql_results")
df = pd.read_csv(os.path.join(BASE, "clean", "payments_clean.csv"), dtype={"supplier_number": str}, parse_dates=["date"])
raw = pd.read_csv(os.path.join(BASE, "raw", "payments-to-suppliers-over-gbp500.csv"), encoding="utf-8-sig", dtype={"supplier_number": str})
m = lambda x: round(x / 1e6, 2)
fy = df[df.financial_year == "2025/26"]
K = {}

# ---- spend report ----
# Budgets moved between corporate directorates in the Sept 2025 restructure, so compare them as one group
CORP = {"Council Management", "Finance", "HR, OD & Transformation", "Strategy, Insight & Governance"}
df["report_group"] = np.where(df.directorate.isin(CORP), "Corporate services (combined)", df.directorate)
fy = df[df.financial_year == "2025/26"]
by_dir = fy.groupby("report_group").amount.sum().sort_values(ascending=False)
last = df.date.max()                                   # data ends part-way through July 2026
same_day_ly = last - pd.DateOffset(years=1)
ytd_cur = df[(df.date >= "2026-04-01") & (df.date <= last)]
ytd_prev = df[(df.date >= "2025-04-01") & (df.date <= same_day_ly)]
K_period = f"1 Apr - {last.day} Jul"
c25, c26 = f"{K_period} 2025 £m", f"{K_period} 2026 £m"
ytd = pd.DataFrame({"FY2025/26 outturn £m": by_dir.map(m),
                    c25: ytd_prev.groupby("report_group").amount.sum().map(m),
                    c26: ytd_cur.groupby("report_group").amount.sum().map(m)}).fillna(0)
ytd["YTD change %"] = ((ytd[c26] / ytd[c25] - 1) * 100).round(1)
# variance drivers: biggest supplier movements behind each group's year-to-date change
drv = []
for g in ytd.index:
    a = ytd_prev[ytd_prev.report_group == g].groupby("supplier_name_std").amount.sum()
    b = ytd_cur[ytd_cur.report_group == g].groupby("supplier_name_std").amount.sum()
    v = (b.reindex(a.index.union(b.index), fill_value=0) - a.reindex(a.index.union(b.index), fill_value=0)).sort_values(key=abs, ascending=False).head(3)
    for sname, val in v.items():
        drv.append({"Group": g, "Supplier": sname, "Prior YTD £m": m(a.get(sname, 0)), "Current YTD £m": m(b.get(sname, 0)), "Movement £m": m(val)})
drivers = pd.DataFrame(drv)
ytd.loc["Total"] = [m(fy.amount.sum()), m(ytd_prev.amount.sum()), m(ytd_cur.amount.sum()),
                    round((ytd_cur.amount.sum() / ytd_prev.amount.sum() - 1) * 100, 1)]
monthly = df.pivot_table(index="month", columns="report_group", values="amount", aggfunc="sum").div(1e6).round(2)
monthly["Total"] = monthly.sum(axis=1)
cat = fy.groupby("spend_category").amount.sum().sort_values(ascending=False).head(20).map(m).rename("FY2025/26 £m")
K.update(fy_total_m=m(fy.amount.sum()), fy_payments=len(fy), ytd_change_pct=ytd.loc["Total", "YTD change %"],
         po_accrual_share_pct=round(fy[fy.is_po_accrual].amount.sum() / fy.amount.sum() * 100, 1),
         adult_social_care_share_pct=round(by_dir.get("Adult Social Care & Health", 0) / fy.amount.sum() * 100, 1), ytd_period=K_period)

# ---- suppliers ----
sup = fy[~fy.is_personal_data].groupby("supplier_name_std").amount.sum().sort_values(ascending=False)
top25 = pd.DataFrame({"FY2025/26 £m": sup.head(25).map(m), "% of total": (sup.head(25) / fy.amount.sum() * 100).round(2)})
top25["Cumulative %"] = top25["% of total"].cumsum().round(2)
K.update(suppliers_paid_fy=int(fy.supplier_number.nunique()), top10_share_pct=round(sup.head(10).sum() / fy.amount.sum() * 100, 1),
         top25_share_pct=round(sup.head(25).sum() / fy.amount.sum() * 100, 1))

# ---- agency staff ----
ag = df[df.is_agency_staff]
ag_month = ag.groupby("month").amount.sum().div(1e6).round(2).rename("Agency staff £m")
ag_ytd_cur, ag_ytd_prev = ag[ag.date >= "2026-04-01"].amount.sum(), ag[(ag.date >= "2025-04-01") & (ag.date <= same_day_ly)].amount.sum()
ag_sup = ag[ag.financial_year == "2025/26"].groupby("supplier_name_std").amount.sum().sort_values(ascending=False)
K.update(agency_fy_m=m(ag[ag.financial_year == "2025/26"].amount.sum()), agency_ytd_change_pct=round((ag_ytd_cur / ag_ytd_prev - 1) * 100, 1),
         agency_top_supplier=ag_sup.index[0], agency_top_supplier_share_pct=round(ag_sup.iloc[0] / ag_sup.sum() * 100, 1))

# ---- AP control exceptions ----
x = df[~df.is_personal_data & (df.amount >= 1000)]
two = x[x.groupby(["supplier_number", "amount"]).amount.transform("size") == 2]
pairs = two.sort_values("date").groupby(["supplier_number", "amount"]).agg(
    supplier=("supplier_name_std", "first"), directorate=("directorate", "first"), category=("spend_category", "first"),
    first_date=("date", "min"), second_date=("date", "max"),
    service_area_1=("summary", "first"), service_area_2=("summary", "last")).reset_index()
pairs["days_apart"] = (pairs.second_date - pairs.first_date).dt.days
dups = pairs[pairs.days_apart <= 3].sort_values("amount", ascending=False)
dups["first_date"], dups["second_date"] = dups.first_date.dt.date, dups.second_date.dt.date
K.update(dup_pairs=len(dups), dup_value_m=m(dups.amount.sum()), dup_same_day=int((dups.days_apart == 0).sum()))
credits = df[df.is_credit].sort_values("amount")[["date", "directorate", "supplier_name_std", "spend_category", "summary", "amount"]]
credits["date"] = credits.date.dt.date
large = df[df.is_large_500k].sort_values("amount", ascending=False)[["date", "directorate", "supplier_name_std", "spend_category", "summary", "amount"]]
large["date"] = large.date.dt.date
K.update(credits_n=len(credits), credits_m=m(credits.amount.sum()), large_n=len(large), large_m=m(large.amount.sum()))
supm = pd.read_csv(os.path.join(R, "04_duplicate_supplier_records.csv"))
K.update(dup_supplier_names=len(supm))

# ---- information governance ----
red = raw.beneficiary.str.upper().str.replace(r"[\s-]", "", regex=True).str.startswith("REDACTEDPERSONALDATA")
exposed = set(raw[red].supplier_number) & set(raw[~red].supplier_number)
ig = pd.DataFrame([
    ("Payments to individuals (name redacted)", int(red.sum()), f"£{m(raw[red].amount.sum())}m"),
    ("Distinct supplier numbers behind redacted names", raw[red].supplier_number.nunique(), "Published unredacted: links all payments to the same person"),
    ("Supplier numbers shown both redacted and with a name", len(exposed), "Redaction can be reversed by looking the number up elsewhere in the file"),
    ("Redacted payments re-identifiable this way", int((red & raw.supplier_number.isin(exposed)).sum()), "Refer to Information Governance"),
    ("Spellings of the redaction label", raw[red].beneficiary.nunique(), "Inconsistent redaction process"),
], columns=["Check", "Result", "Note"])
K.update(redacted_rows=int(red.sum()), exposed_numbers=len(exposed), exposed_rows=int((red & raw.supplier_number.isin(exposed)).sum()))

# ---- data quality ----
dq = pd.DataFrame([
    ("Directorates renamed in Sept 2025 (e.g. 'Adults Social Care' became 'Adult Social Care & Health')", "Breaks month-on-month trends", "Mapped 18 source names to 9 reporting directorates (clean/directorate_mapping.csv)"),
    ("Typo directorate 'Council Managament' (34 rows, Sept 2025)", "Spend split across two names", "Mapped to Council Management"),
    ("'Accounts payable PO Accrual - GRNI' used as a spend category", f"{K['po_accrual_share_pct']}% of FY2025/26 spend has no true category", "Flagged is_po_accrual; reported separately"),
    ("Double spaces in category names", "Duplicate categories", "Whitespace normalised"),
    ("Supplier names vary under one supplier number (215 numbers)", "Supplier totals split", "One standard name per supplier number"),
    (f"{len(credits)} negative payments (credits)", f"£{abs(K['credits_m'])}m netted off spend", "Kept; listed for review"),
    ("Two spellings of the personal-data redaction label", "Individuals counted as two suppliers", "Standardised and pseudonymised"),
    ("No invoice or document reference published", "Duplicates can't be confirmed from this data alone", "Exceptions listed for checking against the finance system"),
], columns=["Issue", "Impact", "Resolution"])

# ---- workbook ----
path = os.path.join(O, "BCC_Spend_and_Payment_Controls_Pack.xlsx")
with pd.ExcelWriter(path, engine="openpyxl") as xw:
    pd.DataFrame({"Birmingham City Council: spend and payment controls pack": [
        "Source: Birmingham City Council 'Payments to Suppliers over £500', City Observatory (OGL). Jul 2024 - Jul 2026, 247,785 payment lines.",
        "Spend is net of credits. Directorates harmonised across the September 2025 restructure.",
        "Payee names of individuals are redacted by the council; their supplier numbers have been pseudonymised here.",
        "Year-to-date compares 1 Apr to 23 Jul in both years (the data ends 23 Jul 2026). Corporate directorates are combined because the restructure moved budgets between them.",
        "Sheets: Spend by directorate | YTD variance drivers | Monthly spend | Top categories | Top suppliers | Agency staff | Possible duplicates | Credits | Payments over £500k | Duplicate supplier records | Personal data check | Data quality log"]}) \
        .to_excel(xw, sheet_name="Read me", index=False)
    ytd.to_excel(xw, sheet_name="Spend by directorate")
    drivers.to_excel(xw, sheet_name="YTD variance drivers", index=False)
    monthly.to_excel(xw, sheet_name="Monthly spend £m")
    cat.to_frame().to_excel(xw, sheet_name="Top categories FY25-26")
    top25.to_excel(xw, sheet_name="Top suppliers FY25-26")
    ag_month.to_frame().to_excel(xw, sheet_name="Agency staff monthly")
    dups.to_excel(xw, sheet_name="Possible duplicates", index=False)
    credits.to_excel(xw, sheet_name="Credits", index=False)
    large.to_excel(xw, sheet_name="Payments over £500k", index=False)
    supm.to_excel(xw, sheet_name="Duplicate supplier records", index=False)
    ig.to_excel(xw, sheet_name="Personal data check", index=False)
    dq.to_excel(xw, sheet_name="Data quality log", index=False)
    for ws in xw.book.worksheets:
        ws.freeze_panes = "A2"
        for col in ws.columns:
            w = max(len(str(c.value)) if c.value is not None else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(10, w + 2), 70)

# ---- charts ----
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(9, 4.5))
tot = monthly["Total"]; ax.bar(range(len(tot)), tot.values, color="#1f6f8b")
ax.set_xticks(range(len(tot))); ax.set_xticklabels(tot.index, rotation=90); ax.set_ylabel("£m")
ax.set_title("Monthly payments over £500, net of credits"); fig.tight_layout(); fig.savefig(os.path.join(O, "chart1_monthly_spend.png"), dpi=160); plt.close()
fig, ax = plt.subplots(figsize=(9, 4.5)); ax.plot(ag_month.index, ag_month.values, "o-", color="#c0392b")
ax.set_xticks(range(len(ag_month))); ax.set_xticklabels(ag_month.index, rotation=90); ax.set_ylabel("£m")
ax.set_title("Agency staff spend by month"); fig.tight_layout(); fig.savefig(os.path.join(O, "chart2_agency_spend.png"), dpi=160); plt.close()
pd.Series(K).to_csv(os.path.join(O, "key_figures.csv"), header=["value"])
pd.set_option("display.width", 200)
print(pd.Series(K).to_string()); print(ytd.to_string()); print(drivers.to_string()); print(top25.head(10).to_string()); print(ag_sup.head(5).map(m))
