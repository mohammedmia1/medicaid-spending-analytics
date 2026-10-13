# Medicaid Prescription Spending | Healthcare Data Analytics

[![Validate analytics](https://github.com/mohammedmia1/medicaid-spending-analytics/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/mohammedmia1/medicaid-spending-analytics/actions/workflows/validate.yml)

**An audit-first analysis of an archived 2024 utilization extract covering 11 states and Washington, DC.**

I refined a university group project into a reproducible Python and SQL analysis of spending concentration, source-data coverage, and product reimbursement differences. The first finding changed the scope of the project: a workbook described as national retained only 12 jurisdictions and reached Excel's row limit. All results below refer to that retained extract.

![Portfolio overview](reports/figures/portfolio_overview.png)

## Business question

Where does reported Medicaid prescription spending concentrate, and which comparable product formulations should an analyst prioritize for further price review?

The intended reader is a healthcare finance or analytics team. The deliverable combines a concise spending brief with traceable data preparation, SQL analyses, and a documented screening method. It supports investigation priorities; it does not recommend clinical substitutions or estimate net budget savings.

## Verified results

| Measure | Result | Interpretation |
|---|---:|---|
| Retained utilization records | 1,048,575 | Exactly Excel's row capacity minus the header |
| Jurisdictions | 12 | AK, AL, AR, AZ, CA, CO, CT, DC, DE, FL, GA, HI |
| Records with reported reimbursement | 504,630 | Suppressed records remain in coverage analysis |
| Reported reimbursement | **$27.54 billion** | Medicaid reimbursement before manufacturer rebates |
| Top 10 product NDC spending share | **16.4%** | Product NDCs combine package sizes, not all strengths of a brand |
| Top 50 product NDC spending share | **37.1%** | Same denominator, including unmatched metadata |
| California's observed spending share | **56.5%** | Absolute extract share, not a measure of efficiency |
| Product metadata coverage | **99.42% of reported reimbursement** | Unmatched spending remains in totals |

![Product spending concentration](reports/figures/top_products.png)

**Decision implication:** start product reviews with the largest contributors, but validate rebates, unit types, therapeutic equivalence, and local utilization before proposing a savings intervention. Jurisdiction rankings require enrollment and drug-mix adjustments before they can be interpreted as efficiency comparisons.

## What the audit changed

| Original approach | Refined approach |
|---|---|
| National framing | Explicit scope of 11 states plus DC; no national extrapolation |
| Brand/generic inferred by name equality | Preserve directory application categories without equating them to brand status |
| Ingredient-only substitution estimates | Exact recorded ingredient, strength, strength unit, dosage form, and route; compare within jurisdiction, quarter, and utilization type |
| First-match Excel lookups | Validated many-to-one left join; quarantine conflicting metadata |
| Rounded row prices used in calculations | Ratios of summed reimbursement and units; round only for presentation |
| Missing descriptors removed from spending analysis | Keep unmatched products in the spending denominator |
| Broad AI-generated drug classes | Directory application categories and optional overlapping source EPC tags |
| Random-forest importance interpreted as cost drivers | Descriptive analysis without causal claims; original model retained only in the archive |
| Approximately $1.2B class-adjusted savings in the paper | Reproduced saved result of $987.70M; documented assumptions and discrepancy |

The original median and weighted Q3 outputs reproduce to the cent. Their reproducibility does not establish that the assumptions support actual savings. See the [audit report](docs/AUDIT_REPORT.md).

## Analytical workflow

1. **Extract:** stream cached XLSX values into compressed CSV files with original worksheet row identifiers.
2. **Validate:** check 2024 observation grain, suppression flags, numeric eligibility, NDC formatting, and jurisdiction coverage.
3. **Reconcile:** compare original and cleaned observation fingerprints, source totals, and coverage.
4. **Join:** normalize segmented directory NDCs; collapse identical metadata and exclude 424 conflicting keys from metadata enrichment.
5. **Analyze in SQL:** rank product spending with window functions, measure concentration, report jurisdiction coverage, and summarize quarters and application categories.
6. **Screen reimbursement gaps:** compare NDA- and ANDA-listed prescription products within exact recorded formulation and local reporting strata.
7. **Publish evidence:** generate charts, CSV tables, audit JSON, and an executive brief from the verified outputs.

### Optional reimbursement-gap screening

The refined screen identifies **562 recorded formulations across 6,675 paired strata**. It produces a **$516.16M illustrative positive gross reimbursement gap** in the retained extract. This is a mechanical price-review scenario, **not verified substitution potential or net savings**. Negative differences are retained separately rather than hidden.

Application categories are not a complete brand/generic classification. Identical recorded descriptors are not an FDA therapeutic-equivalence determination. The snapshot lacks rebates and unit-type verification, and it is not a historical point-in-time directory. These constraints make spending and coverage the primary portfolio findings; gap screening is a secondary investigation tool.

![Observed jurisdiction coverage](reports/figures/jurisdiction_coverage.png)

## Explore the project

| Start here | Purpose |
|---|---|
| [Executive brief](reports/EXECUTIVE_BRIEF.pdf) | Two-page overview for a business reader |
| [Executed analysis notebook](notebooks/Medicaid_Spending_Analysis.ipynb) | Narrative, SQL results, figures, and original-result reconciliation |
| [SQL analyses](sql/) | Aggregation, ranking, cumulative shares, coverage and quarterly comparisons |
| [Python modules](src/medicaid_analytics/) | Extraction, preparation, comparisons, reporting and verification |
| [Methodology](docs/METHODOLOGY.md) | Grain, denominators, join decisions and screening formula |
| [Audit report](docs/AUDIT_REPORT.md) | Material findings and original-to-refined reconciliation |
| [Data guide](data/README.md) | Sources, snapshot boundaries and field definitions |
| [Interview guide](docs/INTERVIEW_GUIDE.md) | Technical explanations and honest portfolio positioning |
| [Original submission archive](archive/) | Unmodified original papers/notebooks and source hashes |

## Reproduce locally

Requires Python 3.11 or newer; allow at least 2 GB available memory and 500 MB of free disk space. The included compressed source extracts are sufficient; no credentials or database server are required. The regenerated SQLite database is approximately 336 MB.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m medicaid_analytics.pipeline
PYTHONPATH=src python -m medicaid_analytics.verify
```

On Windows, activate with `.venv\Scripts\activate` and install the package using `pip install -e .`; then omit the `PYTHONPATH=src` prefix. Jupyter is optional and only needed to rerun the notebook interactively.

The pipeline rebuilds `data/processed/analytics.sqlite`, `reports/audit.json`, the analysis tables, and five figures. It fails if legacy Q3 values no longer reproduce or the original/cleaned source observations do not reconcile. [GitHub Actions](https://github.com/mohammedmia1/medicaid-spending-analytics/actions) runs the same checks on pushes and pull requests.

To regenerate the included worksheet extracts from the two original supplied workbooks:

```bash
PYTHONPATH=src python -m medicaid_analytics.extract --source-dir /path/to/original/workbooks
```

Extraction reads stored formula results; it does not recalculate Excel formulas. Input checksums in the audit are specific to this archived export, not a live CMS release.

After rebuilding the pipeline, `python scripts/build_notebook.py` re-executes the notebook's seven code cells and refreshes its embedded figures. To rebuild the executive PDF, install the optional report dependency with `pip install -e '.[reports]'` and run `python scripts/build_brief.py`.

## Scope and limitations

- **Coverage:** this is a retained 12-jurisdiction extract. Reaching the Excel limit is consistent with truncation, but the exact export history is unavailable. Completeness within each jurisdiction is not certified.
- **Suppression:** 543,945 records have suppressed amounts. Their missing dollars are unknown and are not replaced with zero. Record suppression rates do not estimate missing dollar shares.
- **Reimbursement:** observed amounts precede manufacturer rebates; net spending is unavailable.
- **Metadata:** the supplied directory includes marketing dates after 2024. A quarter-overlap check helps screening but cannot reconstruct historical metadata.
- **Comparability:** the price screen cannot establish therapeutic equivalence, unit-type consistency, practical substitution, or patient-level suitability.
- **Interpretation:** descriptive associations and random-forest importance do not establish causal cost drivers.

## Attribution

The original ASU CIS 450 submission was a group project by **Annie Qin, Marcello Borromeo, Dhruv Nair, and Mo Mia (Mohammed Mia)**. This repository is a subsequent individual portfolio refinement by Mohammed Mia, developed with AI assistance. The original documents remain unchanged in the archive; the workbooks remain unchanged in the supplied source collection and are indexed by checksum. Original member-by-member task ownership is not inferred from filenames.

## Sources

- [CMS 2024 State Drug Utilization Data](https://data.medicaid.gov/dataset/61729e5a-7aa8-448c-8903-ba3e0cd0ea3c): original upstream dataset; this repository uses the supplied archived workbook extract.
- [CMS SDUD FAQs](https://www.medicaid.gov/medicaid/prescription-drugs/state-drug-utilization-data/state-drug-utilization-data-faq): reporting definitions, suppression and Excel capacity.
- [CMS reimbursement FAQ](https://www.medicaid.gov/faq/2020-04-09/92001): pre-rebate interpretation.
- [FDA NDC Directory](https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory): listing data and its limitations.
- [FDA Orange Book Preface](https://www.fda.gov/drugs/development-approval-process-drugs/orange-book-preface): therapeutic equivalence requires more than ingredient matching.
