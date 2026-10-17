-- Monthly spend by directorate (credits netted off)
SELECT d.month, r.directorate, ROUND(SUM(f.amount), 2) AS spend, COUNT(*) AS payments
FROM fact_payment f
JOIN dim_date d ON d.date = f.date
JOIN dim_directorate r ON r.directorate_id = f.directorate_id
GROUP BY d.month, r.directorate
ORDER BY d.month, spend DESC;
