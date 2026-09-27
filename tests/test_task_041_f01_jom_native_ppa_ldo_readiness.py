from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f01_jom_native_ppa_ldo_readiness import (
    Task041Error,
    validate_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E41 = ROOT / "docs/evidence/TASK_041_F01_JOM_NATIVE_PPA_LDO_READINESS_REVIEW_0.8.0.json"
E40 = ROOT / "docs/evidence/TASK_040_LOA_SCOPED_SILVER_CREATE_ONLY_READBACK_0.8.0.json"


class Task041ReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e41 = json.loads(E41.read_text(encoding="utf-8"))
        cls.e40 = json.loads(E40.read_text(encoding="utf-8"))

    def validate(self, e41=None, e40=None):
        return validate_evidence(copy.deepcopy(e41 or self.e41), copy.deepcopy(e40 or self.e40))

    def test_canonical_evidence_passes(self):
        result = self.validate()
        self.assertEqual(result["status"], "PASS_TASK041_JOM_NATIVE_PPA_LDO_SCOPED_SILVER_CANDIDATES_READY_NO_WRITE")
        self.assertEqual(result["ppa_boundary"], "JOM_PAGES_5_64")
        self.assertEqual(result["ldo_boundary"], "JOM_PAGES_5_38")
        self.assertEqual(result["loa_status"], "SILVER_SCOPED_PARTIAL_VALIDATED")
        self.assertFalse(result["new_remote_write"])

    def assert_stop(self, mutate, expected_code):
        data = copy.deepcopy(self.e41)
        mutate(data)
        with self.assertRaisesRegex(Task041Error, expected_code):
            validate_evidence(data, copy.deepcopy(self.e40))

    def test_base_sha_is_pinned(self):
        self.assert_stop(lambda d: d.__setitem__("base_sha", "0" * 40), "BASE_SHA_MISMATCH")

    def test_ppa_source_hash_cannot_drift(self):
        self.assert_stop(lambda d: d["ppa_candidate"]["source"].__setitem__("sha256", "0" * 64), "PPA_SOURCE_PIN_MISMATCH")

    def test_ppa_boundary_cannot_expand(self):
        self.assert_stop(lambda d: d["ppa_candidate"]["legal_instrument"].__setitem__("law_page_end", 65), "PPA_PRIMARY_JOM_BOUNDARY_MISMATCH")

    def test_ldo_old_5_41_boundary_cannot_return(self):
        def mutate(d):
            d["ldo_candidate"]["legal_instrument"]["law_page_end"] = 41
            d["ldo_candidate"]["legal_instrument"]["law_page_count"] = 37
        self.assert_stop(mutate, "LDO_PRIMARY_JOM_BOUNDARY_MISMATCH")

    def test_ldo_marker_must_remain_found(self):
        self.assert_stop(lambda d: d["ldo_candidate"]["structural_markers"][0].__setitem__("found", False), "LDO_REQUIRED_MARKER_MISSING")

    def test_ppa_indicator_target_drift_stops(self):
        self.assert_stop(lambda d: d["ppa_candidate"]["program_2001"]["indicator"].__setitem__("2029", 60), "PPA_EITI_INDICATOR_OR_TARGET_DRIFT")

    def test_ppa_selected_action_value_drift_stops(self):
        self.assert_stop(lambda d: d["ppa_candidate"]["program_2001"]["selected_actions"][2].__setitem__("total", 119807), "PPA_SELECTED_ACTION_VALUE_DRIFT")

    def test_ppa_selected_action_cannot_become_eiti_specific(self):
        self.assert_stop(lambda d: d["ppa_candidate"]["program_2001"]["selected_actions"][0].__setitem__("eiti_specific", True), "PPA_ACTION_EITI_SCOPE_WEAKENED")

    def test_ambiguous_ppa_row_cannot_be_promoted(self):
        self.assert_stop(lambda d: d["ppa_candidate"]["program_2001"]["excluded_review_rows"][0].__setitem__("promoted", True), "PPA_AMBIGUOUS_ROW_PROMOTED")

    def test_complete_parse_claims_are_forbidden(self):
        self.assert_stop(lambda d: d["ppa_candidate"]["guardrails"].__setitem__("complete_ppa_parse_claim", True), "PPA_GUARDRAIL_COMPLETE_PPA_PARSE_CLAIM_WEAKENED")
        self.assert_stop(lambda d: d["ldo_candidate"]["guardrails"].__setitem__("complete_ldo_parse_claim", True), "LDO_GUARDRAIL_COMPLETE_LDO_PARSE_CLAIM_WEAKENED")

    def test_financial_identity_cannot_be_claimed(self):
        self.assert_stop(lambda d: d["ppa_candidate"]["guardrails"].__setitem__("eiti_financial_identity", "FINANCIAL_IDENTITY_PROVEN"), "PPA_EITI_IDENTITY_WEAKENED")

    def test_no_new_silver_write_or_downstream_promotion(self):
        self.assert_stop(lambda d: d["observed_effects"].__setitem__("drive_writes", 1), "TASK041_EFFECT_DRIVE_WRITES_NONZERO")
        self.assert_stop(lambda d: d["promotion"].__setitem__("ppa_silver", True), "TASK041_NEW_SILVER_PROMOTION_FORBIDDEN")
        self.assert_stop(lambda d: d["promotion"].__setitem__("gold", True), "TASK041_GOLD_PROMOTION_FORBIDDEN")

    def test_task040_existing_loa_silver_is_required(self):
        e40 = copy.deepcopy(self.e40)
        e40["promotion"]["f01_status"] = "NOT_SILVER"
        with self.assertRaisesRegex(Task041Error, "TASK040_F01_STATUS_MISMATCH"):
            validate_evidence(copy.deepcopy(self.e41), e40)


if __name__ == "__main__":
    unittest.main()
