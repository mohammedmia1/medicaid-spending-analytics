-- Suppressed records remain counted; their missing reimbursement is not zero-filled.
SELECT state, MAX(region) AS region, COUNT(*) AS source_records,
       SUM(suppressed) AS suppressed_records,
       1.0 * SUM(suppressed) / COUNT(*) AS suppressed_record_share,
       SUM(spend_eligible) AS spend_eligible_records,
       COUNT(DISTINCT quarter) AS observed_quarters,
       COUNT(DISTINCT utilization_type) AS observed_utilization_types,
       COUNT(DISTINCT ndc11) AS observed_package_ndcs,
       SUM(CASE WHEN spend_eligible = 1 THEN reimbursement ELSE 0 END) AS reimbursement,
       SUM(CASE WHEN spend_eligible = 1 AND metadata_matched = 1 THEN reimbursement ELSE 0 END)
          / NULLIF(SUM(CASE WHEN spend_eligible = 1 THEN reimbursement ELSE 0 END), 0)
          AS metadata_matched_spend_share
FROM utilization
GROUP BY state ORDER BY reimbursement DESC;
