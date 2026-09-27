from __future__ import annotations

import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_get_runtime_route_diagnostics import (
    SiopePublicGetRuntimeRouteDiagnosticsError,
    _is_allowed_static_asset,
    _matches_exact_indexed_document,
    load_public_get_runtime_route_diagnostics_config,
    probe_public_get_runtime_routes,
    summarize_blocked_requests,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_get_runtime_route_diagnostics_gate.json"


class FakeRuntime:
    def __init__(self, raw):
        self.raw = raw

    def run_probe(self, config):
        return self.raw


def _raw(events=None, *, challenge=False):
    events = list(events or [])
    return {
        "browser_binary_name": "google-chrome",
        "browser_version": "TEST",
        "page_surface_verified": True,
        "initial_document_continued_count": 1,
        "initial_document_network_sent": True,
        "static_assets_continued_count": 4,
        "local_requests_continued_count": 1,
        "dynamic_candidate_network_sent": False,
        "browser_download_denied": True,
        "human_challenge_active_dom": challenge,
        "blocked_requests": events,
    }


class TestSiopePublicGetRuntimeRouteDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_public_get_runtime_route_diagnostics_config(CONFIG)

    def test_config_uses_public_indexed_example_not_limeira_pilot(self):
        payload = json.dumps(self.config, sort_keys=True)
        self.assertNotIn("352690", payload)
        self.assertIn("292430", self.config["public_indexed_example_url"])
        self.assertEqual(self.config["pilot_limeira_values_send"], "PROHIBITED")
        self.assertEqual(self.config["dynamic_candidate_network_send"], "PROHIBITED")
        self.assertEqual(self.config["form_submission"], "PROHIBITED")
        self.assertEqual(self.config["captcha_bypass"], "PROHIBITED")

    def test_exact_indexed_document_matches_even_if_query_order_changes(self):
        url = self.config["public_indexed_example_url"]
        self.assertTrue(_matches_exact_indexed_document(url, "GET", "Document", self.config))
        prefix, query = url.split("?", 1)
        reordered = prefix + "?" + "&".join(reversed(query.split("&")))
        self.assertTrue(_matches_exact_indexed_document(reordered, "GET", "Document", self.config))
        self.assertFalse(_matches_exact_indexed_document(url, "POST", "Document", self.config))
        self.assertFalse(_matches_exact_indexed_document(url, "GET", "XHR", self.config))

    def test_limeira_value_does_not_match_exact_public_document(self):
        changed = self.config["public_indexed_example_url"].replace("292430", "352690")
        self.assertFalse(_matches_exact_indexed_document(changed, "GET", "Document", self.config))

    def test_only_official_static_get_assets_are_allowlisted(self):
        self.assertTrue(_is_allowed_static_asset("https://www.fnde.gov.br/siope/js/app.js", "GET", "Script", self.config))
        self.assertTrue(_is_allowed_static_asset("https://www.fnde.gov.br/siope/css/app.css?v=1", "GET", "Stylesheet", self.config))
        self.assertTrue(_is_allowed_static_asset("https://www.fnde.gov.br/siope/img/a.png", "GET", "Image", self.config))
        self.assertFalse(_is_allowed_static_asset("https://evil.example/siope/js/app.js", "GET", "Script", self.config))
        self.assertFalse(_is_allowed_static_asset("https://www.fnde.gov.br/siope/api/data", "GET", "Fetch", self.config))
        self.assertFalse(_is_allowed_static_asset("https://www.fnde.gov.br/siope/js/app.js", "POST", "Script", self.config))

    def test_sanitizer_persists_query_keys_but_not_values(self):
        events = [{
            "url": "https://www.fnde.gov.br/siope/dadosAjax.do?acao=planilhas&token=SECRET",
            "method": "GET",
            "resource_type": "XHR",
        }]
        shapes, candidates = summarize_blocked_requests(events, self.config)
        self.assertEqual(len(shapes), 1)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(shapes[0]["query_keys"], ["acao", "token"])
        self.assertNotIn("SECRET", json.dumps(shapes, sort_keys=True))
        self.assertFalse(shapes[0]["network_sent"])
        self.assertTrue(shapes[0]["intercepted_before_network"])

    def test_cross_origin_xhr_is_blocked_but_not_promoted_candidate(self):
        events = [{
            "url": "https://captcha.example/challenge?id=SECRET",
            "method": "GET",
            "resource_type": "XHR",
        }]
        shapes, candidates = summarize_blocked_requests(events, self.config)
        self.assertEqual(len(shapes), 1)
        self.assertEqual(candidates, [])
        self.assertFalse(shapes[0]["official_host"])
        self.assertNotIn("SECRET", json.dumps(shapes))

    def test_success_reports_candidate_shapes_without_sending_them(self):
        events = [
            {
                "url": "https://www.fnde.gov.br/siope/buscarPlanilhas.do?cod=ABC",
                "method": "GET",
                "resource_type": "XHR",
            },
            {
                "url": "https://www.fnde.gov.br/siope/buscarDados.do?pagina=2",
                "method": "POST",
                "resource_type": "Fetch",
            },
        ]
        result = probe_public_get_runtime_routes(self.config, runtime=FakeRuntime(_raw(events)))
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS")
        self.assertEqual(result["candidate_shape_count"], 2)
        self.assertFalse(result["dynamic_candidate_network_sent"])
        self.assertFalse(result["pilot_limeira_values_sent"])
        self.assertFalse(result["form_submission"])
        self.assertFalse(result["artifact_downloaded"])
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("ABC", serialized)
        self.assertNotIn('"pagina": "2"', serialized)

    def test_zero_dynamic_candidates_is_still_valid_diagnostic_result(self):
        result = probe_public_get_runtime_routes(self.config, runtime=FakeRuntime(_raw([])))
        self.assertEqual(result["candidate_shape_count"], 0)
        self.assertEqual(result["blocked_shape_count"], 0)
        self.assertFalse(result["dynamic_candidate_network_sent"])

    def test_dynamic_network_sent_flag_fails_closed(self):
        raw = _raw([])
        raw["dynamic_candidate_network_sent"] = True
        with self.assertRaisesRegex(SiopePublicGetRuntimeRouteDiagnosticsError, "DYNAMIC_NETWORK_SENT"):
            probe_public_get_runtime_routes(self.config, runtime=FakeRuntime(raw))

    def test_more_than_one_initial_document_send_fails_closed(self):
        raw = _raw([])
        raw["initial_document_continued_count"] = 2
        with self.assertRaisesRegex(SiopePublicGetRuntimeRouteDiagnosticsError, "INITIAL_DOCUMENT_CONTRACT"):
            probe_public_get_runtime_routes(self.config, runtime=FakeRuntime(raw))

    def test_human_challenge_fails_closed_and_keeps_sanitized_shapes(self):
        events = [{
            "url": "https://www.fnde.gov.br/siope/buscarDados.do?secret=VALUE",
            "method": "GET",
            "resource_type": "XHR",
        }]
        with self.assertRaisesRegex(SiopePublicGetRuntimeRouteDiagnosticsError, "HUMAN_CHALLENGE_ACTIVE") as ctx:
            probe_public_get_runtime_routes(self.config, runtime=FakeRuntime(_raw(events, challenge=True)))
        serialized = json.dumps(ctx.exception.diagnostics, sort_keys=True)
        self.assertNotIn("VALUE", serialized)
        self.assertIn("secret", serialized)

    def test_shape_limit_fails_closed(self):
        config = dict(self.config)
        config["max_blocked_shapes"] = 1
        events = [
            {"url": "https://www.fnde.gov.br/siope/a.do", "method": "GET", "resource_type": "XHR"},
            {"url": "https://www.fnde.gov.br/siope/b.do", "method": "GET", "resource_type": "XHR"},
        ]
        with self.assertRaisesRegex(SiopePublicGetRuntimeRouteDiagnosticsError, "SHAPE_LIMIT"):
            probe_public_get_runtime_routes(config, runtime=FakeRuntime(_raw(events)))


if __name__ == "__main__":
    unittest.main()
