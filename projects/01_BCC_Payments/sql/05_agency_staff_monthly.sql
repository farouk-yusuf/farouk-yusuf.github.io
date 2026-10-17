-- Agency staff spend by month and directorate (a standing KPI for councils under spending controls)
SELECT d.month, r.directorate, ROUND(SUM(f.amount), 2) AS agency_spend
FROM fact_payment f
JOIN dim_date d ON d.date = f.date
JOIN dim_category c ON c.category_id = f.category_id
JOIN dim_directorate r ON r.directorate_id = f.directorate_id
WHERE c.is_agency_staff = 1
GROUP BY d.month, r.directorate ORDER BY d.month, agency_spend DESC;
