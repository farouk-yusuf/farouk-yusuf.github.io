"""
Platform Housing - step 1: extract Housing Ombudsman 2025-26 landlord report figures from PDF into a table.
Input : raw/landlord_reports/HO_Landlord_Report_2025-26_*.pdf (21 landlords)
Output: clean/ombudsman_2025_26.csv, clean/ombudsman_findings_by_category.csv
"""
import os, re, glob, subprocess
import pandas as pd
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(BASE, "clean"), exist_ok=True)
num = lambda s: float(s.replace(",", "").replace("£", "").replace("%", ""))
rows, cats = [], []
CAT_NAMES = ["Managing Relations", "Responsive repairs/activity", "ASB/Abuse/Nuisance", "Moving/Buying/Selling Home", "Financial",
             "Planned works", "Estate Management", "Occupancy Rights", "Health and Safety (inc. building safety)",
             "Information and Data Management", "Complaints Handling", "Leasehold Management", "Staff", "Charges",
             "Allocations / Lettings", "Compensation"]
for f in sorted(glob.glob(os.path.join(BASE, "raw", "landlord_reports", "HO_Landlord_Report_2025-26_*.pdf"))):
    if "Guidance" in f: continue
    t = subprocess.run(["pdftotext", "-layout", f, "-"], capture_output=True, text=True).stdout
    lines = [l for l in t.splitlines() if l.strip()]
    rec = {"file": os.path.basename(f)}
    m = re.search(r"Landlord:\s*(.+?)\s{2,}", t + "  "); rec["landlord"] = m.group(1).strip() if m else None
    m = re.search(r"Landlord Homes:\s*([\d,]+)\s+Landlord Type:\s*(.+)", t)
    rec["homes"], rec["landlord_type"] = (num(m.group(1)), m.group(2).strip()) if m else (None, None)
    i = next(k for k, l in enumerate(lines) if "Determinations" in l and "Orders Made" in l)
    d = re.findall(r"[\d,]+", lines[i + 1]); rec.update(determinations=num(d[0]), findings=num(d[1]), mal_findings=num(d[2]), orders=num(d[3]))
    i = next(k for k, l in enumerate(lines) if l.strip().startswith("Recommendations"))
    j = next(k for k in range(i + 1, i + 5) if "%" in lines[k])   # values line sits below the 'Rate' label
    vals = re.findall(r"£[\d,]+|\d+%|\b\d[\d,]*\b", lines[j])
    rec.update(recommendations=num(vals[0]), chfos=num(vals[1]), compensation=num(vals[2]), mal_rate_2025_26=num(vals[3]))
    i = next(k for k, l in enumerate(lines) if "PERFORMANCE 2023-2024" in l)
    j = next(k for k in range(i + 1, i + 6) if re.search(r"\d+%", lines[k]))
    p = re.findall(r"\d+%?", lines[j])
    if len(p) >= 4: rec.update(determinations_2023_24=num(p[0]), mal_rate_2023_24=num(p[1]), determinations_2024_25=num(p[2]), mal_rate_2024_25=num(p[3]))
    m = re.search(r"Received Cases:\s*([\d,]+)\s+Duly Made Cases:\s*([\d,]+)", t)
    if m: rec.update(cases_received=num(m.group(1)), cases_duly_made=num(m.group(2)))
    rows.append(rec)
    # findings by category (Table 2.3)
    s = t.find("Landlord Findings by Category"); e = t.find("Findings by Category Comparison", s)
    block = t[s:e]
    for l in block.splitlines():
        m = re.match(r"\s*(.*?)\s{2,}((?:\d+\s+){8}\d+)\s*$", l)
        if not m: continue
        label = " ".join(m.group(1).split())
        if not label or label.startswith("Total"): continue
        full = next((c for c in CAT_NAMES if c.startswith(label) or label.startswith(c)), label)  # labels wrap onto two lines in the PDF
        v = [int(x) for x in m.group(2).split()]
        cats.append({"landlord": rec["landlord"], "category": full, "severe_mal": v[0], "mal": v[1],
                     "service_failure": v[2], "mediation": v[3], "redress": v[4], "no_mal": v[5], "outside_jurisdiction": v[6],
                     "withdrawn": v[7], "total": v[8]})
om = pd.DataFrame(rows)
om["determinations_per_10k_homes"] = (om.determinations / om.homes * 10000).round(2)
om["mal_findings_per_10k_homes"] = (om.mal_findings / om.homes * 10000).round(2)
om.to_csv(os.path.join(BASE, "clean", "ombudsman_2025_26.csv"), index=False)
cat = pd.DataFrame(cats); cat.to_csv(os.path.join(BASE, "clean", "ombudsman_findings_by_category.csv"), index=False)
# check: category totals reconcile with headline findings
chk = cat.groupby("landlord").total.sum().reindex(om.landlord).values - om.findings.values
print(om[["landlord", "homes", "determinations", "findings", "mal_findings", "mal_rate_2025_26", "mal_rate_2024_25", "mal_rate_2023_24", "compensation"]].to_string())
print("category reconciliation differences:", list(chk))
