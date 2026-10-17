-- Supplier master check: the same organisation held under more than one supplier number
SELECT supplier_name_key, COUNT(DISTINCT supplier_number) AS supplier_numbers,
       GROUP_CONCAT(DISTINCT supplier_name) AS names_used,
       GROUP_CONCAT(DISTINCT supplier_number) AS numbers
FROM dim_supplier
WHERE is_individual = 0 AND supplier_name_key <> ''
GROUP BY supplier_name_key
HAVING COUNT(DISTINCT supplier_number) > 1
ORDER BY supplier_numbers DESC;
