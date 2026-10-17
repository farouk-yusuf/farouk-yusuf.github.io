"""
Severn Trent storm overflows - step 1: build clean, combined data.
Inputs : raw/ (Environment Agency EDM annual returns 2020-2025, Met Office Midlands & England rainfall)
Outputs: clean/st_overflows_2020_2025.csv   one row per Severn Trent overflow per year
         clean/company_summary_2020_2025.csv one row per water company per year (from EA summary tables)
         clean/rainfall_annual.csv          Midlands and England annual rainfall (mm)
Run from the project folder:  python3 scripts/01_build_clean_data.py
"""
import glob, os, zipfile, datetime as dt, re
import pandas as pd, numpy as np, openpyxl

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW, WORK, CLEAN = (os.path.join(BASE, d) for d in ("raw", "work", "clean"))
os.makedirs(WORK, exist_ok=True); os.makedirs(CLEAN, exist_ok=True)

# 0. unzip archives into work/ (raw stays untouched)
for z in glob.glob(os.path.join(RAW, "*.zip")):
    out = os.path.join(WORK, os.path.splitext(os.path.basename(z))[0])
    if not os.path.isdir(out):
        zipfile.ZipFile(z).extractall(out)

def find(pattern):
    hits = glob.glob(os.path.join(WORK, "**", pattern), recursive=True)
    assert len(hits) == 1, (pattern, hits)
    return hits[0]

def to_hours(v):
    """Duration arrives as float hours (2020-23), timedelta (2024-25) or time-of-day (<24h, 2025)."""
    if v is None or (isinstance(v, str) and v.strip() == ""): return np.nan
    if isinstance(v, dt.timedelta): return v.total_seconds() / 3600
    if isinstance(v, dt.time): return v.hour + v.minute / 60 + v.second / 3600
    if isinstance(v, dt.datetime):  # Excel serial >= 1 day stored as date from 1899-12-30/31
        return (v - dt.datetime(1899, 12, 30)).total_seconds() / 3600
    if isinstance(v, str):
        m = re.match(r"^\s*(\d+):(\d{2}):(\d{2})\s*$", v)
        if m: return int(m[1]) + int(m[2]) / 60 + int(m[3]) / 3600
        try: return float(v)
        except ValueError: return np.nan
    return float(v)

def to_num(v):
    if v is None: return np.nan
    if isinstance(v, (int, float)): return float(v)
    try: return float(str(v).replace("%", "").strip())
    except ValueError: return np.nan

def read_sheet(path, sheet, header_row):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[sheet]
    rows = list(ws.iter_rows(values_only=True))
    hdr, seen = [], {}
    for i, h in enumerate(rows[header_row]):
        name = str(h).split("\n")[0].strip() if h is not None else f"col{i}"
        if name in seen:  # e.g. two 'Site Name' columns (EA vs company name): keep first as-is
            seen[name] += 1; name = f"{name}__{seen[name]}"
        else:
            seen[name] = 0
        hdr.append(name)
    df = pd.DataFrame(rows[header_row + 1:], columns=hdr)
    return df.dropna(how="all")

frames = []
# 2020: separate Severn Trent file, header in first row
p = find("*Severn_Trent_Water_Annual_2020.xlsx")
d = read_sheet(p, openpyxl.load_workbook(p, read_only=True).sheetnames[0], 0)
frames.append(pd.DataFrame({
    "year": 2020, "unique_id": None, "old_id": None,
    "site_name": d["Site Name"].astype(str).str.strip(), "permit": d["Permit No."],
    "activity_ref": d["Activity Reference (if more than one discharge) on permit"],
    "asset_type": None, "receiving_water": None, "wfd_waterbody_id": None, "wfd_catchment": None,
    "duration_hrs_raw": d.iloc[:, 6], "spills_raw": d.iloc[:, 7], "edm_op_raw": d.iloc[:, 8],
    "edm_op_scale": 100.0}))  # stored as fraction -> x100

for yr, hdr_row, sheet, op_scale in [(2021, 1, "Severn Trent 2021", 100.0), (2022, 1, "Severn Trent 2022", 100.0),
                                     (2023, 1, "Severn Trent 2023", 1.0), (2024, 1, "Severn Trent 2024", 1.0),
                                     (2025, 5, "Severn Trent Water", 1.0)]:
    p = find(f"EDM {yr} Storm Overflow Annual Return - all water and sewerage companies.xlsx")
    d = read_sheet(p, sheet, hdr_row)
    d = d[d["Water Company Name"].astype(str).str.contains("Severn", na=False)]
    dur_col = [c for c in d.columns if c.startswith("Total Duration")][0]
    old = [c for c in d.columns if c.startswith("Old format Unique ID")]
    frames.append(pd.DataFrame({
        "year": yr, "unique_id": d["Unique ID"] if "Unique ID" in d else None,
        "old_id": d[old[0]] if old else None,
        "site_name": d["Site Name"].astype(str).str.strip(), "permit": d["EA Permit Reference"],
        "activity_ref": d["Activity Reference on Permit"] if "Activity Reference on Permit" in d else d.iloc[:, 5],
        "asset_type": d["Storm Discharge Asset Type"],
        "receiving_water": d["Receiving Water / Environment (common name)"],
        "wfd_waterbody_id": d[[c for c in d.columns if c.startswith("WFD Waterbody ID")][0]],
        "wfd_catchment": d[[c for c in d.columns if c.startswith("WFD Waterbody Catchment Name")][0]],
        "duration_hrs_raw": d[dur_col], "spills_raw": d["Counted spills using 12-24h count method"],
        "edm_op_raw": d["EDM Operation -"] if "EDM Operation -" in d else d["EDM Operation - % of reporting period EDM operational"],
        "edm_op_scale": op_scale,
        "low_op_reason": d[[c for c in d.columns if "Primary Reason <90%" in c or c.startswith("EDM Operation -__1")][0]] if any(("Primary Reason <90%" in c) or c.startswith("EDM Operation -__1") for c in d.columns) else None,
        "high_spill_reason": d[[c for c in d.columns if c.startswith("High Spill Frequency")][0]] if any(c.startswith("High Spill Frequency") for c in d.columns) else None,
        "investigation_activity": d["Investigation activity for the reporting period"] if "Investigation activity for the reporting period" in d else None,
        "improvement_activity": d["Improvement activity for the reporting period"] if "Improvement activity for the reporting period" in d else None}))

st = pd.concat(frames, ignore_index=True)
st["duration_hrs"] = st["duration_hrs_raw"].map(to_hours)
st["spills"] = st["spills_raw"].map(to_num)
st["edm_op_pct"] = st["edm_op_raw"].map(to_num) * st["edm_op_scale"]
# data-quality flags
st["dq_no_spill_data"] = st["spills"].isna()
st["dq_low_edm_op"] = st["edm_op_pct"] < 90
st["dq_op_over_100"] = st["edm_op_pct"] > 100.5
st["dq_spills_but_zero_hrs"] = (st["spills"] > 0) & (st["duration_hrs"] == 0)
for col in ["site_name", "receiving_water"]:  # source has '¿' where an apostrophe was lost in encoding
    st[col] = st[col].astype(str).str.replace("\u00bf", "'", regex=False).replace("None", pd.NA)
st = st.drop(columns=["duration_hrs_raw", "spills_raw", "edm_op_raw", "edm_op_scale"])
st.to_csv(os.path.join(CLEAN, "st_overflows_2020_2025.csv"), index=False)

# Company summary from EA long-term trends workbook (already validated by EA)
p = find("EDM Storm Overflow Annual Return - Long-term Trends 2016-2025.xlsx")
wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
rows = []
labels = {  # (year-sheet label fragment -> field)
    "with spill data": "overflows_with_spill_data",
    "monitored spill events": "total_spills", "number of spill events": "total_spills",
    "Total duration": "total_duration_hrs", "Duration (hrs) of Spill events": "total_duration_hrs",
    "<90% EDM Operation": "share_edm_op_below_90", "percentage return <90": "share_edm_op_below_90",
    "Overflows with numeric data": "overflows_with_spill_data",
}
companies = ["Anglian", "Dwr Cymru", "Northumbrian", "Severn Trent", "South West", "Southern", "Thames", "United Utilities", "Wessex", "Yorkshire"]
for yr in range(2020, 2026):
    ws = wb[f"{yr} Summary Data"]
    seen = set()
    for r in ws.iter_rows(values_only=True):
        r = [c for c in r]
        while r and r[0] is None: r = r[1:]          # labels sit in column B in later sheets
        if not r or not isinstance(r[0], str): continue
        lab = r[0]
        for frag, field in labels.items():
            if frag.lower() in lab.lower() and field not in seen and not lab.lower().startswith("table") and "average" not in lab.lower():
                vals = [v for v in r[1:11]]
                if all(isinstance(v, (int, float)) for v in vals):
                    seen.add(field)
                    for c, v in zip(companies, vals):
                        rows.append({"year": yr, "company": c, "field": field, "value": v})
comp = pd.DataFrame(rows).pivot_table(index=["year", "company"], columns="field", values="value").reset_index()
comp["avg_spills_per_overflow"] = comp["total_spills"] / comp["overflows_with_spill_data"]
comp.to_csv(os.path.join(CLEAN, "company_summary_2020_2025.csv"), index=False)

# Rainfall
def read_rain(fn, region):
    lines = open(os.path.join(RAW, fn)).read().splitlines()
    start = [i for i, l in enumerate(lines) if l.startswith("year")][0]
    df = pd.read_csv(os.path.join(RAW, fn), sep=r"\s+", skiprows=start, na_values=["---"])
    df["region"] = region
    return df
rain = pd.concat([read_rain("Midlands.txt", "Midlands"), read_rain("England.txt", "England")])
rain.to_csv(os.path.join(CLEAN, "rainfall_monthly_annual.csv"), index=False)

print(st.groupby("year").agg(rows=("site_name", "size"), spills=("spills", "sum"), hrs=("duration_hrs", "sum"),
      no_data=("dq_no_spill_data", "sum"), low_op=("dq_low_edm_op", "sum"), op_over100=("dq_op_over_100", "sum"),
      zero_hrs=("dq_spills_but_zero_hrs", "sum")))
print(comp[comp.company == "Severn Trent"])
print(rain[rain.year >= 2015][["region", "year", "ann"]].pivot(index="year", columns="region", values="ann"))
