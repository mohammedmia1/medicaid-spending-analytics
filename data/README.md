# The data

I use a 2024 Medicaid utilization extract and an FDA product directory extract. The files are included as compressed CSVs, so the project runs without credentials or a database server.

I need both sources to move through the project's five questions. Utilization supplies the dollars for product, jurisdiction, and quarterly rankings. The directory supplies pharmacologic tags for class context and the ingredient, strength, form, and route needed for matched price review. I keep missing descriptions visible so that incomplete classification does not remove reported spending.

| File | Contents | Records |
|---|---|---:|
| `raw/utilization.csv.gz` | Jurisdiction, reporting period, package NDC, suppression flags, units, prescriptions, and reimbursement | 1,048,575 |
| `raw/product_directory.csv.gz` | Product NDCs, names, ingredients, forms, routes, strengths, application categories, and listing dates | 113,878 |
| `raw/extraction_manifest.json` | Worksheet names, export counts, and source-row information | Two source exports |

## Coverage

The utilization extract covers 2024 reporting in AK, AL, AR, AZ, CA, CO, CT, DC, DE, FL, GA, and HI. It reaches the worksheet's 1,048,576-row capacity including the header. Complete national or within-jurisdiction coverage is not established.

Of the utilization observations, 504,630 contain reported reimbursement totaling $27.54B. Another 543,945 have suppressed amounts. I leave those amounts missing rather than impute them.

The product directory includes marketing dates through November 2025; its download date is not documented. I use quarter-overlap checks for price comparisons, while treating the directory as a supplied snapshot rather than historical point-in-time data.

## Key fields

| Analysis field | Meaning | Handling |
|---|---|---|
| `source_row` | Row in the source worksheet | Traceability within the source file |
| `utilization_type` | Managed-care or fee-for-service reporting | Part of the observation key |
| `state` | Jurisdiction abbreviation | Includes Washington, DC |
| `ndc11` | Package-level NDC | An 11-character string |
| `product_key` | Labeler/product code | Nine characters; combines package sizes |
| `year`, `quarter` | Reporting period | Year 2024, quarters 1-4 |
| `suppressed` | Whether reported values are suppressed | Missing dollars remain unknown |
| `units`, `prescriptions` | Reported utilization measures | Aggregate reporting values |
| `reimbursement` | Medicaid amount reimbursed | Before manufacturer rebates |
| `cost_per_unit` | Reimbursement divided by positive units | Calculated without row-level rounding |
| `application_type` | Product directory marketing category | Not a definitive brand/generic label |
| `ingredient`, `dosage_form`, `route` | Recorded product descriptors | Salt and release distinctions remain intact |
| `strength`, `strength_unit` | Recorded potency descriptors | Separate from reimbursement unit type |
| `marketing_start`, `marketing_end` | Recorded listing dates | Used to check quarter overlap |
| `pharm_classes` | Recorded pharmacologic descriptors | Distinct EPC tags can overlap across products and must not be added as budget shares |
| `spend_eligible`, `price_eligible` | Calculation eligibility | Spending and price comparisons have distinct requirements |
| `metadata_matched` | Product information was attached without conflict | Unmatched dollars remain in spending totals |

## Using the files

Load NDC columns explicitly as strings. For example:

```python
import pandas as pd

utilization = pd.read_csv("data/raw/utilization.csv.gz", dtype={"NDC": "string"})
products = pd.read_csv("data/raw/product_directory.csv.gz", dtype="string")
```

The CSV files contain stored worksheet values, including blanks and source error markers. The optional extraction command reads cached formula values; it does not recalculate a workbook. `source_row` refers to the worksheet rather than a CMS patient identifier.

The pipeline creates `processed/analytics.sqlite`, which is excluded from Git. I organize finished tables and figures by question in the [results guide](../reports/README.md). Calculation counts and input checksums are in `reports/analysis_summary.json`.

## Sources

- [CMS 2024 State Drug Utilization Data](https://data.medicaid.gov/dataset/61729e5a-7aa8-448c-8903-ba3e0cd0ea3c): upstream utilization source; the included extract is the fixed dataset used here, rather than a fresh national download.
- [FDA NDC Directory](https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory): upstream product listing source.
- [CMS SDUD definitions](https://www.medicaid.gov/medicaid/prescription-drugs/state-drug-utilization-data/state-drug-utilization-data-faq): suppression, reimbursement, and reporting units.

The workbook export locations are recorded in `raw/extraction_manifest.json`. To export the two worksheets again, run `python -m medicaid_analytics.extract --source-dir /path/to/workbooks` from the repository root.
