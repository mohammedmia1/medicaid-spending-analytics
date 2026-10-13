-- Directory marketing category is an application category, not a brand/generic flag.
SELECT COALESCE(application_type, 'Unmatched') AS application_type,
       SUM(reimbursement) AS reimbursement, COUNT(*) AS records,
       SUM(reimbursement) / (SELECT SUM(reimbursement) FROM utilization WHERE spend_eligible = 1)
           AS spend_share
FROM utilization WHERE spend_eligible = 1
GROUP BY COALESCE(application_type, 'Unmatched') ORDER BY reimbursement DESC;
