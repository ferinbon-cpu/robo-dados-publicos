from __future__ import annotations

import unittest
from pathlib import Path

from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_signal_diagnostics_review as review
from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_locality_diagnostics_design as design
from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_locality_diagnostics as live

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_signal_diagnostics_review.json"
DESIGN_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_locality_diagnostics_design.json"
LIVE_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_locality_diagnostics.json"
WORKFLOW = ROOT / ".github/workflows/siope-official-olinda-api-application-hash-routing-locality-diagnostics-gate.yml"

def pinned_review():
    cfg = review.load_json(REVIEW_CONFIG)
    evidence_path = ROOT / cfg["evidence_path"]
    return review.run_review(cfg, review.load_json(evidence_path), evidence_path=evidence_path)

def designed():
    return design.run_design(design.load_json(DESIGN_CONFIG), pinned_review())

class HashRoutingLocalityDiagnosticsTests(unittest.TestCase):
    def test_pinned_review_is_exact_offline_and_unproven(self):
        result = pinned_review()
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS_REVIEW")
        self.assertEqual(result["hash_routing_locality_status"], "UNPROVEN_SAME_SCRIPT_ONLY")
        self.assertEqual(result["resource_route_contract_status"], "UNPROVEN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["resource_get_authorized"])

    def test_review_rejects_tampered_counts(self):
        cfg = review.load_json(REVIEW_CONFIG)
        evidence_path = ROOT / cfg["evidence_path"]
        evidence = review.load_json(evidence_path)
        evidence["hash_routing_signal_counts"]["location_hash_token_occurrence_count"] += 1
        with self.assertRaises(review.SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsReviewError):
            review.run_review(cfg, evidence)

    def test_design_is_bounded_and_closed(self):
        result = designed()
        self.assertEqual(result["window_radii_chars"], [1024, 4096, 16384, 65536])
        self.assertEqual(len(result["returned_observations"]), 36)
        self.assertTrue(result["script_source_transient_read_authorized"])
        for key in ("fragment_value_read_authorized", "navigation_execution_authorized", "resource_get_authorized", "collection_authorized", "processing_authorized"):
            self.assertFalse(result[key])

    def test_analyzer_counts_callable_centered_locality(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        source = "location.hash; " + "x" * 300 + " " + "Dados_Gerais_Siope(Ano_Consulta, Num_Peri, Sig_UF);" + " " + "x" * 300 + " $routeProvider ngRoute hashchange hashPrefix"
        live._analyze_source_into_counts(source, cfg, counts)
        self.assertEqual(counts["callable_occurrence_count"], 1)
        self.assertEqual(counts["any_routing_signal_window_1024_count"], 1)
        self.assertEqual(counts["all_parameter_names_and_any_routing_signal_window_1024_count"], 1)
        self.assertEqual(counts["location_hash_window_1024_count"], 1)
        self.assertEqual(counts["route_provider_window_1024_count"], 1)

    def test_dry_run_is_network_free(self):
        result = live.dry_run(live.load_json(LIVE_CONFIG), designed())
        self.assertFalse(result["network_called"])
        self.assertFalse(result["script_source_transient_read_performed"])
        self.assertFalse(result["fragment_value_read_performed"])
        self.assertFalse(result["navigation_executed"])

    def test_nonmonotonic_counts_fail_closed(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        counts.update({"parsed_script_count": 1, "source_read_count": 1, "callable_occurrence_count": 1})
        counts["any_routing_signal_window_1024_count"] = 1
        counts["any_routing_signal_window_4096_count"] = 0
        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationHashRoutingLocalityDiagnosticsError):
            live._validate_counts(counts, cfg)

    def test_dynamic_candidate_fails_closed(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        class FakeRuntime:
            def run_probe(self, _config):
                return {"initial_document_continued_count": 1, "application_surface_verified": True, "browser_download_denied": True, "script_source_transient_read_performed": True, "loaded_script_signature_counts": counts, "blocked_shapes": [], "candidate_shapes": [{"network_sent": False}]}
        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationHashRoutingLocalityDiagnosticsError):
            live.run_hash_routing_locality_diagnostics(cfg, designed(), runtime=FakeRuntime())

    def test_fake_live_passes_without_route_promotion(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        class FakeRuntime:
            def run_probe(self, _config):
                return {"initial_document_continued_count": 1, "application_surface_verified": True, "browser_download_denied": True, "script_source_transient_read_performed": True, "fragment_present": True, "loaded_script_signature_counts": counts, "blocked_shapes": [], "candidate_shapes": [], "static_assets_continued_count": 0, "local_requests_continued_count": 0}
        result = live.run_hash_routing_locality_diagnostics(cfg, designed(), runtime=FakeRuntime())
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_LOCALITY_DIAGNOSTICS")
        self.assertFalse(result["safety"]["route_synthesized_or_guessed"])
        self.assertFalse(result["safety"]["automatic_route_promotion"])
        self.assertFalse(result["safety"]["resource_get_authorized"])

    def test_manual_workflow_full_qa_precedes_live(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_official_olinda_application_hash_routing_locality_diagnostics", text)
        self.assertIn("contents: read", text)
        self.assertLess(text.index("python -m unittest discover -s tests -v"), text.index("Diagnosticar localidade de hash-routing"))
        self.assertLess(text.index("python main.py selftest"), text.index("Diagnosticar localidade de hash-routing"))
        self.assertIn("continue-on-error: true", text)
        self.assertIn("Propagar STOP do gate", text)

if __name__ == "__main__":
    unittest.main()
