# Data guide

## What is included

The compressed CSVs are cached-value exports of the supplied Excel worksheets. They are **not a newly downloaded CMS national release**. They preserve source strings, numeric cell values, Excel errors and blank values; formulas are represented by their stored outputs, not recalculated.

| File | Worksheet | Role |
|---|---|---|
| `raw/utilization_original.csv.gz` | STATE (OG) | Independent source reconciliation |
| `raw/utilization_cleaned_legacy.csv.gz` | STATE (cleaned ndc) | Main fact source; preserves explicit 11-character NDC strings |
| `raw/ndc_directory.csv.gz` | NDC Directory (OG) | Product descriptors, strengths, routes and application categories |
| `raw/ndc_labels_legacy.csv.gz` | NDC Directory (FINAL) | Preserved legacy classification evidence; not used as an authoritative taxonomy |
| `raw/analysis_legacy.csv.gz` | INNER JOIN MASTER (No Nulls) | Reproduction of the original Q3 calculations |
| `raw/extraction_manifest.json` | All five exports | Counts, row positions, error counts and Excel-limit flags |

Sources: supplied 2024 State Drug Utilization workbook and FDA NDC Directory workbook. The original upstream utilization dataset is [CMS 2024 SDUD](https://data.medicaid.gov/dataset/61729e5a-7aa8-448c-8903-ba3e0cd0ea3c). The supplied directory has marketing dates through November 2025; its acquisition date is not documented. No live external source is silently substituted.

## Main analysis fields

| Field | Type / meaning | Handling |
|---|---|---|
| `source_row` | Original worksheet row | Traceability, not a patient identifier |
| `utilization_type` | MCOU or FFSU | Preserved in observation grain and price strata |
| `state` | Jurisdiction abbreviation | Includes Washington, DC |
| `ndc11` | 11-character package code | Load as a string to preserve leading zeros |
| `product_key` | 9-character labeler/product key | Combines package sizes |
| `year`, `quarter` | Reporting period | 2024; quarters 1-4 |
| `suppressed` | CMS suppression flag | Missing amounts remain unknown |
| `units` | Reported units reimbursed | Physical unit type is unavailable in this snapshot |
| `prescriptions` | Reported prescription count | Aggregate reporting measure |
| `reimbursement` | Medicaid amount reimbursed | Before rebates; not a net cost |
| `cost_per_unit` | Reimbursement divided by positive units | Computed without row-level rounding |
| `region` | Census-style geography | Midwest is included in the mapping but not the extract |
| `application_type` | Directory marketing category | Does not guarantee brand/generic identity |
| `ingredient`, `dosage_form`, `route` | Recorded formulation descriptors | Preserve salts and release markers |
| `strength`, `strength_unit` | Recorded potency descriptors | Not equivalent to the reimbursement unit type |
| `marketing_start`, `marketing_end` | Recorded listing dates | Temporal overlap check, not historical snapshot proof |
| `spend_eligible`, `price_eligible` | Validation flags | Separate spending from price-screening eligibility |
| `metadata_matched` | Unambiguous enrichment status | Unmatched dollars stay in spending totals |

## Generated outputs

`processed/analytics.sqlite` contains the regenerated `utilization` table and is excluded from Git. `reports/tables/` contains additive spending tables, overlapping EPC tags, conflict listings, legacy reproduction and gap-screening detail. `reports/audit.json` records counts, checksums and reconciliation evidence.

The source CSVs are gzip-compressed to keep each GitHub file below its ordinary per-file size limit. Read NDC fields explicitly as strings in pandas or spreadsheet import tools. Do not open a CSV by double-clicking in Excel and assume the leading zeros will remain intact.
