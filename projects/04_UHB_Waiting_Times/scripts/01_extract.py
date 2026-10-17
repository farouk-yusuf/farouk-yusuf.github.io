"""
UHB waiting times - step 1: extract provider-level RTT data from NHS England monthly full CSV extracts.
Keeps University Hospitals Birmingham (RRK), six large Midlands acute trusts for benchmarking, and an England total.
Commissioner rows are summed to provider level. Weekly wait bands are reduced to the bands used in reporting.
Usage: python3 scripts/01_extract.py [zip ...]   (no args = all zips not yet extracted)
Output: clean/monthly/<period>.csv, combined later by 02_build.py
"""
import os, sys, glob, zipfile, re
import pandas as pd, numpy as np
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# v2 adds known-clock-start totals (Part_2 rows leave "Total" blank)
OUT = os.path.join(BASE, "clean", "monthly_v2"); os.makedirs(OUT, exist_ok=True)
PROVIDERS = {"RRK": "University Hospitals Birmingham", "RXK": "Sandwell & West Birmingham", "RKB": "UH Coventry & Warwickshire",
             "RX1": "Nottingham University Hospitals", "RWE": "University Hospitals of Leicester", "RL4": "Royal Wolverhampton",
             "RJE": "UH North Midlands"}
zips = sys.argv[1:] or sorted(glob.glob(os.path.join(BASE, "raw", "Full-CSV-data-file-*.zip")))
for z in zips:
    with zipfile.ZipFile(z) as zf:
        name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        out = os.path.join(OUT, name.split("-RTT-")[0] + ".csv")
        if os.path.exists(out): continue
        week_cols = None; parts = []
        for ch in pd.read_csv(zf.open(name), chunksize=200_000, low_memory=False):
            if week_cols is None:
                week_cols = [c for c in ch.columns if c.startswith("Gt ")]
            wk = ch[week_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
            # band boundaries by the lower edge of each weekly column (Gt 18 To 19 = waiting 18+ weeks)
            lower = np.array([int(re.findall(r"\d+", c)[0]) for c in week_cols])
            agg = pd.DataFrame({
                "period": ch["Period"], "provider": ch["Provider Org Code"], "part": ch["RTT Part Type"],
                "specialty": ch["Treatment Function Name"],
                "total": pd.to_numeric(ch["Total"], errors="coerce").fillna(0),
                "known_clock_start": wk.sum(axis=1),
                "unknown_clock_start": pd.to_numeric(ch["Patients with unknown clock start date"], errors="coerce").fillna(0),
                "total_all": pd.to_numeric(ch["Total All"], errors="coerce").fillna(0),
                "within_18": wk.loc[:, lower < 18].sum(axis=1),
                "over_52": wk.loc[:, lower >= 52].sum(axis=1),
                "over_65": wk.loc[:, lower >= 65].sum(axis=1),
                "over_78": wk.loc[:, lower >= 78].sum(axis=1),
                "over_104": wk.loc[:, lower >= 104].sum(axis=1)})
            nat = agg.assign(provider="ENGLAND").groupby(["period", "provider", "part", "specialty"], as_index=False).sum(numeric_only=True)
            keep = agg[agg.provider.isin(PROVIDERS)].groupby(["period", "provider", "part", "specialty"], as_index=False).sum(numeric_only=True)
            parts += [nat, keep]
        res = pd.concat(parts).groupby(["period", "provider", "part", "specialty"], as_index=False).sum(numeric_only=True)
        res.to_csv(out, index=False); print(os.path.basename(z), "->", os.path.basename(out), len(res))
