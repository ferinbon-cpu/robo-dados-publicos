from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_syntax_skeleton_diagnostics_review import (
    SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsReviewError,
    load_json as load_review_json,
    run_review,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_fragment_target_structure_diagnostics_design import (
    COUNT_FIELDS,
    run_design,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_fragment_target_structure_diagnostics import (
    SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError,
    dry_run,
    load_json,
    run_fragment_target_structure_diagnostics,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_dom_syntax_skeleton_diagnostics_review.json"
DESIGN_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_fragment_target_structure_diagnostics_design.json"
LIVE_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_fragment_target_structure_diagnostics.json"
MODULE = ROOT / "robo_dados_publicos/sources/siope_official_olinda_api_application_fragment_target_structure_diagnostics.py"
WORKFLOW = ROOT / ".github/workflows/siope-official-olinda-api-application-fragment-target-structure-diagnostics-gate.yml"


def review_result():
    cfg = load_review_json(REVIEW_CONFIG)
    evidence_path = ROOT / cfg["evidence_path"]
    return run_review(cfg, load_review_json(evidence_path), evidence_path=evidence_path)


def design_result():
    return run_design(load_json(DESIGN_CONFIG), review_result())


def valid_counts():
    counts = {field: 0 for field in COUNT_FIELDS}
    counts.update({
        "fragment_navigation_match_count": 2,
        "distinct_fragment_value_count": 2,
        "fragment_route_like_count": 2,
        "fragment_target_resolved_count": 1,
        "fragment_target_contains_callable_name_count": 1,
        "fragment_target_contains_all_parameter_names_count": 1,
        "fragment_target_ordered_parameter_sequence_count": 1,
    })
    return counts


class FakeRuntime:
    def __init__(self, counts=None, candidates=None):
        self.counts = counts or valid_counts()
        self.candidates = candidates or []

    def run_probe(self, config):
        return {
            "application_surface_verified": True,
            "fragment_present": True,
            "fragment_target_structure_counts": self.counts,
            "initial_document_continued_count": 1,
            "official_static_asset_network_sent_count": 23,
            "local_request_count": 0,
            "blocked_shapes": [{"network_sent": False, "candidate_dynamic_request": False}],
            "candidate_shapes": self.candidates,
            "browser_download_denied": True,
        }


class TestM7SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnostics(unittest.TestCase):
    def test_pinned_dom_syntax_review_passes_exact_run_two(self):
        result = review_result()
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS_REVIEW")
        self.assertEqual(result["evidence_run_id"], 32923640522)
        self.assertEqual(result["technical_callable_presence_status"], "TWO_EXACT_CALLABLE_OCCURRENCES_IN_MINIMAL_CONTAINER_ON_PINNED_RUN")
        self.assertEqual(result["rendered_dom_known_syntax_strategy_status"], "EXHAUSTED_FOR_THIS_KNOWN_TEXTUAL_SKELETON_ON_PINNED_RUN")
        self.assertEqual(result["resource_route_contract_status"], "UNPROVEN")

    def test_tampered_dom_syntax_evidence_fails_closed(self):
        cfg = load_review_json(REVIEW_CONFIG)
        evidence_path = ROOT / cfg["evidence_path"]
        evidence = copy.deepcopy(load_review_json(evidence_path))
        evidence["dom_syntax_skeleton_counts"]["callable_open_paren_in_minimal_container_count"] = 1
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsReviewError):
            run_review(cfg, evidence)

    def test_design_has_exact_sixteen_counts_and_closed_operations(self):
        cfg = load_json(DESIGN_CONFIG)
        result = run_design(cfg, review_result())
        self.assertEqual(result["returned_observations"], COUNT_FIELDS)
        self.assertTrue(result["fragment_value_transient_read_authorized"])
        self.assertTrue(result["fragment_target_text_transient_read_authorized"])
        self.assertFalse(result["raw_fragment_material_return_authorized"])
        self.assertFalse(result["navigation_execution_authorized"])
        self.assertFalse(result["history_state_mutation_authorized"])
        self.assertFalse(result["resource_get_authorized"])
        self.assertFalse(result["network_called"])

    def test_dry_run_has_zero_network_raw_material_and_authorization(self):
        result = dry_run(load_json(LIVE_CONFIG), design_result())
        self.assertFalse(result["network_called"])
        self.assertFalse(result["fragment_value_transient_read_performed"])
        self.assertFalse(result["fragment_target_text_transient_read_performed"])
        self.assertFalse(result["dynamic_candidate_network_sent"])
        self.assertFalse(result["resource_get_authorized"])

    def test_valid_fake_runtime_passes_without_route_promotion(self):
        result = run_fragment_target_structure_diagnostics(load_json(LIVE_CONFIG), design_result(), runtime=FakeRuntime())
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS")
        self.assertEqual(result["fragment_target_structure_counts"], valid_counts())
        self.assertEqual(result["candidate_shape_count"], 0)
        self.assertTrue(result["safety"]["fragment_value_transient_read_performed"])
        self.assertTrue(result["safety"]["fragment_target_text_transient_read_performed"])
        self.assertFalse(result["safety"]["raw_navigation_value_returned"])
        self.assertFalse(result["safety"]["navigation_executed"])
        self.assertFalse(result["safety"]["history_state_mutated"])
        self.assertFalse(result["safety"]["route_synthesized_or_guessed"])
        self.assertFalse(result["safety"]["resource_get_authorized"])

    def test_invalid_counts_fail_closed(self):
        variants = []
        extra = valid_counts(); extra["raw_fragment"] = 1; variants.append(extra)
        nonint = valid_counts(); nonint["fragment_navigation_match_count"] = True; variants.append(nonint)
        too_few = valid_counts(); too_few["fragment_navigation_match_count"] = 1; variants.append(too_few)
        too_many = valid_counts(); too_many["fragment_navigation_match_count"] = 9; variants.append(too_many)
        distinct = valid_counts(); distinct["distinct_fragment_value_count"] = 3; variants.append(distinct)
        subset = valid_counts(); subset["fragment_target_contract_like_count"] = 1; variants.append(subset)
        for counts in variants:
            with self.subTest(counts=counts):
                with self.assertRaises(SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError):
                    run_fragment_target_structure_diagnostics(load_json(LIVE_CONFIG), design_result(), runtime=FakeRuntime(counts=counts))

    def test_unexpected_dynamic_candidate_fails_closed(self):
        with self.assertRaises(SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError):
            run_fragment_target_structure_diagnostics(
                load_json(LIVE_CONFIG), design_result(), runtime=FakeRuntime(candidates=[{"network_sent": False}])
            )

    def test_live_config_is_nonpilot_and_every_operation_stays_closed(self):
        cfg = load_json(LIVE_CONFIG)
        self.assertNotIn("352690", cfg["exact_application_url"])
        self.assertNotIn("Limeira", cfg["exact_application_url"])
        for key in (
            "raw_navigation_value_return", "navigation_fragment_return", "fragment_target_identifier_return",
            "fragment_target_text_return", "dom_interaction", "navigation_execution", "history_state_mutation",
            "dynamic_candidate_network_send", "resource_data_request", "pilot_limeira_values_send",
            "post_request_send", "head_request", "route_synthesis_or_guessing", "automatic_route_promotion",
        ):
            self.assertEqual(cfg[key], "PROHIBITED")

    def test_source_reads_fragment_and_existing_target_only_transiently_without_navigation(self):
        text = MODULE.read_text(encoding="utf-8")
        self.assertIn("getAttribute('href')", text)
        self.assertIn("document.getElementById(key)", text)
        self.assertIn("document.getElementsByName(key)", text)
        self.assertIn("textContent", text)
        self.assertNotIn("Page.click", text)
        self.assertNotIn("location.href =", text)
        self.assertNotIn("window.location =", text)
        self.assertNotIn("history.pushState", text)
        self.assertNotIn("history.replaceState", text)
        self.assertNotIn("dispatchEvent", text)
        self.assertNotIn(".click()", text)
        self.assertNotIn("rawFragment\":", text)
        self.assertNotIn("fragment_target_text\":", text)

    def test_workflow_is_manual_read_only_full_qa_sanitized_and_no_navigation(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("contents: read", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("confirm_official_olinda_application_fragment_target_structure_diagnostics", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        self.assertIn("siope-official-olinda-application-fragment-target-structure-diagnostics-evidence/result.json", text)
        for forbidden in ("352690", "Limeira", "curl ", "wget ", "requests.get", "requests.post", "Page.click", "form.submit", "history.pushState"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
