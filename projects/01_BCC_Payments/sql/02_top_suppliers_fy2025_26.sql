-- Top 25 suppliers in FY2025/26 with share of total and running (cumulative) share
WITH s AS (
  SELECT sp.supplier_name, SUM(f.amount) AS spend
  FROM fact_payment f
  JOIN dim_date d ON d.date = f.date
  JOIN dim_supplier sp ON sp.supplier_number = f.supplier_number
  WHERE d.financial_year = '2025/26'
  GROUP BY sp.supplier_name
), t AS (SELECT SUM(spend) AS total FROM s)
SELECT supplier_name, ROUND(spend, 2) AS spend,
       ROUND(100.0 * spend / total, 2) AS pct_of_total,
       ROUND(100.0 * SUM(spend) OVER (ORDER BY spend DESC) / total, 2) AS cumulative_pct,
       RANK() OVER (ORDER BY spend DESC) AS rank
FROM s, t ORDER BY spend DESC LIMIT 25;
