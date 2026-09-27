from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_structural_binding_diagnostics import (
    SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsError,
    dry_run,
    load_json,
    run_dom_structural_binding_diagnostics,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_structural_binding_diagnostics.json"


class FakeRuntime:
    def __init__(self, signature: dict, shapes=None, candidates=None):
        self.signature = signature
        self.shapes = shapes or []
        self.candidates = candidates or []

    def run_probe(self, config: dict) -> dict:
        return {
            "initial_document_continued_count": 1,
            "static_assets_continued_count": 23,
            "local_requests_continued_count": 0,
            "application_surface_verified": True,
            "fragment_present": True,
            "structural_boolean_signature": self.signature,
            "blocked_shapes": self.shapes,
            "candidate_shapes": self.candidates,
            "browser_download_denied": True,
        }


class TestM7SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.design = {
            "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_STRUCTURAL_BINDING_DIAGNOSTICS_DESIGN",
            "returned_observations": cls.config["returned_boolean_fields"],
            "structural_binding_status": "UNPROVEN_PENDING_BOOLEAN_DIAGNOSTICS",
            "resource_get_authorized": False,
        }
        cls.signature = {key: False for key in cls.config["returned_boolean_fields"]}

    def test_dry_run_has_zero_network_and_no_raw_dom(self):
        result = dry_run(self.config, self.design)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_STRUCTURAL_BINDING_DIAGNOSTICS_DRY_RUN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["dom_text_returned"])
        self.assertFalse(result["dom_attribute_values_returned"])
        self.assertFalse(result["element_material_returned"])
        self.assertFalse(result["resource_get_authorized"])

    def test_any_boolean_combination_is_diagnostic_not_authorization(self):
        signature = dict(self.signature)
        signature["technical_name_in_dom_text"] = True
        signature["all_parameters_in_dom_text"] = True
        signature["minimal_container_with_callable_and_all_parameters"] = True
        signature["ordered_callable_parameter_sequence_in_minimal_container"] = True
        result = run_dom_structural_binding_diagnostics(self.config, self.design, runtime=FakeRuntime(signature))
        self.assertEqual(result["matched_structural_relation_count"], 4)
        self.assertEqual(result["structural_boolean_signature"], signature)
        self.assertFalse(result["resource_get_authorized"])
        self.assertFalse(result["automatic_route_promotion"])
        self.assertFalse(result["element_material_returned"])

    def test_non_boolean_or_extra_signature_fails_closed(self):
        bad = dict(self.signature)
        bad["technical_name_in_dom_text"] = "yes"
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsError):
            run_dom_structural_binding_diagnostics(self.config, self.design, runtime=FakeRuntime(bad))
        extra = dict(self.signature)
        extra["raw_element"] = "secret"
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsError):
            run_dom_structural_binding_diagnostics(self.config, self.design, runtime=FakeRuntime(extra))

    def test_any_sent_blocked_shape_fails_closed(self):
        bad = {
            "method": "GET", "resource_type": "XHR", "scheme": "https", "host": "www.fnde.gov.br",
            "route_without_query": "https://www.fnde.gov.br/internal", "query_present": False, "query_keys": [],
            "official_host": True, "candidate_dynamic_request": True, "network_sent": True,
            "intercepted_before_network": False, "occurrences": 1,
        }
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsError):
            run_dom_structural_binding_diagnostics(self.config, self.design, runtime=FakeRuntime(self.signature, [bad], [bad]))

    def test_config_cannot_open_resource_interaction_post_head_pilot_or_collection(self):
        mutations = {
            "dom_interaction": "ALLOWED",
            "resource_data_request": "ALLOWED",
            "pilot_limeira_values_send": "ALLOWED",
            "post_request_send": "ALLOWED",
            "head_request": "ALLOWED",
            "dom_text_return": "ALLOWED",
            "dom_attribute_value_return": "ALLOWED",
            "element_text_return": "ALLOWED",
            "collection_authorized": True,
            "schedule_enabled": True,
        }
        for key, value in mutations.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationDomStructuralBindingDiagnosticsError, msg=key):
                validate_config(config, self.design)

    def test_source_uses_transient_dom_relations_but_returns_only_boolean_contract(self):
        source = (ROOT / "robo_dados_publicos" / "sources" / "siope_official_olinda_api_application_dom_structural_binding_diagnostics.py").read_text(encoding="utf-8")
        self.assertIn("Fetch.failRequest", source)
        self.assertIn('Browser.setDownloadBehavior", {"behavior": "deny"}', source)
        self.assertIn("minimalContainers", source)
        self.assertIn("orderedIn", source)
        self.assertNotIn("Network.getResponseBody", source)
        self.assertNotIn("Fetch.getResponseBody", source)
        self.assertNotIn("document.documentElement.innerHTML", source)
        self.assertNotIn("352690", self.config["exact_application_url"])
        self.assertEqual(set(self.config["returned_boolean_fields"]), set(self.signature))


if __name__ == "__main__":
    unittest.main()
