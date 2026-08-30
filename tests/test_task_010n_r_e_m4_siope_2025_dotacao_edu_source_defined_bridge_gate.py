import copy
import json
import unittest

from scripts.github_task_010n_r_e_m4_siope_2025_dotacao_edu_source_defined_bridge_gate import EVIDENCE, validate


class Task010NREM4DotacaoEduSourceDefinedBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def assert_rejected(self, mutate, message):
        evidence = copy.deepcopy(self.evidence)
        mutate(evidence)
        with self.assertRaisesRegex(ValueError, message):
            validate(evidence, verify_files=False)

    def test_pinned_negative_evidence_passes(self):
        self.assertEqual(
            "KEEP_S2_NOT_PROVEN_DOTACAO_EDU_SOURCE_DEFINED_BRIDGE_MISSING",
            validate(copy.deepcopy(self.evidence)),
        )

    def test_rejects_missing_search_term_or_inventory_artifact(self):
        self.assert_rejected(lambda e: e["search_terms"].pop(), "search inventory")
        self.assert_rejected(lambda e: e["inventory"].pop(), "exactly the pinned")
        self.assert_rejected(lambda e: e["inventory"][0].update(sha256="0" * 64), "pinned hash")
        self.assert_rejected(lambda e: e["inventory"].append(copy.deepcopy(e["inventory"][0])), "exactly the pinned")

    def test_rejects_arithmetic_or_candidate_promotion(self):
        self.assert_rejected(lambda e: e["candidate_assessment"][0]["observations"].update(variance="0.00"), "observations")
        self.assert_rejected(lambda e: e["candidate_assessment"][0].update(classification="PROVEN"), "classifications")
        self.assert_rejected(lambda e: e["candidate_assessment"][1].update(insufficiency=""), "insufficiency")
        self.assert_rejected(lambda e: e["field_result"].update(source_defined_current_rule="PROVEN"), "promoted")
        self.assert_rejected(lambda e: e["field_result"].update(promotion_performed=True), "promoted")

    def test_rejects_every_forbidden_state_promotion(self):
        changes = {
            "release_0_8_0": "ACTIVE", "S1_NUM_POPU": "PROVEN",
            "S2_FINANCIAL_ALIAS_BRIDGE": "PROVEN", "annual_closure_status": "PROVEN",
            "semantic_comparability_status": "PROVEN", "closed_annual_series": "2016-2025",
            "gold_2025": "PROVEN", "year_2026": "PROVEN_CURRENT_YEAR",
        }
        for field, value in changes.items():
            with self.subTest(field=field):
                self.assert_rejected(lambda e, field=field, value=value: e["canonical_state"].update({field: value}), "canonical state")

    def test_rejects_network_drive_publication_gold_or_edu_mde(self):
        changes = {"EDU_equals_MDE": True, "network_requests": 1, "drive_reads": 1,
                   "drive_writes": 1, "publication": True, "gold_computation": True}
        for field, value in changes.items():
            with self.subTest(field=field):
                self.assert_rejected(lambda e, field=field, value=value: e["guards"].update({field: value}), "guards")

    def test_rejects_incomplete_next_acquisition_or_decision_change(self):
        self.assert_rejected(lambda e: e["smallest_next_evidence_acquisition"].update(required_artifact=""), "incomplete")
        self.assert_rejected(lambda e: e.update(decision="PROMOTE_VL_DESP_DOTA_ATUA_EDU_SOURCE_DEFINED_BRIDGE"), "decision")


if __name__ == "__main__":
    unittest.main()
