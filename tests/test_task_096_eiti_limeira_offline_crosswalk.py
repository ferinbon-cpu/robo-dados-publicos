from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.research.eiti_crosswalk import (
    EitiCrosswalkStop,
    load_and_validate_eiti_crosswalk,
    validate_eiti_crosswalk,
)


ROOT = Path(__file__).resolve().parents[1]
CROSSWALK = ROOT / "config/eiti_limeira_research_crosswalk.v1.json"
EDGES = ROOT / "tests/fixtures/edges_v08.csv"
GRAPH_QA = ROOT / "tests/fixtures/graph_qa_v08.csv"


def load_data():
    return json.loads(CROSSWALK.read_text(encoding="utf-8"))


def validate(data):
    return validate_eiti_crosswalk(
        data,
        legacy_edges_csv=EDGES.read_text(encoding="utf-8-sig"),
        graph_qa_csv=GRAPH_QA.read_text(encoding="utf-8-sig"),
    )


class TestTask096EitiLimeiraOfflineCrosswalk(unittest.TestCase):
    def test_canonical_crosswalk_passes_from_repository_only(self):
        result = load_and_validate_eiti_crosswalk(
            CROSSWALK,
            legacy_edges_path=EDGES,
            graph_qa_path=GRAPH_QA,
        )
        self.assertEqual("PASS_TASK096_EITI_LIMEIRA_OFFLINE_CROSSWALK", result["status"])
        self.assertEqual("PROVEN", result["normative_status"])
        self.assertEqual("CORROBORATED", result["planning_status"])
        self.assertEqual("UNKNOWN", result["budgetary_policy_identity_status"])
        self.assertEqual("PROVEN", result["financial_reporting_status"])
        self.assertEqual("UNKNOWN", result["transaction_execution_identity_status"])
        self.assertFalse(result["page_numbering_reconciled"])
        self.assertEqual(0, result["remote_effects"])

    def test_financial_identity_cannot_be_promoted(self):
        data = load_data()
        claim = next(
            c for c in data["research_bundle"]["claims"]
            if c["claim_id"] == "CLAIM:EITI_FINANCIAL_IDENTITY"
        )
        claim["status"] = "PROVEN"
        with self.assertRaisesRegex(EitiCrosswalkStop, "FINANCIAL_IDENTITY_STATUS"):
            validate(data)

    def test_policy_program_overlap_cannot_be_upgraded_to_financial_identity(self):
        data = load_data()
        relation = next(
            r for r in data["research_bundle"]["relations"]
            if r["relation_id"] == "REL:POLICY_PROGRAM_OVERLAP"
        )
        relation["attributes"]["financial_identity"] = True
        with self.assertRaisesRegex(EitiCrosswalkStop, "POLICY_PROGRAM_FINANCIAL_OVERREACH"):
            validate(data)

    def test_generic_loa_expense_cannot_be_marked_eiti_specific(self):
        data = load_data()
        expense = next(
            e for e in data["research_bundle"]["entities"]
            if e["id"] == "EXPENSE:LOA2026_2720_12_306"
        )
        expense["attributes"]["eiti_specific"] = True
        with self.assertRaisesRegex(EitiCrosswalkStop, "GENERIC_LOA_EITI_FLAG"):
            validate(data)

    def test_fomento_reporting_bucket_cannot_become_transaction_identity(self):
        data = load_data()
        bucket = next(
            e for e in data["research_bundle"]["entities"]
            if e["id"] == "EXPENSE:FOMENTO_ETI_FUNDEB_2026_B1"
        )
        bucket["attributes"]["transaction_identity_proven"] = True
        with self.assertRaisesRegex(EitiCrosswalkStop, "FOMENTO_TRANSACTION_OVERREACH"):
            validate(data)

    def test_no_match_cannot_be_rewritten_as_no_eiti_spending(self):
        data = load_data()
        claim = next(
            c for c in data["research_bundle"]["claims"]
            if c["claim_id"] == "CLAIM:PPA_NO_EXPLICIT_EITI_ACTION_LABEL"
        )
        claim["attributes"]["proves_no_eiti_spending"] = True
        with self.assertRaisesRegex(EitiCrosswalkStop, "ACTION_SEARCH_OVERREACH"):
            validate(data)

    def test_page_numbering_difference_must_remain_unreconciled(self):
        data = load_data()
        data["page_numbering_issue"]["reconciled"] = True
        with self.assertRaisesRegex(EitiCrosswalkStop, "PAGE_SILENT_RECONCILIATION"):
            validate(data)

    def test_legacy_graph_financial_identity_absence_is_pinned(self):
        data = load_data()
        qa_text = GRAPH_QA.read_text(encoding="utf-8-sig").replace(
            "G10,policy_eiti_limeira,ppa_program_2001,financial_identity,0,0,1",
            "G10,policy_eiti_limeira,ppa_program_2001,financial_identity,1,1,1",
        )
        with self.assertRaisesRegex(EitiCrosswalkStop, "G10_FINANCIAL_IDENTITY_ABSENT"):
            validate_eiti_crosswalk(
                data,
                legacy_edges_csv=EDGES.read_text(encoding="utf-8-sig"),
                graph_qa_csv=qa_text,
            )

    def test_institutionalization_matrix_cannot_overclaim_budgetary_persistence(self):
        data = load_data()
        data["institutionalization_matrix"]["budgetary_persistence"]["status"] = "PROVEN"
        with self.assertRaisesRegex(EitiCrosswalkStop, "MATRIX_BUDGETARY_PERSISTENCE"):
            validate(data)

    def test_causal_claim_is_forbidden_in_current_crosswalk(self):
        data = load_data()
        base = copy.deepcopy(data["research_bundle"]["claims"][0])
        base.update(
            {
                "claim_id": "CLAIM:CAUSAL_FORBIDDEN",
                "text": "A política causou melhoria de resultado.",
                "subject_ids": ["POLICY:EITI_LIMEIRA"],
                "status": "CANDIDATE",
                "attributes": {"claim_domain": "CAUSAL_EFFECT"},
            }
        )
        data["research_bundle"]["claims"].append(base)
        with self.assertRaisesRegex(EitiCrosswalkStop, "CAUSAL_CLAIM_FORBIDDEN"):
            validate(data)

    def test_any_remote_effect_fails_closed(self):
        data = load_data()
        data["effects"]["drive_read"] = 1
        with self.assertRaisesRegex(EitiCrosswalkStop, "REMOTE_EFFECT"):
            validate(data)


if __name__ == "__main__":
    unittest.main()
