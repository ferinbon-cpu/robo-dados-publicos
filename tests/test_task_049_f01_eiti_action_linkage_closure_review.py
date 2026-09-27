from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f01_eiti_action_linkage_closure_review import (
    Task049Error,
    validate_task049_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E49 = ROOT / "docs/evidence/TASK_049_F01_EITI_ACTION_LINKAGE_CLOSURE_REVIEW_0.8.0.json"
E45 = ROOT / "docs/evidence/TASK_045_F01_BOUNDED_EXISTING_CUSTODY_READONLY_REVIEW_0.8.0.json"
E48 = ROOT / "docs/evidence/TASK_048_F01_LOA_SCOPED_SILVER_V2_CANDIDATE_REVIEW_0.8.0.json"


class Task049EitiActionLinkageClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.e49 = json.loads(E49.read_text(encoding="utf-8"))
        self.e45 = json.loads(E45.read_text(encoding="utf-8"))
        self.e48 = json.loads(E48.read_text(encoding="utf-8"))

    def validate(self, evidence=None, task045=None, task048=None):
        return validate_task049_evidence(evidence or self.e49, task045 or self.e45, task048 or self.e48)

    def test_canonical_review_passes(self) -> None:
        result = self.validate()
        self.assertEqual(result["status"], "PASS_TASK049_EITI_ACTION_LINKAGE_CLOSURE_REVIEW")
        self.assertEqual(result["action_rows_reviewed"], 27)
        self.assertEqual(result["explicit_eiti_action_label_matches"], 0)
        self.assertEqual(result["program_to_explicit_eiti_action_linkage"], "NOT_PROVEN")
        self.assertEqual(result["eiti_financial_identity"], "EVIDENCIA_INSUFICIENTE")
        self.assertFalse(result["gold_authorized"])

    def test_explicit_integral_action_label_would_stop_closure(self) -> None:
        e = copy.deepcopy(self.e49)
        e["action_rows"][0]["label"] = "MANUTENCAO DA EDUCACAO INTEGRAL"
        with self.assertRaises(Task049Error):
            self.validate(evidence=e)

    def test_generic_action_cannot_be_promoted_to_eiti(self) -> None:
        e = copy.deepcopy(self.e49)
        e["conclusion"]["program_or_generic_action_financial_attribution_to_eiti"] = "ALLOWED"
        with self.assertRaises(Task049Error):
            self.validate(evidence=e)

    def test_claim_cannot_expand_to_all_municipal_documents(self) -> None:
        e = copy.deepcopy(self.e49)
        e["scope"]["claim_boundary"] = "NO_EITI_ACTION_ANYWHERE_IN_LIMEIRA"
        with self.assertRaises(Task049Error):
            self.validate(evidence=e)

    def test_next_live_read_cannot_be_preauthorized(self) -> None:
        e = copy.deepcopy(self.e49)
        e["next_evidence_boundary"]["automatic_next_live_read_authorized"] = True
        with self.assertRaises(Task049Error):
            self.validate(evidence=e)

    def test_eiti_identity_cannot_be_promoted(self) -> None:
        e = copy.deepcopy(self.e49)
        e["conclusion"]["eiti_financial_identity"] = "PROVEN"
        with self.assertRaises(Task049Error):
            self.validate(evidence=e)


if __name__ == "__main__":
    unittest.main()
