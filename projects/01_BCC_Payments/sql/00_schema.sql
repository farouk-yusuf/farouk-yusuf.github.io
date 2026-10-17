-- Star schema for council payments. One row per published payment line in fact_payment.
DROP TABLE IF EXISTS fact_payment; DROP TABLE IF EXISTS dim_supplier;
DROP TABLE IF EXISTS dim_directorate; DROP TABLE IF EXISTS dim_category; DROP TABLE IF EXISTS dim_date;

CREATE TABLE dim_supplier (
  supplier_number   TEXT PRIMARY KEY,      -- pseudonymised (IND-...) where the payee is an individual
  supplier_name     TEXT NOT NULL,
  supplier_name_key TEXT NOT NULL,         -- normalised name used to spot duplicate supplier records
  is_individual     INTEGER NOT NULL
);
CREATE TABLE dim_directorate (directorate_id INTEGER PRIMARY KEY, directorate TEXT UNIQUE NOT NULL);
CREATE TABLE dim_category (
  category_id INTEGER PRIMARY KEY, spend_category TEXT UNIQUE NOT NULL,
  is_po_accrual INTEGER NOT NULL, is_agency_staff INTEGER NOT NULL
);
CREATE TABLE dim_date (date TEXT PRIMARY KEY, month TEXT NOT NULL, financial_year TEXT NOT NULL);
CREATE TABLE fact_payment (
  payment_id      INTEGER PRIMARY KEY,
  date            TEXT NOT NULL REFERENCES dim_date(date),
  supplier_number TEXT NOT NULL REFERENCES dim_supplier(supplier_number),
  directorate_id  INTEGER NOT NULL REFERENCES dim_directorate(directorate_id),
  category_id     INTEGER NOT NULL REFERENCES dim_category(category_id),
  service_area    TEXT,                    -- council 'summary' field (business unit)
  amount          REAL NOT NULL
);
CREATE INDEX ix_fact_supplier ON fact_payment(supplier_number, amount, date);
CREATE INDEX ix_fact_date ON fact_payment(date);
