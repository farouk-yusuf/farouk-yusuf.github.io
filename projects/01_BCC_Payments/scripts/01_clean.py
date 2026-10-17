"""
Birmingham City Council payments over £500 - step 1: clean and standardise.
Input : raw/payments-to-suppliers-over-gbp500.csv (City Observatory full export, Jul 2024 - Jul 2026)
Output: clean/payments_clean.csv  (personal-data rows pseudonymised)
        clean/directorate_mapping.csv
"""
import os, hashlib, re
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(BASE, "clean"), exist_ok=True)
df = pd.read_csv(os.path.join(BASE, "raw", "payments-to-suppliers-over-gbp500.csv"),
                 encoding="utf-8-sig", dtype={"supplier_number": str}, parse_dates=["date"])
n0, total0 = len(df), df.amount.sum()

# 1. Directorates were renamed in September 2025 and contain typos; map to one reporting name
dir_map = {
    "Adults Social Care Directorate": "Adult Social Care & Health",
    "Adult Social Care & Health Directorate": "Adult Social Care & Health",
    "Non-BCC N2 - Adults Social Care Dir": "Adult Social Care & Health",
    "City Ops Directorate": "City Operations",
    "Children and Families Directorate": "Children & Families",
    "City Housing Directorate": "City Housing",
    "Council Management": "Council Management",
    "Council Managament": "Council Management",
    "Finance": "Finance",
    "Finance Control- Monitoring": "Finance",
    "Finance Control- Other": "Finance",
    "Non-BCC N2 - Finance Control- Other": "Finance",
    "Places, Prosperity & Sustainability Directorate": "Place, Prosperity & Sustainability",
    "Place, Prosperity & Sustainability Directorate": "Place, Prosperity & Sustainability",
    "Strategy, Insight and Governance Deputy CE": "Strategy, Insight & Governance",
    "Strategy, Equalities & Partnerships": "Strategy, Insight & Governance",
    "HR, OD and Transformation": "HR, OD & Transformation",
    "Birmingham City Council Directorate Dir": "Council Management",
}
unmapped = set(df.department) - set(dir_map)
assert not unmapped, unmapped
pd.Series(dir_map, name="reporting_directorate").rename_axis("source_department").to_csv(os.path.join(BASE, "clean", "directorate_mapping.csv"))
df["directorate"] = df.department.map(dir_map)

# 2. Personal data: the council redacts individuals' names but still publishes their supplier numbers,
#    which link all payments to the same person. Replace with a one-way pseudonym and drop the name.
df["is_personal_data"] = df.beneficiary.str.upper().str.replace(r"[\s-]", "", regex=True).str.startswith("REDACTEDPERSONALDATA")
SALT = os.environ.get("PSEUDONYM_SALT", "set-your-own-secret")  # secret key kept outside the code, so pseudonyms cannot be reversed
def pseudo(x): return "IND-" + hashlib.sha256((SALT + x).encode()).hexdigest()[:10].upper()
df.loc[df.is_personal_data, "supplier_number"] = df.loc[df.is_personal_data, "supplier_number"].map(pseudo)
df.loc[df.is_personal_data, "beneficiary"] = "Individual (redacted)"

# 3. Supplier name standardisation: one display name per supplier number (most frequent spelling)
def norm(s):
    s = re.sub(r"[^a-z0-9 ]", " ", s.lower())
    s = re.sub(r"\b(ltd|limited|plc|llp|the|co|company|uk|bcc)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()
df["supplier_name_std"] = df.groupby("supplier_number").beneficiary.transform(lambda s: s.value_counts().index[0])
df["supplier_name_key"] = df.supplier_name_std.map(norm)

# 4. Spend categories: PO accrual lines are an accounting treatment, not a type of spend
df["spend_category"] = df.merchant_category.str.replace(r"\s+", " ", regex=True).str.strip()
df["is_po_accrual"] = df.spend_category.str.contains("Accrual", case=False)
df["is_agency_staff"] = df.spend_category.str.contains("Agency", case=False)

# 5. Dates and flags
df["month"] = df.date.dt.to_period("M").astype(str)
df["financial_year"] = df.date.apply(lambda d: f"{d.year}/{str(d.year+1)[2:]}" if d.month >= 4 else f"{d.year-1}/{str(d.year)[2:]}")
df["is_credit"] = df.amount < 0
df["is_large_500k"] = df.amount >= 500_000

assert len(df) == n0 and abs(df.amount.sum() - total0) < 0.01  # nothing lost or altered
df.drop(columns=["department", "merchant_category"]).to_csv(os.path.join(BASE, "clean", "payments_clean.csv"), index=False)
print(f"rows {n0:,}  total £{total0/1e6:,.1f}m  personal-data rows {df.is_personal_data.sum():,}  "
      f"suppliers {df.supplier_number.nunique():,}  directorates {df.directorate.nunique()}")
