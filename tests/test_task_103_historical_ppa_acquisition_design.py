from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.research.eiti_historical_ppa_acquisition import (
    HistoricalPpaAcquisitionDesignStop,
    load_and_validate_acquisition_design,
    validate_acquisition_design,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/eiti_historical_ppa_primary_acquisition.v1.json"


def load() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


class TestTask103HistoricalPpaAcquisitionDesign(unittest.TestCase):
    def test_canonical_design_passes_offline(self):
        result = load_and_validate_acquisition_design(CONTRACT)
        self.assertEqual(
            "PASS_TASK103_HISTORICAL_PPA_ACQUISITION_DESIGN_OFFLINE",
            result["status"],
        )
        self.assertEqual(2, result["period_count"])
        self.assertEqual(1, result["resolved_primary_pdf_candidates"])
        self.assertEqual(1, result["unresolved_primary_pdf_candidates"])
        self.assertFalse(result["live_execution_performed"])
        self.assertFalse(result["financial_identity_created"])
        self.assertFalse(result["causal_effect_created"])

    def test_design_has_zero_remote_effects(self):
        data = load()
        self.assertTrue(all(value is False for value in data["design_remote_effects"].values()))
        self.assertFalse(data["future_execution_authorized_by_design"])

    def test_request_budget_and_method_are_exact(self):
        live = load()["live_contract"]
        self.assertEqual(["GET"], live["allowed_methods"])
        self.assertEqual(6, live["maximum_http_requests_total"])
        self.assertEqual(3, live["maximum_http_requests_per_period"])
        self.assertFalse(live["pagination_allowed"])
        self.assertFalse(live["retry_allowed"])

    def test_required_task098_evidence_cannot_be_weakened(self):
        data = load()
        data["required_before_promotion"].remove("STABLE_SOURCE_HASH_OR_EQUIVALENT_IDENTITY")
        with self.assertRaisesRegex(HistoricalPpaAcquisitionDesignStop, "REQUIRED_EVIDENCE_DRIFT"):
            validate_acquisition_design(data)

    def test_unresolved_2018_primary_cannot_be_silently_filled(self):
        data = load()
        data["periods"][0]["primary_pdf_candidate_url"] = (
            "https://www.limeira.sp.gov.br/invented.pdf"
        )
        data["periods"][0]["primary_pdf_resolution_required"] = False
        with self.assertRaisesRegex(HistoricalPpaAcquisitionDesignStop, "2018_PRIMARY_NOT_YET_PROVEN"):
            validate_acquisition_design(data)

    def test_2022_primary_candidate_is_pinned_to_official_url(self):
        data = load()
        data["periods"][1]["primary_pdf_candidate_url"] = (
            "https://www.limeira.sp.gov.br/other.pdf"
        )
        with self.assertRaisesRegex(HistoricalPpaAcquisitionDesignStop, "2022_PRIMARY_CANDIDATE"):
            validate_acquisition_design(data)

    def test_non_allowlisted_host_fails_closed(self):
        data = load()
        data["periods"][1]["primary_pdf_candidate_url"] = "https://example.org/ppa.pdf"
        with self.assertRaisesRegex(HistoricalPpaAcquisitionDesignStop, "PRIMARY_HOST"):
            validate_acquisition_design(data)

    def test_http_instead_of_https_fails_closed(self):
        data = load()
        data["periods"][1]["official_anchors"][0]["url"] = (
            "http://www.limeira.sp.gov.br/orcamentos"
        )
        with self.assertRaisesRegex(HistoricalPpaAcquisitionDesignStop, "URL_SCHEME"):
            validate_acquisition_design(data)

    def test_retry_or_pagination_cannot_be_enabled(self):
        for key in ("retry_allowed", "pagination_allowed"):
            data = load()
            data["live_contract"][key] = True
            with self.assertRaises(HistoricalPpaAcquisitionDesignStop):
                validate_acquisition_design(data)

    def test_semantic_guard_cannot_be_removed(self):
        data = load()
        data["semantic_guards"].remove(
            "PLANNING_SIGNAL_DOES_NOT_CREATE_FINANCIAL_IDENTITY"
        )
        with self.assertRaisesRegex(HistoricalPpaAcquisitionDesignStop, "SEMANTIC_GUARDS"):
            validate_acquisition_design(data)

    def test_design_cannot_self_authorize_live_execution(self):
        data = load()
        data["future_execution_authorized_by_design"] = True
        with self.assertRaisesRegex(HistoricalPpaAcquisitionDesignStop, "SELF_AUTHORIZATION"):
            validate_acquisition_design(data)

    def test_period_order_and_law_identity_are_pinned(self):
        data = load()
        swapped = copy.deepcopy(data)
        swapped["periods"].reverse()
        with self.assertRaisesRegex(HistoricalPpaAcquisitionDesignStop, "PERIOD_ORDER"):
            validate_acquisition_design(swapped)

        wrong = copy.deepcopy(data)
        wrong["periods"][0]["law_identity"] = "LEI_MUNICIPAL_INVENTED"
        with self.assertRaisesRegex(HistoricalPpaAcquisitionDesignStop, "2018-2021_LAW"):
            validate_acquisition_design(wrong)


if __name__ == "__main__":
    unittest.main()
