# Medicaid Prescription Drug Spending: A Five-Question Healthcare Analytics Study

**A portfolio presentation of my CIS 450 group final project | Arizona State University | December 2025**

**Original collaborators:** Annie Qin, Marcello Borromeo, Dhruv Nair, and Mo Mia. I am presenting our collaborative research in the first person to explain the analytical decisions, results, challenges, and lessons I took from it. I do not claim sole authorship of the group analysis.


## Executive summary

Medicaid prescription spending poses a practical question: can a program identify a relatively small set of drugs, therapeutic classes, and purchasing patterns where closer review might make the biggest difference? Our project explored that question with 2024 Medicaid drug utilization data and drug-product information. We organized the work into five linked research questions: **spending by drug, spending by class, hypothetical savings through generic substitution, potential alternatives, and cost drivers including geography**.

The work combined data preparation, exploratory data analysis, Excel summaries, price-per-unit calculations, scenario modeling, machine-learning experiments, and nonparametric statistical testing. The original paper reported **195,003 usable analytical records** after its cleaning and filtering process. It identified **537 ingredient-name groups with both brand- and generic-classified records** and modeled savings between roughly **$900 million and $1.8 billion**, with a **class-adjusted scenario around $1.2 billion**. Those savings are *model scenarios*, not verified realizable savings. Our regional comparison reported approximately **$9.9 billion** in spending in the West.

I present the methods and limitations alongside the findings because they are essential to understanding what the analysis can—and cannot—establish.

## At a glance

| Question | What we investigated | Main analytical approach |
|---|---|---|
| **Q1** | Which medications account for the most reimbursement? | NDC-level reimbursement aggregation and rankings |
| **Q2** | Which therapeutic classes account for the most reimbursement? | Drug-class summaries, pivots, and descriptive comparisons |
| **Q3** | What could substitution from brand-classified to generic-classified drugs save? | Ingredient grouping, medians, weighted generic prices, substitution-rate scenarios |
| **Q4** | Where might alternatives exist, and how do costs differ? | Brand/generic comparisons, therapeutic-class exploration, tree-based modeling |
| **Q5** | What characteristics and geographic patterns relate to unit cost? | Regional aggregations, Random Forest exploration, Kruskal–Wallis testing, heatmap |

## 1. The problem I wanted to understand

Prescription spending is not uniformly distributed. A small number of high-cost medications may account for substantial reimbursement, but high spending alone does not mean a product is overpriced: reimbursement depends on price, utilization, and the mix of patients and therapies. A cost-control proposal also has to distinguish between a cheaper-looking product and a clinically appropriate alternative.

We therefore started with the *structure* of spending before estimating possible savings. That ordering was an important lesson from our scoping discussions. We wanted to identify high-impact categories first, then examine where price differences and available alternatives might justify a closer review. We also explored whether drug category, brand/generic classification, utilization, or geography appeared related to cost per unit.

This was an exploratory academic study, not a clinical formulary recommendation or a validated budget forecast.

## 2. Data sources and preparation

### The two datasets

Our source materials were the **2024 All States Drug Utilization** dataset and the **National Drug Code (NDC) Directory**. The utilization data provided reimbursement and units; the product directory supplied product descriptions and drug attributes. Together, these sources made it possible to connect spending with drug identities and classifications.

| Field or concept | Why it mattered |
|---|---|
| NDC / product code | Connect utilization records to drug-product descriptions |
| Medicaid amount reimbursed | Measure total reported spending |
| Units reimbursed | Compute reimbursement per unit and scale scenarios |
| Proprietary / nonproprietary names | Explore brand-versus-generic classifications and ingredient grouping |
| Pharmacologic class / assigned drug class | Group medications into interpretable therapeutic categories |
| State and derived region | Compare geography and spending distributions |

### NDC standardization

A major practical challenge was that NDC identifiers were represented differently across the datasets. The original paper describes standardizing labeler and product segments to a common **nine-digit labeler/product key**, including leading zeros. This was necessary to reduce mismatches caused by formatting rather than by genuinely missing drug information.

The paper also describes cleaning missing values, standardizing categories, deriving **cost per unit = Medicaid amount reimbursed ÷ units reimbursed**, and assigning regions from states. It describes a brand/generic *heuristic* based on whether proprietary and nonproprietary names matched, and an AI-assisted classification of therapeutic classes from pharmacologic text.

These steps deserve documentation because they affect the interpretation of all downstream results. A name-based brand/generic label is not a regulatory determination, and an AI-assisted therapeutic category requires validation.

### The original merge code: a left join

The supplied [group Colab merge notebook](https://colab.research.google.com/drive/1nVJM00DSUrFDWJn6T2iPNSagcFOv9A3w?usp=sharing) reads two **prepared Excel workbooks** and uses a **left join on `NDC Code`**, retaining utilization rows while adding matching product information. It exports the result as `merged_output.csv`.

This is the join performed in the actual supplied notebook. The final paper also mentions an inner join when describing the broader preparation process; the two descriptions should not be treated as identical. I use **left join** when documenting this notebook, and I do not pretend the notebook contains earlier cleaning code that it does not show.

The final paper reports **195,003 usable records** after cleaning and excluding the ambiguous “Other” class. That is the original group's reported analysis population; its exact reconstruction remains dependent on the other original project files.

## 3. Analytical design: five questions, one progression

Our workflow was intentionally sequential. First, we ranked reimbursement by drug and class. Next, we narrowed the analysis to ingredient groups where both brand- and generic-classified records appeared. We then estimated possible substitution savings under multiple assumptions. Finally, we explored broader price differences, modeling, and geographic variation.

The original report includes a **problem-scoping and methodological hierarchy** diagram. That figure belongs here because it explains why we did not begin with a predictive model before understanding the spending distribution.

### Why exploratory analysis came first

The distributions were highly skewed: a few high-cost products could dominate averages. We used medians, rankings, and grouped comparisons to make the results interpretable. We also used weighted generic prices where a utilization-aware estimate was more relevant than treating every record equally.

This exploratory work is not a preliminary step to discard; it is a central part of the project.

## 4. Q1 — Which medications accounted for the most spending?

We aggregated Medicaid reimbursement at the NDC level and ranked the products. In the original report, **Biktarvy, Humira, and Ozempic (semaglutide) NDCs** were prominent among the highest-spending records. This result suggested that a relatively small group of medications could be a useful starting point for targeted spending review.

**Original visualization:** *Medicaid Reimbursements ($) by NDC* (original paper, results section, page 12 of the PDF).

### Interpretation

A high reimbursement total can arise from a high unit price, high utilization, or both. It should not automatically be interpreted as evidence of inefficiency. We used the ranking to identify **where to investigate**, not to declare that the highest-spending drugs should be restricted.

Another important distinction is that an NDC is not the same as an ingredient-level or brand-level total. Multiple strengths or product presentations can appear separately. The ranking therefore describes the granularity of the data used.

## 5. Q2 — Which therapeutic classes accounted for the most spending?

We grouped reimbursement by the project's therapeutic-class labels. The original report identified **Antidiabetic** and **Immunology/Autoimmune** drugs as major categories, together accounting for approximately **32%** of spending in the analyzed dataset.

**Original visualization:** *Medicaid Reimbursements ($) by Drug Class* (original paper, page 12).

### Interpretation

Class-level totals complement NDC rankings: they show whether high spending is concentrated around broader treatment areas rather than a single product. Chronic therapies can create substantial recurring expenditure because patients may need ongoing treatment.

The original class labels were created partly through an AI-assisted classification process and later filtered to remove “Other.” That choice improved interpretability but also changed coverage. I would not describe the class totals as independently validated without checking the underlying classifications.

## 6. Q3 — Where might generic substitution reduce spending?

This was one of the most involved parts of the original project. We wanted to move beyond the statement that generics are often less expensive and estimate how the observed price differences might translate into dollars at reported utilization.

### Step 1: identify candidate ingredient groups

We grouped records by **nonproprietary name** and retained groups that contained both brand- and generic-classified records. The original report identified **537 such groups**. These were *exploratory substitution candidates*, not 537 clinically verified interchangeable drug pairs.

### Step 2: compare prices while addressing outliers

For each group, we compared **median brand reimbursement per unit** with **median generic reimbursement per unit**. Because extreme prices can distort means, the median was an important descriptive choice. We also computed a **utilization-weighted generic reimbursement per unit**, which gives more influence to records with greater observed utilization.

### Step 3: scale price differences by brand utilization

The original scenario used a per-unit price difference multiplied by brand units to estimate the magnitude of potential savings. The conceptual calculation was:

```text
Estimated unit gap = brand unit-price benchmark - generic unit-price benchmark
Modeled gross savings = estimated unit gap × eligible brand units × assumed substitution rate
```

The original group code should be used to confirm exactly how the benchmark and any negative differences were handled. This formula explains the *concept* rather than claiming to reproduce every original implementation detail.

### Step 4: test substitution assumptions

The paper reports approximately **$900M** at **50%** substitution and **$1.8B** at **100%** substitution. It also reports a **class-adjusted estimate around $1.2B**, using different assumed substitution feasibility across therapeutic categories. Mental-health medications were discussed as potentially more substitutable, while oncology and biologic therapies were treated more cautiously.

**Original visualizations:** the savings ranking and *Substitution Rate vs. Estimated Savings* curve, in the Q3 results pages of the original report.

### Step 5: interpret the concentration of opportunity

The original report highlighted **aripiprazole, lisdexamfetamine dimesylate, risperidone, budesonide, and albuterol sulfate** among contributors to modeled savings. The business implication was that reviewing a smaller set of high-volume brand-classified drugs could be more productive than treating every medication as an equal target.

### What the savings numbers do—and do not—mean

These estimates are **gross hypothetical scenarios**. They do not establish that every ingredient-name match is therapeutically equivalent, that reimbursement units are directly comparable, that substitution is clinically appropriate, or that manufacturer rebates and actual net prices would preserve the modeled difference. The class-adjusted estimate is an *assumption-based scenario*, not an observed annual saving or a validated forecast.

Preserving those limitations makes the original project more defensible without replacing its analytical question.

## 7. Q4 — Which drugs might have comparable alternatives?

The group compared brand- and generic-classified drug records across therapeutic categories. The original paper reported a **median cost per unit of $9.97 for brand-classified records versus $0.39 for generic-classified records**, a roughly 25-fold descriptive difference.

**Original visualizations:** *Brand vs. Generic Cost per Unit Comparison* and *Median Cost per Unit by Drug Class* (Q4 results section).

The project described substantial apparent price gaps in **Mental Health, Cardiovascular, GI/Acid Suppression, and Pain/Analgesic** categories. In contrast, specialty areas such as **Oncology** and **Immunology/Autoimmune** often showed high costs and more limited alternative-product opportunities.

### Why the median comparison is informative but not sufficient

The $9.97 and $0.39 figures compare distributions of records labeled brand and generic. They are **not** a matched-pair estimate showing that replacing any particular drug will produce a 25-fold price reduction. Differences in formulation, route, strength, units, and drug mix can affect the comparison.

The original study used these results to motivate closer review of non-specialty categories. Actual therapeutic equivalence would need to be established separately.

## 8. Q5 — What characteristics and regional patterns were associated with cost?

The project explored whether price differences were associated with **brand status, drug class, ingredient identity, utilization, and region**. It also examined spending totals and cost-per-unit distributions across geographic groups.

### Modeling experiments

The paper describes an unsuccessful attempt to use **linear regression** for generic cost estimation. Skewed prices and correlated predictors produced implausible outputs, including negative aggregate savings. Rather than conceal that result, I include it as an analytical lesson: a model can produce numerical predictions while failing a basic plausibility check.

The paper subsequently describes tree-based methods. Its analytical-techniques section discusses **Random Forest regression predicting log-transformed cost per unit**, while the challenges section also mentions a **gradient boosting decision tree**. These references should be reconciled against the original Q3 and Q4–Q5 notebooks before asserting which specific model generated a published figure.

The original Q4 discussion identified **brand status** as a leading predictor, followed by drug class and ingredient identity, with geography comparatively less important. Feature importance describes a model's use of predictors; it is **not a causal estimate** of what would happen if a policy changed brand status.

### Regional exploration

The original report found the **West** had the highest total reimbursement, approximately **$9.9B**, and reported differences in average cost per unit among regions. It also discussed high-cost classes appearing across regions, despite different aggregate totals.

**Original visualizations:** regional reimbursement charts and the therapeutic-class-by-region heatmap in the Q5 results section.

### Statistical comparison

The group used the **Kruskal–Wallis test** to evaluate whether regional cost-per-unit distributions differed. The paper reports a statistically significant result. Statistical significance indicates evidence of distributional differences under the test; it does not demonstrate that geography itself caused the differences or establish their practical magnitude.

Likewise, a region's higher total spending does not imply higher unit prices without accounting for enrollment, utilization, and case mix.

## 9. Challenges, decisions, and what I learned

### Joining messy healthcare data

Inconsistent NDC formatting made it difficult to connect utilization with drug descriptions. The project required deliberate handling of leading zeros, labeler/product segments, naming differences, and missing matches. This is the kind of problem that can invalidate an analysis before any model is fitted.

### Interpreting drug names and classifications

A shared ingredient name does not guarantee identical formulation or interchangeability. The brand/generic naming heuristic and AI-assisted class labels helped organize the exploratory work, but both should be treated as approximations.

### Handling skew and implausible predictions

Extreme prices motivated median comparisons. The unsuccessful linear regression attempt also showed why predictions must be checked against domain and arithmetic constraints, rather than accepted solely because a model runs.

### Separating total spending from unit price

Total reimbursement, median reimbursement per unit, and hypothetical substitution savings answer different questions. A high-spending medication may have high utilization; a high-price medication may contribute little to the overall budget if rarely used.

### Keeping assumptions visible

The difference between the full-substitution and class-adjusted savings scenarios shows how strongly results can depend on assumptions. I would present the range and the assumptions together, rather than a single savings number without context.

## 10. Discussion and implications

Taken together, the original findings suggested a targeted review strategy. Start with the highest-spending NDCs and therapeutic classes. Within those areas, identify candidate ingredient groups with observed brand/generic price differences. Prioritize potential savings by the scale of brand utilization, then investigate formulation, clinical equivalence, coverage, availability, and net economics before recommending a policy change.

The regional findings suggested that expensive chronic-disease categories appeared across multiple regions. However, the evidence does not justify treating all jurisdictions as equivalent or interpreting geographic differences as causal effects.

The practical value of the study is its **structured prioritization process**. It converts a broad budget question into a sequence of measurable exploratory questions and makes assumptions explicit.

## 11. Limitations and scope

- **Collaborative work:** the source research and figures were produced by a four-person team; this README is my portfolio explanation of that shared project.
- **Source coverage:** the original paper uses broad “national” wording, but the actual extract's completeness must be verified before claiming representative nationwide coverage.
- **Join reproducibility:** the provided merge Colab shows a **left join on prepared files**; it does not show every earlier cleaning or classification step.
- **Classification uncertainty:** name comparisons and AI-assisted therapeutic class assignments can misclassify records.
- **Unit comparability:** reimbursement per unit can be misleading when unit definitions differ.
- **Savings assumptions:** substitution rates, clinical feasibility, and rebate-adjusted prices were not independently validated in the scenario.
- **Model attribution:** the exact Random Forest versus gradient boosting outputs require original notebook verification.
- **Causality:** predictive feature importance and regional significance tests do not establish causal cost drivers.

## 12. Tools and original project materials

The original study used **Excel** for preparation and grouped summaries, **Google Colab/Python** for analysis, and statistical and machine-learning techniques including medians, weighted averages, regression experiments, Random Forest exploration, and the Kruskal–Wallis test. The original paper links to separate Q1–Q2 Excel, Q3 Colab, and Q4–Q5 Colab files, which should be preserved alongside the data merge.

**Verified merge notebook:** [medicaid_data_merge.ipynb on Google Colab](https://colab.research.google.com/drive/1nVJM00DSUrFDWJn6T2iPNSagcFOv9A3w?usp=sharing)

**Original report:** *CIS 450 Group Project – Final Paper*, December 10, 2025, 21 pages.

**Visuals to embed from the original report:** problem-scoping diagram; Q1 NDC and Q2 drug-class reimbursement charts; Q3 substitution savings and candidate rankings; Q4 brand/generic and therapeutic-class comparisons; Q5 regional spending and heatmap. **These are not interchangeable with the newer charts currently in the repository.**

---

*Original collaborative research: Annie Qin, Marcello Borromeo, Dhruv Nair, and Mo Mia. First-person portfolio adaptation by Mo Mia. Reported values above come from the original group paper; analytical caveats and reconstruction status are made explicit.*
