from __future__ import annotations

import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_export_runtime_route_probe import (
    SiopeRuntimeRouteProbeError,
    classify_intercepted_requests,
    load_runtime_route_probe_config,
    probe_export_runtime_route,
    sanitize_intercepted_url,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_export_runtime_route_probe_gate.json"


def _base_raw(events):
    return {
        "browser_binary_name": "google-chrome",
        "browser_version": "Google Chrome TEST",
        "page_verified": True,
        "artifact_declared": True,
        "export_control_found": True,
        "click_executed": True,
        "post_click_interception_active": True,
        "browser_download_denied": True,
        "candidate_route_network_sent": False,
        "cross_origin_initial_aborted_count": 2,
        "post_click_aborted_request_count": len(events),
        "intercepted_requests": events,
    }


class FakeRuntime:
    def __init__(self, raw):
        self.raw = raw
    def run_probe(self, config):
        return self.raw


class TestM7SiopeExportRuntimeRouteProbe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_runtime_route_probe_config(CONFIG)

    def test_sanitizer_removes_query_values_and_fragment(self):
        item = sanitize_intercepted_url("https://www.fnde.gov.br/api/export?id=20&token=SECRET#frag")
        self.assertEqual(item["route_without_query"], "https://www.fnde.gov.br/api/export")
        self.assertEqual(item["query_keys"], ["id", "token"])
        self.assertNotIn("SECRET", json.dumps(item))

    def test_unique_intercepted_export_request_passes_without_network_send(self):
        events = [{
            "url": "https://www.fnde.gov.br/plataforma-antonieta-de-barros-api/artifacts/20/export?key=SECRET",
            "method": "GET",
            "resource_type": "Fetch",
            "initiator_functions": ["downloadFile"],
        }]
        result = probe_export_runtime_route(self.config, runtime=FakeRuntime(_base_raw(events)))
        self.assertEqual(result["runtime_probe_status"], "UNIQUE_INTERCEPTED_EXPORT_REQUEST_OBSERVED_NOT_SENT")
        self.assertFalse(result["candidate_route_network_sent"])
        self.assertFalse(result["artifact_downloaded"])
        self.assertEqual(result["candidate"]["query_keys"], ["key"])
        self.assertNotIn("SECRET", json.dumps(result))

    def test_unrelated_post_click_request_is_not_candidate(self):
        events = [{
            "url": "https://www.fnde.gov.br/assets/icon.svg",
            "method": "GET",
            "resource_type": "Other",
            "initiator_functions": [],
        }]
        self.assertEqual(classify_intercepted_requests(events, self.config), [])

    def test_target_identifier_can_mark_candidate_without_route_marker(self):
        events = [{
            "url": "https://www.fnde.gov.br/api/v1/file?id=20",
            "method": "POST",
            "resource_type": "XHR",
            "initiator_functions": ["getArtifactByDataProductId"],
        }]
        candidates = classify_intercepted_requests(events, self.config)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["method"], "POST")

    def test_zero_candidates_fails_closed(self):
        with self.assertRaisesRegex(SiopeRuntimeRouteProbeError, "ZERO_CANDIDATES"):
            probe_export_runtime_route(self.config, runtime=FakeRuntime(_base_raw([])))

    def test_multiple_candidates_fail_closed(self):
        events = [
            {"url": "https://www.fnde.gov.br/api/export/one", "method": "GET", "resource_type": "Fetch", "initiator_functions": []},
            {"url": "https://www.fnde.gov.br/api/export/two", "method": "GET", "resource_type": "Fetch", "initiator_functions": []},
        ]
        with self.assertRaisesRegex(SiopeRuntimeRouteProbeError, "MULTIPLE_CANDIDATES"):
            probe_export_runtime_route(self.config, runtime=FakeRuntime(_base_raw(events)))

    def test_any_network_sent_flag_fails_closed(self):
        raw = _base_raw([{"url": "https://www.fnde.gov.br/api/export", "method": "GET", "resource_type": "Fetch", "initiator_functions": []}])
        raw["candidate_route_network_sent"] = True
        with self.assertRaisesRegex(SiopeRuntimeRouteProbeError, "NETWORK_SENT"):
            probe_export_runtime_route(self.config, runtime=FakeRuntime(raw))

    def test_runtime_contract_requires_click_interception_and_download_denial(self):
        for key in ("click_executed", "post_click_interception_active", "browser_download_denied"):
            with self.subTest(key=key):
                raw = _base_raw([])
                raw[key] = False
                with self.assertRaisesRegex(SiopeRuntimeRouteProbeError, "RUNTIME_CONTRACT"):
                    probe_export_runtime_route(self.config, runtime=FakeRuntime(raw))


if __name__ == "__main__":
    unittest.main()
