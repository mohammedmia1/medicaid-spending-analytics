-- One row per product-level NDC, combining package sizes and observed jurisdictions.
-- The denominator includes unmatched metadata; it is never a national total.
WITH product_totals AS (
    SELECT product_key,
           COALESCE(MAX(product_name), MAX(source_product_name)) AS product_name,
           MAX(ingredient) AS ingredient,
           SUM(reimbursement) AS reimbursement,
           COUNT(*) AS records,
           COUNT(DISTINCT state) AS jurisdictions
    FROM utilization
    WHERE spend_eligible = 1
    GROUP BY product_key
), ranked AS (
    SELECT *, ROW_NUMBER() OVER (ORDER BY reimbursement DESC, product_key) AS spend_rank,
           reimbursement / SUM(reimbursement) OVER () AS spend_share,
           SUM(reimbursement) OVER (ORDER BY reimbursement DESC, product_key
               ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
               / SUM(reimbursement) OVER () AS cumulative_share
    FROM product_totals
)
SELECT * FROM ranked ORDER BY spend_rank;
