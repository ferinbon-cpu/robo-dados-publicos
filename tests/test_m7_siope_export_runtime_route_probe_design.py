from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_export_runtime_route_probe_design import (
    SiopeRuntimeRouteProbeDesignError,
    validate_runtime_route_probe_design,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_export_runtime_route_probe_design.json"


class TestM7SiopeExportRuntimeRouteProbeDesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_design_passes_and_executes_nothing(self):
        result = validate_runtime_route_probe_design(copy.deepcopy(self.config))
        self.assertEqual(result["status"], "PASS_M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_DESIGN_GATE")
        self.assertFalse(result["browser_execution"])
        self.assertFalse(result["click_executed"])
        self.assertFalse(result["candidate_route_network_sent"])
        self.assertFalse(result["artifact_downloaded"])
        self.assertEqual(result["remote_writes"], "NONE")

    def test_browser_install_or_download_cannot_be_enabled(self):
        bad = copy.deepcopy(self.config)
        bad["browser_download_or_install"] = "ALLOWED"
        with self.assertRaises(SiopeRuntimeRouteProbeDesignError):
            validate_runtime_route_probe_design(bad)

    def test_post_click_requests_must_abort_before_network(self):
        bad = copy.deepcopy(self.config)
        bad["post_click_network_policy"] = "ALLOW"
        with self.assertRaises(SiopeRuntimeRouteProbeDesignError):
            validate_runtime_route_probe_design(bad)

    def test_response_and_request_material_cannot_be_captured(self):
        for key in ("response_body_capture", "request_body_capture", "request_headers_capture", "cookie_capture", "query_value_capture"):
            with self.subTest(key=key):
                bad = copy.deepcopy(self.config)
                bad[key] = "ALLOWED"
                with self.assertRaises(SiopeRuntimeRouteProbeDesignError):
                    validate_runtime_route_probe_design(bad)

    def test_only_official_initial_host_is_allowed(self):
        bad = copy.deepcopy(self.config)
        bad["initial_allowed_hosts"].append("example.com")
        with self.assertRaises(SiopeRuntimeRouteProbeDesignError):
            validate_runtime_route_probe_design(bad)

    def test_single_click_and_unique_candidate_are_required(self):
        bad = copy.deepcopy(self.config)
        bad["max_clicks"] = 2
        with self.assertRaises(SiopeRuntimeRouteProbeDesignError):
            validate_runtime_route_probe_design(bad)
        bad = copy.deepcopy(self.config)
        bad["unique_candidate_required_for_pass"] = False
        with self.assertRaises(SiopeRuntimeRouteProbeDesignError):
            validate_runtime_route_probe_design(bad)

    def test_collection_processing_recurrence_and_schedule_stay_closed(self):
        for key, value in (
            ("source_collection", "ALLOWED"),
            ("source_processing", "ALLOWED"),
            ("recurrence", "ALLOWED"),
            ("schedule", "ENABLED"),
        ):
            with self.subTest(key=key):
                bad = copy.deepcopy(self.config)
                bad[key] = value
                with self.assertRaises(SiopeRuntimeRouteProbeDesignError):
                    validate_runtime_route_probe_design(bad)

    def test_fail_closed_switches_are_mandatory(self):
        for key in (
            "fail_closed_on_interception_error",
            "fail_closed_on_browser_unavailable",
            "fail_closed_on_zero_candidates",
            "fail_closed_on_multiple_candidates",
        ):
            with self.subTest(key=key):
                bad = copy.deepcopy(self.config)
                bad[key] = False
                with self.assertRaises(SiopeRuntimeRouteProbeDesignError):
                    validate_runtime_route_probe_design(bad)


if __name__ == "__main__":
    unittest.main()
