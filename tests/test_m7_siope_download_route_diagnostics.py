import json
import unittest

from robo_dados_publicos.sources.siope_download_route_discovery import SiopeDownloadRouteDiscoveryError


class TestM7SiopeDownloadRouteDiagnostics(unittest.TestCase):
    def test_error_diagnostics_default_to_empty_mapping(self):
        exc = SiopeDownloadRouteDiscoveryError("STOP_TEST")
        self.assertEqual({}, exc.diagnostics)

    def test_diagnostics_contract_can_hold_only_sanitized_counts_and_codes(self):
        diagnostics = {
            "page_verified": True,
            "artifact_declared": True,
            "page_bytes": 1234,
            "declared_script_count": 2,
            "fetched_script_count": 1,
            "script_failure_count": 1,
            "script_failures": [{"script_index": 2, "reason": "STOP_SIOPE_DOWNLOAD_ROUTE_RESPONSE_TOO_LARGE"}],
            "total_fetched_script_bytes": 3456,
            "page_markers": {
                "export_label_present": True,
                "inline_script_count": 1,
                "inline_script_export_marker_count": 0,
                "inline_event_attribute_count": 0,
                "inline_event_export_marker_count": 0,
                "data_attribute_count": 2,
                "data_attribute_export_marker_count": 1,
                "href_action_count": 4,
                "href_action_export_marker_count": 0,
            },
            "route_candidate_count": 0,
        }
        exc = SiopeDownloadRouteDiscoveryError("STOP_TEST", diagnostics=diagnostics)
        serialized = json.dumps(exc.diagnostics)
        self.assertNotIn("https://", serialized)
        self.assertNotIn("token", serialized.lower())
        self.assertNotIn("exports/SIOPE", serialized)
        self.assertEqual(2, exc.diagnostics["declared_script_count"])


if __name__ == "__main__":
    unittest.main()
