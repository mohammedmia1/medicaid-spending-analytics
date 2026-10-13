"""Validate observation grain and attach unambiguous product metadata."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

REGIONS = {
    "Northeast": "CT ME MA NH RI VT NJ NY PA",
    "Midwest": "IN IL MI OH WI IA KS MN MO NE ND SD",
    "South": "DE DC FL GA MD NC SC VA WV AL KY MS TN AR LA OK TX",
    "West": "AZ CO ID MT NV NM UT WY AK CA HI OR WA",
    "Territories": "AS GU MP PR VI",
}
STATE_TO_REGION = {state: region for region, states in REGIONS.items() for state in states.split()}


def ndc_product_key(value: str) -> str | None:
    """Normalize the segmented product NDC to historical 5-labeler/4-product.

    Segment lengths must be supplied; an unsegmented ten-digit NDC cannot
    be safely converted by padding the entire number.
    """
    parts = str(value).strip().split("-")
    if len(parts) != 2 or not all(x.isdigit() for x in parts):
        return None
    labeler, product = parts
    if len(labeler) not in (4, 5) or len(product) not in (3, 4):
        return None
    return labeler.zfill(5) + product.zfill(4)


def normalize_text(value: object) -> str:
    """Standardize whitespace/case without deleting salts or release markers."""
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).strip()).casefold()


def prepare_utilization(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    mapping = {
        "source_row": "source_row", "Utilization Type": "utilization_type",
        "State": "state", "NDC": "ndc11", "Year": "year", "Quarter": "quarter",
        "Suppression Used": "suppressed", "Product Name": "source_product_name",
        "Units Reimbursed": "units", "Number of Prescriptions": "prescriptions",
        "Medicaid Amount Reimbursed": "reimbursement",
    }
    frame = raw[list(mapping)].rename(columns=mapping).copy()
    for col in ["state", "utilization_type", "source_product_name", "ndc11"]:
        frame[col] = frame[col].astype("string").str.strip()
    # The cleaned worksheet stores explicit 11-character strings, including zeros.
    frame["ndc11"] = frame["ndc11"].str.replace("'", "", regex=False)
    frame["ndc_valid"] = frame["ndc11"].str.fullmatch(r"\d{11}").fillna(False)
    frame["product_key"] = frame["ndc11"].where(frame["ndc_valid"]).str[:9]
    suppression_text = frame["suppressed"].astype("string").str.lower()
    suppression_known = suppression_text.isin(["0", "1", "false", "true"])
    frame["suppressed"] = suppression_text.isin(["1", "true"])
    for col in ["year", "quarter", "units", "prescriptions", "reimbursement"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame["region"] = frame["state"].map(STATE_TO_REGION).fillna("Unmapped")
    grain = ["utilization_type", "state", "ndc11", "year", "quarter"]
    duplicate = frame.duplicated(grain, keep=False)
    frame["duplicate_key"] = duplicate
    valid_structure = (frame["ndc_valid"] & suppression_known & frame["year"].eq(2024)
                       & frame["quarter"].isin([1, 2, 3, 4])
                       & frame["utilization_type"].isin(["MCOU", "FFSU"])
                       & frame["state"].isin(STATE_TO_REGION))
    frame["spend_eligible"] = (valid_structure & ~duplicate & ~frame["suppressed"]
                               & frame["reimbursement"].notna() & frame["reimbursement"].ge(0))
    frame["price_eligible"] = (frame["spend_eligible"] & frame["units"].gt(0))
    frame["cost_per_unit"] = np.where(frame["price_eligible"],
                                        frame["reimbursement"] / frame["units"].replace(0, np.nan), np.nan)
    audit = {
        "source_records": len(frame), "invalid_ndc_records": int((~frame["ndc_valid"]).sum()),
        "suppressed_records": int(frame["suppressed"].sum()),
        "duplicate_grain_records_quarantined": int(duplicate.sum()),
        "invalid_structure_records": int((~valid_structure).sum()),
        "unknown_suppression_flag_records": int((~suppression_known).sum()),
        "missing_reimbursement_records": int(frame["reimbursement"].isna().sum()),
        "negative_reimbursement_records": int(frame["reimbursement"].lt(0).sum()),
        "zero_units_records": int(frame["units"].eq(0).sum()),
        "negative_units_records": int(frame["units"].lt(0).sum()),
        "spend_eligible_records": int(frame["spend_eligible"].sum()),
        "price_eligible_records": int(frame["price_eligible"].sum()),
        "observed_pre_rebate_reimbursement": float(frame.loc[frame["spend_eligible"], "reimbursement"].sum()),
        "observed_states": sorted(frame["state"].dropna().unique().tolist()),
        "years": sorted(frame["year"].dropna().unique().tolist()),
    }
    return frame, audit


def prepare_directory(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """One metadata row per key; reject conflicting descriptors instead of first-match."""
    mapping = {
        "PRODUCTNDC": "product_ndc", "PROPRIETARYNAME": "product_name",
        "NONPROPRIETARYNAME": "ingredient", "DOSAGEFORMNAME": "dosage_form",
        "ROUTENAME": "route", "ACTIVE_NUMERATOR_STRENGTH": "strength",
        "ACTIVE_INGRED_UNIT": "strength_unit", "MARKETINGCATEGORYNAME": "application_type",
        "PHARM_CLASSES": "pharm_classes", "STARTMARKETINGDATE": "marketing_start",
        "ENDMARKETINGDATE": "marketing_end", "LABELERNAME": "labeler",
        "PRODUCTTYPENAME": "product_type",
    }
    frame = raw[list(mapping)].rename(columns=mapping).copy()
    frame["product_key"] = frame["product_ndc"].map(ndc_product_key)
    for col in ["ingredient", "dosage_form", "route", "strength", "strength_unit"]:
        frame[col] = frame[col].map(normalize_text)
    # Canonicalize purely numeric strength representations (10 vs 10.0).
    frame["strength"] = frame["strength"].map(lambda s: format(float(s), ".12g") if re.fullmatch(r"\d+(\.\d+)?", s) else s)
    frame["application_type"] = frame["application_type"].fillna("Unknown").str.strip().str.upper()
    # No alphabetical splitting/sorting of multi-ingredient strength strings:
    # their correspondence is not safely inferable from free text.
    descriptor = [x for x in frame.columns if x not in ["product_ndc", "product_key"]]
    distinct = frame.drop_duplicates(["product_key"] + descriptor)
    conflicts = distinct.loc[distinct["product_key"].notna() & distinct.duplicated("product_key", keep=False)].copy()
    conflict_keys = set(conflicts["product_key"])
    directory = distinct.loc[distinct["product_key"].notna() & ~distinct["product_key"].isin(conflict_keys)].copy()
    audit = {"directory_records": len(raw), "invalid_directory_keys": int(frame["product_key"].isna().sum()),
             "unique_directory_keys": int(frame["product_key"].nunique()),
             "conflicting_directory_keys": len(conflict_keys), "unambiguous_directory_keys": len(directory),
             "identical_descriptor_duplicates_collapsed": len(frame) - len(distinct)}
    return directory, conflicts, audit


def attach_metadata(utilization: pd.DataFrame, directory: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    merged = utilization.merge(directory, on="product_key", how="left", validate="many_to_one", indicator=True)
    assert len(merged) == len(utilization), "Join changed the observation count"
    assert np.isclose(merged["reimbursement"].sum(), utilization["reimbursement"].sum()), "Join changed spending"
    unmatched = merged["_merge"].eq("left_only")
    eligible = merged["spend_eligible"]
    total = merged.loc[eligible, "reimbursement"].sum()
    audit = {"join_output_records": len(merged), "unmatched_records": int(unmatched.sum()),
             "unmatched_spend_eligible_records": int((unmatched & eligible).sum()),
             "unmatched_reimbursement": float(merged.loc[unmatched & eligible, "reimbursement"].sum()),
             "matched_spending_share": float(merged.loc[~unmatched & eligible, "reimbursement"].sum() / total) if total else 0}
    merged["metadata_matched"] = ~unmatched
    return merged.drop(columns="_merge"), audit
