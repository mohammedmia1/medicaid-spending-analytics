"""Check source integrity, spending totals and price-comparison bounds."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .pipeline import sha256


def verify(root: Path) -> None:
    summary = json.loads((root / "reports/analysis_summary.json").read_text())
    for filename, expected in summary["input_sha256"].items():
        assert sha256(root / "data/raw" / filename) == expected, f"Input changed: {filename}"
    total = summary["utilization"]["observed_pre_rebate_reimbursement"]
    for filename in ["product_spending.csv", "jurisdiction_coverage.csv", "quarterly_spending.csv", "application_spending.csv"]:
        table = pd.read_csv(root / "reports/tables" / filename)
        assert np.isclose(table.reimbursement.sum(), total, atol=.01, rtol=0), filename
    coverage = pd.read_csv(root / "reports/tables/jurisdiction_coverage.csv")
    assert set(coverage.state) == set(summary["utilization"]["observed_states"])
    assert coverage.source_records.sum() == summary["utilization"]["source_records"]
    assert coverage.suppressed_records.sum() == summary["utilization"]["suppressed_records"]
    product = pd.read_csv(root / "reports/tables/product_spending.csv", dtype={"product_key": "string"})
    assert product.product_key.str.fullmatch(r"\d{9}").all()
    assert np.isclose(product.iloc[-1].cumulative_share, 1)
    gaps = pd.read_csv(root / "reports/tables/formulation_strata_gaps.csv.gz")
    assert np.isclose(gaps.positive_gross_gap.sum(), summary["reimbursement_gap_screening"]["illustrative_positive_gross_gap"])
    assert (gaps.positive_gross_gap <= gaps.reimbursement_nda + .01).all()
    assert not gaps.duplicated(["ingredient", "dosage_form", "route", "strength", "strength_unit", "state", "quarter", "utilization_type"]).any()
    print("PASS: source checksums, spending totals, jurisdiction coverage, and price-comparison bounds")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args()
    verify(args.project_root.resolve())


if __name__ == "__main__":
    main()
