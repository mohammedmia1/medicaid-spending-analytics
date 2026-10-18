"""Execute the guided spending analysis and save notebook outputs and figures."""
from __future__ import annotations

import base64
import contextlib
import io
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cells = []

    def markdown(text: str):
        cells.append({"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)})

    def code(text: str):
        cells.append({"cell_type": "code", "metadata": {}, "source": text.splitlines(keepends=True),
                      "execution_count": None, "outputs": []})

    def figure(filename: str, title: str):
        cells.append({"cell_type": "markdown", "metadata": {},
                      "source": [f"![{title}](attachment:{filename})"],
                      "attachments": {filename: {"image/png": base64.b64encode((ROOT / "reports/figures" / filename).read_bytes()).decode()}}})

    markdown("# Medicaid prescription spending\n\n**Mohammed Mia | Python + SQL | 2024**\n\nI built this analysis to answer a practical question: **where does Medicaid prescription spending concentrate, and which products deserve a closer price review?**\n\nI work through the data, prepare a product-enriched utilization table, and use SQL to answer three questions: which product NDCs account for spending, how spending varies across jurisdictions and quarters, and where comparable products have different reimbursement per unit.\n\nThe dataset covers **11 states and Washington, DC**. It contains **$27.54B in reported reimbursement before rebates**. This is a descriptive analysis of the included extract; it is not a national spending estimate.")
    code('''from pathlib import Path
import sys
import json
import sqlite3
import pandas as pd

ROOT = next(p for p in [Path.cwd(), Path.cwd().parent] if (p / "src/medicaid_analytics").exists())
sys.path.insert(0, str(ROOT / "src"))
from medicaid_analytics.pipeline import run
from medicaid_analytics.prepare import prepare_utilization, prepare_directory, attach_metadata
from medicaid_analytics.compare import reimbursement_gaps
from medicaid_analytics.verify import verify

if not (ROOT / "data/processed/analytics.sqlite").exists():
    run(ROOT)
summary = json.loads((ROOT / "reports/analysis_summary.json").read_text())
connection = sqlite3.connect(ROOT / "data/processed/analytics.sqlite")
print(summary["scope"])
''')

    markdown("## 1. Get to know the data\n\nI start with utilization records and a product directory. A utilization record represents a reporting type, jurisdiction, package NDC, year, and quarter. The product directory supplies the ingredient, formulation, and application category.\n\nI load NDCs as text because their leading zeros matter. I use only the source fields needed for this analysis.")
    code('''columns = ["source_row", "Utilization Type", "State", "NDC", "Year", "Quarter",
           "Suppression Used", "Product Name", "Units Reimbursed",
           "Number of Prescriptions", "Medicaid Amount Reimbursed"]
records = pd.read_csv(ROOT / "data/raw/utilization.csv.gz", usecols=columns, dtype={"NDC": "string"})
product_records = pd.read_csv(ROOT / "data/raw/product_directory.csv.gz", dtype="string")
print(f"Utilization records: {len(records):,}")
print(f"Product listings: {len(product_records):,}")
print(records[["State", "NDC", "Quarter", "Suppression Used"]].head().to_string(index=False))
''')
    markdown("## 2. Keep missing amounts separate from zero\n\n**Question:** which records can support spending and price calculations?\n\nI check reporting fields, NDC format, suppression, duplicates, and numeric values. Suppressed amounts remain missing. A price calculation additionally requires positive units. The preparation function keeps these rules in one place so the notebook and pipeline use the same definitions.")
    code('''utilization, record_stats = prepare_utilization(records)
print(f"Records with reported reimbursement: {record_stats['spend_eligible_records']:,}")
print(f"Records with suppressed amounts: {record_stats['suppressed_records']:,}")
print(f"Reported reimbursement: ${record_stats['observed_pre_rebate_reimbursement']:,.2f}")
print("Jurisdictions:", ", ".join(record_stats["observed_states"]))
''')
    markdown("**Observation:** 504,630 records contain reported reimbursement, while 543,945 have suppressed amounts. **Decision:** I use reported amounts for spending totals and retain all observations for coverage reporting. I do not estimate the dollars hidden by suppression.")

    markdown("## 3. Join product information without changing spending\n\n**Question:** can each utilization record receive one product description?\n\nI normalize the directory's segmented product codes and join them to the product portion of the package NDC. I collapse identical descriptors, leave conflicting keys unmatched, and require a many-to-one left join. This keeps unmatched spending in the denominator and prevents duplicate listings from multiplying reimbursement.")
    code('''directory, conflicts, directory_stats = prepare_directory(product_records)
joined, join_stats = attach_metadata(utilization, directory)
print(f"Conflicting product keys left unmatched: {directory_stats['conflicting_directory_keys']:,}")
print(f"Product metadata coverage by dollars: {join_stats['matched_spending_share']:.2%}")
print(f"Unmatched reimbursement retained in totals: ${join_stats['unmatched_reimbursement']:,.2f}")
print(f"Utilization rows before / after join: {len(utilization):,} / {len(joined):,}")
''')
    markdown("**Result:** unambiguous product descriptions cover 99.42% of reported dollars. The remaining $160.85M remains part of spending totals. Matching information affects how a record can be described, not whether its reported reimbursement exists.")

    markdown("## 4. Find the products that account for spending\n\n**Question:** which product NDCs contribute the most reimbursement?\n\nI use SQL to aggregate eligible spending, rank products with `ROW_NUMBER`, and calculate cumulative shares with a window sum. The denominator includes unmatched product information.\n\nA product NDC combines package sizes. Different strengths of the same brand can still appear as separate product keys.")
    code('''products = pd.read_sql_query((ROOT / "sql/product_spending.sql").read_text(), connection)
top_products = products.head(10)[["product_key", "product_name", "reimbursement", "spend_share"]].copy()
top_products["reimbursement"] = top_products["reimbursement"].map(lambda x: f"${x:,.2f}")
top_products["spend_share"] = top_products["spend_share"].map(lambda x: f"{x:.2%}")
print(top_products.to_string(index=False))
''')
    figure("top_products.png", "Top product NDCs by reported reimbursement")
    code('''for count in [10, 50, 100]:
    share = products.head(count)["spend_share"].sum()
    print(f"Top {count} product NDCs: {share:.1%} of reported reimbursement")
''')
    figure("spending_concentration.png", "Cumulative spending share")
    markdown("**Observation:** Biktarvy product NDC 619582501 accounts for $907.89M. The top 50 product NDCs account for 37.1% of reimbursement. **Decision:** I would start detailed spending reviews with this concentrated product set rather than treating every product as an equal priority.")

    markdown("## 5. Compare jurisdictions with coverage in view\n\n**Question:** where are the reported dollars concentrated?\n\nI compare jurisdiction totals alongside suppression and record coverage. The SQL query keeps suppressed record counts separate from known reimbursement. These amounts are not adjusted for enrollment or drug mix.")
    code('''coverage = pd.read_sql_query((ROOT / "sql/jurisdiction_coverage.sql").read_text(), connection)
view = coverage[["state", "source_records", "suppressed_record_share", "reimbursement"]].copy()
view["suppressed_record_share"] = view["suppressed_record_share"].map(lambda x: f"{x:.1%}")
view["reimbursement"] = view["reimbursement"].map(lambda x: f"${x / 1e9:.3f}B")
print(view.to_string(index=False))
ca_share = coverage.loc[coverage["state"].eq("CA"), "reimbursement"].sum() / coverage["reimbursement"].sum()
print(f"California share of reported reimbursement: {ca_share:.1%}")
''')
    figure("jurisdiction_coverage.png", "Jurisdiction spending and suppression")
    markdown("**Observation:** California contributes 56.5% of the dataset's reimbursement. **Interpretation:** this describes concentration in the extract, not relative efficiency. A fair efficiency comparison would require enrollment, patient and drug mix, and confirmed reporting completeness. Suppressed record share is not the share of dollars missing.")

    markdown("## 6. Look at quarters and application categories\n\nI use quarterly totals and `LAG` to describe changes during 2024. I also summarize directory application categories. These comparisons help describe the spending mix; application categories are not a complete brand/generic classification.")
    code('''quarters = pd.read_sql_query((ROOT / "sql/quarterly_spending.sql").read_text(), connection)
view = quarters[["quarter", "reimbursement", "reimbursement_per_prescription", "quarter_change"]].copy()
view["reimbursement"] = view["reimbursement"].map(lambda x: f"${x / 1e9:.3f}B")
view["reimbursement_per_prescription"] = view["reimbursement_per_prescription"].map(lambda x: f"${x:.2f}")
view["quarter_change"] = view["quarter_change"].map(lambda x: "--" if pd.isna(x) else f"{x:+.1%}")
print(view.to_string(index=False))
''')
    code('''applications = pd.read_sql_query((ROOT / "sql/application_spending.sql").read_text(), connection)
view = applications.head(5)[["application_type", "reimbursement", "spend_share"]].copy()
view["reimbursement"] = view["reimbursement"].map(lambda x: f"${x / 1e9:.3f}B")
view["spend_share"] = view["spend_share"].map(lambda x: f"{x:.1%}")
print(view.to_string(index=False))
''')
    markdown("**Interpretation:** quarterly changes describe this extract; they do not establish a policy effect. Category totals describe recorded product listings, without implying that every NDA-listed product is a brand or every comparison is substitutable.")

    markdown("## 7. Compare like-for-like recorded formulations\n\n**Question:** where do products with matching recorded descriptors have different reimbursement per unit?\n\nI compare NDA- and ANDA-listed prescription products only when ingredient, strength, strength unit, dosage form, and route match. I also match jurisdiction, quarter, and utilization type, and check whether recorded marketing dates overlap the quarter.\n\nFor each side, I calculate **total reimbursement ÷ total units**. I then multiply the unit-price difference by NDA units to obtain a signed gross difference. I retain negative differences and report positive differences separately.")
    code('''gaps, price_stats = reimbursement_gaps(joined)
print(f"Matched recorded formulations: {price_stats['distinct_paired_formulations']:,}")
print(f"Matched reporting groups: {price_stats['paired_strata']:,}")
print(f"Positive gross reimbursement gap: ${price_stats['illustrative_positive_gross_gap']:,.2f}")
print(f"Signed gross gap, including negative differences: ${price_stats['signed_gross_gap']:,.2f}")
del records, product_records, utilization, directory, joined
''')
    figure("formulation_gaps.png", "Recorded formulations for price review")
    markdown("**Result:** 562 recorded formulations appear in 6,675 matched reporting groups. Positive differences sum to $516.16M. **Decision:** I treat these as products to investigate, not as a forecast of savings. The extract lacks verified reimbursement unit types, rebate effects, and therapeutic-equivalence determinations. Identical descriptors do not establish clinical substitutability.")

    markdown("## 8. Check the results and identify the next decision\n\nI check source-file integrity, matching assumptions, spending totals, coverage, and price-comparison bounds. The same checks run in GitHub Actions.\n\nMy recommendation is to prioritize the high-dollar product set, then verify complete reporting, unit types, equivalence, availability, and net rebate effects before evaluating an intervention. The spending findings stand on their own; the price comparison supports a narrower investigation.\n\nDetails: [methodology](../docs/METHODOLOGY.md), [data guide](../data/README.md), and [SQL queries](../sql/).")
    code('''verify(ROOT)
connection.close()
''')

    namespace = {"__name__": "__main__"}
    os.chdir(ROOT)
    execution = 0
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        execution += 1
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            exec(compile("".join(cell["source"]), f"notebook-cell-{execution}", "exec"), namespace)
        cell["execution_count"] = execution
        if captured.getvalue():
            cell["outputs"] = [{"output_type": "stream", "name": "stdout", "text": captured.getvalue().splitlines(keepends=True)}]
    for i, cell in enumerate(cells):
        cell["id"] = f"analysis-{i:02d}"
    notebook = {"nbformat": 4, "nbformat_minor": 5,
                "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                             "language_info": {"name": "python", "version": "3.11"}}, "cells": cells}
    path = ROOT / "notebooks/Medicaid_Spending_Analysis.ipynb"
    path.write_text(json.dumps(notebook, indent=1) + "\n")
    print(f"Executed {execution} code cells; wrote {path.name}")


if __name__ == "__main__":
    main()
