from __future__ import annotations

import copy
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_navigation_attribute_contract_diagnostics_review import run_review
from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_navigation_match_distribution_diagnostics import (
    COUNT_FIELDS,
    SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError,
    dry_run,
    load_json,
    run_navigation_match_distribution_diagnostics,
)
from robo_dados_publicos.sources.siope_official_olinda_api_application_dom_navigation_match_distribution_diagnostics_design import run_design

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_dom_navigation_attribute_contract_diagnostics_review.json"
EVIDENCE = ROOT / "docs/evidence/M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_RUN_1_0.8.0.json"
DESIGN_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_dom_navigation_match_distribution_diagnostics_design.json"
LIVE_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_api_application_dom_navigation_match_distribution_diagnostics.json"
WORKFLOW = ROOT / ".github/workflows/siope-official-olinda-api-application-dom-navigation-match-distribution-diagnostics-gate.yml"
SOURCE = ROOT / "robo_dados_publicos/sources/siope_official_olinda_api_application_dom_navigation_match_distribution_diagnostics.py"


def prior_review() -> dict:
    return run_review(load_json(REVIEW_CONFIG), load_json(EVIDENCE))


def design_result() -> dict:
    return run_design(load_json(DESIGN_CONFIG), prior_review())


def valid_counts() -> dict:
    return {
        "navigation_match_count": 3,
        "href_match_count": 3,
        "action_match_count": 0,
        "fragment_only_match_count": 1,
        "relative_nonfragment_match_count": 2,
        "same_origin_absolute_match_count": 0,
        "resolves_to_application_document_match_count": 1,
        "contains_all_parameter_names_match_count": 2,
        "ordered_callable_parameter_sequence_match_count": 2,
        "query_present_match_count": 2,
        "parentheses_present_match_count": 2,
        "callable_parameter_contract_like_match_count": 2,
        "same_origin_contract_like_match_count": 2,
    }


class FakeRuntime:
    def __init__(self, counts: dict):
        self.counts = counts

    def run_probe(self, config: dict) -> dict:
        return {
            "initial_document_continued_count": 1,
            "static_assets_continued_count": 23,
            "local_requests_continued_count": 0,
            "application_surface_verified": True,
            "fragment_present": True,
            "navigation_match_distribution_counts": self.counts,
            "blocked_shapes": [],
            "candidate_shapes": [],
            "browser_download_denied": True,
        }


class TestM7SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnostics(unittest.TestCase):
    def test_pinned_review_and_design_pass(self):
        review = prior_review()
        self.assertEqual(review["navigation_match_cardinality_status"], "MULTIPLE_MATCHES_OBSERVED_NO_SINGLE_TARGET_SELECTED")
        design = design_result()
        self.assertEqual(design["returned_observations"], COUNT_FIELDS)
        self.assertFalse(design["resource_get_authorized"])

    def test_dry_run_has_zero_network_and_no_raw_navigation_material(self):
        result = dry_run(load_json(LIVE_CONFIG), design_result())
        self.assertFalse(result["network_called"])
        self.assertFalse(result["raw_navigation_value_returned"])
        self.assertFalse(result["navigation_executed"])
        self.assertFalse(result["resource_get_authorized"])

    def test_valid_bounded_distribution_passes_without_authorization(self):
        result = run_navigation_match_distribution_diagnostics(load_json(LIVE_CONFIG), design_result(), runtime=FakeRuntime(valid_counts()))
        self.assertEqual(result["navigation_match_distribution_counts"]["navigation_match_count"], 3)
        self.assertFalse(result["dynamic_candidate_network_sent"])
        self.assertFalse(result["resource_get_authorized"])
        self.assertFalse(result["route_synthesized_or_guessed"])

    def test_lost_multiple_match_prerequisite_fails_closed(self):
        counts = valid_counts()
        counts.update({"navigation_match_count": 1, "href_match_count": 1, "fragment_only_match_count": 0, "relative_nonfragment_match_count": 1, "resolves_to_application_document_match_count": 0, "contains_all_parameter_names_match_count": 1, "ordered_callable_parameter_sequence_match_count": 1, "query_present_match_count": 1, "parentheses_present_match_count": 1, "callable_parameter_contract_like_match_count": 1, "same_origin_contract_like_match_count": 1})
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError):
            run_navigation_match_distribution_diagnostics(load_json(LIVE_CONFIG), design_result(), runtime=FakeRuntime(counts))

    def test_match_overflow_and_partition_mismatch_fail_closed(self):
        counts = valid_counts()
        counts["navigation_match_count"] = 33
        counts["href_match_count"] = 33
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError):
            run_navigation_match_distribution_diagnostics(load_json(LIVE_CONFIG), design_result(), runtime=FakeRuntime(counts))
        counts = valid_counts()
        counts["action_match_count"] = 1
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError):
            run_navigation_match_distribution_diagnostics(load_json(LIVE_CONFIG), design_result(), runtime=FakeRuntime(counts))

    def test_count_contract_rejects_extra_field_or_non_integer(self):
        counts = valid_counts()
        counts["raw_value"] = "forbidden"
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError):
            run_navigation_match_distribution_diagnostics(load_json(LIVE_CONFIG), design_result(), runtime=FakeRuntime(counts))
        counts = valid_counts()
        counts["href_match_count"] = True
        with self.assertRaises(SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError):
            run_navigation_match_distribution_diagnostics(load_json(LIVE_CONFIG), design_result(), runtime=FakeRuntime(counts))

    def test_source_keeps_values_transient_and_returns_only_counts(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("getAttribute(name)", source)
        self.assertIn("navigation_match_distribution_counts", source)
        self.assertNotIn('"navigation_values"', source)
        self.assertNotIn('"matched_values"', source)
        self.assertNotIn("Page.getResourceContent", source)
        self.assertNotIn("Network.getResponseBody", source)
        self.assertNotIn("Runtime.callFunctionOn", source)

    def test_workflow_is_manual_read_only_full_qa_and_no_navigation(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("confirm_official_olinda_application_dom_navigation_match_distribution_diagnostics", workflow)
        self.assertIn("python -m unittest discover -s tests -v", workflow)
        self.assertIn("python main.py selftest", workflow)
        self.assertIn("--dry-run", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertNotIn("schedule:", workflow)
        self.assertNotIn("curl ", workflow)
        self.assertNotIn("wget ", workflow)
        self.assertNotIn("352690", workflow)
        self.assertNotIn("drive", workflow.lower())

    def test_tampered_evidence_fails_pinned_review(self):
        config = load_json(REVIEW_CONFIG)
        evidence = load_json(EVIDENCE)
        tampered = copy.deepcopy(evidence)
        tampered["navigation_boolean_signature"]["navigation_match_unique"] = True
        with self.assertRaises(Exception):
            run_review(config, tampered)


if __name__ == "__main__":
    unittest.main()
