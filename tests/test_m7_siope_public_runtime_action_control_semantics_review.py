from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_runtime_action_control_semantics_review import (
    SiopePublicRuntimeActionControlSemanticsReviewError,
    load_json,
    review_action_control_semantics,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_action_control_semantics_review.json"


class TestM7SiopePublicRuntimeActionControlSemanticsReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.evidence = load_json(ROOT / cls.config["evidence_path"])

    def test_exact_evidence_passes_with_stable_internal_mismatch(self):
        result = review_action_control_semantics(self.config, self.evidence)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_REVIEW")
        self.assertEqual(result["relation_stability_status"], "STABLE_ACROSS_OBSERVED_WINDOW")
        self.assertEqual(result["internal_consistency_status"], "PROPERTY_EQUALS_ATTRIBUTE_ON_BOTH_OBSERVATIONS")
        self.assertEqual(result["query_equivalence_status"], "PROPERTY_AND_ATTRIBUTE_DIFFER_FROM_QUERY_ON_BOTH_OBSERVATIONS")
        self.assertEqual(result["value_origin_status"], "UNPROVEN")
        self.assertFalse(result["post_authorized"])
        self.assertFalse(result["automatic_value_promotion"])

    def test_any_runtime_relation_change_fails_closed(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["result"]["boolean_relation_state_changed"] = True
        with self.assertRaisesRegex(SiopePublicRuntimeActionControlSemanticsReviewError, "RELATION_STATE_CHANGED"):
            review_action_control_semantics(self.config, evidence)

    def test_query_equivalence_cannot_be_silently_promoted(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["result"]["final_observation"]["property_equals_query"] = True
        with self.assertRaisesRegex(SiopePublicRuntimeActionControlSemanticsReviewError, "FINAL_OBSERVATION"):
            review_action_control_semantics(self.config, evidence)

    def test_value_material_or_operational_actions_fail_closed(self):
        for key in (
            "actual_control_value_returned",
            "actual_query_value_returned",
            "actual_attribute_value_returned",
            "dom_interaction_performed",
            "control_mutation_performed",
            "form_submission",
            "post_request_performed",
            "pilot_limeira_values_sent",
            "dynamic_candidate_network_sent",
            "automatic_value_promotion",
            "collection_authorized",
            "processing_authorized",
            "recurrence_authorized",
            "schedule_enabled",
        ):
            evidence = copy.deepcopy(self.evidence)
            evidence["result"][key] = True
            with self.assertRaises(SiopePublicRuntimeActionControlSemanticsReviewError, msg=key):
                review_action_control_semantics(self.config, evidence)

    def test_identity_and_artifact_are_pinned(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["artifact"]["digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(SiopePublicRuntimeActionControlSemanticsReviewError, "ARTIFACT_DIGEST"):
            review_action_control_semantics(self.config, evidence)

    def test_review_code_is_offline_and_does_not_embed_pilot_request(self):
        module = (ROOT / "robo_dados_publicos" / "sources" / "siope_public_runtime_action_control_semantics_review.py").read_text(encoding="utf-8")
        script = (ROOT / "scripts" / "github_siope_public_runtime_action_control_semantics_review_gate.py").read_text(encoding="utf-8")
        combined = module + "\n" + script
        for forbidden in ("import requests", "from requests", "import urllib", "from urllib", "import websocket", "from websocket", "Page.navigate", "Fetch.enable", "cod_muni=352690"):
            self.assertNotIn(forbidden, combined)

    def test_next_gate_is_partition_design_not_post_or_pilot(self):
        result = review_action_control_semantics(self.config, self.evidence)
        self.assertEqual(result["next_gate"], "M7_SIOPE_PUBLIC_RUNTIME_QUERY_EQUIVALENCE_PARTITION_DESIGN_0_8_0")
        self.assertFalse(result["pilot_limeira_values_sent"])
        self.assertFalse(result["route_synthesized_or_guessed"])


if __name__ == "__main__":
    unittest.main()
