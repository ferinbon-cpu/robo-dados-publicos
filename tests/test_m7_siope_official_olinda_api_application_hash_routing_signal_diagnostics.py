from __future__ import annotations

import copy
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_official_olinda_api_application_fragment_target_structure_diagnostics_review import (
    EXPECTED_COUNTS,
    SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsReviewError,
    load_json as load_review_json,
    run_review,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_hash_routing_signal_diagnostics_design import (
    COUNT_FIELDS,
    load_json as load_design_json,
    run_design,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_hash_routing_signal_diagnostics import (
    SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError,
    _analyze_source_into_counts,
    _empty_counts,
    dry_run,
    load_json,
    run_hash_routing_signal_diagnostics,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_fragment_target_structure_diagnostics_review.json"
DESIGN_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_signal_diagnostics_design.json"
LIVE_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_signal_diagnostics.json"


class FakeRuntime:
    def __init__(self, counts: dict, *, candidates=None):
        self.counts = counts
        self.candidates = candidates or []

    def run_probe(self, config: dict) -> dict:
        return {
            "initial_document_continued_count": 1,
            "static_assets_continued_count": 23,
            "local_requests_continued_count": 0,
            "application_surface_verified": True,
            "fragment_present": True,
            "loaded_script_signature_counts": self.counts,
            "blocked_shapes": [{
                "candidate_dynamic_request": False,
                "host": "www.fnde.gov.br",
                "intercepted_before_network": True,
                "method": "GET",
                "network_sent": False,
                "occurrences": 1,
                "official_host": True,
                "query_keys": [],
                "query_present": False,
                "resource_type": "Other",
                "route_without_query": "https://www.fnde.gov.br/favicon.ico",
                "scheme": "https",
            }],
            "candidate_shapes": self.candidates,
            "browser_download_denied": True,
            "script_source_transient_read_performed": True,
        }


class HashRoutingSignalDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review_config = load_review_json(REVIEW_CONFIG)
        cls.evidence_path = ROOT / cls.review_config["evidence_path"]
        cls.evidence = load_review_json(cls.evidence_path)
        cls.review = run_review(cls.review_config, cls.evidence, evidence_path=cls.evidence_path)
        cls.design_config = load_design_json(DESIGN_CONFIG)
        cls.design = run_design(cls.design_config, cls.review)
        cls.live_config = load_json(LIVE_CONFIG)

    def test_pinned_review_is_exact_and_offline(self):
        self.assertEqual(self.evidence["fragment_target_structure_counts"], EXPECTED_COUNTS)
        self.assertEqual(self.review["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS_REVIEW")
        self.assertEqual(self.review["resource_route_contract_status"], "UNPROVEN")
        self.assertFalse(self.review["network_called"])

    def test_review_rejects_tampered_counts(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["fragment_target_structure_counts"]["fragment_route_like_count"] = 1
        with self.assertRaises(SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsReviewError):
            run_review(self.review_config, evidence)

    def test_design_keeps_all_operational_authorizations_closed(self):
        self.assertEqual(self.design["returned_observations"], COUNT_FIELDS)
        self.assertFalse(self.design["fragment_value_read_authorized"])
        self.assertFalse(self.design["navigation_execution_authorized"])
        self.assertFalse(self.design["resource_get_authorized"])
        self.assertFalse(self.design["collection_authorized"])
        self.assertFalse(self.design["processing_authorized"])

    def test_dry_run_is_network_free(self):
        result = dry_run(self.live_config, self.design)
        self.assertIn("DRY_RUN", result["status"])
        self.assertFalse(result["network_called"])
        self.assertFalse(result["fragment_value_read_performed"])
        self.assertFalse(result["navigation_executed"])

    def test_fixed_token_analyzer_returns_counts_only(self):
        counts = _empty_counts()
        source = (
            'angular.module("x",["ngRoute"]).config(function($routeProvider,$locationProvider){'
            '$locationProvider.hashPrefix("!");});'
            'window.onhashchange=function(){return location.hash;};'
            'var x="Dados_Gerais_Siope"; var a="Ano_Consulta",b="Num_Peri",c="Sig_UF";'
        )
        _analyze_source_into_counts(source, self.live_config, counts)
        self.assertGreaterEqual(counts["routing_signal_script_count"], 1)
        self.assertEqual(counts["callable_and_routing_signal_same_script_count"], 1)
        self.assertEqual(counts["callable_parameter_and_routing_signal_same_script_count"], 1)
        self.assertEqual(set(counts), set(COUNT_FIELDS))

    def test_fake_live_runtime_passes_without_fragment_values(self):
        counts = _empty_counts()
        counts.update({
            "parsed_script_count": 3,
            "source_read_count": 3,
            "routing_signal_script_count": 1,
            "callable_name_script_count": 1,
            "callable_and_routing_signal_same_script_count": 1,
            "all_parameter_names_and_routing_signal_same_script_count": 1,
            "callable_parameter_and_routing_signal_same_script_count": 1,
            "hashchange_token_occurrence_count": 1,
        })
        result = run_hash_routing_signal_diagnostics(self.live_config, self.design, runtime=FakeRuntime(counts))
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS")
        self.assertFalse(result["safety"]["fragment_value_read_performed"])
        self.assertFalse(result["safety"]["navigation_executed"])
        self.assertFalse(result["safety"]["resource_get_authorized"])

    def test_dynamic_candidate_is_fail_closed(self):
        counts = _empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        with self.assertRaises(SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError):
            run_hash_routing_signal_diagnostics(
                self.live_config,
                self.design,
                runtime=FakeRuntime(counts, candidates=[{"candidate_dynamic_request": True}]),
            )

    def test_manual_workflow_runs_full_qa_before_live(self):
        text = (ROOT / ".github/workflows/siope-official-olinda-api-application-hash-routing-signal-diagnostics-gate.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        self.assertIn("continue-on-error: true", text)
        self.assertIn("Propagar STOP do gate", text)
        self.assertLess(text.index("python main.py selftest"), text.index("Diagnosticar sinais de hash-routing"))


if __name__ == "__main__":
    unittest.main()
