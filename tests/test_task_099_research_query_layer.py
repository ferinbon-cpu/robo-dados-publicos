from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.research.query import (
    ResearchQueryStop,
    execute_research_query,
    load_query_contract,
)


ROOT = Path(__file__).resolve().parents[1]
QUERY_CONTRACT = ROOT / "config/research_query.v1.json"
EITI = ROOT / "config/eiti_limeira_research_crosswalk.v1.json"
HISTORICAL = ROOT / "config/eiti_historical_planning_crosswalk.v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def policy_query(query_type="POLICY_STATUS_PACKET", **overrides):
    spec = {
        "query_id": "Q:EITI_STATUS",
        "query_type": query_type,
        "subject_id": "POLICY:EITI_LIMEIRA",
        "include_evidence": True,
        "include_unknown_gaps": True,
    }
    spec.update(overrides)
    return spec


class TestTask099ResearchQueryLayer(unittest.TestCase):
    def setUp(self) -> None:
        self.eiti = load(EITI)
        self.historical = load(HISTORICAL)

    def test_contract_is_t0_and_remote_effect_free(self):
        contract = load_query_contract(QUERY_CONTRACT)
        self.assertEqual("RESEARCH_QUERY_V1", contract["schema"])
        self.assertTrue(all(value is False for value in contract["remote_effects"].values()))

    def test_policy_status_packet_preserves_claims_evidence_and_gaps(self):
        result = execute_research_query(
            self.eiti["research_bundle"],
            policy_query(),
            institutionalization_matrix=self.eiti["institutionalization_matrix"],
            historical_planning=self.historical,
        )
        self.assertEqual("RESEARCH_QUERY_RESULT_V1", result["schema"])
        self.assertEqual("POLICY:EITI_LIMEIRA", result["subject"]["id"])
        self.assertGreater(result["claim_count"], 0)
        self.assertGreater(result["evidence_reference_count"], 0)
        self.assertGreater(len(result["institutionalization_dimensions"]), 0)
        self.assertGreater(len(result["institutionalization_gaps"]), 0)
        self.assertEqual(2, len(result["historical_acquisition_gaps"]))
        self.assertEqual(0, result["status_promotions_performed"])
        self.assertFalse(result["financial_identity_created"])
        self.assertFalse(result["causal_effect_created"])
        self.assertFalse(result["natural_language_generation_performed"])
        self.assertEqual(64, len(result["result_sha256"]))

    def test_unknown_financial_identity_is_returned_not_hidden(self):
        result = execute_research_query(
            self.eiti["research_bundle"],
            policy_query("CLAIM_AUDIT"),
        )
        financial = next(
            claim for claim in result["claims"]
            if claim["claim_id"] == "CLAIM:EITI_FINANCIAL_IDENTITY"
        )
        self.assertEqual("UNKNOWN", financial["status"])
        self.assertIn(
            "CLAIM:EITI_FINANCIAL_IDENTITY",
            {item["claim_id"] for item in result["unresolved_claims"]},
        )

    def test_claim_text_is_preserved_exactly(self):
        source_claim = next(
            claim for claim in self.eiti["research_bundle"]["claims"]
            if claim["claim_id"] == "CLAIM:EITI_FINANCIAL_IDENTITY"
        )
        result = execute_research_query(
            self.eiti["research_bundle"],
            policy_query("CLAIM_AUDIT"),
        )
        output_claim = next(
            claim for claim in result["claims"]
            if claim["claim_id"] == source_claim["claim_id"]
        )
        self.assertEqual(source_claim["text"], output_claim["text"])

    def test_status_filter_does_not_promote_excluded_unknown_claim(self):
        result = execute_research_query(
            self.eiti["research_bundle"],
            policy_query(
                "CLAIM_AUDIT",
                allowed_claim_statuses=["PROVEN", "CORROBORATED"],
            ),
        )
        ids = {item["claim_id"] for item in result["claims"]}
        self.assertNotIn("CLAIM:EITI_FINANCIAL_IDENTITY", ids)
        self.assertEqual(0, result["status_promotions_performed"])

    def test_evidence_packet_keeps_document_identity_and_locator(self):
        result = execute_research_query(
            self.eiti["research_bundle"],
            policy_query("CLAIM_AUDIT"),
        )
        claims_with_evidence = [item for item in result["claims"] if item.get("evidence")]
        self.assertTrue(claims_with_evidence)
        packet = claims_with_evidence[0]["evidence"][0]
        self.assertTrue(packet["source_document_id"].startswith("DOC:"))
        self.assertTrue(packet["source_document_label"])
        self.assertIsInstance(packet["locator"], dict)
        self.assertTrue(packet["locator"])

    def test_no_evidence_mode_removes_payload_not_evidence_ids(self):
        result = execute_research_query(
            self.eiti["research_bundle"],
            policy_query("CLAIM_AUDIT", include_evidence=False),
        )
        claim = result["claims"][0]
        self.assertNotIn("evidence", claim)
        self.assertIn("evidence_ids", claim)

    def test_unknown_matrix_dimensions_are_explicit_gaps(self):
        result = execute_research_query(
            self.eiti["research_bundle"],
            policy_query("INSTITUTIONALIZATION_MATRIX"),
            institutionalization_matrix=self.eiti["institutionalization_matrix"],
        )
        gap_names = {item["dimension"] for item in result["institutionalization_gaps"]}
        self.assertIn("budgetary_policy_identity", gap_names)
        self.assertIn("transaction_execution_identity", gap_names)
        self.assertIn("outcome_effect", gap_names)

    def test_missing_subject_fails_closed(self):
        with self.assertRaisesRegex(ResearchQueryStop, "SUBJECT_NOT_FOUND"):
            execute_research_query(
                self.eiti["research_bundle"],
                policy_query(subject_id="POLICY:MISSING"),
            )

    def test_invalid_status_filter_fails_closed(self):
        with self.assertRaisesRegex(ResearchQueryStop, "INVALID_STATUS"):
            execute_research_query(
                self.eiti["research_bundle"],
                policy_query(allowed_claim_statuses=["PROVEN", "INVENTED"]),
            )

    def test_matrix_status_cannot_be_invented(self):
        matrix = copy.deepcopy(self.eiti["institutionalization_matrix"])
        matrix["normative"]["status"] = "CERTAIN"
        with self.assertRaisesRegex(ResearchQueryStop, "MATRIX_STATUS_NORMATIVE"):
            execute_research_query(
                self.eiti["research_bundle"],
                policy_query("INSTITUTIONALIZATION_MATRIX"),
                institutionalization_matrix=matrix,
            )


if __name__ == "__main__":
    unittest.main()
