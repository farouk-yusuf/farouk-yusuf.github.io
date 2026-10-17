"""
Severn Trent storm overflows - step 2: analysis.
Business questions
  Q1 How much of Severn Trent's 2025 fall in spills is explained by a drier year?
  Q2 Has monitoring reliability changed, and how does that bias year-on-year comparisons?
  Q3 Which overflows spill heavily every year even after allowing for rainfall (investment priorities)?
Inputs : clean/*.csv from 01_build_clean_data.py
Outputs: outputs/*.csv and outputs/*.png
"""
import os, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C, O = os.path.join(BASE, "clean"), os.path.join(BASE, "outputs")
os.makedirs(O, exist_ok=True)
st = pd.read_csv(os.path.join(C, "st_overflows_2020_2025.csv"))
comp = pd.read_csv(os.path.join(C, "company_summary_2020_2025.csv"))
rain = pd.read_csv(os.path.join(C, "rainfall_monthly_annual.csv"))
mid = rain[rain.region == "Midlands"].set_index("year")["ann"]
eng = rain[rain.region == "England"].set_index("year")["ann"]
HIGH = 60  # spills/year: the high-spill level used in the EA's own summary tables
out = {}

# ---------- Q2: monitoring reliability ----------
st["reliable"] = st["edm_op_pct"] >= 90
yearly = st.groupby("year").agg(
    overflows_listed=("site_name", "size"),
    with_spill_data=("spills", lambda s: s.notna().sum()),
    total_spills=("spills", "sum"), total_hours=("duration_hrs", "sum"),
    monitors_below_90pct=("dq_low_edm_op", "sum")).reset_index()
yearly["share_monitors_below_90pct"] = yearly.monitors_below_90pct / yearly.with_spill_data
rel = st[st.reliable & st.spills.notna()].groupby("year").agg(
    reliable_overflows=("spills", "size"), avg_spills_reliable=("spills", "mean"),
    avg_hours_reliable=("duration_hrs", "mean")).reset_index()
yearly = yearly.merge(rel, on="year")
yearly["avg_spills_all"] = yearly.total_spills / yearly.with_spill_data
yearly["midlands_rain_mm"] = yearly.year.map(mid)
yearly.to_csv(os.path.join(O, "st_yearly_summary.csv"), index=False)

# ---------- Q1: rainfall model ----------
# Fit avg spills per reliably-monitored overflow on Midlands annual rainfall, 2020-2024, then predict 2025.
fit = yearly[yearly.year <= 2024]
b, a = np.polyfit(fit.midlands_rain_mm, fit.avg_spills_reliable, 1)
pred = a + b * yearly.midlands_rain_mm
r2 = 1 - ((fit.avg_spills_reliable - (a + b * fit.midlands_rain_mm)) ** 2).sum() / ((fit.avg_spills_reliable - fit.avg_spills_reliable.mean()) ** 2).sum()
yearly["expected_from_rain"] = pred
y24, y25 = yearly.set_index("year").loc[2024], yearly.set_index("year").loc[2025]
actual_fall = y24.avg_spills_reliable - y25.avg_spills_reliable
rain_fall = b * (y24.midlands_rain_mm - y25.midlands_rain_mm)
out.update(slope_spills_per_100mm=b * 100, intercept=a, r2_2020_24=r2,
           expected_2025=y25.expected_from_rain, actual_2025=y25.avg_spills_reliable,
           gap_2025_pct=(y25.avg_spills_reliable / y25.expected_from_rain - 1) * 100,
           fall_2024_25=actual_fall, fall_explained_by_rain=rain_fall,
           share_explained_by_rain=rain_fall / actual_fall,
           headline_total_spills_change_pct=(y25.total_spills / y24.total_spills - 1) * 100,
           headline_hours_change_pct=(y25.total_hours / y24.total_hours - 1) * 100,
           rain_change_pct=(y25.midlands_rain_mm / y24.midlands_rain_mm - 1) * 100)
# Like-for-like dry years: 2022 vs 2025
y22 = yearly.set_index("year").loc[2022]
out.update(dry_2022_rain=y22.midlands_rain_mm, dry_2022_avg=y22.avg_spills_reliable,
           dry_2025_rain=y25.midlands_rain_mm, dry_2025_avg=y25.avg_spills_reliable,
           dry_year_change_pct=(y25.avg_spills_reliable / y22.avg_spills_reliable - 1) * 100,
           share_below90_2022=y22.share_monitors_below_90pct, share_below90_2025=y25.share_monitors_below_90pct)

# National context: all companies, England rainfall
nat = comp.groupby("year")[["total_spills", "overflows_with_spill_data"]].sum()
nat["avg"] = nat.total_spills / nat.overflows_with_spill_data
nat["eng_rain"] = nat.index.map(eng)
st_c = comp[comp.company == "Severn Trent"].set_index("year")
cmp = comp.copy()
cmp = cmp.pivot(index="company", columns="year", values="avg_spills_per_overflow")
cmp["change_2024_25_pct"] = (cmp[2025] / cmp[2024] - 1) * 100
cmp["change_2022_25_pct"] = (cmp[2025] / cmp[2022] - 1) * 100
cmp.sort_values("change_2024_25_pct").to_csv(os.path.join(O, "company_comparison_avg_spills.csv"))
out.update(national_change_2024_25_pct=(nat.loc[2025, "avg"] / nat.loc[2024, "avg"] - 1) * 100,
           england_rain_change_pct=(nat.loc[2025, "eng_rain"] / nat.loc[2024, "eng_rain"] - 1) * 100)

# ---------- Q3: overflow-level priorities (2023-2025 linked panel) ----------
s25 = st[st.year == 2025].set_index("unique_id")
s24 = st[st.year == 2024].set_index("unique_id")
s23 = st[st.year == 2023].set_index("unique_id")
panel = pd.DataFrame({
    "site_name": s25.site_name, "receiving_water": s25.receiving_water, "asset_type": s25.asset_type,
    "permit": s25.permit, "spills_2025": s25.spills, "hours_2025": s25.duration_hrs, "op_2025": s25.edm_op_pct,
    "improvement_2025": s25.improvement_activity, "investigation_2025": s25.investigation_activity})
panel["spills_2024"] = s24.spills.reindex(panel.index)
panel["op_2024"] = s24.edm_op_pct.reindex(panel.index)
old = s24.old_id.reindex(panel.index)
panel["spills_2023"] = old.map(s23.spills)
panel["op_2023"] = old.map(s23.edm_op_pct)
linked = panel.dropna(subset=["spills_2023", "spills_2024", "spills_2025"])
reliable3 = linked[(linked[["op_2023", "op_2024", "op_2025"]] >= 90).all(axis=1)].copy()
# rainfall adjustment: scale each year's count to a 'typical wet year' (1,000mm) using the fitted model
ref = a + b * 1000.0
for y in (2023, 2024, 2025):
    reliable3[f"adj_{y}"] = reliable3[f"spills_{y}"] * ref / (a + b * mid[y])
reliable3["adj_mean"] = reliable3[[f"adj_{y}" for y in (2023, 2024, 2025)]].mean(axis=1)
reliable3["years_at_or_above_60_adj"] = (reliable3[[f"adj_{y}" for y in (2023, 2024, 2025)]] >= HIGH).sum(axis=1)
reliable3["persistent_high"] = reliable3.years_at_or_above_60_adj == 3
reliable3["no_improvement_2025"] = reliable3.improvement_2025.astype(str).str.startswith("No improvement")
# not improving: 2025 rainfall-adjusted count at least as high as the 2023-24 adjusted average, from a material base
reliable3["adj_2023_24"] = reliable3[["adj_2023", "adj_2024"]].mean(axis=1)
reliable3["not_improving"] = (reliable3.adj_2025 >= reliable3.adj_2023_24) & (reliable3.adj_2023_24 >= 30)
pr = reliable3[reliable3.persistent_high].sort_values("adj_mean", ascending=False)
cols = ["site_name", "receiving_water", "asset_type", "spills_2023", "spills_2024", "spills_2025",
        "adj_2023", "adj_2024", "adj_2025", "adj_mean", "hours_2025", "improvement_2025", "investigation_2025"]
pr[cols].round(1).to_csv(os.path.join(O, "priority_overflows_persistent_high.csv"))
reliable3[reliable3.not_improving].sort_values("adj_2025", ascending=False)[cols].round(1).to_csv(
    os.path.join(O, "overflows_not_improving_2025.csv"))
out.update(panel_linked=len(linked), panel_reliable_all3=len(reliable3),
           persistent_high_n=len(pr), persistent_high_no_improvement=int(pr.no_improvement_2025.sum()),
           persistent_high_share_of_2025_spills=pr.spills_2025.sum() / reliable3.spills_2025.sum(),
           persistent_high_share_of_overflows=len(pr) / len(reliable3),
           not_improving_n=int(reliable3.not_improving.sum()),
           asset_type_of_persistent=pr.asset_type.value_counts().to_dict())
pd.Series(out).to_csv(os.path.join(O, "key_figures.csv"), header=["value"])

# ---------- Charts ----------
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(7, 4.5))
ax.scatter(yearly.midlands_rain_mm, yearly.avg_spills_reliable, s=60, color="#1f6f8b")
for _, r in yearly.iterrows():
    ax.annotate(int(r.year), (r.midlands_rain_mm, r.avg_spills_reliable), xytext=(6, 4), textcoords="offset points")
xs = np.linspace(690, 1030, 50); ax.plot(xs, a + b * xs, "--", color="grey", label="Fitted on 2020-2024")
ax.set_xlabel("Midlands annual rainfall (mm)"); ax.set_ylabel("Average spills per overflow\n(monitors working ≥90% of year)")
ax.set_title("Severn Trent: spills track rainfall, but 2025 sits below the line"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(os.path.join(O, "chart1_spills_vs_rainfall.png"), dpi=160); plt.close()

fig, ax1 = plt.subplots(figsize=(7, 4.5))
ax1.bar(yearly.year, yearly.total_spills / 1000, color="#9fc5d6")
ax1.set_ylabel("Total recorded spills (thousands)"); ax2 = ax1.twinx()
ax2.plot(yearly.year, yearly.share_monitors_below_90pct * 100, "o-", color="#c0392b")
ax2.set_ylabel("% of monitors working <90% of the year", color="#c0392b"); ax2.spines["top"].set_visible(False)
ax1.set_title("Spill totals and monitor reliability, 2020-2025"); fig.tight_layout()
fig.savefig(os.path.join(O, "chart2_spills_and_monitor_reliability.png"), dpi=160); plt.close()

top = pr.head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(8, 5.5))
ax.barh(top.site_name.str.slice(0, 40), top.adj_mean, color=np.where(top.no_improvement_2025, "#c0392b", "#1f6f8b"))
ax.axvline(HIGH, color="grey", ls="--"); ax.set_xlabel("Rainfall-adjusted spills per year, 2023-2025 average")
ax.set_title("Top 15 persistent high-spilling overflows\n(red = no improvement action reported in 2025)")
fig.tight_layout(); fig.savefig(os.path.join(O, "chart3_priority_overflows.png"), dpi=160); plt.close()

pd.set_option("display.width", 200)
print(yearly.round(2).to_string()); print(); print(pd.Series(out).to_string()); print()
print(cmp[[2022, 2024, 2025, "change_2024_25_pct", "change_2022_25_pct"]].round(1).sort_values("change_2024_25_pct").to_string())
print(pr[cols].head(12).round(0).to_string())
