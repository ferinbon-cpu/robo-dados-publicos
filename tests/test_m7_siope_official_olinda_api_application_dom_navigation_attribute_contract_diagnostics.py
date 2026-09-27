from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_navigation_attribute_contract_diagnostics import (
    SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError,
    dry_run,
    load_json,
    run_navigation_attribute_contract_diagnostics,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_dom_navigation_attribute_contract_diagnostics.json"


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
            "navigation_boolean_signature": self.signature,
            "blocked_shapes": self.shapes,
            "candidate_shapes": self.candidates,
            "browser_download_denied": True,
        }


class TestM7SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.design = {
            "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_DESIGN",
            "returned_observations": cls.config["returned_boolean_fields"],
            "navigation_execution_authorized": False,
            "raw_navigation_value_return_authorized": False,
            "resource_get_authorized": False,
        }
        cls.empty = {key: False for key in cls.config["returned_boolean_fields"]}

    def test_dry_run_has_zero_network_navigation_and_raw_material(self):
        result = dry_run(self.config, self.design)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_DRY_RUN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["navigation_executed"])
        self.assertFalse(result["navigation_attribute_value_returned"])
        self.assertFalse(result["resource_get_authorized"])

    def test_unique_fragment_href_is_diagnostic_not_authorization(self):
        signature = dict(self.empty)
        signature.update({
            "navigation_match_present": True,
            "navigation_match_unique": True,
            "navigation_attribute_is_href": True,
            "navigation_value_fragment_only": True,
            "navigation_value_resolves_to_application_document": True,
            "navigation_value_contains_callable_name": True,
        })
        result = run_navigation_attribute_contract_diagnostics(self.config, self.design, runtime=FakeRuntime(signature))
        self.assertEqual(result["navigation_boolean_signature"], signature)
        self.assertFalse(result["navigation_executed"])
        self.assertFalse(result["navigation_attribute_value_returned"])
        self.assertFalse(result["resource_get_authorized"])
        self.assertFalse(result["automatic_route_promotion"])

    def test_nonunique_match_cannot_emit_detailed_classification(self):
        signature = dict(self.empty)
        signature["navigation_match_present"] = True
        signature["navigation_attribute_is_href"] = True
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError):
            run_navigation_attribute_contract_diagnostics(self.config, self.design, runtime=FakeRuntime(signature))

    def test_extra_or_nonboolean_signature_fails_closed(self):
        bad = dict(self.empty)
        bad["navigation_match_present"] = "yes"
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError):
            run_navigation_attribute_contract_diagnostics(self.config, self.design, runtime=FakeRuntime(bad))
        extra = dict(self.empty)
        extra["raw_href"] = "forbidden"
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError):
            run_navigation_attribute_contract_diagnostics(self.config, self.design, runtime=FakeRuntime(extra))

    def test_any_sent_blocked_shape_fails_closed(self):
        bad = {
            "method": "GET", "resource_type": "XHR", "scheme": "https", "host": "www.fnde.gov.br",
            "route_without_query": "https://www.fnde.gov.br/internal", "query_present": False, "query_keys": [],
            "official_host": True, "candidate_dynamic_request": True, "network_sent": True,
            "intercepted_before_network": False, "occurrences": 1,
        }
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError):
            run_navigation_attribute_contract_diagnostics(self.config, self.design, runtime=FakeRuntime(self.empty, [bad], [bad]))

    def test_config_cannot_open_navigation_resource_post_head_pilot_or_collection(self):
        mutations = {
            "navigation_attribute_value_return": "ALLOWED",
            "navigation_path_return": "ALLOWED",
            "navigation_query_return": "ALLOWED",
            "navigation_fragment_return": "ALLOWED",
            "element_material_return": "ALLOWED",
            "dom_interaction": "ALLOWED",
            "navigation_execution": "ALLOWED",
            "resource_data_request": "ALLOWED",
            "pilot_limeira_values_send": "ALLOWED",
            "post_request_send": "ALLOWED",
            "head_request": "ALLOWED",
            "collection_authorized": True,
            "schedule_enabled": True,
        }
        for key, value in mutations.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError, msg=key):
                validate_config(config, self.design)

    def test_source_reads_attribute_transiently_but_never_returns_or_executes_it(self):
        source = (ROOT / "robo_dados_publicos" / "sources" / "siope_official_olinda_api_application_dom_navigation_attribute_contract_diagnostics.py").read_text(encoding="utf-8")
        self.assertIn("getAttribute", source)
        self.assertIn("Fetch.failRequest", source)
        self.assertIn('Browser.setDownloadBehavior", {"behavior": "deny"}', source)
        self.assertNotIn("Network.getResponseBody", source)
        self.assertNotIn("Fetch.getResponseBody", source)
        self.assertNotIn("location.assign", source)
        self.assertNotIn("location.replace", source)
        self.assertNotIn(".click()", source)
        self.assertNotIn("352690", self.config["exact_application_url"])


if __name__ == "__main__":
    unittest.main()
