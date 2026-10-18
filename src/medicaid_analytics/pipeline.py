"""Build spending tables, price comparisons and figures from source CSV files."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from .compare import FORMULATION, reimbursement_gaps
from .prepare import attach_metadata, prepare_directory, prepare_utilization


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(root: Path) -> dict:
    raw = root / "data/raw"
    tables = root / "reports/tables"
    processed = root / "data/processed"
    tables.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    source = pd.read_csv(raw / "utilization.csv.gz", dtype={"NDC": "string"})
    utilization, utilization_stats = prepare_utilization(source)
    del source
    directory_raw = pd.read_csv(raw / "product_directory.csv.gz", dtype="string")
    directory, conflicts, directory_stats = prepare_directory(directory_raw)
    conflicts.to_csv(tables / "directory_conflicts.csv", index=False)
    merged, join_stats = attach_metadata(utilization, directory)
    # Source EPC tags can overlap; each distinct tag is counted once per record.
    tagged = merged.loc[merged["spend_eligible"], ["source_row", "reimbursement", "pharm_classes"]].copy()
    tagged["epc_tag"] = tagged["pharm_classes"].map(
        lambda x: sorted(set(re.findall(r"([^,]+?)\s*\[EPC\]", str(x)))) if pd.notna(x) else [])
    tagged["epc_tag"] = tagged["epc_tag"].map(lambda tags: [t.strip() for t in tags] or ["No recorded EPC tag / unmatched"])
    epc = tagged.explode("epc_tag").groupby("epc_tag").agg(
        tagged_reimbursement=("reimbursement", "sum"), tagged_records=("source_row", "size")
    ).sort_values("tagged_reimbursement", ascending=False).reset_index()
    epc["interpretation"] = "Overlapping source tags; tagged amounts must not be added across classes"
    epc.to_csv(tables / "epc_tag_spending.csv", index=False)
    del tagged
    gaps, gap_stats = reimbursement_gaps(merged)
    gaps.to_csv(tables / "formulation_strata_gaps.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    if not gaps.empty:
        formulation = gaps.groupby(FORMULATION).agg(
            positive_gross_gap=("positive_gross_gap", "sum"), signed_gross_gap=("signed_gross_gap", "sum"),
            nda_reimbursement=("reimbursement_nda", "sum"), nda_units=("units_nda", "sum"),
            paired_strata=("state", "size"), jurisdictions=("state", "nunique"),
        ).sort_values("positive_gross_gap", ascending=False).reset_index()
    else:
        formulation = pd.DataFrame(columns=FORMULATION + ["positive_gross_gap"])
    formulation.to_csv(tables / "formulation_gap_ranking.csv", index=False)
    scenario = pd.DataFrame({"hypothetical_fraction": [.25, .50, .75, 1.0]})
    scenario["illustrative_gross_gap"] = scenario["hypothetical_fraction"] * gap_stats["illustrative_positive_gross_gap"]
    scenario["interpretation"] = "Mechanical sensitivity only; not feasible substitution or net budget savings"
    scenario.to_csv(tables / "illustrative_scenarios.csv", index=False)

    with sqlite3.connect(processed / "analytics.sqlite") as connection:
        # pandas boolean columns become explicit integer flags in SQLite.
        merged.to_sql("utilization", connection, if_exists="replace", index=False, chunksize=10000)
        connection.execute("CREATE INDEX IF NOT EXISTS product_lookup ON utilization(product_key)")
        results = {}
        for sql in sorted((root / "sql").glob("*.sql")):
            result = pd.read_sql_query(sql.read_text(), connection)
            result.to_csv(tables / (sql.stem + ".csv"), index=False)
            results[sql.stem] = result
    product = results["product_spending"]
    coverage = results["jurisdiction_coverage"]
    total = utilization_stats["observed_pre_rebate_reimbursement"]
    assert np.isclose(product["reimbursement"].sum(), total)
    assert np.isclose(coverage["reimbursement"].sum(), total)
    assert np.isclose(results["quarterly_spending"]["reimbursement"].sum(), total)
    headline = {"total_reimbursement": total, "jurisdictions": len(coverage),
                "top10_product_share": float(product.head(10)["spend_share"].sum()),
                "top50_product_share": float(product.head(50)["spend_share"].sum()),
                "california_spend_share": float(coverage.loc[coverage["state"].eq("CA"), "reimbursement"].sum() / total),
                "observed_product_keys": len(product), "top_product": product.iloc[0]["product_name"],
                "top_product_reimbursement": float(product.iloc[0]["reimbursement"])}
    summary = {"scope": "2024 Medicaid utilization extract: 11 states and Washington, DC",
             "utilization": utilization_stats,
             "directory": directory_stats, "join": join_stats,
             "reimbursement_gap_screening": gap_stats,
             "headline": headline,
             "input_sha256": {p.name: sha256(p) for p in sorted(raw.glob("*.csv.gz"))}}
    (root / "reports/analysis_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    from .visualize import figures
    figures(root, results, formulation, summary)
    print(json.dumps(summary, indent=2), flush=True)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args()
    run(args.project_root.resolve())


if __name__ == "__main__":
    main()
