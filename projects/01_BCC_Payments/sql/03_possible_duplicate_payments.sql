-- Possible duplicate payments: same supplier, same amount (£1,000+), paid within 3 days of each other.
-- Recurring care-package amounts are excluded by requiring a gap of 0-3 days (weekly cycles are 7).
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
