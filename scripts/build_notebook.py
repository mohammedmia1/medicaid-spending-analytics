"""Build and execute the compact portfolio notebook without requiring Jupyter."""
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

    markdown("# Medicaid prescription spending\n\nA reproducible healthcare analytics case study using an archived 2024 extract.\n\n**Scope:** 11 states and Washington, DC. **Primary questions:** where does reported spending concentrate, and what data-quality constraints shape interpretation?\n\nThe original ASU project was completed by Annie Qin, Marcello Borromeo, Dhruv Nair and Mo Mia. This subsequent portfolio refinement preserves the original submission and documents its changes.")
    code('''from pathlib import Path
import sys
import json
import sqlite3
import pandas as pd

ROOT = next(p for p in [Path.cwd(), Path.cwd().parent] if (p / "src/medicaid_analytics").exists())
sys.path.insert(0, str(ROOT / "src"))
from medicaid_analytics.pipeline import run
from medicaid_analytics.verify import verify
if not (ROOT / "data/processed/analytics.sqlite").exists():
    run(ROOT)
audit = json.loads((ROOT / "reports/audit.json").read_text())
connection = sqlite3.connect(ROOT / "data/processed/analytics.sqlite")
print(audit["scope"])
''')
    markdown("## 1. Audit the retained source before interpreting results\n\nBoth utilization sheets reach Excel's maximum populated row. Suppression means the reported dollar total excludes unknown amounts. It is not a national or complete net-spending estimate.")
    code('''summary = pd.Series({
    "Retained records": audit["utilization"]["source_records"],
    "Suppressed records": audit["utilization"]["suppressed_records"],
    "Reported spending records": audit["utilization"]["spend_eligible_records"],
    "Reported pre-rebate reimbursement": audit["headline"]["total_reimbursement"],
    "Original/cleaned fact rows reconcile": audit["original_source_reconciliation"]["order_independent_fact_rows_match"],
    "Metadata matched share of dollars": audit["join"]["matched_spending_share"],
})
print(summary.to_string())
print("Jurisdictions:", ", ".join(audit["utilization"]["observed_states"]))
''')
    markdown("## 2. Rank spending with SQL\n\nThe query uses `ROW_NUMBER`, cumulative window sums, and a denominator that includes unmatched metadata. Product keys combine package sizes; repeated product names can represent distinct product codes.")
    code('''product_sql = (ROOT / "sql/product_spending.sql").read_text()
products = pd.read_sql_query(product_sql, connection)
print(products.head(10)[["product_key", "product_name", "reimbursement", "spend_share"]].to_string(index=False))
print(f"Top 10 share: {products.head(10).spend_share.sum():.1%}")
print(f"Top 50 share: {products.head(50).spend_share.sum():.1%}")
''')
    figure("top_products.png", "Highest-spending product keys")
    figure("spending_concentration.png", "Cumulative spending concentration")
    markdown("## 3. Assess coverage and quarterly patterns\n\nAbsolute jurisdiction amounts do not measure efficiency. Suppressed record shares do not estimate missing dollars. No Midwest jurisdiction is retained. Quarterly changes are descriptive and are not attributed to policy interventions.")
    code('''coverage = pd.read_sql_query((ROOT / "sql/jurisdiction_coverage.sql").read_text(), connection)
quarters = pd.read_sql_query((ROOT / "sql/quarterly_spending.sql").read_text(), connection)
print(coverage[["state", "source_records", "suppressed_record_share", "reimbursement"]].to_string(index=False))
print("\\nQuarterly results:")
print(quarters.to_string(index=False))
''')
    figure("jurisdiction_coverage.png", "Jurisdiction spending and suppression coverage")
    markdown("## 4. Reproduce and challenge the original Q3 result\n\nThe original ingredient-level calculations reproduce to the cent. However, name-based brand labels, ingredient-only grouping, rounded prices and unsupported adoption assumptions prevent those figures from establishing practical or net savings.")
    code('''legacy = audit["legacy_reproduction"]
for key in ["legacy_median_scenario", "legacy_weighted_scenario", "legacy_class_adjusted_scenario"]:
    print(f"{key}: ${legacy[key]:,.2f}")
print(f"Paper's approximate class-adjusted claim: ${legacy['paper_claimed_class_adjusted_scenario']:,.0f}")
''')
    markdown("## 5. A narrower price-review screen\n\nNDA- and ANDA-listed prescription products are compared within identical recorded ingredient, strength, strength unit, dosage form, route, jurisdiction, quarter and utilization type. Reimbursement-weighted prices are ratios of sums. Marketing-date overlap is checked. This is **not an equivalence determination or net-savings estimate**. Unit types, rebates and feasibility remain unverified.")
    code('''screen = audit["reimbursement_gap_screening"]
print("Paired formulations:", screen["distinct_paired_formulations"])
print("Paired reporting strata:", screen["paired_strata"])
print(f"Illustrative positive gross reimbursement gap: ${screen['illustrative_positive_gross_gap']:,.2f}")
print(f"Signed gap including negative comparisons: ${screen['signed_gross_gap']:,.2f}")
print(screen["interpretation"])
ranking = pd.read_csv(ROOT / "reports/tables/formulation_gap_ranking.csv")
print(ranking.head(5)[["ingredient", "dosage_form", "strength", "strength_unit", "positive_gross_gap"]].to_string(index=False))
''')
    figure("formulation_gaps.png", "Formulations for further price review")
    markdown("## 6. Validation and decision boundary\n\nPrioritize high-dollar products for investigation. Before proposing interventions, obtain complete dated source coverage, unit types, appropriate FDA equivalence references, net rebate effects and stakeholder review. No new machine-learning model is needed for this descriptive decision.\n\nSee `docs/METHODOLOGY.md`, `docs/AUDIT_REPORT.md` and `data/README.md` for detailed definitions and limitations.")
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
