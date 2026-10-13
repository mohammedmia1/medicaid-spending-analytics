# Interview and portfolio guide

## A concise project explanation

"I refined a group Medicaid spending project into a reproducible analytics deliverable. I first audited the archived extract and found that it covered only 11 states and DC, although the original report used national language. I preserved the submission, reconciled more than a million original and cleaned observations, validated the product join, and used SQL to analyze spending concentration and coverage. I also rebuilt the price-review screen with recorded formulation matching and made its assumptions explicit."

Use this only after reviewing the code and results well enough to explain the decisions yourself.

## Questions to prepare for

**Why analytics rather than data science?** The business decision needs reliable aggregation, source validation and clear interpretation. There is no new prediction target requiring machine learning. The original model's importance plot alone did not validate a useful predictive application.

**What is the observation grain?** Utilization type, jurisdiction, 11-digit package NDC, year and quarter. Keeping that grain avoids confusing managed-care and fee-for-service observations or collapsing unlike products.

**Why a left join?** Overall spending should not disappear when product descriptors are missing. A many-to-one constraint prevents duplicate directory listings from multiplying reimbursement. Conflicting metadata is quarantined while the utilization record stays in the denominator.

**How did you prove the original was preserved?** The source manifest has file hashes. Original papers and notebooks are archived byte-for-byte. Order-independent fingerprints reconcile the original and cleaned utilization rows, including amounts and keys.

**What did the top 50 mean?** Fifty product-level NDC keys account for 37.1% of the $27.54B eligible observed reimbursement. That is not fifty brands or a national share.

**Does California spend inefficiently?** That cannot be concluded. California contributes 56.5% of dollars in this extract, but enrollment, drug mix, suppression and source completeness are not controlled.

**Why not report $516M in savings?** It is a mechanical positive reimbursement gap under recorded NDA/ANDA comparisons. Equivalence, unit type, patient suitability, availability and rebates are unverified. It identifies review candidates rather than executable substitutions or net savings.

**What does weighted price mean?** Sum reimbursement divided by sum units within the matched stratum. This is different from averaging row-level prices; large and small utilization records should not receive identical weight.

**Why retain negative gaps?** They show where the comparison does not favor the NDA-to-ANDA price direction. Positive review candidates and the signed overall gap are different measures, so both are disclosed.

**What would you do next with real stakeholder access?** Obtain a complete dated utilization release, confirm reporting coverage and unit types, join appropriate equivalence references, and examine net rebate effects before presenting an operational savings case.

## Suggested resume bullets

- Refined a team-based Medicaid project into a reproducible Python and SQL analysis of 1.05 million utilization records across 11 states and Washington, DC, reconciling $27.54B in reported pre-rebate reimbursement.
- Built validated product enrichment, spending concentration and coverage analyses; identified that the top 50 product NDCs represented 37.1% of observed spending and documented suppression and metadata limitations.

Do not claim actual savings, national coverage, production deployment or sole authorship of the original group project. The paper lists Annie Qin, Marcello Borromeo, Dhruv Nair and Mo Mia. Describe your original contribution more specifically only when you can personally confirm the task ownership. The portfolio refinement used AI assistance; be ready to explain and validate it yourself.
