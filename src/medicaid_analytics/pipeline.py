"""Build the audit, SQL tables and portfolio figures from archived CSV extracts."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from .compare import FORMULATION, reimbursement_gaps, reproduce_legacy
from .prepare import attach_metadata, prepare_directory, prepare_utilization


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fact_fingerprints(frame: pd.DataFrame) -> np.ndarray:
    """Order-independent row reconciliation, including amounts and observation keys."""
    fields = ["utilization_type", "state", "ndc11", "year", "quarter", "suppressed",
              "source_product_name", "units", "prescriptions", "reimbursement"]
    stable = frame[fields].copy()
    for col in fields:
        if col in ["year", "quarter", "units", "prescriptions", "reimbursement"]:
            stable[col] = pd.to_numeric(stable[col], errors="coerce").astype(float)
        elif col == "suppressed":
            stable[col] = stable[col].astype(bool)
        else:
            stable[col] = stable[col].astype("string").str.strip()
    return pd.util.hash_pandas_object(stable, index=False).to_numpy()


def run(root: Path) -> dict:
    raw = root / "data/raw"
    tables = root / "reports/tables"
    processed = root / "data/processed"
    tables.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    source = pd.read_csv(raw / "utilization_cleaned_legacy.csv.gz", dtype={"NDC": "string"})
    utilization, utilization_audit = prepare_utilization(source)
    # Independent pre/post-cleaning source reconciliation, without trusting duplicate NDC headers.
    original_total = 0.0
    original_rows = 0
    original_states = set()
    legacy_ndc_mismatches = 0
    original_hashes = []
    for chunk in pd.read_csv(raw / "utilization_original.csv.gz", chunksize=100000,
                             dtype={"NDC": "string", "NDC__2": "string"}):
        original_total += pd.to_numeric(chunk["Medicaid Amount Reimbursed"], errors="coerce").sum()
        original_rows += len(chunk)
        original_states.update(chunk["State"].dropna())
        legacy_ndc_mismatches += int(chunk["NDC"].ne(chunk["NDC__2"]).sum())
        chunk["NDC"] = chunk["NDC"].str.zfill(11)
        prepared_chunk, _ = prepare_utilization(chunk)
        original_hashes.append(fact_fingerprints(prepared_chunk))
    row_values_match = np.array_equal(np.sort(np.concatenate(original_hashes)), np.sort(fact_fingerprints(utilization)))
    original_audit = {"original_records": original_rows, "original_observed_states": sorted(original_states),
                      "original_reimbursement": float(original_total),
                      "duplicate_header_ndc_disagreement_records": legacy_ndc_mismatches,
                      "original_cleaned_reimbursement_difference": float(original_total - utilization_audit["observed_pre_rebate_reimbursement"]),
                      "order_independent_fact_rows_match": bool(row_values_match)}
    assert original_rows == len(utilization)
    assert abs(original_audit["original_cleaned_reimbursement_difference"]) < .01
    assert sorted(original_states) == utilization_audit["observed_states"]
    assert row_values_match, "Original and cleaned observations differ beyond ordering"
    del source
    directory_raw = pd.read_csv(raw / "ndc_directory.csv.gz", dtype="string")
    directory, conflicts, directory_audit = prepare_directory(directory_raw)
    conflicts.to_csv(tables / "directory_conflicts.csv", index=False)
    merged, join_audit = attach_metadata(utilization, directory)
    # Source EPC tags are descriptive and multi-label; never force a single AI class.
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
    gaps, gap_audit = reimbursement_gaps(merged)
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
    scenario["illustrative_gross_gap"] = scenario["hypothetical_fraction"] * gap_audit["illustrative_positive_gross_gap"]
    scenario["interpretation"] = "Mechanical sensitivity only; not feasible substitution or net budget savings"
    scenario.to_csv(tables / "illustrative_scenarios.csv", index=False)

    legacy = pd.read_csv(raw / "analysis_legacy.csv.gz", dtype={"NDC CODE": "string"})
    legacy_prices, legacy_audit = reproduce_legacy(legacy)
    legacy_prices.to_csv(tables / "legacy_q3_reproduction.csv", index=False)
    assert abs(legacy_audit["legacy_median_scenario"] - 1824211090.03) < .01
    assert abs(legacy_audit["legacy_weighted_scenario"] - 1752285190.51) < .01
    assert abs(legacy_audit["legacy_class_adjusted_scenario"] - 987704842.04) < .01
    legacy_audit["paper_overstatement_vs_saved_class_adjusted_output"] = 1200000000 - legacy_audit["legacy_class_adjusted_scenario"]
    del legacy

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
    total = utilization_audit["observed_pre_rebate_reimbursement"]
    assert np.isclose(product["reimbursement"].sum(), total)
    assert np.isclose(coverage["reimbursement"].sum(), total)
    assert np.isclose(results["quarterly_spending"]["reimbursement"].sum(), total)
    headline = {"total_reimbursement": total, "jurisdictions": len(coverage),
                "top10_product_share": float(product.head(10)["spend_share"].sum()),
                "top50_product_share": float(product.head(50)["spend_share"].sum()),
                "california_spend_share": float(coverage.loc[coverage["state"].eq("CA"), "reimbursement"].sum() / total),
                "observed_product_keys": len(product), "top_product": product.iloc[0]["product_name"],
                "top_product_reimbursement": float(product.iloc[0]["reimbursement"])}
    audit = {"scope": "Archived 2024 extract: 11 states and Washington, DC; not national",
             "utilization": utilization_audit, "original_source_reconciliation": original_audit,
             "directory": directory_audit, "join": join_audit,
             "legacy_reproduction": legacy_audit, "reimbursement_gap_screening": gap_audit,
             "headline": headline,
             "input_sha256": {p.name: sha256(p) for p in sorted(raw.glob("*.csv.gz"))}}
    (root / "reports/audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    from .visualize import figures
    figures(root, results, formulation, audit)
    print(json.dumps(audit, indent=2), flush=True)
    return audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    args = parser.parse_args()
    run(args.project_root.resolve())


if __name__ == "__main__":
    main()
