from __future__ import annotations

import copy
import unittest
from pathlib import Path

from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_locality_diagnostics_review as review
from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_family_intersection_diagnostics_design as design
from robo_dados_publicos.sources import siope_official_olinda_api_application_hash_routing_family_intersection_diagnostics as live

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_locality_diagnostics_review.json"
DESIGN_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_family_intersection_diagnostics_design.json"
LIVE_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_hash_routing_family_intersection_diagnostics.json"
WORKFLOW = ROOT / ".github/workflows/siope-official-olinda-api-application-hash-routing-family-intersection-diagnostics-gate.yml"


def pinned_review() -> dict:
    cfg = review.load_json(REVIEW_CONFIG)
    evidence_path = ROOT / cfg["evidence_path"]
    return review.run_review(cfg, review.load_json(evidence_path), evidence_path=evidence_path)


def designed() -> dict:
    return design.run_design(design.load_json(DESIGN_CONFIG), pinned_review())


class HashRoutingFamilyIntersectionDiagnosticsTests(unittest.TestCase):
    def test_pinned_review_is_exact_offline_and_overlap_unproven(self):
        result = pinned_review()
        self.assertEqual(
            result["status"],
            "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_LOCALITY_DIAGNOSTICS_REVIEW",
        )
        self.assertEqual(
            result["routing_family_overlap_status"],
            "UNPROVEN_COUNTS_DO_NOT_IDENTIFY_WHETHER_LOCATION_HASH_AND_NGROUTE_OCCUR_ON_SAME_OR_DIFFERENT_CALLABLE_OCCURRENCES",
        )
        self.assertEqual(result["resource_route_contract_status"], "UNPROVEN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["resource_get_authorized"])

    def test_review_rejects_tampered_locality_count(self):
        cfg = review.load_json(REVIEW_CONFIG)
        evidence_path = ROOT / cfg["evidence_path"]
        evidence = review.load_json(evidence_path)
        evidence["hash_routing_locality_counts"]["location_hash_window_4096_count"] += 1
        with self.assertRaises(review.SiopeOfficialOlindaApiApplicationHashRoutingLocalityDiagnosticsReviewError):
            review.run_review(cfg, evidence)

    def test_design_has_exact_partition_fields_and_closed_operations(self):
        result = designed()
        self.assertEqual(result["window_radii_chars"], [1024, 4096, 16384, 65536])
        self.assertEqual(len(result["returned_observations"]), 52)
        self.assertEqual(
            result["observation_semantics"],
            "CALLABLE_CENTERED_EXACT_PRIMARY_ROUTING_PRESENCE_MASK_PARTITION_AND_SECONDARY_ONLY_INTEGER_COUNTS",
        )
        self.assertTrue(result["script_source_transient_read_authorized"])
        for key in (
            "script_source_return_authorized",
            "fragment_value_read_authorized",
            "new_script_network_request_authorized",
            "navigation_execution_authorized",
            "history_state_mutation_authorized",
            "resource_get_authorized",
            "collection_authorized",
            "processing_authorized",
            "recurrence_authorized",
            "schedule_enabled",
        ):
            self.assertFalse(result[key])

    def test_analyzer_assigns_exact_location_hash_ngroute_mask(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        source = (
            "location.hash; "
            + "x" * 200
            + " Dados_Gerais_Siope(Ano_Consulta, Num_Peri, Sig_UF); "
            + "x" * 200
            + " ngRoute"
        )
        live._analyze_source_into_counts(source, cfg, counts)
        self.assertEqual(counts["callable_occurrence_count"], 1)
        self.assertEqual(counts["location_hash_ngroute_window_1024_count"], 1)
        self.assertEqual(counts["location_hash_only_window_1024_count"], 0)
        self.assertEqual(counts["ngroute_only_window_1024_count"], 0)
        self.assertEqual(counts["primary_none_window_1024_count"], 0)
        self.assertEqual(counts["any_known_routing_window_1024_count"], 1)
        self.assertEqual(counts["all_parameter_names_window_1024_count"], 1)
        self.assertEqual(counts["all_parameter_names_and_any_known_routing_window_1024_count"], 1)

    def test_secondary_only_partition_equation_is_valid(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        counts["callable_occurrence_count"] = 1
        for radius in live.RADII:
            counts[f"primary_none_window_{radius}_count"] = 1
            counts[f"secondary_routing_without_primary_window_{radius}_count"] = 1
            counts[f"any_known_routing_window_{radius}_count"] = 1
        live._validate_counts(counts, cfg)

    def test_partition_mismatch_fails_closed(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        counts["callable_occurrence_count"] = 1
        for radius in live.RADII:
            counts[f"primary_none_window_{radius}_count"] = 1
        counts["location_hash_only_window_4096_count"] = 1
        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationHashRoutingFamilyIntersectionDiagnosticsError):
            live._validate_counts(counts, cfg)

    def test_nonmonotonic_any_known_routing_fails_closed(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1
        counts["callable_occurrence_count"] = 1
        for radius in live.RADII:
            counts[f"primary_none_window_{radius}_count"] = 1
        counts["primary_none_window_1024_count"] = 0
        counts["location_hash_only_window_1024_count"] = 1
        counts["any_known_routing_window_1024_count"] = 1
        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationHashRoutingFamilyIntersectionDiagnosticsError):
            live._validate_counts(counts, cfg)

    def test_dry_run_is_network_free(self):
        result = live.dry_run(live.load_json(LIVE_CONFIG), designed())
        self.assertFalse(result["network_called"])
        self.assertFalse(result["script_source_transient_read_performed"])
        self.assertFalse(result["fragment_value_read_performed"])
        self.assertFalse(result["navigation_executed"])
        self.assertFalse(result["resource_get_authorized"])

    def test_dynamic_candidate_fails_closed(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1

        class FakeRuntime:
            def run_probe(self, _config):
                return {
                    "initial_document_continued_count": 1,
                    "application_surface_verified": True,
                    "browser_download_denied": True,
                    "script_source_transient_read_performed": True,
                    "loaded_script_signature_counts": counts,
                    "blocked_shapes": [],
                    "candidate_shapes": [{"network_sent": False}],
                }

        with self.assertRaises(live.SiopeOfficialOlindaApiApplicationHashRoutingFamilyIntersectionDiagnosticsError):
            live.run_hash_routing_family_intersection_diagnostics(cfg, designed(), runtime=FakeRuntime())

    def test_fake_live_passes_without_route_promotion(self):
        cfg = live.load_json(LIVE_CONFIG)
        counts = live._empty_counts()
        counts["parsed_script_count"] = 1
        counts["source_read_count"] = 1

        class FakeRuntime:
            def run_probe(self, _config):
                return {
                    "initial_document_continued_count": 1,
                    "application_surface_verified": True,
                    "browser_download_denied": True,
                    "script_source_transient_read_performed": True,
                    "fragment_present": True,
                    "loaded_script_signature_counts": counts,
                    "blocked_shapes": [],
                    "candidate_shapes": [],
                    "static_assets_continued_count": 0,
                    "local_requests_continued_count": 0,
                }

        result = live.run_hash_routing_family_intersection_diagnostics(cfg, designed(), runtime=FakeRuntime())
        self.assertEqual(
            result["status"],
            "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_FAMILY_INTERSECTION_DIAGNOSTICS",
        )
        self.assertFalse(result["safety"]["route_synthesized_or_guessed"])
        self.assertFalse(result["safety"]["automatic_route_promotion"])
        self.assertFalse(result["safety"]["resource_get_authorized"])
        self.assertFalse(result["safety"]["pilot_limeira_values_sent"])

    def test_manual_workflow_full_qa_precedes_live(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_official_olinda_application_hash_routing_family_intersection_diagnostics", text)
        self.assertIn("contents: read", text)
        live_step = text.index("Diagnosticar interseções entre famílias de hash-routing")
        self.assertLess(text.index("python -m unittest discover -s tests -v"), live_step)
        self.assertLess(text.index("python main.py selftest"), live_step)
        self.assertIn("continue-on-error: true", text)
        self.assertIn("Propagar STOP do gate", text)
        self.assertNotIn("curl ", text)
        self.assertNotIn("wget ", text)


if __name__ == "__main__":
    unittest.main()
