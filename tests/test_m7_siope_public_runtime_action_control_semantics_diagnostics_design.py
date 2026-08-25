from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_runtime_action_control_semantics_diagnostics_design import (
    SiopePublicRuntimeActionControlSemanticsDesignError,
    load_json,
    validate_design,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_action_control_semantics_diagnostics_design.json"


class TestM7SiopePublicRuntimeActionControlSemanticsDiagnosticsDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.review = load_json(ROOT / cls.config["prerequisite_review_config_path"])
        cls.public = load_json(ROOT / cls.config["public_runtime_config_path"])

    def test_design_targets_only_acao_with_boolean_relations(self):
        result = validate_design(self.config, self.review, self.public)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_DIAGNOSTICS_DESIGN")
        self.assertEqual(result["target_control_name"], "acao")
        self.assertEqual(result["target_control_structure"], "HIDDEN_INPUT_STRUCTURALLY_OBSERVED")
        self.assertEqual(result["observation_mode"], "PASSIVE_NO_INTERACTION_BOOLEAN_RELATIONS_ONLY")
        self.assertFalse(result["actual_values_may_leave_browser"])
        self.assertFalse(result["dom_interaction_authorized"])
        self.assertFalse(result["control_mutation_authorized"])
        self.assertFalse(result["post_authorized"])

    def test_return_scope_has_only_boolean_semantic_relations(self):
        result = validate_design(self.config, self.review, self.public)
        self.assertEqual(result["returned_boolean_fields"], [
            "control_present", "control_is_hidden_input", "query_key_present", "value_attribute_present",
            "property_equals_query", "attribute_equals_query", "property_equals_attribute",
        ])
        self.assertEqual(result["observation_points"], ["STABLE_SURFACE_FIRST_OBSERVATION", "PASSIVE_CAPTURE_WINDOW_FINAL_OBSERVATION"])

    def test_values_scripts_interaction_and_post_cannot_be_opened(self):
        for key in (
            "actual_control_value_return", "actual_query_value_return", "actual_attribute_value_return",
            "script_source_capture", "dom_interaction", "control_mutation", "form_submission", "post_request",
            "pilot_limeira_values_send", "automatic_value_promotion", "route_synthesis_or_guessing",
        ):
            config = copy.deepcopy(self.config)
            config[key] = "ALLOWED"
            with self.assertRaises(SiopePublicRuntimeActionControlSemanticsDesignError, msg=key):
                validate_design(config, self.review, self.public)

    def test_review_must_have_exact_single_acao_mismatch(self):
        review = copy.deepcopy(self.review)
        review["mismatched_control_names"] = ["acao", "pag"]
        with self.assertRaisesRegex(SiopePublicRuntimeActionControlSemanticsDesignError, "REVIEW_MISMATCH_SCOPE"):
            validate_design(self.config, review, self.public)

    def test_review_must_keep_acao_semantics_unproven(self):
        review = copy.deepcopy(self.review)
        review["acao_value_semantics_status"] = "PROVEN"
        with self.assertRaisesRegex(SiopePublicRuntimeActionControlSemanticsDesignError, "REVIEW_ACAO_SEMANTICS"):
            validate_design(self.config, review, self.public)

    def test_public_example_must_stay_non_pilot(self):
        public = copy.deepcopy(self.public)
        public["public_indexed_example_url"] += "&sentinel=352690"
        with self.assertRaisesRegex(SiopePublicRuntimeActionControlSemanticsDesignError, "PUBLIC_CONFIG_PILOT_VALUE"):
            validate_design(self.config, self.review, public)

    def test_design_code_is_offline(self):
        module = (ROOT / "robo_dados_publicos" / "sources" / "siope_public_runtime_action_control_semantics_diagnostics_design.py").read_text(encoding="utf-8")
        script = (ROOT / "scripts" / "github_siope_public_runtime_action_control_semantics_diagnostics_design_gate.py").read_text(encoding="utf-8")
        combined = module + "\n" + script
        for forbidden in ("import requests", "from requests", "import urllib", "from urllib", "import websocket", "from websocket", "Page.navigate", "Fetch.enable"):
            self.assertNotIn(forbidden, combined)


if __name__ == "__main__":
    unittest.main()
