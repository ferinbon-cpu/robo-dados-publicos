from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_runtime_route_diagnostics_review import (
    SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsReviewError,
    load_json,
    review,
    validate_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_official_olinda_api_application_runtime_route_diagnostics_review.json"


class TestM7SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.evidence = load_json(ROOT / cls.config["evidence_path"])

    def test_exact_pinned_stop_evidence_passes_offline(self):
        result = review(self.config, self.evidence)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_REVIEW")
        self.assertFalse(result["network_called"])
        self.assertEqual(result["dynamic_route_status"], "UNPROVEN_ZERO_CANDIDATES")
        self.assertEqual(result["failure_classification"], "INSUFFICIENT_BOOLEAN_TELEMETRY_TO_DISTINGUISH_LOCATION_FROM_READY_STATE")
        self.assertFalse(result["resource_get_authorized"])
        self.assertFalse(result["collection_authorized"])

    def test_tampered_identity_or_candidate_fails_closed(self):
        for mutate in (
            lambda e: e.__setitem__("run_id", 1),
            lambda e: e["artifact"].__setitem__("id", 1),
            lambda e: e.__setitem__("candidate_shapes", [{"candidate_dynamic_request": True}]),
            lambda e: e["safety"].__setitem__("dynamic_candidate_network_sent", True),
        ):
            evidence = copy.deepcopy(self.evidence)
            mutate(evidence)
            with self.assertRaises(SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsReviewError):
                review(self.config, evidence)

    def test_operational_switches_cannot_be_opened(self):
        for key, value in {
            "network_access": "ALLOWED",
            "resource_get": "ALLOWED",
            "query_parameters": "ALLOWED",
            "post_request": "ALLOWED",
            "head_request": "ALLOWED",
            "pilot_limeira_values_send": "ALLOWED",
            "collection_authorized": True,
            "processing_authorized": True,
            "recurrence_authorized": True,
            "schedule_enabled": True,
        }.items():
            config = copy.deepcopy(self.config)
            config[key] = value
            with self.assertRaises(SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsReviewError, msg=key):
                validate_config(config)

    def test_next_gate_is_boolean_surface_diagnostics_only(self):
        result = review(self.config, self.evidence)
        self.assertEqual(result["next_gate"], "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS_0_8_0")

    def test_review_source_is_offline(self):
        source = (ROOT / "robo_dados_publicos" / "sources" / "siope_official_olinda_api_application_runtime_route_diagnostics_review.py").read_text(encoding="utf-8")
        for forbidden in ("urllib.request", "requests.get", "requests.post", "subprocess", "websocket", "Runtime.evaluate"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
