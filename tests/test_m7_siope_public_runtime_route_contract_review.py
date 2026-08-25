from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_runtime_route_contract_review import (
    SiopePublicRuntimeRouteContractReviewError,
    review_runtime_route_contract,
    run_review,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_route_contract_review.json"
EVIDENCE = ROOT / "docs" / "evidence" / "M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_ATTEMPT_5_0.8.0.json"


class TestM7SiopePublicRuntimeRouteContractReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_real_attempt_5_evidence_passes_offline_review(self):
        result = run_review(CONFIG, EVIDENCE)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_RUNTIME_ROUTE_CONTRACT_REVIEW")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["dynamic_route_proven"])
        self.assertEqual(result["candidate_shape_count"], 0)
        self.assertEqual(result["observed_document_route_status"], "CANDIDATE_NOT_AUTHORIZED")

    def test_review_does_not_authorize_limeira_or_collection(self):
        result = review_runtime_route_contract(self.config, self.evidence)
        self.assertEqual(result["pilot_limeira_values_send"], "PROHIBITED")
        self.assertEqual(result["dynamic_candidate_network_send"], "PROHIBITED")
        self.assertFalse(result["collection_authorized"])
        self.assertFalse(result["processing_authorized"])
        self.assertFalse(result["recurrence_authorized"])
        self.assertFalse(result["schedule_enabled"])
        self.assertEqual(result["remote_writes"], "NONE")

    def test_zero_runtime_candidates_are_mandatory_for_this_review(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["result"]["candidate_shape_count"] = 1
        evidence["result"]["candidate_shapes"] = [{"route_without_query": "https://www.fnde.gov.br/siope/example.do"}]
        with self.assertRaisesRegex(SiopePublicRuntimeRouteContractReviewError, "ZERO_CANDIDATE_CONTRACT"):
            review_runtime_route_contract(self.config, evidence)

    def test_dynamic_network_send_fails_closed(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["result"]["dynamic_candidate_network_sent"] = True
        with self.assertRaisesRegex(SiopePublicRuntimeRouteContractReviewError, "DYNAMIC_NETWORK_SENT"):
            review_runtime_route_contract(self.config, evidence)

    def test_route_guessing_cannot_be_enabled(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["interpretation"]["route_synthesis_or_guessing"] = "ALLOWED"
        with self.assertRaisesRegex(SiopePublicRuntimeRouteContractReviewError, "ROUTE_GUESSING"):
            review_runtime_route_contract(self.config, evidence)

    def test_next_gate_is_design_only_for_indexed_get_acquisition_contract(self):
        result = review_runtime_route_contract(self.config, self.evidence)
        self.assertEqual(result["next_gate"], "M7_SIOPE_PUBLIC_INDEXED_GET_ACQUISITION_CONTRACT_DESIGN_0_8_0")
        self.assertEqual(result["observed_document_route_role"], "SOLE_OBSERVED_SAME_HOST_DATA_SURFACE_CANDIDATE")


if __name__ == "__main__":
    unittest.main()
