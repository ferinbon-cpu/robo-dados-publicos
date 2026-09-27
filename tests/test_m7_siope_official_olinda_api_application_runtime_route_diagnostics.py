from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_runtime_route_diagnostics import (
    SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError,
    _route_shape,
    dry_run,
    load_json,
    run_application_route_diagnostics,
    summarize_blocked_requests,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_runtime_route_diagnostics.json"


class FakeRuntime:
    def __init__(self, probe: dict):
        self.probe = probe

    def run_probe(self, config: dict) -> dict:
        return self.probe


class TestM7SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.design = load_json(ROOT / cls.config["design_config_path"])

    def test_dry_run_has_zero_network(self):
        result = dry_run(self.config, self.design)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_DRY_RUN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["initial_document_network_sent"])
        self.assertFalse(result["dynamic_candidate_network_sent"])

    def test_shape_strips_query_values_and_marks_official_xhr_candidate(self):
        shape = _route_shape(
            "https://www.fnde.gov.br/olinda-ide/internal/spec?token=secret&ano=2024",
            "GET",
            "XHR",
            self.config,
        )
        self.assertEqual(shape["route_without_query"], "https://www.fnde.gov.br/olinda-ide/internal/spec")
        self.assertEqual(shape["query_keys"], ["ano", "token"])
        self.assertNotIn("secret", repr(shape))
        self.assertNotIn("2024", repr(shape))
        self.assertTrue(shape["candidate_dynamic_request"])
        self.assertFalse(shape["network_sent"])
        self.assertTrue(shape["intercepted_before_network"])

    def test_cross_origin_dynamic_is_visible_but_not_candidate(self):
        shape = _route_shape("https://example.org/api?q=secret", "GET", "Fetch", self.config)
        self.assertFalse(shape["official_host"])
        self.assertFalse(shape["candidate_dynamic_request"])
        self.assertNotIn("secret", repr(shape))

    def test_summary_dedupes_without_query_values(self):
        events = [
            {"url": "https://www.fnde.gov.br/api/spec?a=1", "method": "GET", "resource_type": "XHR"},
            {"url": "https://www.fnde.gov.br/api/spec?a=2&b=3", "method": "GET", "resource_type": "XHR"},
        ]
        shapes, candidates = summarize_blocked_requests(events, self.config)
        self.assertEqual(len(shapes), 1)
        self.assertEqual(shapes[0]["occurrences"], 2)
        self.assertEqual(shapes[0]["query_keys"], ["a", "b"])
        self.assertEqual(len(candidates), 1)
        self.assertNotIn("=1", repr(shapes))
        self.assertNotIn("=2", repr(shapes))

    def test_fake_runtime_passes_with_all_dynamic_routes_unsent(self):
        events = [{"url": "https://www.fnde.gov.br/olinda-ide/spec?x=secret", "method": "GET", "resource_type": "XHR"}]
        shapes, candidates = summarize_blocked_requests(events, self.config)
        probe = {
            "initial_document_continued_count": 1,
            "static_assets_continued_count": 4,
            "local_requests_continued_count": 1,
            "application_surface_verified": True,
            "blocked_shapes": shapes,
            "candidate_shapes": candidates,
            "browser_download_denied": True,
        }
        result = run_application_route_diagnostics(self.config, self.design, runtime=FakeRuntime(probe))
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS")
        self.assertEqual(result["candidate_shape_count"], 1)
        self.assertFalse(result["dynamic_candidate_network_sent"])
        self.assertFalse(result["resource_data_request_performed"])
        self.assertFalse(result["collection_authorized"])
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
            "blocked_shapes": [bad],
            "candidate_shapes": [bad],
            "browser_download_denied": True,
        }
        with self.assertRaises(SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError):
            run_application_route_diagnostics(self.config, self.design, runtime=FakeRuntime(probe))

    def test_config_cannot_open_resource_post_head_pilot_or_collection(self):
        mutations = {
            "dynamic_candidate_network_send": "ALLOWED",
            "resource_data_request": "ALLOWED",
            "pilot_limeira_values_send": "ALLOWED",
            "post_request_send": "ALLOWED",
            "head_request": "ALLOWED",
            "response_body_capture": "ALLOWED",
            "query_value_persistence": "ALLOWED",
            "route_synthesis_or_guessing": "ALLOWED",
            "automatic_route_promotion": "ALLOWED",
            "collection_authorized": True,
            "schedule_enabled": True,
        }
        for key, value in mutations.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError, msg=key):
                validate_config(config, self.design)

    def test_source_denies_download_and_aborts_unapproved_requests(self):
        source = (ROOT / "robo_dados_publicos" / "sources" / "siope_official_olinda_api_application_runtime_route_diagnostics.py").read_text(encoding="utf-8")
        self.assertIn('Browser.setDownloadBehavior", {"behavior": "deny"}', source)
        self.assertIn("Fetch.failRequest", source)
        self.assertNotIn("Network.getResponseBody", source)
        self.assertNotIn("Fetch.getResponseBody", source)
        self.assertIn('if "352690" in config["exact_application_url"]', source)
        self.assertNotIn("352690", self.config["exact_application_url"])


if __name__ == "__main__":
    unittest.main()
