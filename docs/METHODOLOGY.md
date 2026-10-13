# Methodology

## Scope and observation grain

The utilization fact table represents a reported **utilization type x jurisdiction x 11-digit package NDC x year x quarter**. The year is fixed to 2024. The 12 retained jurisdictions are AK, AL, AR, AZ, CA, CO, CT, DC, DE, FL, GA and HI.

The original and cleaned worksheets each contain 1,048,575 observations. Sorting does not change the normalized row fingerprints: keys, suppression indicators, source product names, units, prescriptions and reimbursement reconcile. Original numerical CMS-format NDCs are restored to 11 characters only for this reconciliation; arbitrary unsegmented FDA NDCs are not globally padded.

The source sheet has two columns both named `NDC`; their values disagree on every row. The first is the observation NDC. The second is preserved as `NDC__2` in the extracted CSV and is not used for joins. The cleaned worksheet retains explicit zero-padded 11-character codes and the actual labeler/product/package fields. Source-row identifiers refer to the named worksheet, not to the original CMS download.

## Eligibility and denominators

Spending analysis accepts valid NDCs, recognized jurisdictions and utilization types, 2024 quarters 1-4, known suppression indicators, and reported nonnegative reimbursement. All records sharing a duplicated fact key are quarantined rather than arbitrarily retaining one. No duplicate keys are present in this snapshot.

Suppressed observations remain in coverage reporting. Their missing reimbursement is not imputed. Of 1,048,575 retained records, 543,945 are suppressed and 504,630 have reported reimbursement. The spending denominator is $27,539,974,390.90 across eligible observed records, including those without matched product metadata.

Price screening additionally requires strictly positive reported units. A zero-unit record can retain reported dollars in the spending table but cannot supply a cost-per-unit estimate. Negative and invalid source values are explicitly counted in the audit.

## Product NDC normalization and enrichment

The directory's segmented labeler/product codes are separately padded to historical 5/4 lengths. Taking the first nine digits of the explicit 11-digit utilization code gives the matching product key. The product key combines package sizes but distinguishes different product codes, often corresponding to different strengths or formulations.

The directory has 113,878 records and 112,708 distinct normalized keys. Fully identical analytic descriptors are collapsed. Keys whose remaining descriptors conflict are excluded from enrichment: 424 keys are quarantined and their source rows are retained in `directory_conflicts.csv`. The left join enforces `many_to_one`, unchanged row count, and unchanged reimbursement. The resulting unambiguous metadata covers 99.4159% of observed dollars. The remaining $160,852,518.29 stays in every overall spending denominator.

This conservative conflict rule includes differences in dates, labels, and class text; it is not limited to strength conflicts. It favors transparent exclusions over choosing a first listing. NDC Directory listings include submitted information and are not by themselves proof of approval or equivalence [FDA NDC Directory](https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory).

## Spending analyses

SQLite provides an inspectable local SQL implementation. Four query files compute product ranks and cumulative shares, jurisdiction suppression/coverage, quarterly totals with `LAG`, and marketing application category totals. Each additive output must reconcile to the same spending denominator.

Product comparisons use actual reimbursement rather than row averages. Quarterly reimbursement per prescription is total reimbursement divided by total reported prescriptions. Jurisdiction amounts are absolute values; no enrollment or case-mix adjustment is available. There is no inference that a higher-spending jurisdiction is inefficient.

The optional EPC table uses the directory's recorded `[EPC]` tags. A record may have multiple distinct tags; spending across tags overlaps and is **not additive**. Repeated identical tags on a record are counted once. No single broad clinical class is fabricated for a multi-class product.

## Secondary reimbursement-gap screen

The comparison uses prescription products labeled `NDA` or `ANDA` in the supplied directory. Biologics, OTC products, authorized-generic categories and unknown application types are excluded from this narrow screen. Category exclusion is not a statement about whether those products can ever be substituted.

Comparators must have the same recorded ingredient, dosage form, route, numeric strength string and strength unit. Names are case/whitespace normalized without deleting salts, formulations, or release descriptors. Multi-ingredient strings retain their recorded order; no automated equivalence across synonym or ordering differences is inferred.

Within each formulation, the comparison also matches jurisdiction, quarter and utilization type. A known marketing start date must precede the end of the observation quarter, and a recorded end date must not precede its start. This checks temporal overlap but does not make a later directory snapshot a point-in-time 2024 source.

For reporting stratum `s` and directory application category `a`:

```
weighted_cpu(s, a) = sum(reimbursement(s, a)) / sum(units(s, a))
signed_gap(s) = [weighted_cpu(s, NDA) - weighted_cpu(s, ANDA)] * sum(units(s, NDA))
positive_gap(s) = max(signed_gap(s), 0)
```

Negative gaps remain in the detail and signed aggregate. A separate positive-gap aggregate identifies price-review candidates; it does not offset these candidates with products whose comparators cost more. The 25%, 50%, 75% and 100% table mechanically scales the positive aggregate. These fractions are hypothetical sensitivities, not estimated adoption rates.

The results are bounded by observed paired NDA reimbursement. They are not observed savings or a fiscal forecast: unit-type consistency, therapeutic-equivalence ratings, substitution rules, patient needs, market availability and rebates are absent. CMS defines reimbursement as before rebates [CMS FAQ](https://www.medicaid.gov/faq/2020-04-09/92001); the [FDA Orange Book Preface](https://www.fda.gov/drugs/development-approval-process-drugs/orange-book-preface) provides the separate equivalence framework.

## Why there is no new predictive model

The business question is descriptive and prioritizes transparent aggregation and validation. The original random forest provided feature importance without reported predictive validation; importance is not causal evidence. Its code is preserved in the original notebook. Adding a new model without a meaningful prediction target and use case would not strengthen this deliverable.

## Verification

The test suite exercises NDC segmentation, name preservation, suppression/duplicate handling, many-to-one enforcement, unmatched spending, utilization weighting, stratum mismatches, future metadata and negative gaps. Integration checks reconcile source row fingerprints, input hashes, SQL totals, coverage and screening bounds. Original median, weighted and class-adjusted Q3 totals must reproduce to the cent.
