-- Changes are descriptive within a retained extract, not causal policy effects.
WITH quarterly AS (
    SELECT quarter, SUM(reimbursement) AS reimbursement,
           COUNT(*) AS spend_eligible_records,
           SUM(prescriptions) AS prescriptions
    FROM utilization WHERE spend_eligible = 1 GROUP BY quarter
)
SELECT *, reimbursement / NULLIF(prescriptions, 0) AS reimbursement_per_prescription,
       reimbursement / LAG(reimbursement) OVER (ORDER BY quarter) - 1 AS quarter_change
FROM quarterly ORDER BY quarter;
