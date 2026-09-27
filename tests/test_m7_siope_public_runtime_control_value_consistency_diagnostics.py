from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_runtime_control_value_consistency_diagnostics import (
    SiopePublicRuntimeControlValueConsistencyDiagnosticsError,
    _comparison_expression,
    diagnose_control_value_consistency,
    load_json,
    sanitize_comparisons,
    validate_diagnostics_config,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_control_value_consistency_diagnostics.json"


class FakeRuntime:
    def __init__(self, *, comparisons=None, blocked=None, **overrides):
        self.comparisons = comparisons
        self.blocked = blocked or []
        self.overrides = overrides

    def run_consistency(self, config, public_config):
        comparisons = self.comparisons
        if comparisons is None:
            comparisons = [
                {"control_name": name, "control_present": True, "query_key_present": True, "value_matches_query": True}
                for name in config["comparison_control_names"]
            ]
        payload = {
            "page_surface_verified": True,
            "initial_document_network_sent": True,
            "initial_document_continued_count": 1,
            "browser_download_denied": True,
            "dom_interaction_performed": False,
            "form_submission": False,
            "navigation_after_initial_document": False,
            "dynamic_candidate_network_sent": False,
            "human_challenge_active_dom": False,
            "static_assets_continued_count": 3,
            "local_requests_continued_count": 0,
            "blocked_requests": self.blocked,
            "raw_comparisons": comparisons,
            "browser_binary_name": "google-chrome",
            "browser_version": "fake",
        }
        payload.update(self.overrides)
        return payload


class TestM7SiopePublicRuntimeControlValueConsistencyDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.public = load_json(ROOT / cls.config["public_runtime_config_path"])
        cls.design = load_json(ROOT / cls.config["design_config_path"])

    def test_config_is_pinned_to_boolean_design_and_keeps_operations_closed(self):
        validate_diagnostics_config(self.config, self.public, self.design)
        self.assertEqual(self.config["comparison_result"], "BOOLEAN_ONLY")
        for key in (
            "actual_control_value_return", "actual_query_value_return", "option_text_return", "option_value_return",
            "html_return", "free_text_return", "dom_interaction", "form_submission", "post_request",
            "pilot_limeira_values_send", "dynamic_candidate_network_send", "authentication", "captcha_bypass",
            "request_body_capture", "response_body_capture", "query_value_persistence", "artifact_download", "remote_writes",
        ):
            self.assertEqual(self.config[key], "PROHIBITED")

    def test_pass_returns_only_boolean_comparisons_and_authorizes_nothing(self):
        result = diagnose_control_value_consistency(self.config, self.public, self.design, runtime=FakeRuntime())
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS")
        self.assertEqual(result["comparison_count"], 8)
        self.assertTrue(result["all_controls_present"])
        self.assertTrue(result["all_query_keys_present"])
        self.assertTrue(result["all_values_match_query"])
        self.assertTrue(result["comparison_result_boolean_only"])
        self.assertFalse(result["actual_control_values_returned"])
        self.assertFalse(result["actual_query_values_returned"])
        self.assertFalse(result["dom_interaction_performed"])
        self.assertFalse(result["form_submission"])
        self.assertFalse(result["post_request_performed"])
        self.assertFalse(result["pilot_limeira_values_sent"])
        self.assertFalse(result["collection_authorized"])
        for row in result["comparison_results"]:
            self.assertEqual(set(row), {"control_name", "control_present", "query_key_present", "value_matches_query"})
            self.assertIsInstance(row["control_present"], bool)
            self.assertIsInstance(row["query_key_present"], bool)
            self.assertIsInstance(row["value_matches_query"], bool)

    def test_mismatch_is_diagnostic_not_network_or_post_authorization(self):
        comparisons = [
            {"control_name": name, "control_present": True, "query_key_present": True, "value_matches_query": index != 2}
            for index, name in enumerate(self.config["comparison_control_names"])
        ]
        result = diagnose_control_value_consistency(
            self.config, self.public, self.design, runtime=FakeRuntime(comparisons=comparisons)
        )
        self.assertFalse(result["all_values_match_query"])
        self.assertFalse(result["post_request_performed"])
        self.assertFalse(result["collection_authorized"])
        self.assertEqual(result["next_gate"], "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_REVIEW_0_8_0")

    def test_unexpected_comparison_field_fails_closed(self):
        rows = [
            {"control_name": name, "control_present": True, "query_key_present": True, "value_matches_query": True}
            for name in self.config["comparison_control_names"]
        ]
        rows[0]["value"] = "forbidden"
        with self.assertRaisesRegex(SiopePublicRuntimeControlValueConsistencyDiagnosticsError, "UNEXPECTED_FIELD"):
            sanitize_comparisons(rows, self.config)

    def test_wrong_name_or_count_fails_closed(self):
        rows = [
            {"control_name": name, "control_present": True, "query_key_present": True, "value_matches_query": True}
            for name in self.config["comparison_control_names"]
        ]
        with self.assertRaisesRegex(SiopePublicRuntimeControlValueConsistencyDiagnosticsError, "COMPARISON_COUNT"):
            sanitize_comparisons(rows[:-1], self.config)
        bad = copy.deepcopy(rows)
        bad[0]["control_name"] = "other"
        with self.assertRaisesRegex(SiopePublicRuntimeControlValueConsistencyDiagnosticsError, "COMPARISON_NAME"):
            sanitize_comparisons(bad, self.config)

    def test_any_interaction_submit_second_navigation_or_dynamic_send_fails_closed(self):
        for key in ("dom_interaction_performed", "form_submission", "navigation_after_initial_document", "dynamic_candidate_network_sent"):
            with self.assertRaises(SiopePublicRuntimeControlValueConsistencyDiagnosticsError, msg=key):
                diagnose_control_value_consistency(
                    self.config, self.public, self.design, runtime=FakeRuntime(**{key: True})
                )

    def test_same_host_xhr_candidate_is_blocked_and_stops(self):
        blocked = [{
            "url": "https://www.fnde.gov.br/siope/unproven.do?opaque=redacted",
            "method": "GET",
            "resource_type": "XHR",
        }]
        with self.assertRaisesRegex(SiopePublicRuntimeControlValueConsistencyDiagnosticsError, "UNEXPECTED_DYNAMIC_CANDIDATE"):
            diagnose_control_value_consistency(self.config, self.public, self.design, runtime=FakeRuntime(blocked=blocked))

    def test_browser_expression_returns_no_actual_value_fields(self):
        expression = _comparison_expression(self.config)
        self.assertIn("value_matches_query", expression)
        self.assertIn("String(el.value) === String(params.get(name))", expression)
        self.assertNotIn("actual_control_value", expression)
        self.assertNotIn("actual_query_value", expression)
        self.assertNotIn("option_text", expression)
        self.assertNotIn("option_value", expression)

    def test_public_example_is_non_limeira_and_exact_scope_is_eight(self):
        self.assertNotIn("cod_muni=352690", self.public["public_indexed_example_url"])
        self.assertEqual(self.config["comparison_control_names"], self.public["expected_query_keys"])


if __name__ == "__main__":
    unittest.main()
