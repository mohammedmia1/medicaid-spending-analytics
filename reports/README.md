# Results: from spending concentration to price review

I organized these outputs around the five questions in the [project narrative](../README.md). All dollar amounts describe reported reimbursement before rebates in the included 2024 extract: 11 states and Washington, DC.

| Question | Table | Visualization | How I use it |
|---|---|---|---|
| Q1. Which products account for spending? | [Product ranking](tables/product_spending.csv) | [Top products](figures/top_products.png) and [cumulative share](figures/spending_concentration.png) | Identify the product set that warrants detailed spending review. |
| Q2. Which pharmacologic categories are prominent? | [Recorded EPC tags](tables/epc_tag_spending.csv) | [Pharmacologic tags](figures/pharmacologic_classes.png) | Add category context without treating overlapping tags as an additive budget. |
| Q3. Where do matched prices differ? | [Formulation ranking](tables/formulation_gap_ranking.csv) | [Positive gross gaps](figures/formulation_gaps.png) | Prioritize observed differences for investigation. |
| Q4. Which recorded matches support that review? | [Matched reporting groups, compressed CSV](tables/formulation_strata_gaps.csv.gz) | Formulation labels in the gross-gap chart | Inspect the ingredient, strength, form, route, reporting period, and utilization type behind each comparison. |
| Q5. How does reporting context change the interpretation? | [Jurisdiction coverage](tables/jurisdiction_coverage.csv), [quarters](tables/quarterly_spending.csv), and [application categories](tables/application_spending.csv) | [Jurisdiction context](figures/jurisdiction_coverage.png) and [quarter/category context](figures/spending_context.png) | Separate absolute spending patterns from claims about efficiency or causation. |

## The findings I would bring to a stakeholder

I found $27.54B in reported reimbursement, with the top 50 product NDCs accounting for 37.1%. Biktarvy product NDC 619582501 contributes $907.89M. The GLP-1 Receptor Agonist tag is associated with $2.94B, although class tags overlap and must not be added together.

The matched price comparison covers 562 formulations and 6,675 reporting groups. Its positive gross gap is $516.16M; its signed aggregate, including negative differences, is $506.73M. These calculations support a review list, not a claim of achievable savings. California contributes 56.5% of observed reimbursement, an absolute amount that requires coverage and population context.

## Reading the price-comparison files

In `formulation_strata_gaps.csv.gz`, each row is one matched ingredient, strength, strength unit, dosage form, route, jurisdiction, quarter, and utilization type. The file includes reimbursement, units, weighted prices, signed differences, and positive differences for the NDA/ANDA comparison.

In `formulation_gap_ranking.csv`, I aggregate the signed and positive amounts over reporting groups for each recorded formulation. Positive amounts are clipped at zero **before** aggregation. Consequently, a formulation can have a positive review gap even when its signed aggregate is negative. I retain both columns so that this distinction remains visible.

The [illustrative scenarios](tables/illustrative_scenarios.csv) multiply the positive aggregate by 25%, 50%, 75%, and 100%. I use them only to show arithmetic scaling. These fractions are not predicted substitution rates or clinically feasible adoption estimates.

## Supporting outputs

- [Executive brief](EXECUTIVE_BRIEF.pdf): a visual summary of the questions, findings, and review priorities.
- [Analysis summary](analysis_summary.json): source checksums, row counts, coverage, and headline totals.
- [Conflicting directory listings](tables/directory_conflicts.csv): product keys I left without attached descriptors because their analytical descriptions conflict.

The [methodology](../docs/METHODOLOGY.md) defines the calculations. The [executed notebook](../notebooks/Medicaid_Spending_Analysis.ipynb) shows the source loading, preparation, inline SQL, price calculations, and chart code directly. It calculates from source records, then compares every row of the nine result tables against these published outputs.
