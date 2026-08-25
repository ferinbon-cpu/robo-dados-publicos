from __future__ import annotations

import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_export_runtime_route_diagnostics import (
    diagnose_export_runtime_route,
    summarize_post_click_requests,
)
from robo_dados_publicos.sources.siope_export_runtime_route_probe import (
    SiopeRuntimeRouteProbeError,
    load_runtime_route_probe_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_export_runtime_route_probe_gate.json"


def _base_raw(events):
    return {
        "page_verified": True,
        "artifact_declared": True,
        "export_control_found": True,
        "click_executed": True,
        "post_click_interception_active": True,
        "browser_download_denied": True,
        "candidate_route_network_sent": False,
        "cross_origin_initial_aborted_count": 12,
        "post_click_aborted_request_count": len(events),
        "intercepted_requests": events,
    }


class FakeRuntime:
    def __init__(self, raw):
        self.raw = raw

    def run_probe(self, config):
        return self.raw


class TestM7SiopeExportRuntimeRouteDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_runtime_route_probe_config(CONFIG)

    def test_summary_removes_query_values_and_aggregates_duplicates(self):
        events = [
            {"url": "https://api.example.gov.br/v1/file?id=20&token=SECRET", "method": "GET", "resource_type": "Fetch"},
            {"url": "https://api.example.gov.br/v1/file?id=21&token=OTHER", "method": "GET", "resource_type": "Fetch"},
        ]
        summary = summarize_post_click_requests(events, self.config)
        self.assertEqual(summary["unique_route_shape_count"], 1)
        self.assertEqual(summary["request_inventory"][0]["occurrences"], 2)
        self.assertEqual(summary["request_inventory"][0]["query_keys"], ["id", "token"])
        rendered = json.dumps(summary)
        self.assertNotIn("SECRET", rendered)
        self.assertNotIn("OTHER", rendered)

    def test_cross_origin_shape_is_visible_but_not_sent(self):
        events = [{
            "url": "https://dados.fnde.gov.br/api/file/20?key=SECRET",
            "method": "POST",
            "resource_type": "XHR",
        }]
        summary = summarize_post_click_requests(events, self.config)
        item = summary["request_inventory"][0]
        self.assertEqual(item["host"], "dados.fnde.gov.br")
        self.assertEqual(item["route_without_query"], "https://dados.fnde.gov.br/api/file/20")
        self.assertFalse(item["network_sent"])
        self.assertNotIn("SECRET", json.dumps(item))

    def test_diagnostics_passes_with_sanitized_inventory_and_authorizes_nothing(self):
        events = [{
            "url": "https://www.fnde.gov.br/api/v1/file?id=20&token=SECRET",
            "method": "POST",
            "resource_type": "XHR",
        }]
        result = diagnose_export_runtime_route(self.config, runtime=FakeRuntime(_base_raw(events)))
        self.assertEqual(result["status"], "PASS_M7_SIOPE_EXPORT_RUNTIME_ROUTE_DIAGNOSTICS_GATE")
        self.assertFalse(result["candidate_route_network_sent"])
        self.assertFalse(result["artifact_downloaded"])
        self.assertFalse(result["collection_authorized"])
        self.assertFalse(result["processing_authorized"])
        self.assertFalse(result["recurrence_authorized"])
        self.assertFalse(result["schedule_enabled"])
        self.assertNotIn("SECRET", json.dumps(result))

    def test_network_sent_fails_closed(self):
        raw = _base_raw([{"url": "https://www.fnde.gov.br/api/file", "method": "GET", "resource_type": "Fetch"}])
        raw["candidate_route_network_sent"] = True
        with self.assertRaisesRegex(SiopeRuntimeRouteProbeError, "NETWORK_SENT"):
            diagnose_export_runtime_route(self.config, runtime=FakeRuntime(raw))

    def test_no_eligible_requests_fails_closed(self):
        events = [{"url": "data:text/plain,hello", "method": "GET", "resource_type": "Other"}]
        with self.assertRaisesRegex(SiopeRuntimeRouteProbeError, "NO_ELIGIBLE_REQUESTS"):
            diagnose_export_runtime_route(self.config, runtime=FakeRuntime(_base_raw(events)))

    def test_inventory_limit_is_fail_closed(self):
        with self.assertRaisesRegex(SiopeRuntimeRouteProbeError, "BAD_LIMIT"):
            summarize_post_click_requests([], self.config, limit=129)


if __name__ == "__main__":
    unittest.main()
