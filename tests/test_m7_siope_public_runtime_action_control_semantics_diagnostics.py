from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_runtime_action_control_semantics_diagnostics import (
    SiopePublicRuntimeActionControlSemanticsDiagnosticsError,
    diagnose_action_control_semantics,
    load_json,
    sanitize_snapshot,
    validate_diagnostics_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_action_control_semantics_diagnostics.json"


class FakeRuntime:
    def __init__(self, first=None, final=None, **overrides):
        base = {
            "control_present": True,
            "control_is_hidden_input": True,
            "query_key_present": True,
            "value_attribute_present": True,
            "property_equals_query": False,
            "attribute_equals_query": False,
            "property_equals_attribute": True,
        }
        self.payload = {
            "page_surface_verified": True,
            "human_challenge_active_dom": False,
            "initial_document_continued_count": 1,
            "initial_document_network_sent": True,
            "static_assets_continued_count": 3,
            "local_requests_continued_count": 0,
            "blocked_requests": [],
            "browser_download_denied": True,
            "dom_interaction_performed": False,
            "control_mutation_performed": False,
            "form_submission": False,
            "post_request_performed": False,
            "navigation_after_initial_document": False,
            "dynamic_candidate_network_sent": False,
            "raw_first_snapshot": first or base,
            "raw_final_snapshot": final or base,
        }
        self.payload.update(overrides)

    def run_semantics(self, config, public_config):
        return copy.deepcopy(self.payload)


class TestM7SiopePublicRuntimeActionControlSemanticsDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.public = load_json(ROOT / cls.config["public_runtime_config_path"])
        cls.design = load_json(ROOT / cls.config["design_config_path"])

    def test_config_is_exact_and_keeps_actions_closed(self):
        validate_diagnostics_config(self.config, self.public, self.design)
        self.assertEqual(self.config["target_control_name"], "acao")
        self.assertEqual(self.config["post_request"], "PROHIBITED")
        self.assertEqual(self.config["control_mutation"], "PROHIBITED")
        self.assertEqual(self.config["pilot_limeira_values_send"], "PROHIBITED")

    def test_fake_pass_returns_only_boolean_semantic_snapshots(self):
        result = diagnose_action_control_semantics(self.config, self.public, self.design, runtime=FakeRuntime())
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_RUNTIME_ACTION_CONTROL_SEMANTICS_DIAGNOSTICS")
        self.assertEqual(result["target_control_name"], "acao")
        self.assertFalse(result["first_observation"]["property_equals_query"])
        self.assertTrue(result["first_observation"]["property_equals_attribute"])
        self.assertFalse(result["boolean_relation_state_changed"])
        self.assertFalse(result["actual_control_value_returned"])
        self.assertFalse(result["actual_query_value_returned"])
        self.assertFalse(result["actual_attribute_value_returned"])
        self.assertFalse(result["dom_interaction_performed"])
        self.assertFalse(result["post_request_performed"])
        self.assertFalse(result["pilot_limeira_values_sent"])

    def test_boolean_state_change_is_observable_without_values(self):
        final = {
            "control_present": True,
            "control_is_hidden_input": True,
            "query_key_present": True,
            "value_attribute_present": True,
            "property_equals_query": False,
            "attribute_equals_query": False,
            "property_equals_attribute": False,
        }
        result = diagnose_action_control_semantics(self.config, self.public, self.design, runtime=FakeRuntime(final=final))
        self.assertTrue(result["boolean_relation_state_changed"])

    def test_snapshot_rejects_extra_value_material(self):
        raw = {key: False for key in self.config["returned_boolean_fields"]}
        raw["actual_value"] = "secret"
        with self.assertRaisesRegex(SiopePublicRuntimeActionControlSemanticsDiagnosticsError, "SNAPSHOT_FIELDS"):
            sanitize_snapshot(raw, self.config)

    def test_missing_or_wrong_control_structure_fails_closed(self):
        for field in ("control_present", "control_is_hidden_input", "query_key_present"):
            first = {key: True for key in self.config["returned_boolean_fields"]}
            first[field] = False
            with self.assertRaises(SiopePublicRuntimeActionControlSemanticsDiagnosticsError, msg=field):
                diagnose_action_control_semantics(self.config, self.public, self.design, runtime=FakeRuntime(first=first))

    def test_network_interaction_and_challenge_flags_fail_closed(self):
        for key, value in (
            ("dom_interaction_performed", True), ("control_mutation_performed", True),
            ("form_submission", True), ("post_request_performed", True),
            ("navigation_after_initial_document", True), ("dynamic_candidate_network_sent", True),
            ("human_challenge_active_dom", True),
        ):
            with self.assertRaises(SiopePublicRuntimeActionControlSemanticsDiagnosticsError, msg=key):
                diagnose_action_control_semantics(self.config, self.public, self.design, runtime=FakeRuntime(**{key: value}))

    def test_expression_does_not_embed_limeira_or_return_value_fields(self):
        source = (ROOT / "robo_dados_publicos" / "sources" / "siope_public_runtime_action_control_semantics_diagnostics.py").read_text(encoding="utf-8")
        self.assertNotIn("cod_muni=352690", source)
        self.assertNotIn('"actual_value":', source)
        self.assertNotIn("innerHTML", source)
        self.assertNotIn("outerHTML", source)


if __name__ == "__main__":
    unittest.main()
