# Medicaid Prescription Spending (Python + SQL)

[![Validate analytics](https://github.com/mohammedmia1/medicaid-spending-analytics/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/mohammedmia1/medicaid-spending-analytics/actions/workflows/validate.yml)

**[Read the analysis notebook →](notebooks/Medicaid_Spending_Analysis.ipynb)** · **[View the executive brief →](reports/EXECUTIVE_BRIEF.pdf)**

[![Medicaid prescription spending overview](reports/figures/portfolio_overview.png)](notebooks/Medicaid_Spending_Analysis.ipynb)

I built this project to understand where Medicaid prescription spending goes and which products deserve a closer price review. I used Python to prepare utilization records and drug information, then SQL to analyze spending by product, jurisdiction, quarter, and application category.

The analysis covers 2024 data for **11 states and Washington, DC**. It includes **$27.54 billion in reported Medicaid reimbursement**, before manufacturer rebates.

## What I found

| Finding | Result |
|---|---:|
| Share of spending accounted for by the top 50 product NDCs | **37.1%** |
| Highest-spending product NDC: Biktarvy | **$907.89M** |
| California's share of spending in this dataset | **56.5%** |
| Recorded formulations with matched NDA/ANDA price comparisons | **562** |

The top 50 product NDCs give an analyst a focused starting point for spending reviews. A product NDC combines package sizes but does not combine every strength sold under the same brand name.

![Top prescription products by reimbursement](reports/figures/top_products.png)

## How I approached it

I organized the analysis around three questions:

1. **Which products account for the most spending?** I grouped reimbursement by product NDC, ranked the results, and calculated cumulative spending shares.
2. **How does spending vary across jurisdictions and quarters?** I compared reported totals alongside record coverage and suppression. These are descriptive comparisons, without enrollment or drug-mix adjustments.
3. **Where do comparable products have different reimbursement per unit?** I matched recorded ingredient, strength, dosage form, and route within the same jurisdiction, quarter, and utilization type. I calculated each price as total reimbursement divided by total units.

The [notebook](notebooks/Medicaid_Spending_Analysis.ipynb) walks through the questions, code, results, and interpretation. The [methodology notes](docs/METHODOLOGY.md) explain the matching rules and calculations.

## Stack

Python, pandas, SQLite, SQL, matplotlib, and GitHub Actions. The data starts as compressed CSV files, becomes a product-enriched utilization table, and feeds four SQL analyses plus the product price comparison.

## The data

| Source | One row per | Records |
|---|---|---:|
| Medicaid utilization extract | Utilization type, jurisdiction, package NDC, year, quarter | 1,048,575 |
| FDA product directory extract | Product listing | 113,878 |

Of the utilization records, **504,630 contain reported reimbursement**. The other **543,945 have suppressed amounts**, which I leave missing. Product information matches **99.42% of reported dollars**; unmatched spending stays in the overall totals.

See the [data guide](data/README.md) for source links, fields, and file descriptions.

## Running it

Requires Python 3.11 or newer. The source files are included; no credentials or database server are needed.

```bash
pip install -r requirements.txt
pip install -e . --no-deps

# Generate the database, analysis tables, and figures.
python -m medicaid_analytics.pipeline

# Run the tests and check the output totals.
python -m unittest discover -s tests -v
python -m medicaid_analytics.verify

# Execute the notebook and save its outputs.
python scripts/build_notebook.py
```

The pipeline writes a local SQLite database, the [result tables](reports/tables/), five figures, and a machine-readable [analysis summary](reports/analysis_summary.json). It also runs automatically through GitHub Actions. Allow about 500 MB of free disk space and at least 2 GB of available memory.

## A few notes

- The dataset covers 11 states and DC, rather than the whole country. Suppressed amounts are unknown, and completeness within each jurisdiction is not certified.
- The price comparison produces a **$516.16M illustrative positive gross reimbursement gap**. This identifies products for investigation; it is not an estimate of achievable or net savings. Rebates, unit types, therapeutic equivalence, and substitution feasibility still need confirmation.
- NDA and ANDA are application categories, not a complete brand/generic classification. The directory is not a point-in-time 2024 snapshot.
- The tests cover join duplication, missing values, NDC formatting, weighted prices, and formulation matching. Spending tables must reconcile to the same total.

Sources: [CMS 2024 State Drug Utilization Data](https://data.medicaid.gov/dataset/61729e5a-7aa8-448c-8903-ba3e0cd0ea3c), [FDA NDC Directory](https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory), and the [CMS reporting definitions](https://www.medicaid.gov/medicaid/prescription-drugs/state-drug-utilization-data/state-drug-utilization-data-faq).

Academic collaborators: Annie Qin, Marcello Borromeo, Dhruv Nair, and Mo Mia (Mohammed Mia), ASU CIS 450.
