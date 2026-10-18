-- Initial candidate screening: same supplier, same amount (£1,000+), within 3 days.
-- This broad rule can include legitimate recurring care-package amounts.
-- scripts/03_finance_pack.py adds the supplier-amount frequency condition:
-- exactly two occurrences across the dataset, then a gap of at most 3 days.
-- The refined Python output supplies the final 281-pair AP review list.
SELECT a.payment_id AS payment_a, b.payment_id AS payment_b, sp.supplier_name, r.directorate,
       a.date AS date_a, b.date AS date_b,
       CAST(julianday(b.date) - julianday(a.date) AS INTEGER) AS days_apart,
       a.amount, a.service_area
FROM fact_payment a
JOIN fact_payment b
  ON b.supplier_number = a.supplier_number AND b.amount = a.amount AND b.payment_id > a.payment_id
 AND julianday(b.date) - julianday(a.date) BETWEEN -3 AND 3
JOIN dim_supplier sp ON sp.supplier_number = a.supplier_number
JOIN dim_directorate r ON r.directorate_id = a.directorate_id
WHERE a.amount >= 1000 AND sp.is_individual = 0
ORDER BY a.amount DESC;
