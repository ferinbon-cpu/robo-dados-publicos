from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_runtime_control_value_consistency_review import (
    SiopePublicRuntimeControlValueConsistencyReviewError,
    load_json,
    review_public_runtime_control_value_consistency,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_control_value_consistency_review.json"


class TestM7SiopePublicRuntimeControlValueConsistencyReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.evidence = load_json(ROOT / cls.config["evidence_path"])
        cls.inventory = load_json(ROOT / cls.config["inventory_evidence_path"])

    def test_review_accepts_exact_seven_match_one_mismatch_evidence(self):
        result = review_public_runtime_control_value_consistency(self.config, self.evidence, self.inventory)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_REVIEW")
        self.assertEqual(result["matched_control_names"], ["admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"])
        self.assertEqual(result["mismatched_control_names"], ["acao"])
        self.assertEqual(result["acao_control_structure"], "HIDDEN_INPUT_STRUCTURALLY_OBSERVED")
        self.assertEqual(result["acao_value_semantics_status"], "UNPROVEN_MISMATCH_ON_PINNED_PUBLIC_EXAMPLE")
        self.assertEqual(result["overall_value_mapping_status"], "PARTIAL_7_OF_8_PINNED_EXAMPLE_ONLY")
        self.assertFalse(result["post_authorized"])
        self.assertFalse(result["dom_interaction_authorized"])
        self.assertFalse(result["pilot_limeira_values_sent"])
        self.assertEqual(result["next_gate"], "M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_DIAGNOSTICS_DESIGN_0_8_0")

    def test_mismatch_is_not_silently_promoted_or_corrected(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["result"]["comparison_results"][0]["value_matches_query"] = True
        evidence["result"]["all_values_match_query"] = True
        with self.assertRaises(SiopePublicRuntimeControlValueConsistencyReviewError):
            review_public_runtime_control_value_consistency(self.config, evidence, self.inventory)

    def test_second_mismatch_fails_closed(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["result"]["comparison_results"][1]["value_matches_query"] = False
        with self.assertRaisesRegex(SiopePublicRuntimeControlValueConsistencyReviewError, "MATCHED_CONTROLS"):
            review_public_runtime_control_value_consistency(self.config, evidence, self.inventory)

    def test_actual_values_or_operational_actions_fail_closed(self):
        for key in ("actual_control_values_returned", "actual_query_values_returned", "dom_interaction_performed", "form_submission", "post_request_performed", "pilot_limeira_values_sent"):
            evidence = copy.deepcopy(self.evidence)
            evidence["result"][key] = True
            with self.assertRaises(SiopePublicRuntimeControlValueConsistencyReviewError, msg=key):
                review_public_runtime_control_value_consistency(self.config, evidence, self.inventory)

    def test_acao_must_remain_structurally_hidden_input(self):
        inventory = copy.deepcopy(self.inventory)
        inventory["result"]["controls_structural_summary"][0]["type"] = "text"
        with self.assertRaisesRegex(SiopePublicRuntimeControlValueConsistencyReviewError, "ACAO_STRUCTURE"):
            review_public_runtime_control_value_consistency(self.config, self.evidence, inventory)

    def test_run_and_artifact_identity_are_pinned(self):
        for target, key, value in (("run", "id", 1), ("run", "head_sha", "bad"), ("artifact", "id", 1), ("artifact", "digest", "bad")):
            evidence = copy.deepcopy(self.evidence)
            evidence[target][key] = value
            with self.assertRaises(SiopePublicRuntimeControlValueConsistencyReviewError):
                review_public_runtime_control_value_consistency(self.config, evidence, self.inventory)

    def test_review_code_is_offline(self):
        module = (ROOT / "robo_dados_publicos" / "sources" / "siope_public_runtime_control_value_consistency_review.py").read_text(encoding="utf-8")
        script = (ROOT / "scripts" / "github_siope_public_runtime_control_value_consistency_review_gate.py").read_text(encoding="utf-8")
        combined = module + "\n" + script
        for forbidden in ("import requests", "from requests", "import urllib", "from urllib", "import websocket", "from websocket", "Page.navigate", "Fetch.enable"):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
