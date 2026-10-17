"""
Platform Housing - step 2: Tenant Satisfaction Measures benchmarking (the annual board report a housing
association performance team produces), with Housing Ombudsman complaint outcomes alongside.
Inputs : raw/2024_TSM_Full_Data_v2.1_FINAL.xlsx (2023/24), raw/2025_TSM_Full_Data_v1.1_FINAL.xlsx (2024/25), clean/ombudsman_*.csv
Output : outputs/Platform_TSM_Benchmarking_Pack.xlsx, charts, key_figures.csv
"""
import os, re, numpy as np, pandas as pd, openpyxl
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, C, O = (os.path.join(BASE, d) for d in ("raw", "clean", "outputs")); os.makedirs(O, exist_ok=True)
PLATFORM = "Platform Housing Group Limited"
TP = {"TP01": "Overall satisfaction", "TP02": "Repairs service", "TP03": "Time taken for repair", "TP04": "Home well maintained",
      "TP05": "Home is safe", "TP06": "Listens and acts", "TP07": "Keeps tenants informed", "TP08": "Treats fairly and with respect",
      "TP09": "Complaints handling", "TP10": "Communal areas", "TP11": "Positive contribution to neighbourhood", "TP12": "ASB handling"}
MI = {"BS01": "Gas safety checks", "BS02": "Fire risk assessments", "BS03": "Asbestos surveys", "BS04": "Legionella assessments",
      "BS05": "Lift safety checks", "RP01": "Homes not meeting Decent Homes (%)", "RP02 1": "Non-emergency repairs in target (%)",
      "RP02 2": "Emergency repairs in target (%)", "NM01 1": "ASB cases per 1,000 homes"}

def table(path, sheet_prefix):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sn = [s for s in wb.sheetnames if s.replace(" ", "").startswith(sheet_prefix)][0]
    rows = list(wb[sn].iter_rows(values_only=True))
    h = [i for i, r in enumerate(rows) if r[0] == "Landlord name"][0]
    df = pd.DataFrame(rows[h + 1:], columns=[str(c) for c in rows[h]]).dropna(subset=["Landlord name"])
    return df[~df["Landlord name"].astype(str).str.startswith(("Notes", "1.", "2."))]

def pick(df, code, prefix="Proportion"):
    cols = [c for c in df.columns if f"({code})" in c and c.startswith(prefix) and "unweighted" not in c and "responses)" not in c]
    return pd.to_numeric(df[cols[0]], errors="coerce") if cols else pd.Series(np.nan, index=df.index)

frames = []
for year, f in [("2023/24", "2024_TSM_Full_Data_v2.1_FINAL.xlsx"), ("2024/25", "2025_TSM_Full_Data_v1.1_FINAL.xlsx")]:
    tag = "TSM24" if year == "2023/24" else "TSM25"
    p, mi = table(os.path.join(RAW, f), f"{tag}_LCRA"), table(os.path.join(RAW, f), f"{tag}_Management")
    out = pd.DataFrame({"year": year, "landlord": p["Landlord name"], "type": p["Landlord type"],
                        "size_band": p.iloc[:, 4], "region": p["Landlord predominant region"],
                        "method": p[[c for c in p.columns if c.startswith("Predominant collection method")][0]] if any(c.startswith("Predominant collection method") for c in p.columns) else np.nan,
                        "sample": pd.to_numeric(p["Total sample size achieved"], errors="coerce")})
    for k in TP: out[k] = pick(p, k)
    mi_out = pd.DataFrame({"landlord": mi["Landlord name"]})
    for k in MI: mi_out[k] = pick(mi, k, "Proportion" if not k.startswith("NM01") else "Number of anti-social behaviour cases, opened")
    s1 = [c for c in mi.columns if c.startswith("LCRA - Number of stage one complaints") and "per 1,000" in c]
    s1p = [c for c in mi.columns if c.startswith("LCRA - Proportion of stage one complaints")]
    s2p = [c for c in mi.columns if c.startswith("LCRA - Proportion of stage two complaints")]
    mi_out["CH01 1"] = pd.to_numeric(mi[s1[0]], errors="coerce") if s1 else np.nan
    mi_out["CH02 1"] = pd.to_numeric(mi[s1p[0]], errors="coerce") if s1p else np.nan
    mi_out["CH02 2"] = pd.to_numeric(mi[s2p[0]], errors="coerce") if s2p else np.nan
    frames.append(out.merge(mi_out, on="landlord", how="left"))
tsm = pd.concat(frames, ignore_index=True)
MI.update({"CH01 1": "Stage 1 complaints per 1,000 homes", "CH02 1": "Stage 1 complaints answered in time (%)", "CH02 2": "Stage 2 complaints answered in time (%)"})
tsm.to_csv(os.path.join(C, "tsm_2023_24_2024_25.csv"), index=False)
cur = tsm[tsm.year == "2024/25"]; prev = tsm[tsm.year == "2023/24"]
plat, plat_prev = cur[cur.landlord == PLATFORM].iloc[0], prev[prev.landlord == PLATFORM].iloc[0]
large = cur[(cur.type == "PRP") & (cur.size_band.astype(str).str.contains(">40"))]
midl = cur[(cur.type == "PRP") & (cur.region == "Midlands")]

# ---- benchmark table ----
HIGHER_IS_BETTER = {k: True for k in list(TP) + ["BS01", "BS02", "BS03", "BS04", "BS05", "RP02 1", "RP02 2", "CH02 1", "CH02 2"]}
HIGHER_IS_BETTER.update({"RP01": False, "NM01 1": None, "CH01 1": None})
rows = []
for k, label in {**TP, **MI}.items():
    v = plat[k]; vals = large[k].dropna()
    hib = HIGHER_IS_BETTER[k]
    q = (vals < v).mean() if hib else ((vals > v).mean() if hib is False else np.nan)
    rows.append({"Measure": f"{k} {label}", "Platform 2024/25": round(v, 1), "Platform 2023/24": round(plat_prev[k], 1),
                 "Change (pts)": round(v - plat_prev[k], 1), "Large HA median (>40k homes)": round(vals.median(), 1),
                 "Midlands HA median": round(midl[k].median(), 1), "Gap to large HA median": round(v - vals.median(), 1),
                 "Quartile vs large HAs": (None if np.isnan(q) else ("Top" if q >= .75 else "Upper middle" if q >= .5 else "Lower middle" if q >= .25 else "Bottom")),
                 "Large HAs compared": len(vals)})
bench = pd.DataFrame(rows)

# ---- what drives overall satisfaction (all landlords, 2024/25) ----
drv = cur[list(TP)].dropna()
corr = drv.corr()["TP01"].drop("TP01").sort_values(ascending=False)
drivers = pd.DataFrame({"Measure": [f"{k} {TP[k]}" for k in corr.index], "Correlation with overall satisfaction": corr.round(2).values,
                        "Platform gap to large HA median (pts)": [round(plat[k] - large[k].median(), 1) for k in corr.index]})
drivers["Priority"] = np.where((drivers["Correlation with overall satisfaction"] >= 0.8) & (drivers["Platform gap to large HA median (pts)"] < 0), "Improve", "")

# ---- survey method check ----
meth = cur.groupby("method").TP01.agg(["count", "median"]).round(1).reset_index().rename(columns={"method": "Predominant collection method", "count": "Landlords", "median": "Median overall satisfaction"})

# ---- Ombudsman ----
om = pd.read_csv(os.path.join(C, "ombudsman_2025_26.csv"))
om_tab = om[["landlord", "landlord_type", "homes", "determinations", "determinations_per_10k_homes", "findings", "mal_findings",
             "mal_rate_2025_26", "mal_rate_2024_25", "mal_rate_2023_24", "orders", "compensation", "cases_received"]].sort_values("mal_rate_2025_26")
cat = pd.read_csv(os.path.join(C, "ombudsman_findings_by_category.csv"))
cat["upheld"] = cat.severe_mal + cat.mal + cat.service_failure
pc = cat[cat.landlord == PLATFORM].set_index("category")
peer_cat = cat[cat.landlord != PLATFORM].groupby("category")[["upheld", "total"]].sum()
cat_tab = pd.DataFrame({"Platform findings": pc.total, "Platform upheld": pc.upheld,
                        "Platform upheld %": (pc.upheld / pc.total * 100).round(0),
                        "Peer upheld %": (peer_cat.upheld / peer_cat.total * 100).round(0)}).dropna(subset=["Platform findings"]).sort_values("Platform findings", ascending=False)

# ---- year-on-year sense checks before anything goes to the board ----
yoy = pd.DataFrame([
    ("RP02 1 Non-emergency repairs in target", "91.7% -> 62.3%", "Repairs counted fell from 90,250 to 13,872 with the same 28-day target",
     "Likely change in how repairs are classified or counted, not a 29-point fall in performance. Confirm with Repairs before reporting."),
    ("NM01 ASB cases per 1,000 homes", "33 -> 118", "ASB cases opened rose from 1,619 to 5,716 on similar stock",
     "Likely a recording or definition change (e.g. counting reports rather than cases). Confirm with Neighbourhoods."),
    ("CH01 Stage 1 complaints per 1,000 homes", "43 -> 73", "Stage 1 complaints rose from 1,755 to 3,019",
     "Could be real or reflect wider recording of complaints since the Complaint Handling Code became statutory in 2024. Check with Customer Experience."),
], columns=["Measure", "Platform 2023/24 -> 2024/25", "What the underlying counts show", "Interpretation / action"])

K = {"platform_TP01": plat.TP01, "platform_TP01_prev": plat_prev.TP01, "large_median_TP01": large.TP01.median(), "n_large": len(large),
     "platform_method": plat.method, "platform_sample": plat["sample"],
     "top_quartile": int((bench["Quartile vs large HAs"] == "Top").sum()), "bottom_quartile": int((bench["Quartile vs large HAs"] == "Bottom").sum()),
     "platform_mal_rate": float(om.loc[om.landlord == PLATFORM, "mal_rate_2025_26"].iloc[0]),
     "peer_mal_rate_median": float(om[om.landlord != PLATFORM].mal_rate_2025_26.median()),
     "platform_mal_rank": int(om.mal_rate_2025_26.rank(method="min")[om.landlord == PLATFORM].iloc[0]), "n_peers_om": len(om)}
pd.Series(K).to_csv(os.path.join(O, "key_figures.csv"), header=["value"])

with pd.ExcelWriter(os.path.join(O, "Platform_TSM_Benchmarking_Pack.xlsx"), engine="openpyxl") as xw:
    pd.DataFrame({"Platform Housing Group: Tenant Satisfaction Measures benchmarking, 2024/25": [
        "Sources: Regulator of Social Housing TSM full data 2023/24 and 2024/25 (OGL); Housing Ombudsman landlord performance reports 2025/26.",
        f"Peer groups: {len(large)} large housing associations (>40,000 homes) and {len(midl)} Midlands housing associations. Low-cost rental (LCRA) tenants.",
        "Quartile: position against large housing associations, adjusted so 'Top' always means better performance.",
        "Sheets: Benchmark | Satisfaction drivers | Survey method | Ombudsman peers | Ombudsman categories | Year-on-year checks"]}).to_excel(xw, sheet_name="Read me", index=False)
    bench.to_excel(xw, sheet_name="Benchmark", index=False)
    drivers.to_excel(xw, sheet_name="Satisfaction drivers", index=False)
    meth.to_excel(xw, sheet_name="Survey method", index=False)
    om_tab.to_excel(xw, sheet_name="Ombudsman peers", index=False)
    cat_tab.to_excel(xw, sheet_name="Ombudsman categories")
    yoy.to_excel(xw, sheet_name="Year-on-year checks", index=False)
    for ws in xw.book.worksheets:
        ws.freeze_panes = "A2"
        for col in ws.columns:
            w = max(len(str(c.value)) if c.value is not None else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(10, w + 2), 60)

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
b = bench.head(12).iloc[::-1]
fig, ax = plt.subplots(figsize=(8, 5.5))
ax.barh(b.Measure, b["Gap to large HA median"], color=np.where(b["Gap to large HA median"] >= 0, "#1f6f8b", "#c0392b"))
ax.axvline(0, color="grey"); ax.set_xlabel("Percentage points vs median large housing association")
ax.set_title("Platform tenant satisfaction vs large HA median, 2024/25"); fig.tight_layout()
fig.savefig(os.path.join(O, "chart1_tsm_gap_to_peers.png"), dpi=160); plt.close()
o = om.sort_values("mal_rate_2025_26")
fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(o.landlord.str.replace(" Limited", "").str.slice(0, 38), o.mal_rate_2025_26, color=np.where(o.landlord == PLATFORM, "#1f6f8b", "#b8c7d0"))
ax.set_xlabel("Maladministration rate, 2025/26 (%)"); ax.set_title("Housing Ombudsman findings upheld: Platform vs Midlands peers")
fig.tight_layout(); fig.savefig(os.path.join(O, "chart2_ombudsman_peers.png"), dpi=160); plt.close()
pd.set_option("display.width", 220)
print(pd.Series(K).to_string()); print(bench.to_string()); print(drivers.to_string()); print(meth.to_string()); print(cat_tab.to_string())
print(midl.landlord.tolist()[:40])
