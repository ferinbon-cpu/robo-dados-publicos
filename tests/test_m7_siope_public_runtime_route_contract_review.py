from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_public_runtime_route_contract_review import (
    SiopePublicRuntimeRouteContractReviewError,
    load_json,
    review_public_runtime_route_contract,
    validate_review_config,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_runtime_route_contract_review.json"


class TestM7SiopePublicRuntimeRouteContractReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_json(CONFIG)
        cls.evidence = load_json(ROOT / cls.config["evidence_path"])

    def test_review_passes_only_as_offline_zero_candidate_disposition(self):
        result = review_public_runtime_route_contract(self.config, self.evidence)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_RUNTIME_ROUTE_CONTRACT_REVIEW")
        self.assertEqual(result["public_get_contract_status"], "PROVEN_FOR_PINNED_PUBLIC_INDEXED_EXAMPLE")
        self.assertEqual(result["dynamic_route_contract_status"], "UNPROVEN_ZERO_CANDIDATES")
        self.assertEqual(result["candidate_shape_count"], 0)
        self.assertFalse(result["network_called"])
        self.assertFalse(result["contract_promoted"])
        self.assertFalse(result["candidate_route_called"])
        self.assertFalse(result["route_synthesized_or_guessed"])
        self.assertEqual(
            result["next_gate"],
            "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INTERACTION_DIAGNOSTICS_DESIGN_0_8_0",
        )

    def test_candidate_cannot_be_invented_or_promoted(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["result"]["candidate_shape_count"] = 1
        evidence["result"]["candidate_shapes"] = [{
            "method": "GET",
            "resource_type": "XHR",
            "route_without_query": "https://www.fnde.gov.br/siope/guess.do",
            "network_sent": False,
        }]
        with self.assertRaisesRegex(SiopePublicRuntimeRouteContractReviewError, "CANDIDATE_COUNT"):
            review_public_runtime_route_contract(self.config, evidence)

    def test_network_or_limeira_send_fails_closed(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["result"]["dynamic_candidate_network_sent"] = True
        with self.assertRaisesRegex(SiopePublicRuntimeRouteContractReviewError, "DYNAMIC_NETWORK_SENT"):
            review_public_runtime_route_contract(self.config, evidence)

        evidence = copy.deepcopy(self.evidence)
        evidence["result"]["pilot_limeira_values_sent"] = True
        with self.assertRaisesRegex(SiopePublicRuntimeRouteContractReviewError, "PILOT_VALUES_SENT"):
            review_public_runtime_route_contract(self.config, evidence)

    def test_evidence_identity_and_artifact_digest_are_pinned(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["artifact"]["digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(SiopePublicRuntimeRouteContractReviewError, "ARTIFACT_DIGEST"):
            review_public_runtime_route_contract(self.config, evidence)

        evidence = copy.deepcopy(self.evidence)
        evidence["run"]["id"] += 1
        with self.assertRaisesRegex(SiopePublicRuntimeRouteContractReviewError, "RUN_ID"):
            review_public_runtime_route_contract(self.config, evidence)

    def test_config_is_strictly_offline_and_keeps_every_authorization_closed(self):
        validate_review_config(self.config)
        self.assertEqual(self.config["network_access"], "PROHIBITED")
        self.assertEqual(self.config["candidate_route_call"], "PROHIBITED")
        self.assertEqual(self.config["automatic_route_promotion"], "PROHIBITED")
        self.assertEqual(self.config["route_synthesis_or_guessing"], "PROHIBITED")
        self.assertFalse(self.config["collection_authorized"])
        self.assertFalse(self.config["processing_authorized"])
        self.assertFalse(self.config["recurrence_authorized"])
        self.assertFalse(self.config["schedule_enabled"])

    def test_module_and_script_have_no_network_client_or_browser_runtime(self):
        module_text = (ROOT / "robo_dados_publicos" / "sources" / "siope_public_runtime_route_contract_review.py").read_text(encoding="utf-8")
        script_text = (ROOT / "scripts" / "github_siope_public_runtime_route_contract_review_gate.py").read_text(encoding="utf-8")
        combined = module_text + "\n" + script_text
        for forbidden in ("urllib", "requests", "http.client", "websocket", "subprocess", "Page.navigate", "Fetch.enable"):
            self.assertNotIn(forbidden, combined)
        self.assertNotIn("352690", combined)

    def test_evidence_keeps_zero_candidate_interpretation(self):
        serialized = json.dumps(self.evidence, sort_keys=True)
        self.assertEqual(self.evidence["result"]["candidate_shape_count"], 0)
        self.assertEqual(self.evidence["result"]["candidate_shapes"], [])
        self.assertIn("ZERO_SAME_HOST_XHR_OR_FETCH_CANDIDATE_SHAPES_OBSERVED", serialized)
        self.assertNotIn('"dynamic_data_route_proven": true', serialized)


if __name__ == "__main__":
    unittest.main()
