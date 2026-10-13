"""Screen observed NDA/ANDA reimbursement gaps; do not infer therapeutic equivalence."""
from __future__ import annotations

import pandas as pd

FORMULATION = ["ingredient", "dosage_form", "route", "strength", "strength_unit"]
STRATA = FORMULATION + ["state", "quarter", "utilization_type"]


def reimbursement_gaps(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Compare utilization-weighted reimbursement within exact recorded strata.

    NDA and ANDA describe application categories, not guaranteed brand status.
    The retained extract lacks rebate, unit-type, and therapeutic-equivalence
    data; the resulting gaps are screening scenarios, not realizable savings.
    """
    start = pd.to_numeric(frame["marketing_start"], errors="coerce")
    end = pd.to_numeric(frame["marketing_end"], errors="coerce")
    dates_known = start.notna()
    quarter_end = frame["quarter"].map({1: 20240331, 2: 20240630, 3: 20240930, 4: 20241231})
    quarter_start = frame["quarter"].map({1: 20240101, 2: 20240401, 3: 20240701, 4: 20241001})
    overlaps_2024 = dates_known & start.le(quarter_end) & (end.isna() | end.ge(quarter_start))
    descriptors_complete = frame[FORMULATION].fillna("").ne("").all(axis=1)
    eligible = (frame["price_eligible"] & frame["metadata_matched"] & descriptors_complete
                & frame["application_type"].isin(["NDA", "ANDA"])
                & frame["product_type"].eq("HUMAN PRESCRIPTION DRUG") & overlaps_2024)
    sample = frame.loc[eligible].copy()
    grouped = sample.groupby(STRATA + ["application_type"], observed=True).agg(
        reimbursement=("reimbursement", "sum"), units=("units", "sum"),
        records=("source_row", "size"), products=("product_key", "nunique"),
    )
    paired = grouped.unstack("application_type")
    required = [("units", "NDA"), ("units", "ANDA")]
    if not all(x in paired.columns for x in required):
        return pd.DataFrame(), {"screening_input_records": len(sample), "paired_strata": 0,
                                 "illustrative_positive_gross_gap": 0.0}
    paired = paired.dropna(subset=required)
    result = paired.copy()
    result.columns = [f"{metric}_{category.lower()}" for metric, category in result.columns]
    result = result.reset_index()
    result["nda_weighted_cpu"] = result["reimbursement_nda"] / result["units_nda"]
    result["anda_weighted_cpu"] = result["reimbursement_anda"] / result["units_anda"]
    result["signed_gap_per_unit"] = result["nda_weighted_cpu"] - result["anda_weighted_cpu"]
    result["signed_gross_gap"] = result["signed_gap_per_unit"] * result["units_nda"]
    result["positive_gross_gap"] = result["signed_gross_gap"].clip(lower=0)
    result["gap_share_of_nda_reimbursement"] = result["positive_gross_gap"] / result["reimbursement_nda"].replace(0, float("nan"))
    result = result.sort_values("positive_gross_gap", ascending=False).reset_index(drop=True)
    # Nonnegative comparison prices imply a gap bounded by observed NDA spending.
    assert (result["positive_gross_gap"] <= result["reimbursement_nda"] + 0.01).all()
    audit = {
        "screening_input_records": len(sample), "paired_strata": len(result),
        "distinct_paired_formulations": len(result[FORMULATION].drop_duplicates()),
        "positive_gap_strata": int(result["positive_gross_gap"].gt(0).sum()),
        "negative_gap_strata": int(result["signed_gross_gap"].lt(0).sum()),
        "paired_nda_reimbursement": float(result["reimbursement_nda"].sum()),
        "illustrative_positive_gross_gap": float(result["positive_gross_gap"].sum()),
        "signed_gross_gap": float(result["signed_gross_gap"].sum()),
        "interpretation": "Illustrative pre-rebate reimbursement-gap screening; not verified substitution or net savings.",
    }
    return result, audit


def reproduce_legacy(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Reproduce Q3 cached-input calculations solely for an audit comparison."""
    required = ["NONPROPRIETARYNAME", "BRAND OR GENERIC", "PHARM_CLASSES", "Drug Class"]
    sample = frame.dropna(subset=required).copy()
    sample["Cost per Unit"] = pd.to_numeric(sample["Cost per Unit"], errors="coerce")
    counts = sample.groupby(["NONPROPRIETARYNAME", "BRAND OR GENERIC"]).size().unstack(fill_value=0)
    names = counts.index[(counts.get("Brand", 0) > 0) & (counts.get("Generic", 0) > 0)]
    sample = sample.loc[sample["NONPROPRIETARYNAME"].isin(names)]
    prices = sample.groupby(["NONPROPRIETARYNAME", "BRAND OR GENERIC"])["Cost per Unit"].median().unstack().dropna()
    generic = sample.loc[sample["BRAND OR GENERIC"].eq("Generic")].copy()
    generic["weighted_numerator"] = generic["Cost per Unit"] * generic["Units Reimbursed"]
    totals = generic.groupby("NONPROPRIETARYNAME")[["weighted_numerator", "Units Reimbursed"]].sum()
    prices["Weighted_Generic_CPU"] = totals["weighted_numerator"] / totals["Units Reimbursed"]
    prices["Brand_Units"] = sample.loc[sample["BRAND OR GENERIC"].eq("Brand")].groupby("NONPROPRIETARYNAME")["Units Reimbursed"].sum()
    prices["Potential_Savings_Median"] = (prices["Brand"] - prices["Generic"]) * prices["Brand_Units"]
    prices["Potential_Savings_Weighted"] = (prices["Brand"] - prices["Weighted_Generic_CPU"]) * prices["Brand_Units"]
    rates = {"Antidiabetic": .60, "Immunology / Autoimmune": .20, "Mental Health": .70,
             "Cardiovascular": .85, "GI / Acid Suppression": .80, "Pain / Analgesic": .75,
             "Anti-infective": .80, "Respiratory": .70, "Oncology": .10, "Hormonal / Endocrine": .60}
    classes = sample.groupby("NONPROPRIETARYNAME")["Drug Class"].agg(lambda x: x.mode().iloc[0])
    prices["Legacy_Class"] = classes
    prices["Legacy_Rate"] = prices["Legacy_Class"].map(rates).fillna(.50)
    prices["Legacy_Class_Adjusted"] = prices["Potential_Savings_Weighted"] * prices["Legacy_Rate"]
    summary = {"legacy_input_records": len(frame), "legacy_descriptive_complete_records": len(frame.dropna(subset=required)),
               "legacy_eligible_ingredient_names": len(names),
               "legacy_median_scenario": float(prices["Potential_Savings_Median"].sum()),
               "legacy_weighted_scenario": float(prices["Potential_Savings_Weighted"].sum()),
               "legacy_class_adjusted_scenario": float(prices["Legacy_Class_Adjusted"].sum()),
               "paper_claimed_class_adjusted_scenario": 1200000000,
               "status": "Original calculation reproduced, but its assumptions do not establish actual savings."}
    return prices.reset_index(), summary
