import copy
import json
import unittest

from scripts.github_task_010n_r_e_m6_siope_2025_p6_annual_closure_gate import DECISION, EVIDENCE, validate


class Task010NREM6AnnualClosureGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def reject(self, mutation, pattern):
        data = copy.deepcopy(self.data)
        mutation(data)
        with self.assertRaisesRegex(ValueError, pattern):
            validate(data)

    def test_pinned_fail_closed_decision_passes(self):
        self.assertEqual(DECISION, validate(copy.deepcopy(self.data)))

    def test_rejects_p5_or_wrong_identity(self):
        self.reject(lambda d: d["scope"].update(period=5), "P6")
        self.reject(lambda d: d["scope"].update(year=2024), "year")
        self.reject(lambda d: d["scope"].update(municipality_code=350950), "Limeira")

    def test_rejects_missing_or_interpreted_status_field(self):
        self.reject(lambda d: d["candidate_field_inventory"].pop(), "status field")
        self.reject(lambda d: d["candidate_field_inventory"][1].update(official_definition="0 means original"), "undocumented")

    def test_rejects_original_rectifying_date_receipt_or_status_drift(self):
        for field in ("IDN_DECL_RETI", "DAT_DECL", "NUM_RECI", "IDN_TIPO_DECL"):
            with self.subTest(field=field):
                self.reject(lambda d, field=field: next(r for r in d["candidate_field_inventory"] if r["field"] == field).update(observed_value="DRIFT"), "status value")

    def test_rejects_annual_consolidation_alone_as_closure(self):
        self.reject(lambda d: d["closure_proof_model"].update(CURRENTLY_EFFECTIVE_DECLARATION="PROVEN: because P6"), "annual consolidation")

    def test_rejects_rectification_possibility_as_automatic_failure(self):
        self.reject(lambda d: d["guards"].update(rectification_possible_treated_as_automatic_ineffectiveness=True), "guard")

    def test_rejects_undocumented_status_interpretation_or_missing_rule(self):
        self.reject(lambda d: d["candidate_field_inventory"][1].update(currently_effective="PROVEN"), "undocumented")
        self.reject(lambda d: d["official_documentary_sources"].clear(), "source rule")

    def test_rejects_semantic_series_gold_release_and_2026_promotions(self):
        self.reject(lambda d: d["resulting_state"].update(semantic_comparability_status="PROVEN"), "forbidden")
        self.reject(lambda d: d["resulting_state"].update(closed_annual_series="2016-2025"), "forbidden")
        for key, value in (("gold_2025", "PROVEN"), ("release_0_8_0", "ACTIVE"), ("year_2026", "PROVEN"), ("S1_NUM_POPU", "PROVEN"), ("S2_FINANCIAL_ALIAS_BRIDGE", "PROVEN")):
            with self.subTest(key=key):
                self.reject(lambda d, key=key, value=value: d["canonical_state"].update({key: value}), "forbidden")

    def test_rejects_future_immutability_assumption(self):
        self.reject(lambda d: d["guards"].update(future_immutability_assumed=True), "guard")

    def test_rejects_receipt_surface_removal_url_authority_or_proposition_drift(self):
        self.reject(lambda d: d["official_documentary_sources"].pop(), "official source")
        self.reject(lambda d: d["official_documentary_sources"][-1].update(url="https://example.test"), "URL")
        self.reject(lambda d: d["official_documentary_sources"][-1].update(authority="UNKNOWN"), "authority")
        self.reject(lambda d: d["official_documentary_sources"][-1].update(supports="proves finality"), "proposition")

    def test_rejects_receipt_column_drift(self):
        self.reject(lambda d: d["official_documentary_sources"][-1]["receipt_surface_columns"].remove("MAVS"), "column")

    def test_rejects_receipt_status_as_current_or_immutable_finality(self):
        self.reject(lambda d: d["guards"].update(non_retifying_used_as_immutable_finality=True), "guard")
        self.reject(lambda d: d["guards"].update(processing_success_used_as_immutable_finality=True), "guard")
        self.reject(lambda d: d["guards"].update(receipt_row_claimed_current_latest_without_rule=True), "guard")

    def test_rejects_unsupported_no_or_note_only_semantics(self):
        self.reject(lambda d: d["candidate_field_inventory"][-1].update(original_vs_rectifying="NO"), "unsupported")
        self.reject(lambda d: d["candidate_field_inventory"][-2].update(proof_kind="NOTE_ONLY"), "unsupported")

    def test_rejects_documentary_discovery_drift(self):
        self.reject(lambda d: d["documentary_discovery"].update(selection_or_supersession_rule_result="PROVEN"), "documentary")
        self.reject(lambda d: d["documentary_discovery"]["search_terms"].pop(), "documentary")

    def test_rejects_fabricated_limeira_annual_status(self):
        self.reject(lambda d: d["current_observation"].update(performed=True), "fabricated")
        self.reject(lambda d: d["guards"].update(limeira_annual_status_fabricated=True), "guard")


if __name__ == "__main__":
    unittest.main()
