from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_surface_boolean_diagnostics import (
    SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError,
    _sanitize_snapshot,
    dry_run,
    load_json,
    run_surface_boolean_diagnostics,
    validate_config,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_runtime_route_diagnostics import summarize_blocked_requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_surface_boolean_diagnostics.json"


class FakeRuntime:
    def __init__(self, probe: dict):
        self.probe = probe

    def run_probe(self, config: dict) -> dict:
        return self.probe


class TestM7SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.review = load_json(ROOT / cls.config["review_config_path"])
        cls.snapshot = {
            "scheme_matches": True,
            "host_matches": True,
            "path_matches": False,
            "query_empty": True,
            "fragment_empty": True,
            "href_exact": False,
            "ready_interactive": False,
            "ready_complete": True,
            "ready_eligible": True,
        }

    def test_dry_run_has_zero_network_and_no_authorization(self):
        result = dry_run(self.config, self.review)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS_DRY_RUN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["initial_document_network_sent"])
        self.assertFalse(result["dynamic_candidate_network_sent"])
        self.assertFalse(result["surface_authorized"])
        self.assertFalse(result["resource_get_authorized"])

    def test_fake_runtime_returns_boolean_snapshots_without_actual_location(self):
        events = [{"url": "https://www.fnde.gov.br/internal/spec?token=secret&ano=2024", "method": "GET", "resource_type": "XHR"}]
        shapes, candidates = summarize_blocked_requests(events, self.config)
        probe = {
            "initial_document_continued_count": 1,
            "static_assets_continued_count": 3,
            "local_requests_continued_count": 1,
            "first_observation": dict(self.snapshot),
            "final_observation": dict(self.snapshot),
            "blocked_shapes": shapes,
            "candidate_shapes": candidates,
            "browser_download_denied": True,
        }
        result = run_surface_boolean_diagnostics(self.config, self.review, runtime=FakeRuntime(probe))
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS")
        self.assertEqual(result["first_observation"], self.snapshot)
        self.assertEqual(result["final_observation"], self.snapshot)
        self.assertFalse(result["boolean_relation_state_changed"])
        self.assertFalse(result["actual_location_returned"])
        self.assertFalse(result["ready_state_string_returned"])
        self.assertFalse(result["dynamic_candidate_network_sent"])
        self.assertNotIn("secret", repr(result))
        self.assertNotIn("=2024", repr(result))

    def test_state_change_is_diagnostic_not_authorization(self):
        final = dict(self.snapshot)
        final["path_matches"] = True
        final["href_exact"] = True
        probe = {
            "initial_document_continued_count": 1,
            "first_observation": dict(self.snapshot),
            "final_observation": final,
            "blocked_shapes": [],
            "candidate_shapes": [],
            "browser_download_denied": True,
        }
        result = run_surface_boolean_diagnostics(self.config, self.review, runtime=FakeRuntime(probe))
        self.assertTrue(result["boolean_relation_state_changed"])
        self.assertFalse(result["surface_authorized"])
        self.assertFalse(result["collection_authorized"])

    def test_snapshot_must_be_exact_boolean_allowlist(self):
        bad = dict(self.snapshot)
        bad["actual_href"] = "https://secret.example/"
        with self.assertRaises(SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError):
            _sanitize_snapshot(bad, self.config)
        bad = dict(self.snapshot)
        bad["path_matches"] = "false"
        with self.assertRaises(SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError):
            _sanitize_snapshot(bad, self.config)
        bad = dict(self.snapshot)
        bad["ready_eligible"] = False
        with self.assertRaises(SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError):
            _sanitize_snapshot(bad, self.config)

    def test_any_sent_blocked_shape_fails_closed(self):
        bad = {
            "method": "GET", "resource_type": "XHR", "scheme": "https", "host": "www.fnde.gov.br",
            "route_without_query": "https://www.fnde.gov.br/api", "query_present": False, "query_keys": [],
            "official_host": True, "candidate_dynamic_request": True, "network_sent": True,
            "intercepted_before_network": False, "occurrences": 1,
        }
        probe = {
            "initial_document_continued_count": 1,
            "first_observation": dict(self.snapshot),
            "final_observation": dict(self.snapshot),
            "blocked_shapes": [bad],
            "candidate_shapes": [bad],
            "browser_download_denied": True,
        }
        with self.assertRaises(SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError):
            run_surface_boolean_diagnostics(self.config, self.review, runtime=FakeRuntime(probe))

    def test_config_cannot_open_operational_actions(self):
        for key, value in {
            "dynamic_candidate_network_send": "ALLOWED",
            "resource_data_request": "ALLOWED",
            "pilot_limeira_values_send": "ALLOWED",
            "post_request_send": "ALLOWED",
            "head_request": "ALLOWED",
            "actual_location_return": "ALLOWED",
            "response_body_capture": "ALLOWED",
            "query_value_persistence": "ALLOWED",
            "surface_authorized": True,
            "resource_get_authorized": True,
            "collection_authorized": True,
            "schedule_enabled": True,
        }.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError, msg=key):
                validate_config(config, self.review)

    def test_source_uses_boolean_only_expression_and_fail_closed_network(self):
        source = (ROOT / "robo_dados_publicos" / "sources" / "siope_official_olinda_api_application_surface_boolean_diagnostics.py").read_text(encoding="utf-8")
        self.assertIn('Browser.setDownloadBehavior", {"behavior": "deny"}', source)
        self.assertIn("Fetch.failRequest", source)
        self.assertNotIn("Network.getResponseBody", source)
        self.assertNotIn("Fetch.getResponseBody", source)
        self.assertNotIn("document.body.innerText", source)
        self.assertNotIn("actual_href:", source)


if __name__ == "__main__":
    unittest.main()
