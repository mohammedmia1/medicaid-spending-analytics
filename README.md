# Medicaid Prescription Drug Spending Analysis — Original Group Project Portfolio Adaptation

**Arizona State University | CIS 450 | December 2025 | Healthcare analytics**

> This is my first-person portfolio presentation of a collaborative group project completed with Annie Qin, Marcello Borromeo, and Dhruv Nair. The findings and original visuals are group work, not solely mine. This branch is a reconciliation draft; the original figures and analytical workbooks/notebooks still need to be brought into the repository before replacing the published README.

## Why I explored Medicaid drug spending

For my Business Data Analytics coursework, I collaborated on an analysis of Medicaid prescription reimbursement. I wanted to understand where spending was concentrated, where generic substitution might reduce costs, and how cost patterns differed by drug class and geography. Rather than presenting an entirely new analysis, I am documenting the original five-question study in a portfolio-friendly format.

## Q1 — Which drugs accounted for the most spending?

I examined the group's ranking of Medicaid reimbursements by National Drug Code (NDC). Biktarvy, Humira, and Ozempic NDCs appeared among the highest-reimbursement products. The original report's **Medicaid Reimbursements ($) by NDC** figure is the intended visualization for this section.

## Q2 — Which therapeutic classes accounted for the most spending?

The group's therapeutic-class summaries identified antidiabetic and immunology/autoimmune categories as major spending concentrations, together representing approximately **32%** of reimbursement in the analyzed dataset. The original **Medicaid Reimbursements ($) by Drug Class** figure belongs here.

## Q3 — What savings might generic substitution offer?

We identified **537 ingredient-name groups** containing both brand- and generic-classified records, compared median and utilization-weighted unit prices, and modeled different substitution rates. The original report estimated approximately **$900M at 50% substitution**, **$1.8B at full substitution**, and **$1.2B in a class-adjusted scenario**.

I interpret these as **exploratory scenario estimates, not verified achievable savings**. Matching ingredient names and assuming substitution rates does not establish therapeutic equivalence, rebate-adjusted prices, or clinical feasibility. The original savings ranking, brand/generic comparison, and substitution-rate curve should be displayed here unchanged once their source outputs are verified.

## Q4 — Which drugs might have comparable alternatives?

The group compared brand- and generic-classified drugs and reported median reimbursement per unit of **$9.97** versus **$0.39**. We also explored nonlinear modeling of cost drivers. The original **Brand vs Generic Cost per Unit Comparison** and **Median Cost per Unit by Drug Class** visuals belong here. These are descriptive aggregate differences, not interchangeable-product price quotes.

## Q5 — What drove cost differences, and how did regions compare?

The project examined drug class, brand status, utilization, and geographic differences. The West had approximately **$9.9B** in reimbursement in the original analysis. The group used a **Kruskal–Wallis test** to evaluate differences in cost per unit among regions and created regional drug-class heatmaps. A statistically significant difference does not by itself identify its cause.

## How I prepared and combined the data

The original [Colab merge notebook](https://colab.research.google.com/drive/1nVJM00DSUrFDWJn6T2iPNSagcFOv9A3w?usp=sharing) reads two **already-prepared Excel workbooks**: `drug_utilization_2024.xlsm` and `drug_utilization_product.xlsm`. It combines them with a **left join on `NDC Code`**, retaining rows from the utilization workbook, then exports `merged_output.csv`.

The final paper also describes NDC formatting, deriving cost per unit and region, brand/generic and therapeutic-class classification, and a cleaned analytical dataset of **195,003 records**. Those preparation and filtering steps are **not shown in the supplied merge notebook** and should be verified from the other original project files before being described as reproducible code.

## Challenges and exploratory modeling

The original study documents inconsistent NDC formats, ambiguous drug categories, skewed prices, unsuccessful linear regression predictions, and exploration of tree-based methods. The paper mentions both gradient boosting and Random Forest. I will attribute individual results to a specific model only after the original Q3 and Q4–Q5 notebooks confirm the implementations.

## Limitations and interpretation

The original brand/generic labels used a name-comparison heuristic; therapeutic classes were assisted by AI classification; and substitution scenarios relied on assumptions. The report's broad national wording should be read in the context of the actual source extract and coverage, which need verification. These limitations are part of the analysis, not reasons to replace the original exploratory findings.

## Original materials and next verification steps

- **Source:** CIS 450 Group Final Paper (December 10, 2025; 21 pages).
- **Data merge:** [Original Google Colab notebook](https://colab.research.google.com/drive/1nVJM00DSUrFDWJn6T2iPNSagcFOv9A3w?usp=sharing), verified as a left join.
- **Original figures:** Q1–Q2 drug and class charts; Q3 savings and substitution charts; Q4 brand/generic and drug-class comparisons; Q5 heatmap and regional rankings.
- **Original analytical files still to reconcile:** Q1–Q2 Excel workbook, Q3 Colab notebook, Q4–Q5 Colab notebook.

**Attribution:** Original collaborative research by Annie Qin, Marcello Borromeo, Dhruv Nair, and Mo Mia. This first-person narrative and GitHub organization are my portfolio adaptation.
