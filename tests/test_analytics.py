"""Tests for material failure modes: join inflation, unit weighting and eligibility."""
import unittest

import pandas as pd

from medicaid_analytics.compare import reimbursement_gaps
from medicaid_analytics.prepare import attach_metadata, ndc_product_key, normalize_text, prepare_directory, prepare_utilization


class PreparationTests(unittest.TestCase):
    def test_conflicting_directory_keys_are_not_silently_first_matched(self):
        base = {"PRODUCTNDC": "0002-0152", "PROPRIETARYNAME": "Test", "NONPROPRIETARYNAME": "drug",
                "DOSAGEFORMNAME": "TABLET", "ROUTENAME": "ORAL", "ACTIVE_NUMERATOR_STRENGTH": "10",
                "ACTIVE_INGRED_UNIT": "mg/1", "MARKETINGCATEGORYNAME": "NDA", "PHARM_CLASSES": "Class [EPC]",
                "STARTMARKETINGDATE": "20200101", "ENDMARKETINGDATE": None, "LABELERNAME": "Company",
                "PRODUCTTYPENAME": "HUMAN PRESCRIPTION DRUG"}
        conflicting = dict(base, ACTIVE_NUMERATOR_STRENGTH="20")
        directory, conflicts, audit = prepare_directory(pd.DataFrame([base, conflicting]))
        self.assertTrue(directory.empty)
        self.assertEqual(len(conflicts), 2)
        self.assertEqual(audit["conflicting_directory_keys"], 1)

    def test_identical_directory_descriptors_collapse_safely(self):
        base = {"PRODUCTNDC": "0002-0152", "PROPRIETARYNAME": "Test", "NONPROPRIETARYNAME": "drug",
                "DOSAGEFORMNAME": "TABLET", "ROUTENAME": "ORAL", "ACTIVE_NUMERATOR_STRENGTH": "10",
                "ACTIVE_INGRED_UNIT": "mg/1", "MARKETINGCATEGORYNAME": "NDA", "PHARM_CLASSES": "Class [EPC]",
                "STARTMARKETINGDATE": "20200101", "ENDMARKETINGDATE": None, "LABELERNAME": "Company",
                "PRODUCTTYPENAME": "HUMAN PRESCRIPTION DRUG"}
        directory, conflicts, audit = prepare_directory(pd.DataFrame([base, base]))
        self.assertEqual(len(directory), 1)
        self.assertTrue(conflicts.empty)
        self.assertEqual(audit["identical_descriptor_duplicates_collapsed"], 1)

    def test_segment_aware_ndc_normalization(self):
        self.assertEqual(ndc_product_key("0002-0152"), "000020152")
        self.assertEqual(ndc_product_key("12345-123"), "123450123")
        self.assertIsNone(ndc_product_key("1234567890"))
        self.assertIsNone(ndc_product_key("123456-1234"))

    def test_names_preserve_salts_and_release_descriptors(self):
        self.assertEqual(normalize_text("  METOPROLOL   SUCCINATE "), "metoprolol succinate")
        self.assertNotEqual(normalize_text("metoprolol tartrate"), normalize_text("metoprolol succinate"))
        self.assertNotEqual(normalize_text("tablet, extended release"), normalize_text("tablet"))

    def test_suppression_and_duplicate_grain_are_quarantined(self):
        data = pd.DataFrame({
            "source_row": [2, 3, 4, 5, 6], "Utilization Type": ["MCOU"] * 5,
            "State": ["CA"] * 5, "NDC": ["00002015204"] * 5,
            "Year": [2024] * 5, "Quarter": [1, 2, 3, 4, 4],
            "Suppression Used": [0, 1, 0, 0, 0], "Product Name": ["test"] * 5,
            "Units Reimbursed": [2, None, 0, 1, 1], "Number of Prescriptions": [1, None, 1, 1, 1],
            "Medicaid Amount Reimbursed": [10, None, 20, 5, 5],
        })
        prepared, audit = prepare_utilization(data)
        self.assertEqual(audit["spend_eligible_records"], 2)
        self.assertEqual(audit["price_eligible_records"], 1)
        self.assertEqual(audit["duplicate_grain_records_quarantined"], 2)
        self.assertEqual(audit["observed_pre_rebate_reimbursement"], 30)
        self.assertTrue(pd.isna(prepared.loc[1, "reimbursement"]))

    def test_join_rejects_duplicate_dimension_keys(self):
        observations = pd.DataFrame({"product_key": ["000020152"], "reimbursement": [100], "spend_eligible": [True]})
        directory = pd.DataFrame({"product_key": ["000020152", "000020152"], "ingredient": ["a", "b"]})
        with self.assertRaises(pd.errors.MergeError):
            attach_metadata(observations, directory)

    def test_left_join_preserves_unmatched_spending(self):
        observations = pd.DataFrame({"product_key": ["a", "b"], "reimbursement": [100, 50], "spend_eligible": [True, True]})
        directory = pd.DataFrame({"product_key": ["a"], "ingredient": ["a"]})
        joined, audit = attach_metadata(observations, directory)
        self.assertEqual(len(joined), 2)
        self.assertEqual(joined.reimbursement.sum(), 150)
        self.assertEqual(audit["unmatched_reimbursement"], 50)


class GapTests(unittest.TestCase):
    def fixture(self):
        return pd.DataFrame({
            "source_row": [2, 3, 4, 5], "ingredient": ["drug"] * 4,
            "dosage_form": ["tablet"] * 4, "route": ["oral"] * 4,
            "strength": ["10"] * 4, "strength_unit": ["mg/1"] * 4,
            "state": ["AZ"] * 4, "quarter": [1] * 4, "utilization_type": ["MCOU"] * 4,
            "product_key": ["a", "b", "c", "d"], "application_type": ["NDA", "NDA", "ANDA", "ANDA"],
            "units": [1, 9, 2, 8], "reimbursement": [100, 90, 20, 8],
            "price_eligible": [True] * 4, "metadata_matched": [True] * 4,
            "marketing_start": [20200101] * 4, "marketing_end": [None] * 4,
            "product_type": ["HUMAN PRESCRIPTION DRUG"] * 4,
        })

    def test_weighted_price_is_ratio_of_sums(self):
        result, audit = reimbursement_gaps(self.fixture())
        self.assertAlmostEqual(result.iloc[0].nda_weighted_cpu, 19)
        self.assertAlmostEqual(result.iloc[0].anda_weighted_cpu, 2.8)
        self.assertAlmostEqual(audit["illustrative_positive_gross_gap"], 162)

    def test_different_strengths_are_not_compared(self):
        data = self.fixture()
        data.loc[data.application_type.eq("ANDA"), "strength"] = "20"
        result, _ = reimbursement_gaps(data)
        self.assertTrue(result.empty)

    def test_different_states_are_not_compared(self):
        data = self.fixture()
        data.loc[data.application_type.eq("ANDA"), "state"] = "CA"
        result, _ = reimbursement_gaps(data)
        self.assertTrue(result.empty)

    def test_future_marketing_date_cannot_supply_comparator(self):
        data = self.fixture()
        data.loc[data.application_type.eq("ANDA"), "marketing_start"] = 20240401
        result, _ = reimbursement_gaps(data)
        self.assertTrue(result.empty)

    def test_negative_gaps_are_reported_but_not_positive_opportunities(self):
        data = self.fixture()
        data.loc[data.application_type.eq("ANDA"), "reimbursement"] = [500, 500]
        result, audit = reimbursement_gaps(data)
        self.assertLess(result.iloc[0].signed_gross_gap, 0)
        self.assertEqual(audit["illustrative_positive_gross_gap"], 0)
        self.assertEqual(audit["negative_gap_strata"], 1)


if __name__ == "__main__":
    unittest.main()
