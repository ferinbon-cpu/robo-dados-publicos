from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_runtime_route_diagnostics_design import (
    SiopeOfficialOlindaApiApplicationRouteDiagnosticsDesignError,
    design_application_route_diagnostics,
    load_json,
    validate_design,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_runtime_route_diagnostics_design.json"


class TestM7SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.resource_design = load_json(ROOT / cls.config["resource_contract_design_path"])

    def test_design_passes_offline_and_targets_exact_application_surface(self):
        result = design_application_route_diagnostics(self.config, self.resource_design)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_DESIGN")
        self.assertFalse(result["network_called"])
        self.assertEqual(result["initial_document_policy"], "CONTINUE_EXACT_APPLICATION_DOCUMENT_ONCE")
        self.assertEqual(result["surface_verification"], "DOCUMENT_LOCATION_AND_READY_STATE_ONLY_NO_BODY_TEXT")

    def test_dynamic_requests_are_blocked_before_network(self):
        result = design_application_route_diagnostics(self.config, self.resource_design)
        self.assertEqual(result["dynamic_request_policy"], "ABORT_ALL_DYNAMIC_BEFORE_NETWORK_AND_RECORD_SANITIZED_SHAPES")
        self.assertFalse(result["dynamic_candidate_network_sent"])
        self.assertFalse(result["resource_data_request_authorized"])

    def test_shape_contract_never_persists_url_values_or_bodies(self):
        fields = set(self.config["sanitized_shape_fields"])
        self.assertIn("route_without_query", fields)
        self.assertIn("query_keys", fields)
        self.assertFalse(fields.intersection({"url", "query_values", "body", "headers", "response_body", "request_body"}))

    def test_prior_resource_ambiguity_must_remain_unproven(self):
        for key, value in (
            ("name_identity_relation_status", "PROVEN"),
            ("direct_resource_get_safe_status", "SAFE"),
            ("resource_get", "ALLOWED"),
            ("collection_authorized", True),
        ):
            resource = copy.deepcopy(self.resource_design)
            resource[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationRouteDiagnosticsDesignError, msg=key):
                validate_design(self.config, resource)

    def test_operational_guards_cannot_be_relaxed(self):
        for key, value in {
            "dynamic_candidate_network_send": "ALLOWED",
            "resource_data_request": "ALLOWED",
            "pilot_limeira_values_send": "ALLOWED",
            "dom_interaction": "ALLOWED",
            "post_request_send": "ALLOWED",
            "head_request": "ALLOWED",
            "response_body_capture": "ALLOWED",
            "query_value_persistence": "ALLOWED",
            "route_synthesis_or_guessing": "ALLOWED",
            "automatic_route_promotion": "ALLOWED",
            "collection_authorized": True,
            "schedule_enabled": True,
        }.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationRouteDiagnosticsDesignError, msg=key):
                validate_design(config, self.resource_design)

    def test_exact_application_url_has_no_query_or_limeira(self):
        self.assertNotIn("?", self.config["exact_application_url"])
        self.assertNotIn("352690", self.config["exact_application_url"])

    def test_next_gate_is_live_passive_route_diagnostics_only(self):
        result = design_application_route_diagnostics(self.config, self.resource_design)
        self.assertEqual(result["next_gate"], "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0")
        self.assertFalse(result["automatic_route_promotion"])


if __name__ == "__main__":
    unittest.main()
