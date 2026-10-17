"""
Severn Trent storm overflows - step 3: the employee deliverables.
  1. Annual return QA: validation checks on the 2025 return before submission / publication
  2. Year-end performance pack: 2025 vs 2024 KPIs, by river basin and asset type
  3. Exception lists for the teams who act on them:
       - Maintenance: monitors working <90% of the year (with reason), flagging repeat failures
       - Investment/operations: overflows with 60+ spills in 2025, with improvement status
Output: outputs/Severn_Trent_Overflow_Performance_Pack_2025.xlsx
"""
import os, numpy as np, pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C, O = os.path.join(BASE, "clean"), os.path.join(BASE, "outputs")
st = pd.read_csv(os.path.join(C, "st_overflows_2020_2025.csv"))
rain = pd.read_csv(os.path.join(C, "rainfall_monthly_annual.csv"))
mid = rain[rain.region == "Midlands"].set_index("year")["ann"]
HIGH = 60

def basin(wfd):
    w = str(wfd)
    return {"GB104": "Trent (Humber basin)", "GB109": "Severn basin"}.get(w[:5], "Estuary / other")
st["river_basin"] = st.wfd_waterbody_id.map(basin)
cur, prev = st[st.year == 2025].copy(), st[st.year == 2024].copy()

# ---------- 1. QA checks on the 2025 return ----------
ids_cur, ids_prev = set(cur.unique_id), set(prev.unique_id)
merged = cur.merge(prev[["unique_id", "spills"]], on="unique_id", how="left", suffixes=("", "_2024"))
checks = [
    ("Overflows listed", len(cur), "Info", ""),
    ("Duplicate overflow IDs", int(cur.unique_id.duplicated().sum()), "Pass" if not cur.unique_id.duplicated().any() else "Fail", "Each overflow should appear once"),
    ("Overflows with no spill count", int(cur.spills.isna().sum()), "Review", "Expected only for decommissioned overflows"),
    ("Monitors working <90% of year", int(cur.dq_low_edm_op.sum()), "Review", "Reason must be given for each"),
    ("...of which missing a reason", int((cur.dq_low_edm_op & cur.low_op_reason.isna()).sum()), "Pass" if not (cur.dq_low_edm_op & cur.low_op_reason.isna()).any() else "Fail", "EA requires a reason below 90%"),
    ("EDM operation above 100%", int(cur.dq_op_over_100.sum()), "Pass" if cur.dq_op_over_100.sum() == 0 else "Fail", "Impossible value"),
    ("Spill duration above hours in year (8,760)", int((cur.duration_hrs > 8760).sum()), "Pass" if (cur.duration_hrs > 8760).sum() == 0 else "Fail", "Impossible value"),
    ("Spills recorded with zero duration", int(cur.dq_spills_but_zero_hrs.sum()), "Pass" if cur.dq_spills_but_zero_hrs.sum() == 0 else "Review", "Inconsistent pair"),
    ("New overflows vs 2024 return", len(ids_cur - ids_prev), "Review", "Confirm new or re-referenced assets"),
    ("Overflows dropped since 2024 return", len(ids_prev - ids_cur), "Review", "Confirm removal / permit revoked"),
    ("Overflows whose spills rose 50+ in a drier year", int(((merged.spills - merged.spills_2024) >= 50).sum()), "Review", "Confirm with operations before publication"),
]
qa = pd.DataFrame(checks, columns=["Check", "Result", "Status", "Note"])
swings = merged[(merged.spills - merged.spills_2024) >= 50][["unique_id", "site_name", "river_basin", "asset_type", "spills_2024", "spills", "edm_op_pct"]] \
    .rename(columns={"spills": "spills_2025"}).sort_values("spills_2025", ascending=False)

# ---------- 2. KPI pack ----------
def kpis(df):
    rel = df[df.edm_op_pct >= 90]
    return pd.Series({
        "Overflows": len(df),
        "Total spills": df.spills.sum(),
        "Total spill hours": round(df.duration_hrs.sum()),
        "Avg spills per overflow": round(df.spills.mean(), 1),
        "Overflows that did not spill": int((df.spills == 0).sum()),
        "Overflows with 60+ spills": int((df.spills >= HIGH).sum()),
        "Monitors working ≥90% of year (%)": round(len(rel) / df.spills.notna().sum() * 100, 1),
    })
kpi = pd.DataFrame({"2024": kpis(prev), "2025": kpis(cur)})
kpi["Change"] = kpi["2025"] - kpi["2024"]
kpi["Change %"] = (kpi["2025"] / kpi["2024"] - 1).mul(100).round(1)
kpi.loc["Midlands rainfall (mm)"] = [mid[2024], mid[2025], mid[2025] - mid[2024], round((mid[2025] / mid[2024] - 1) * 100, 1)]

def by(col):
    rows = []
    for k, g in cur.groupby(col):
        p = prev[prev[col] == k]
        rows.append({col: k, "Overflows": len(g), "Spills 2024": p.spills.sum(), "Spills 2025": g.spills.sum(),
                     "Change %": round((g.spills.sum() / p.spills.sum() - 1) * 100, 1) if p.spills.sum() else np.nan,
                     "Avg spills/overflow 2025": round(g.spills.mean(), 1),
                     "Overflows 60+ spills 2025": int((g.spills >= HIGH).sum()),
                     "Spill hours 2025": round(g.duration_hrs.sum()),
                     "Monitors <90% 2025": int(g.dq_low_edm_op.sum())})
    return pd.DataFrame(rows).sort_values("Spills 2025", ascending=False)
by_basin, by_asset = by("river_basin"), by("asset_type")
top_catch = cur.groupby("wfd_catchment").agg(Overflows=("spills", "size"), Spills_2025=("spills", "sum"),
                                              Overflows_60plus=("spills", lambda s: int((s >= HIGH).sum()))) \
    .sort_values("Spills_2025", ascending=False).head(20).reset_index()

# ---------- 3. Exception lists ----------
prev_op = prev.set_index("unique_id").edm_op_pct
maint = cur[cur.dq_low_edm_op].copy()
maint["op_2024"] = maint.unique_id.map(prev_op)
maint["Repeat (<90% in 2024 too)"] = maint.op_2024 < 90
maint = maint[["unique_id", "site_name", "river_basin", "asset_type", "edm_op_pct", "op_2024", "Repeat (<90% in 2024 too)", "low_op_reason"]] \
    .sort_values(["Repeat (<90% in 2024 too)", "edm_op_pct"], ascending=[False, True])
maint = maint[~maint.low_op_reason.astype(str).str.startswith("No longer operational")]  # decommissioned: not a maintenance job

prev_sp = prev.set_index("unique_id").spills
high = cur[cur.spills >= HIGH].copy()
high["spills_2024"] = high.unique_id.map(prev_sp)
high["No improvement action 2025"] = high.improvement_activity.astype(str).str.startswith("No improvement")
high = high[["unique_id", "site_name", "receiving_water", "river_basin", "asset_type", "spills", "spills_2024", "duration_hrs",
             "edm_op_pct", "No improvement action 2025", "improvement_activity", "investigation_activity"]] \
    .rename(columns={"spills": "spills_2025", "duration_hrs": "hours_2025"}).sort_values(["No improvement action 2025", "spills_2025"], ascending=[False, False])

# ---------- write workbook ----------
path = os.path.join(O, "Severn_Trent_Overflow_Performance_Pack_2025.xlsx")
with pd.ExcelWriter(path, engine="openpyxl") as xw:
    notes = pd.DataFrame({"Severn Trent storm overflow performance pack, 2025 return": [
        "Source: Environment Agency EDM annual returns 2024-2025; Met Office HadUK-Grid Midlands rainfall.",
        "Spills counted with the EA 12/24-hour method. River basin derived from WFD waterbody ID.",
        "Sheets: KPIs | By river basin | By asset type | Top catchments | QA checks | QA - large rises | Maintenance exceptions | High-spill exceptions",
        "Context: 2025 Midlands rainfall was 28% below 2024; roughly half the fall in spills is weather (see 02_Findings_Summary.md)."]})
    notes.to_excel(xw, sheet_name="Read me", index=False)
    kpi.to_excel(xw, sheet_name="KPIs")
    by_basin.to_excel(xw, sheet_name="By river basin", index=False)
    by_asset.to_excel(xw, sheet_name="By asset type", index=False)
    top_catch.to_excel(xw, sheet_name="Top catchments", index=False)
    qa.to_excel(xw, sheet_name="QA checks", index=False)
    swings.to_excel(xw, sheet_name="QA - large rises", index=False)
    maint.to_excel(xw, sheet_name="Maintenance exceptions", index=False)
    high.to_excel(xw, sheet_name="High-spill exceptions", index=False)
    for ws in xw.book.worksheets:
        ws.freeze_panes = "A2"
        for col in ws.columns:
            w = max(len(str(c.value)) if c.value is not None else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(10, w + 2), 60)
pd.set_option("display.width", 220)
print(kpi.to_string()); print(); print(qa.to_string()); print()
print(by_basin.to_string()); print(); print(by_asset.to_string()); print()
print("maintenance exceptions:", len(maint), "repeat:", int(maint["Repeat (<90% in 2024 too)"].sum()))
print("high-spill exceptions:", len(high), "no improvement:", int(high["No improvement action 2025"].sum()))
print(maint.low_op_reason.value_counts().to_string())
