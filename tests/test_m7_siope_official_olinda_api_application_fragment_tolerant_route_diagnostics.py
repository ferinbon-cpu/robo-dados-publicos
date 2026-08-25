from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_fragment_tolerant_route_diagnostics import (
    SiopeOfficialOlindaApiApplicationFragmentTolerantRouteDiagnosticsError,
    dry_run,
    load_json,
    run_fragment_tolerant_route_diagnostics,
    validate_config,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_runtime_route_diagnostics import summarize_blocked_requests
from robo_dados_publicos.sources.siope_official_olinda_api_application_surface_boolean_diagnostics_review import review_surface_boolean_diagnostics

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_fragment_tolerant_route_diagnostics.json"


class FakeRuntime:
    def __init__(self, probe: dict):
        self.probe = probe

    def run_probe(self, config: dict) -> dict:
        return self.probe


class TestM7SiopeOfficialOlindaApiApplicationFragmentTolerantRouteDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        review_config = load_json(ROOT / cls.config["review_config_path"])
        evidence = load_json(ROOT / review_config["evidence_path"])
        cls.review_result = review_surface_boolean_diagnostics(review_config, evidence)

    def test_dry_run_has_zero_network_and_fragment_value(self):
        result = dry_run(self.config, self.review_result)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TOLERANT_ROUTE_DIAGNOSTICS_DRY_RUN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["fragment_value_returned"])
        self.assertFalse(result["resource_get_authorized"])

    def test_fake_runtime_accepts_fragment_presence_without_using_value_for_identity(self):
        events = [{"url": "https://www.fnde.gov.br/olinda-ide/internal/spec?token=secret", "method": "GET", "resource_type": "XHR"}]
        shapes, candidates = summarize_blocked_requests(events, self.config)
        probe = {
            "initial_document_continued_count": 1,
            "static_assets_continued_count": 23,
            "local_requests_continued_count": 0,
            "application_surface_verified": True,
            "fragment_present_at_ready": True,
            "fragment_present_at_final": True,
            "blocked_shapes": shapes,
            "candidate_shapes": candidates,
            "browser_download_denied": True,
        }
        result = run_fragment_tolerant_route_diagnostics(self.config, self.review_result, runtime=FakeRuntime(probe))
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TOLERANT_ROUTE_DIAGNOSTICS")
        self.assertTrue(result["fragment_present_at_ready"])
        self.assertFalse(result["surface_identity_uses_fragment"])
        self.assertFalse(result["fragment_value_returned"])
        self.assertEqual(result["candidate_shape_count"], 1)
        self.assertFalse(result["dynamic_candidate_network_sent"])
        self.assertNotIn("secret", repr(result))

    def test_any_sent_blocked_shape_fails_closed(self):
        bad = {
            "method": "GET", "resource_type": "XHR", "scheme": "https", "host": "www.fnde.gov.br",
            "route_without_query": "https://www.fnde.gov.br/api", "query_present": False, "query_keys": [],
            "official_host": True, "candidate_dynamic_request": True, "network_sent": True,
            "intercepted_before_network": False, "occurrences": 1,
        }
        probe = {
            "initial_document_continued_count": 1,
            "application_surface_verified": True,
            "fragment_present_at_ready": True,
            "fragment_present_at_final": True,
            "blocked_shapes": [bad],
            "candidate_shapes": [bad],
            "browser_download_denied": True,
        }
        with self.assertRaises(SiopeOfficialOlindaApiApplicationFragmentTolerantRouteDiagnosticsError):
            run_fragment_tolerant_route_diagnostics(self.config, self.review_result, runtime=FakeRuntime(probe))

    def test_review_cannot_be_weakened_to_authorize_resource(self):
        review = copy.deepcopy(self.review_result)
        review["resource_get_authorized"] = True
        with self.assertRaises(SiopeOfficialOlindaApiApplicationFragmentTolerantRouteDiagnosticsError):
            validate_config(self.config, review)

    def test_config_cannot_capture_fragment_or_open_operations(self):
        mutations = {
            "fragment_value_capture": "ALLOWED",
            "dynamic_candidate_network_send": "ALLOWED",
            "resource_data_request": "ALLOWED",
            "pilot_limeira_values_send": "ALLOWED",
            "post_request_send": "ALLOWED",
            "head_request": "ALLOWED",
            "response_body_capture": "ALLOWED",
            "query_value_persistence": "ALLOWED",
            "route_synthesis_or_guessing": "ALLOWED",
            "automatic_route_promotion": "ALLOWED",
            "resource_get_authorized": True,
            "collection_authorized": True,
            "schedule_enabled": True,
        }
        for key, value in mutations.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationFragmentTolerantRouteDiagnosticsError, msg=key):
                validate_config(config, self.review_result)

    def test_source_uses_fragment_presence_only_and_keeps_fail_closed_network(self):
        source = (ROOT / "robo_dados_publicos" / "sources" / "siope_official_olinda_api_application_fragment_tolerant_route_diagnostics.py").read_text(encoding="utf-8")
        self.assertIn("window.location.hash.length > 0", source)
        self.assertNotIn("window.location.hash,", source)
        self.assertNotIn("fragment_value", source.split("inspect_expr", 1)[1].split('"""', 2)[1])
        self.assertIn("Fetch.failRequest", source)
        self.assertIn('Browser.setDownloadBehavior", {"behavior": "deny"}', source)
        self.assertNotIn("Network.getResponseBody", source)
        self.assertNotIn("Fetch.getResponseBody", source)


if __name__ == "__main__":
    unittest.main()
