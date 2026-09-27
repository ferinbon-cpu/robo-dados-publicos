from __future__ import annotations

import unittest
from pathlib import Path

from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_family_intersection_diagnostics_review as review
from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_contract_association_diagnostics_design as design
from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_contract_association_diagnostics as live

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_family_intersection_diagnostics_review.json"
DESIGN_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_contract_association_diagnostics_design.json"
LIVE_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_contract_association_diagnostics.json"
WORKFLOW = ROOT / ".github/workflows/siope-official-olinda-api-application-hash-routing-contract-association-diagnostics-gate.yml"


def reviewed() -> dict:
    cfg = review.load_json(REVIEW_CONFIG)
    evidence_path = ROOT / cfg["evidence_path"]
    return review.run_review(cfg, review.load_json(evidence_path), evidence_path=evidence_path)


def designed() -> dict:
    return design.run_design(design.load_json(DESIGN_CONFIG), reviewed())


def valid_counts() -> dict:
    counts = {field: 0 for field in design.COUNT_FIELDS}
    counts.update({
        "parsed_script_count": 41,
        "source_read_count": 41,
        "source_read_failure_count": 0,
        "callable_occurrence_count": 4,
        "location_hash_family_count": 2,
        "ngroute_family_count": 2,
        "ambiguous_family_count": 0,
        "location_hash_family_all_parameter_names_1024_count": 2,
        "ngroute_family_all_parameter_names_1024_count": 2,
        "location_hash_family_format_window_16384_count": 0,
        "location_hash_family_odata_window_16384_count": 0,
        "location_hash_family_odata_format_window_16384_count": 0,
        "location_hash_family_format_window_65536_count": 0,
        "location_hash_family_odata_window_65536_count": 0,
        "location_hash_family_odata_format_window_65536_count": 0,
        "ngroute_family_format_window_16384_count": 2,
        "ngroute_family_odata_window_16384_count": 0,
        "ngroute_family_odata_format_window_16384_count": 0,
        "ngroute_family_format_window_65536_count": 2,
        "ngroute_family_odata_window_65536_count": 2,
        "ngroute_family_odata_format_window_65536_count": 2,
    })
    return counts


class FakeRuntime:
    def __init__(self, counts=None, candidates=None):
        self.counts = counts or valid_counts()
        self.candidates = candidates or []

    def run_probe(self, config):
        return {
            "initial_document_continued_count": 1,
            "application_surface_verified": True,
            "browser_download_denied": True,
            "script_source_transient_read_performed": True,
            "loaded_script_signature_counts": self.counts,
            "blocked_shapes": [{"network_sent": False, "candidate_dynamic_request": False}],
            "candidate_shapes": self.candidates,
            "fragment_present": True,
            "static_assets_continued_count": 23,
            "local_requests_continued_count": 0,
        }


class HashRoutingContractAssociationDiagnosticsTests(unittest.TestCase):
    def test_pinned_family_review_is_exact_and_offline(self):
        result = reviewed()
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_FAMILY_INTERSECTION_DIAGNOSTICS_REVIEW")
        self.assertEqual(result["primary_family_partition_4096_status"], "EXACT_DISJOINT_TWO_LOCATION_HASH_ONLY_AND_TWO_NGROUTE_ONLY")
        self.assertEqual(result["resource_route_contract_status"], "UNPROVEN")
        self.assertFalse(result["network_called"])

    def test_review_rejects_tampered_family_count(self):
        cfg = review.load_json(REVIEW_CONFIG)
        evidence_path = ROOT / cfg["evidence_path"]
        evidence = review.load_json(evidence_path)
        evidence["hash_routing_family_intersection_counts"]["location_hash_only_window_4096_count"] = 1
        with self.assertRaises(review.SiopeOfficialOlindaApiApplicationHashRoutingFamilyIntersectionDiagnosticsReviewError):
            review.run_review(cfg, evidence)

    def test_design_has_exact_fields_and_closed_operations(self):
        result = designed()
        self.assertEqual(len(result["returned_observations"]), 21)
        self.assertEqual(result["family_classification_window_chars"], 4096)
        self.assertEqual(result["contract_windows_chars"], [16384, 65536])
        self.assertTrue(result["script_source_transient_read_authorized"])
        for key in ("fragment_value_read_authorized", "navigation_execution_authorized", "history_state_mutation_authorized", "resource_get_authorized", "collection_authorized", "processing_authorized"):
            self.assertFalse(result[key])

    def test_analyzer_assigns_location_hash_family_and_contract_buckets(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        source = "$format " + ("x" * 10000) + " location.hash " + ("x" * 100) + " Dados_Gerais_Siope Ano_Consulta Num_Peri Sig_UF " + ("x" * 20000) + "/odata/"
        live._analyze_source_into_counts(source, cfg, counts)
        self.assertEqual(counts["callable_occurrence_count"], 1)
        self.assertEqual(counts["location_hash_family_count"], 1)
        self.assertEqual(counts["ngroute_family_count"], 0)
        self.assertEqual(counts["ambiguous_family_count"], 0)
        self.assertEqual(counts["location_hash_family_all_parameter_names_1024_count"], 1)
        self.assertEqual(counts["location_hash_family_format_window_16384_count"], 1)
        self.assertEqual(counts["location_hash_family_odata_window_16384_count"], 0)
        self.assertEqual(counts["location_hash_family_odata_window_65536_count"], 1)
        self.assertEqual(counts["location_hash_family_odata_format_window_65536_count"], 1)

    def test_analyzer_assigns_ngroute_family(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        source = "ngRoute " + ("x" * 100) + " Dados_Gerais_Siope Ano_Consulta Num_Peri Sig_UF $format /odata/"
        live._analyze_source_into_counts(source, cfg, counts)
        self.assertEqual(counts["ngroute_family_count"], 1)
        self.assertEqual(counts["ngroute_family_format_window_16384_count"], 1)
        self.assertEqual(counts["ngroute_family_odata_window_16384_count"], 1)
        self.assertEqual(counts["ngroute_family_odata_format_window_16384_count"], 1)

    def test_dry_run_is_network_free(self):
        result = live.dry_run(live.load_json(LIVE_CONFIG), designed())
        self.assertFalse(result["network_called"])
        self.assertFalse(result["script_source_transient_read_performed"])
        self.assertFalse(result["fragment_value_read_performed"])
        self.assertFalse(result["navigation_executed"])
        self.assertFalse(result["resource_get_authorized"])

    def test_ambiguous_family_fails_closed(self):
        counts = valid_counts()
        counts["location_hash_family_count"] = 1
        counts["ambiguous_family_count"] = 1
        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationHashRoutingContractAssociationDiagnosticsError):
            live._validate_counts(counts, live.load_json(LIVE_CONFIG))

    def test_family_partition_drift_fails_closed(self):
        counts = valid_counts()
        counts["ngroute_family_count"] = 1
        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationHashRoutingContractAssociationDiagnosticsError):
            live._validate_counts(counts, live.load_json(LIVE_CONFIG))

    def test_nonmonotonic_contract_counts_fail_closed(self):
        counts = valid_counts()
        counts["ngroute_family_odata_window_16384_count"] = 2
        counts["ngroute_family_odata_window_65536_count"] = 1
        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationHashRoutingContractAssociationDiagnosticsError):
            live._validate_counts(counts, live.load_json(LIVE_CONFIG))

    def test_fake_live_passes_without_route_promotion_or_resource_get(self):
        result = live.run_hash_routing_contract_association_diagnostics(live.load_json(LIVE_CONFIG), designed(), runtime=FakeRuntime())
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_CONTRACT_ASSOCIATION_DIAGNOSTICS")
        self.assertFalse(result["safety"]["resource_get_authorized"])
        self.assertFalse(result["safety"]["route_synthesized_or_guessed"])
        self.assertFalse(result["safety"]["automatic_route_promotion"])
        self.assertFalse(result["safety"]["fragment_value_read_performed"])

    def test_dynamic_candidate_fails_closed(self):
        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationHashRoutingContractAssociationDiagnosticsError):
            live.run_hash_routing_contract_association_diagnostics(
                live.load_json(LIVE_CONFIG), designed(),
                runtime=FakeRuntime(candidates=[{"candidate_dynamic_request": True, "network_sent": False}]),
            )

    def test_manual_workflow_full_qa_precedes_live(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_official_olinda_application_hash_routing_contract_association_diagnostics", text)
        self.assertLess(text.index("python -m unittest discover -s tests -v"), text.index("Diagnosticar associação entre famílias de hash-routing e contrato OData"))
        self.assertLess(text.index("python main.py selftest"), text.index("Diagnosticar associação entre famílias de hash-routing e contrato OData"))
        self.assertNotIn("352690", text)
        self.assertNotIn("Limeira", text)


if __name__ == "__main__":
    unittest.main()
