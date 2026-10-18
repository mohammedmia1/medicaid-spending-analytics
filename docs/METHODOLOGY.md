# How I built the analysis

## 1. Define the question and the dataset

I organized the project around five questions: which drugs account for spending, which pharmacologic categories are prominent, where observed price differences merit a savings review, which recorded formulations have potentially comparable alternatives, and how geographic and reporting context affect the interpretation. I use descriptive aggregation and matched price comparisons to answer these questions. The utilization extract contains 1,048,575 records for AK, AL, AR, AZ, CA, CO, CT, DC, DE, FL, GA, and HI.

One observation represents a utilization type, jurisdiction, 11-digit package NDC, year, and quarter. Keeping that grain avoids treating managed-care and fee-for-service reporting as duplicate observations. The extract reaches the worksheet row limit, so I do not assume complete coverage within each jurisdiction or extend the results to the whole country.

## 2. Prepare utilization records

I store NDCs as strings so their leading zeros remain intact. I check the reporting year, quarter, jurisdiction, utilization type, suppression indicator, and reimbursement values before including a record in the spending analysis.

Suppressed records stay in coverage counts, but their amounts remain missing. A missing amount is not zero. The spending analysis includes 504,630 observations totaling **$27,539,974,390.90**. The remaining 543,945 observations have suppressed amounts.

Price comparisons additionally require positive units. A record with zero units could contribute valid reported dollars to spending analysis, but it could not supply a reimbursement-per-unit estimate. Records sharing a duplicate observation key are excluded from calculations pending review; this dataset has no duplicate observation keys.

## 3. Attach product information

The utilization file has 11-character package NDCs. I take the first nine characters to identify the labeler/product combination. In the product directory, I pad the labeler and product segments separately to five and four characters. Padding an arbitrary unsegmented code would not establish where a missing zero belongs.

The directory contains 113,878 listings and 112,708 distinct product keys. I collapse identical analytical descriptors. When the same key has conflicting descriptions, I leave that key unmatched rather than choose a listing arbitrarily. There are 424 such keys; the affected listings are available in `reports/tables/directory_conflicts.csv`.

I use a many-to-one left join. Multiple utilization records can reference one product descriptor, while unmatched utilization records retain their reported spending. The join must preserve both row count and reimbursement. Unambiguous product information covers **99.4159% of reported dollars**; the remaining **$160,852,518.29** stays in the spending denominator.

## 4. Analyze spending in SQL

I load the enriched utilization table into SQLite and use four queries:

| Query | Question | Calculation |
|---|---|---|
| `product_spending.sql` | Which product NDCs account for spending? | Product totals, rank, share, and cumulative share |
| `jurisdiction_coverage.sql` | How do reported amounts and coverage vary? | Jurisdiction totals, suppression, and metadata coverage |
| `quarterly_spending.sql` | How do amounts change across quarters? | Quarterly totals, reimbursement per prescription, and `LAG` comparisons |
| `application_spending.sql` | How is spending distributed across application categories? | Category totals and shares |

All four spending outputs reconcile to the same denominator. Product NDCs combine package sizes but do not combine every strength of a brand. Jurisdiction totals are absolute amounts; they are not adjusted for enrollment, patient mix, or drug mix. Quarterly differences describe this dataset rather than establish policy effects.

For Q2, I use the directory's recorded established-pharmacologic-class (EPC) tags. I extract text marked `[EPC]`, deduplicate each record's tags, and sum that record's reimbursement once for each distinct tag. A product can have several tags, so amounts across tags overlap and must not be added as if the classes were mutually exclusive. I keep records with no EPC tag or unmatched metadata in an explicit category; this group accounts for $5.19B. The GLP-1 Receptor Agonist tag is associated with $2.94B. These figures are category context, not an additive therapeutic-class market share.

This treatment lets me describe pharmacologic categories without assigning new clinical labels. It also keeps the all-spending denominator intact rather than dropping products with incomplete classification.

## 5. Compare reimbursement per unit

I compare prescription products recorded as NDA or ANDA within matching ingredient, strength, strength unit, dosage form, and route. Each comparison also matches jurisdiction, quarter, and utilization type. I preserve salts and release descriptors; I do not infer equivalence from shortened names or reordered multi-ingredient strings.

I require a recorded marketing start date no later than the quarter's end, and any marketing end date must not precede the quarter's start. This checks whether listing dates overlap the reporting period; it does not establish what the directory contained at that historical date.

For each matched reporting group:

```text
weighted reimbursement per unit = total reimbursement / total units
signed gross gap = (NDA price per unit - ANDA price per unit) × NDA units
positive gross gap = max(signed gross gap, 0)
```

Using ratios of sums gives utilization its appropriate weight. A simple average of row-level prices would give small and large observations equal influence.

### Why I use weighted prices for Q3

The estimand is a gross reimbursement difference at observed NDA utilization. I therefore want each unit to contribute equally to the price calculation within its matched group. Algebraically, weighting each row's reimbursement-per-unit value by its units gives total reimbursement divided by total units. This also makes the NDA side reconcile to its observed reimbursement before applying the alternative price.

A median answers a different question: what is the middle row-level price? It can be useful for sensitivity analysis, but rows with different utilization receive equal rank in that summary. With only two observations, the median is their midpoint. It does not automatically provide a better estimate of aggregate dollars. I use weighted prices as the published comparison; the repository does not contain a separate median-based sensitivity result.

For an arithmetic example, suppose a matched group has 100 NDA units at $10 per unit and an ANDA weighted price of $2 per unit. The signed gross difference is ($10 - $2) x 100 = $800. This is an illustrative calculation, not a measured project observation or evidence that all 100 units can be substituted.

The analysis identifies **562 formulations across 6,675 matched reporting groups**. Positive gross differences sum to **$516,161,761.37**. Including negative differences gives a signed aggregate of **$506,733,293.57**. The detail retains both measures. The scenario table mechanically scales the positive aggregate to 25%, 50%, 75%, and 100%; these are hypothetical fractions rather than estimated adoption rates.

I calculate the positive amount within each reporting group before summing to formulation level. The signed amount retains comparisons in which ANDA reimbursement per unit is higher. As a result, a formulation's positive total can remain above zero even if its signed aggregate is negative. I report both instead of discarding the higher-ANDA-price observations.

### What Q4 can establish

For Q4, the same matching rules identify recorded formulations that appear on both sides of the comparison. I retain strengths, salts, routes, and release descriptors to avoid treating a shared ingredient name as sufficient evidence of comparability. Cyclosporine ophthalmic emulsion at 0.5 mg/mL, for example, is a specific formulation rather than a recommendation about every cyclosporine product.

The output is a review list. It cannot certify therapeutic equivalence, consistent reimbursement units, availability, or patient suitability. An actionable alternative would need applicable equivalence evidence and product-level review beyond the NDC directory fields.

## 6. Interpret the results

I use the spending rankings to prioritize high-dollar products for review. The top 50 product NDCs account for **37.1%** of reported reimbursement. California accounts for **56.5%** of this dataset's dollars, but that share alone does not measure efficiency.

The price differences identify investigation candidates. The extract lacks net rebates, verified reimbursement unit types, and therapeutic-equivalence determinations. Identical recorded descriptors do not prove that products can be substituted, and application categories are not definitive brand/generic labels. The comparison is not a clinical recommendation or a forecast of achievable savings.

For Q5, I describe geography at the jurisdiction level because the extract contains only 11 states and DC. Regional totals would inherit that incomplete composition. Q3 has the highest quarterly reimbursement at $7.63B; NDA, BLA, and ANDA listings account for 58.1%, 28.8%, and 10.3% respectively. These are observed distributions. I do not infer causal drivers, price-adjusted efficiency, or statistical significance from them.

My decision sequence follows the analytical questions: prioritize high-dollar products, add pharmacologic context, inspect exact recorded matches, and validate clinical and net economic comparability before considering an intervention.

## 7. Make the results repeatable

The pipeline generates the SQL tables, figures, and `reports/analysis_summary.json`. Source checksums identify the included CSV files. Tests check meaningful failure cases, including duplicate joins, mismatched formulations, future marketing dates, suppressed values, and incorrect price weighting. The verification command checks source integrity, spending totals, jurisdiction coverage, and price-comparison bounds.

The notebook saves executed outputs so the reader can follow each question through the calculation and interpretation.

## References

- [CMS SDUD FAQs](https://www.medicaid.gov/medicaid/prescription-drugs/state-drug-utilization-data/state-drug-utilization-data-faq): reporting fields, suppression, and source-size limitations.
- [CMS reimbursement FAQ](https://www.medicaid.gov/faq/2020-04-09/92001): reimbursement is reported before rebates.
- [FDA NDC Directory](https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory): product listing information and its limits.
- [FDA Orange Book Preface](https://www.fda.gov/drugs/development-approval-process-drugs/orange-book-preface): the separate framework for therapeutic-equivalence evaluations.
