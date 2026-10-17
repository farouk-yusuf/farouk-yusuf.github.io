"""
UHB waiting times - step 2: the monthly elective (RTT) performance report a trust performance analyst produces.
  - Trust KPIs over time vs national milestones (65% <18 weeks by Mar 2026; 70% by Mar 2027; <1% over 52 weeks)
  - Demand vs capacity: clock starts vs clock stops, explaining list growth
  - Specialty table: where the long waits are, and which specialties are deteriorating
  - Benchmark against six large Midlands trusts and England
  - Six-month waiting list forecast, back-tested on held-out months
  - Data checks: missing submissions, unknown clock starts
Output: outputs/UHB_RTT_Performance_Report.xlsx, charts, key_figures.csv
"""
import os, glob, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
O = os.path.join(BASE, "outputs"); os.makedirs(O, exist_ok=True)
NAMES = {"RRK": "University Hospitals Birmingham", "RXK": "Sandwell & West Birmingham", "RKB": "UH Coventry & Warwickshire",
         "RX1": "Nottingham University Hospitals", "RWE": "University Hospitals of Leicester", "RL4": "Royal Wolverhampton",
         "RJE": "UH North Midlands", "ENGLAND": "England"}
frames = []
for f in sorted(glob.glob(os.path.join(BASE, "clean", "monthly_v2", "*.csv"))):
    d = pd.read_csv(f); d["month"] = pd.to_datetime(os.path.basename(f)[:8]).to_period("M"); frames.append(d)
rtt = pd.concat(frames, ignore_index=True)
rtt.to_csv(os.path.join(BASE, "clean", "rtt_provider_specialty_monthly.csv"), index=False)
ALL = "Total"  # NHS England publishes a 'Total' treatment function row; check it exists
spec_total = rtt.specialty.str.strip().eq(ALL)
assert spec_total.any(), rtt.specialty.unique()[:20]
tot = rtt[spec_total]; spec = rtt[~spec_total]

def kpis(g):
    w = g[g.part == "Part_2"]; starts = g[g.part == "Part_3"]; stops = g[g.part.isin(["Part_1A", "Part_1B"])]
    n = w.known_clock_start.sum()
    return pd.Series({"waiting_list": n, "unknown_clock_start": w.unknown_clock_start.sum(),
                      "pct_within_18": w.within_18.sum() / n * 100 if n else np.nan,
                      "over_52": w.over_52.sum(), "over_65": w.over_65.sum(), "over_78": w.over_78.sum(),
                      "pct_over_52": w.over_52.sum() / n * 100 if n else np.nan,
                      "clock_starts": starts.total_all.sum(), "clock_stops": stops.total_all.sum()})
trust = tot.groupby(["provider", "month"])[tot.columns.drop(["provider", "month"])].apply(kpis).reset_index()
trust["net_growth"] = trust.clock_starts - trust.clock_stops
u = trust[trust.provider == "RRK"].set_index("month").sort_index()
latest = u.index.max(); yr_ago = latest - 12

# ---- data checks ----
months = pd.period_range(trust.month.min(), latest, freq="M")
missing = [(NAMES[p], str(m)) for p in NAMES for m in months if not ((trust.provider == p) & (trust.month == m)).any()]
recon = (u.waiting_list.diff() - u.net_growth).dropna()   # list change should roughly equal starts - stops (validation removals explain the rest)
checks = pd.DataFrame([
    ("Months covered", f"{months[0]} to {months[-1]} ({len(months)})"),
    ("Missing provider-months (UHB, peers, England)", len(missing) and "; ".join(f"{a} {b}" for a, b in missing) or "None"),
    ("UHB patients with unknown clock start (latest month)", int(u.loc[latest, "unknown_clock_start"])),
    ("UHB: avg monthly gap between list change and starts minus stops", f"{recon.mean():,.0f} (validation and other removals)"),
], columns=["Check", "Result"])

# ---- specialty table ----
s = spec[(spec.provider == "RRK") & (spec.part == "Part_2")]
cur, old = s[s.month == latest].set_index("specialty"), s[s.month == yr_ago].set_index("specialty")
st = pd.DataFrame({"Waiting list": cur.known_clock_start, "List 12 months ago": old.known_clock_start.reindex(cur.index),
                   "% within 18 weeks": (cur.within_18 / cur.known_clock_start * 100).round(1),
                   "% within 18 weeks 12 months ago": (old.within_18 / old.known_clock_start * 100).reindex(cur.index).round(1),
                   "52+ week waiters": cur.over_52, "65+ week waiters": cur.over_65, "78+ week waiters": cur.over_78})
st["List change %"] = ((st["Waiting list"] / st["List 12 months ago"] - 1) * 100).round(1)
st["18-week change (pts)"] = (st["% within 18 weeks"] - st["% within 18 weeks 12 months ago"]).round(1)
st["Share of trust 52+ waits %"] = (st["52+ week waiters"] / cur.over_52.sum() * 100).round(1)
st = st.sort_values("52+ week waiters", ascending=False)

# ---- benchmark ----
b = trust[trust.month == latest].set_index("provider")
b12 = trust[trust.month == yr_ago].set_index("provider")
bench = pd.DataFrame({"Trust": b.index.map(NAMES), "Waiting list": b.waiting_list, "% within 18 weeks": b.pct_within_18.round(1),
                      "18-week change vs 12m ago (pts)": (b.pct_within_18 - b12.pct_within_18).round(1),
                      "% waiting 52+ weeks": b.pct_over_52.round(2), "List change vs 12m ago %": ((b.waiting_list / b12.waiting_list - 1) * 100).round(1)}) \
    .sort_values("% within 18 weeks", ascending=False)

# ---- forecast: a demand-and-capacity model, back-tested ----
# list(t) = list(t-1) + clock starts - clock stops - other removals (validation etc.)
# Starts and stops follow last year's seasonal pattern, scaled by how the last 3 months compared with a year earlier.
removals = (u.waiting_list.diff() - u.net_growth)
def dc_forecast(hist, h):
    out, wl_ = [], hist.waiting_list.iloc[-1]
    rs = hist.clock_starts.tail(3).sum() / hist.clock_starts.shift(12).tail(3).sum()
    rp = hist.clock_stops.tail(3).sum() / hist.clock_stops.shift(12).tail(3).sum()
    rem = (hist.waiting_list.diff() - hist.net_growth).tail(6).mean()
    for i in range(1, h + 1):
        m = hist.index[-1] + i
        st_, sp_ = hist.clock_starts.loc[m - 12] * rs, hist.clock_stops.loc[m - 12] * rp
        wl_ = wl_ + st_ - sp_ + rem; out.append((m, st_, sp_, wl_))
    return pd.DataFrame(out, columns=["month", "starts", "stops", "waiting_list"]).set_index("month")
wl = u.waiting_list
bt = dc_forecast(u.iloc[:-6], 6).waiting_list
mape = (abs(bt - wl.iloc[-6:]) / wl.iloc[-6:]).mean() * 100
naive_mape = (abs(wl.iloc[-7] - wl.iloc[-6:]) / wl.iloc[-6:]).mean() * 100
trend = wl.iloc[-7] + (wl.iloc[:-6].diff().tail(6).mean()) * np.arange(1, 7)
trend_mape = (abs(trend - wl.iloc[-6:].values) / wl.iloc[-6:].values).mean() * 100
fcdf = dc_forecast(u, 7)            # to March 2027
fc = fcdf.waiting_list
fct = fcdf.round(0); fct.index = fct.index.astype(str)
fct.columns = ["Forecast clock starts", "Forecast clock stops", "Forecast waiting list"]
backtest = pd.DataFrame({"Month": wl.index[-6:].astype(str), "Actual": wl.iloc[-6:].values, "Demand-capacity model": bt.round(0).values,
                         "Trend model": trend.round(0), "No change (naive)": wl.iloc[-7]})
# ---- key figures ----
mar26 = pd.Period("2026-03", "M")
K = {"latest_month": str(latest), "waiting_list": int(u.loc[latest, "waiting_list"]), "waiting_list_12m_ago": int(u.loc[yr_ago, "waiting_list"]),
     "pct_within_18": round(u.loc[latest, "pct_within_18"], 1), "pct_within_18_12m_ago": round(u.loc[yr_ago, "pct_within_18"], 1),
     "pct_within_18_mar26": round(u.loc[mar26, "pct_within_18"], 1), "pct_within_18_mar25": round(u.loc[mar26 - 12, "pct_within_18"], 1),
     "over_52": int(u.loc[latest, "over_52"]), "pct_over_52": round(u.loc[latest, "pct_over_52"], 2), "pct_over_52_mar26": round(u.loc[mar26, "pct_over_52"], 2),
     "england_pct_within_18": round(b.loc["ENGLAND", "pct_within_18"], 1), "england_pct_over_52": round(b.loc["ENGLAND", "pct_over_52"], 2),
     "rank_18wk_among_7_trusts": int(bench.drop(index="ENGLAND")["% within 18 weeks"].rank(ascending=False)["RRK"]),
     "starts_12m": int(u.clock_starts.tail(12).sum()), "stops_12m": int(u.clock_stops.tail(12).sum()),
     "forecast_list_mar27": int(fc.iloc[-1]), "forecast_mape_pct": round(mape, 2), "naive_mape_pct": round(naive_mape, 2), "trend_mape_pct": round(trend_mape, 2),
     "list_low_mar26": int(u.loc[mar26, "waiting_list"]), "stops_aprAug26": int(u.clock_stops.loc["2026-04":"2026-08"].sum()), "stops_aprAug25": int(u.clock_stops.loc["2025-04":"2025-08"].sum()),
     "starts_aprAug26": int(u.clock_starts.loc["2026-04":"2026-08"].sum()), "starts_aprAug25": int(u.clock_starts.loc["2025-04":"2025-08"].sum()),
     "top_52_specialty": st.index[0], "top_52_specialty_share": st.iloc[0]["Share of trust 52+ waits %"], "missing_months": len(missing)}
pd.Series(K).to_csv(os.path.join(O, "key_figures.csv"), header=["value"])

ts = u[["waiting_list", "pct_within_18", "over_52", "over_65", "over_78", "pct_over_52", "clock_starts", "clock_stops", "net_growth", "unknown_clock_start"]].round(2)
ts.index = ts.index.astype(str)
with pd.ExcelWriter(os.path.join(O, "UHB_RTT_Performance_Report.xlsx"), engine="openpyxl") as xw:
    pd.DataFrame({"University Hospitals Birmingham: elective waiting times (RTT) report": [
        f"Source: NHS England RTT full monthly extracts, Apr 2023 - {latest} (OGL). Provider RRK; commissioner rows summed to trust level.",
        "Waiting list = incomplete pathways with a known clock start. 18-week performance = % of those waiting under 18 weeks.",
        "Milestones: 65% within 18 weeks by March 2026 (every trust +5 pts), 70% by March 2027, under 1% waiting 52+ weeks.",
        "Sheets: Trust trend | Specialties | Benchmark | Forecast | Forecast back-test | Data checks"]}).to_excel(xw, sheet_name="Read me", index=False)
    ts.to_excel(xw, sheet_name="Trust trend")
    st.to_excel(xw, sheet_name="Specialties")
    bench.to_excel(xw, sheet_name="Benchmark", index=False)
    fct.to_excel(xw, sheet_name="Forecast")
    backtest.to_excel(xw, sheet_name="Forecast back-test", index=False)
    pd.DataFrame({"Model": ["Demand-capacity", "Trend (6-month average change)", "No change (naive)"],
                  "Mean absolute % error, last 6 months held out": [round(mape, 2), round(trend_mape, 2), round(naive_mape, 2)]}) \
        .to_excel(xw, sheet_name="Forecast back-test", startrow=9, index=False)
    checks.to_excel(xw, sheet_name="Data checks", index=False)
    for ws in xw.book.worksheets:
        ws.freeze_panes = "A2"
        for col in ws.columns:
            w = max(len(str(c.value)) if c.value is not None else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(10, w + 2), 70)

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
x = u.index.to_timestamp()
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(x, u.pct_within_18, "o-", ms=3, color="#1f6f8b", label="UHB")
e = trust[trust.provider == "ENGLAND"].set_index("month").sort_index()
ax.plot(e.index.to_timestamp(), e.pct_within_18, "-", color="grey", label="England")
ax.axhline(65, ls="--", color="#c0392b", lw=1); ax.text(x[0], 65.4, "65% milestone (Mar 2026)", color="#c0392b", fontsize=8)
ax.axhline(70, ls=":", color="#c0392b", lw=1); ax.text(x[0], 70.4, "70% milestone (Mar 2027)", color="#c0392b", fontsize=8)
ax.set_ylabel("% waiting under 18 weeks"); ax.set_title("18-week performance: UHB vs England"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(os.path.join(O, "chart1_18_week_performance.png"), dpi=160); plt.close()
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(x, wl / 1000, "o-", ms=3, color="#1f6f8b", label="Actual")
ax.plot(fc.index.to_timestamp(), fc / 1000, "o--", ms=3, color="#e67e22", label="Forecast")
ax.set_ylabel("Waiting list (thousands)"); ax.set_title("UHB waiting list and six-month forecast"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(os.path.join(O, "chart2_waiting_list_forecast.png"), dpi=160); plt.close()
pd.set_option("display.width", 220)
print(pd.Series(K).to_string()); print(bench.to_string()); print(st.head(12).to_string()); print(checks.to_string())
print(ts.tail(14)[["waiting_list", "pct_within_18", "over_52", "pct_over_52", "clock_starts", "clock_stops"]].to_string())
