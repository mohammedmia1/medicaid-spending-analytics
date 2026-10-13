# Original-to-portfolio audit

## Overall assessment

The original project has a useful business question, substantial preparation work, several analyses, and a complete academic narrative. Its strongest portfolio fit is healthcare data analytics. The refinement makes evidence, scope and reproduction central rather than turning an exploratory exercise into unsupported national policy estimates.

## Material findings

| Finding | Evidence | Resolution |
|---|---|---|
| National coverage not present | Original and cleaned sheets contain only 11 states and DC | All portfolio findings use the retained-extract scope |
| Actual Excel capacity reached | Both source sheets populate row 1,048,576 | Mark possible truncation; do not certify complete state coverage |
| Midwest missing | No Midwest jurisdictions occur in the source | Region map includes Midwest; no fabricated regional values |
| Duplicate NDC headers differ | Every retained row has two disagreeing NDC columns in `STATE (OG)` | Preserve both; reconcile the first observation code to explicit cleaned codes |
| Suppression accounts for missing amounts | 543,945 flagged records, all without reported reimbursement | Preserve coverage counts; do not replace missing dollars with zero |
| Metadata keys are not always unique | 424 normalized keys have conflicting analytic descriptors | Quarantine metadata; preserve their fact-table spending |
| Workbook lookup is not an inner join | Master sheet formulas use first-match `XLOOKUP`; unmatched values exist in the legacy analysis | Replace with a validated many-to-one left join |
| Brand/generic proxy is weak | Legacy rule compares proprietary and nonproprietary names | Use application categories with explicit limitations |
| Broad classes need review | Original class labels are AI-generated; Biktarvy is labeled Immunology/Autoimmune despite recorded antiviral EPC tags | Use source EPC tags and application categories; no forced clinical taxonomy |
| Savings paper and code disagree | Paper claims about $1.2B; final stored class-adjusted output is $987.70M | Reproduce original outputs and separate them from refined screening |
| Ingredient-only comparisons are insufficient | Q3 groups all products by nonproprietary name | Restrict to recorded formulation and local reporting strata |
| Aggressive Q4 normalization erases distinctions | Code strips salts and extended-release terms | Preserve these descriptors |
| Original retention percentage is incorrect | Code divides filtered row count by its own post-filter length | Record pre-filter and post-filter counts separately |
| Random forest lacks reported validation | Q4/Q5 code trains a model and displays feature importance without test performance | Retain original in archive; no causal or predictive portfolio claims |

## Numerical reproduction

| Original Q3 calculation | Reproduced amount |
|---|---:|
| Ingredient-based median scenario, 100% | $1,824,211,090.03 |
| Median scenario, 75% | $1,368,158,317.53 |
| Median scenario, 50% | $912,105,545.02 |
| Weighted-generic scenario, 100% | $1,752,285,190.51 |
| Original class-adjusted scenario | $987,704,842.04 |
| Difference from the paper's approximately $1.2B | Approximately $212.30M |

The legacy input has 504,630 records. Dropping missing descriptive fields leaves 491,838 records and 537 ingredient names with both legacy Brand and Generic labels. Q4/Q5 additionally drops Other classes and reports 195,003 records. Those are different analysis populations; they should not be described as one universal project dataset.

The original weighted-generic calculation weights already rounded row-level prices, then uses median brand pricing. The refined screen uses unrounded ratios of reimbursement and units on both sides. The original class adoption rates are embedded assumptions without supporting evidence in the supplied files; the refinement removes the term "realistic" and does not reuse those rates for decision claims.

## Refined outputs

- $27,539,974,390.90 in observed pre-rebate reimbursement.
- 19,101 product keys with eligible reported spending.
- Top 10 product keys account for 16.3947%; top 50 account for 37.1362%.
- Biktarvy product key 619582501 is the largest individual product key at $907,888,446.52.
- California supplies 56.4796% of observed reimbursement; that is not an efficiency metric.
- Unambiguous directory metadata covers 99.4159% of observed dollars.
- Secondary screening finds 562 recorded formulations in 6,675 paired strata, with a $516,161,761.37 illustrative positive gross gap. This is not verified substitution potential or net savings.

Differences between original and refined gap aggregates reflect changed classification, formulation granularity, temporal checks, population selection, weighting, and geography/quarter/utilization-type matching. They do not measure money saved by the refinement.

## Preservation and remaining uncertainty

Original uploaded files were not edited. Both papers and all three original notebooks are copied byte-for-byte into `archive/`; both large workbooks are indexed by SHA-256 in `source_manifest.json`, and exact cached-value extracts of the relevant worksheets are included. The workbooks themselves remain in the original supplied collection rather than being duplicated into a large GitHub repository.

The export history, exact source acquisition dates, member-by-member contribution split, therapeutic equivalence and rebate effects cannot be established from these files. The repository records these boundaries rather than inventing provenance. A future full-coverage CMS refresh should be stored as a new version and must not overwrite this reproducible archived snapshot.
