"""Step 2: load the clean data into a SQLite star schema and run the SQL in sql/, saving results to outputs/sql_results/."""
import os, glob, sqlite3, shutil, tempfile
import pandas as pd
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
df = pd.read_csv(os.path.join(BASE, "clean", "payments_clean.csv"), dtype={"supplier_number": str})
db = os.path.join(BASE, "clean", "bcc_payments.sqlite")
work_db = os.path.join(tempfile.gettempdir(), "bcc_payments.sqlite")  # build locally: SQLite locking fails on synced/network folders
if os.path.exists(work_db): os.remove(work_db)
con = sqlite3.connect(work_db)
con.executescript(open(os.path.join(BASE, "sql", "00_schema.sql")).read())
sup = df.groupby("supplier_number").agg(supplier_name=("supplier_name_std", "first"), supplier_name_key=("supplier_name_key", "first"),
                                        is_individual=("is_personal_data", "max")).reset_index()
sup.to_sql("dim_supplier", con, if_exists="append", index=False)
dirs = pd.DataFrame({"directorate": sorted(df.directorate.unique())}); dirs["directorate_id"] = range(1, len(dirs) + 1)
dirs.to_sql("dim_directorate", con, if_exists="append", index=False)
cats = df.groupby("spend_category").agg(is_po_accrual=("is_po_accrual", "max"), is_agency_staff=("is_agency_staff", "max")).reset_index()
cats["category_id"] = range(1, len(cats) + 1); cats.to_sql("dim_category", con, if_exists="append", index=False)
df[["date", "month", "financial_year"]].drop_duplicates().to_sql("dim_date", con, if_exists="append", index=False)
fact = df.merge(dirs, on="directorate").merge(cats[["spend_category", "category_id"]], on="spend_category")
fact = fact.rename(columns={"summary": "service_area"})[["date", "supplier_number", "directorate_id", "category_id", "service_area", "amount"]]
fact.to_sql("fact_payment", con, if_exists="append", index=False)
# integrity checks
chk = con.execute("SELECT COUNT(*), ROUND(SUM(amount),2) FROM fact_payment").fetchone()
assert chk[0] == len(df) and abs(chk[1] - df.amount.sum()) < 1, chk
orph = con.execute("SELECT COUNT(*) FROM fact_payment f LEFT JOIN dim_supplier s USING(supplier_number) WHERE s.supplier_number IS NULL").fetchone()[0]
assert orph == 0
out = os.path.join(BASE, "outputs", "sql_results"); os.makedirs(out, exist_ok=True)
for q in sorted(glob.glob(os.path.join(BASE, "sql", "0[1-9]_*.sql"))):
    res = pd.read_sql(open(q).read(), con)
    res.to_csv(os.path.join(out, os.path.basename(q).replace(".sql", ".csv")), index=False)
    print(os.path.basename(q), len(res), "rows")
con.close()
shutil.copyfile(work_db, db)
print("database:", db, f"{chk[0]:,} payments")
