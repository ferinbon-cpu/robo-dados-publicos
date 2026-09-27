from __future__ import annotations

import copy
import re
import unittest
from pathlib import Path

from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_contract_association_diagnostics_review as review
from robo_dados_publicos.sources import siope_official_olinda_api_application_location_hash_odata_side_diagnostics_design as design
from robo_dados_publicos.sources import siope_official_olinda_api_application_location_hash_odata_side_diagnostics as live

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_contract_association_diagnostics_review.json"
DESIGN_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_location_hash_odata_side_diagnostics_design.json"
LIVE_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_location_hash_odata_side_diagnostics.json"
WORKFLOW = ROOT / ".github/workflows/siope-official-olinda-api-application-location-hash-odata-side-diagnostics-gate.yml"


def reviewed() -> dict:
    cfg = review.load_json(REVIEW_CONFIG)
    evidence_path = ROOT / cfg["evidence_path"]
    return review.run_review(cfg, review.load_json(evidence_path), evidence_path=evidence_path)


def designed() -> dict:
    return design.run_design(design.load_json(DESIGN_CONFIG), reviewed())


def valid_counts() -> dict:
    counts = {field: 0 for field in design.COUNT_FIELDS}
    counts.update({
        "parsed_script_count": 43,
        "source_read_count": 43,
        "source_read_failure_count": 0,
        "callable_occurrence_count": 4,
        "location_hash_family_count": 2,
        "ngroute_family_count": 2,
        "ambiguous_family_count": 0,
        "location_hash_family_all_parameter_names_1024_count": 2,
        "location_hash_token_nearest_left_4096_count": 2,
        "location_hash_token_nearest_right_4096_count": 0,
        "location_hash_token_nearest_tie_4096_count": 0,
        "format_nearest_left_16384_count": 2,
        "format_nearest_right_16384_count": 0,
        "format_nearest_tie_16384_count": 0,
        "format_absent_16384_count": 0,
        "odata_nearest_left_65536_count": 2,
        "odata_nearest_right_65536_count": 0,
        "odata_nearest_tie_65536_count": 0,
        "odata_absent_65536_count": 0,
        "nearest_location_hash_and_format_same_side_count": 2,
        "nearest_format_and_odata_same_side_count": 2,
        "nearest_all_three_same_side_count": 2,
        "nearest_all_three_left_count": 2,
        "nearest_all_three_right_count": 0,
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


class LocationHashOdataSideDiagnosticsTests(unittest.TestCase):
    def test_pinned_contract_association_review_is_exact_and_offline(self):
        result = reviewed()
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_CONTRACT_ASSOCIATION_DIAGNOSTICS_REVIEW")
        self.assertEqual(result["contract_family_status"], "KNOWN_ODATA_CONTRACT_TOKENS_ARE_EXCLUSIVELY_ASSOCIATED_WITH_LOCATION_HASH_FAMILY_ON_PINNED_RUN")
        self.assertEqual(result["resource_route_contract_status"], "UNPROVEN")
        self.assertFalse(result["network_called"])

    def test_review_rejects_tampered_contract_count(self):
        cfg = review.load_json(REVIEW_CONFIG)
        evidence_path = ROOT / cfg["evidence_path"]
        evidence = copy.deepcopy(review.load_json(evidence_path))
        evidence["hash_routing_contract_association_counts"]["ngroute_family_odata_window_65536_count"] = 1
        with self.assertRaises(review.SiopeOfficialOlindaApiApplicationHashRoutingContractAssociationDiagnosticsReviewError):
            review.run_review(cfg, evidence)

    def test_design_has_exact_fields_and_closed_operations(self):
        result = designed()
        self.assertEqual(len(result["returned_observations"]), 24)
        self.assertEqual(result["family_classification_window_chars"], 4096)
        self.assertEqual(result["format_window_chars"], 16384)
        self.assertEqual(result["odata_window_chars"], 65536)
        self.assertTrue(result["script_source_transient_read_authorized"])
        for key in ("fragment_value_read_authorized", "navigation_execution_authorized", "history_state_mutation_authorized", "resource_get_authorized", "collection_authorized", "processing_authorized"):
            self.assertFalse(result[key])

    def test_nearest_side_left_right_and_none(self):
        source = "TOKEN----------CALL-TOKEN"
        match = re.search("CALL", source)
        self.assertIsNotNone(match)
        self.assertEqual(live._nearest_side(source, match, "TOKEN", 100), "right")
        source2 = "TOKEN-CALL----------TOKEN"
        match2 = re.search("CALL", source2)
        self.assertEqual(live._nearest_side(source2, match2, "TOKEN", 100), "left")
        source3 = "aaa x CALL zzz"
        self.assertEqual(live._nearest_side(source3, re.search("CALL", source3), "TOKEN", 100), "none")

    def test_nearest_side_tie(self):
        source = "TOKENxxCALLxxTOKEN"
        match = re.search("CALL", source)
        self.assertEqual(live._nearest_side(source, match, "TOKEN", 100), "tie")

    def test_analyzer_counts_all_three_on_left_for_location_hash_family(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        source = "/odata/ " + ("x" * 200) + " $format " + ("x" * 200) + " location.hash " + ("x" * 100) + " Dados_Gerais_Siope Ano_Consulta Num_Peri Sig_UF"
        live._analyze_source_into_counts(source, cfg, counts)
        self.assertEqual(counts["callable_occurrence_count"], 1)
        self.assertEqual(counts["location_hash_family_count"], 1)
        self.assertEqual(counts["location_hash_family_all_parameter_names_1024_count"], 1)
        self.assertEqual(counts["location_hash_token_nearest_left_4096_count"], 1)
        self.assertEqual(counts["format_nearest_left_16384_count"], 1)
        self.assertEqual(counts["odata_nearest_left_65536_count"], 1)
        self.assertEqual(counts["nearest_all_three_same_side_count"], 1)
        self.assertEqual(counts["nearest_all_three_left_count"], 1)

    def test_ngroute_family_is_partitioned_but_not_side_analyzed(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        source = "ngRoute " + ("x" * 100) + " Dados_Gerais_Siope Ano_Consulta Num_Peri Sig_UF"
        live._analyze_source_into_counts(source, cfg, counts)
        self.assertEqual(counts["ngroute_family_count"], 1)
        self.assertEqual(counts["location_hash_family_count"], 0)
        self.assertEqual(sum(counts[field] for field in design.COUNT_FIELDS[8:]), 0)

    def test_dry_run_is_network_free(self):
        result = live.dry_run(live.load_json(LIVE_CONFIG), designed())
        self.assertFalse(result["network_called"])
        self.assertFalse(result["script_source_transient_read_performed"])
        self.assertFalse(result["fragment_value_read_performed"])
        self.assertFalse(result["navigation_executed"])
        self.assertFalse(result["resource_get_authorized"])

    def test_family_partition_drift_fails_closed(self):
        counts = valid_counts()
        counts["location_hash_family_count"] = 1
        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError):
            live._validate_counts(counts, live.load_json(LIVE_CONFIG))

    def test_format_or_odata_absence_fails_closed(self):
        counts = valid_counts()
        counts["format_nearest_left_16384_count"] = 1
        counts["format_absent_16384_count"] = 1
        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError):
            live._validate_counts(counts, live.load_json(LIVE_CONFIG))
        counts = valid_counts()
        counts["odata_nearest_left_65536_count"] = 1
        counts["odata_absent_65536_count"] = 1
        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError):
            live._validate_counts(counts, live.load_json(LIVE_CONFIG))

    def test_side_partition_mismatch_fails_closed(self):
        counts = valid_counts()
        counts["location_hash_token_nearest_left_4096_count"] = 1
        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError):
            live._validate_counts(counts, live.load_json(LIVE_CONFIG))

    def test_fake_live_passes_without_route_promotion_or_resource_get(self):
        result = live.run_location_hash_odata_side_diagnostics(live.load_json(LIVE_CONFIG), designed(), runtime=FakeRuntime())
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOCATION_HASH_ODATA_SIDE_DIAGNOSTICS")
        self.assertFalse(result["safety"]["resource_get_authorized"])
        self.assertFalse(result["safety"]["route_synthesized_or_guessed"])
        self.assertFalse(result["safety"]["automatic_route_promotion"])
        self.assertFalse(result["safety"]["fragment_value_read_performed"])
        self.assertFalse(result["safety"]["navigation_executed"])

    def test_dynamic_candidate_fails_closed(self):
        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError):
            live.run_location_hash_odata_side_diagnostics(
                live.load_json(LIVE_CONFIG), designed(),
                runtime=FakeRuntime(candidates=[{"candidate_dynamic_request": True, "network_sent": False}]),
            )

    def test_manual_workflow_full_qa_precedes_live_and_has_no_forbidden_commands(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        live_step = "Diagnosticar lado relativo entre location.hash e contrato OData"
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_official_olinda_application_location_hash_odata_side_diagnostics", text)
        self.assertLess(text.index("python -m unittest discover -s tests -v"), text.index(live_step))
        self.assertLess(text.index("python main.py selftest"), text.index(live_step))
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("352690", text)
        self.assertNotIn("Limeira", text)
        for forbidden in ("curl ", "wget ", "requests.get", "requests.post", "git push", "schedule:"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
