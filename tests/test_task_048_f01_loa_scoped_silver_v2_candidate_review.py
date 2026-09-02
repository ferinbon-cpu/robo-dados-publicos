from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f01_loa_scoped_silver_v2_candidate_review import (
    CANDIDATE_SHA,
    Task048Error,
    validate_task048_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E48 = ROOT / "docs/evidence/TASK_048_F01_LOA_SCOPED_SILVER_V2_CANDIDATE_REVIEW_0.8.0.json"
E45 = ROOT / "docs/evidence/TASK_045_F01_BOUNDED_EXISTING_CUSTODY_READONLY_REVIEW_0.8.0.json"
E40 = ROOT / "docs/evidence/TASK_040_LOA_SCOPED_SILVER_CREATE_ONLY_READBACK_0.8.0.json"


class Task048LoaSilverV2CandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.e48 = json.loads(E48.read_text(encoding="utf-8"))
        self.e45 = json.loads(E45.read_text(encoding="utf-8"))
        self.e40 = json.loads(E40.read_text(encoding="utf-8"))

    def validate(self, evidence=None, task045=None, task040=None):
        return validate_task048_evidence(evidence or self.e48, task045 or self.e45, task040 or self.e40)

    def test_canonical_candidate_passes(self) -> None:
        result = self.validate()
        self.assertEqual(result["status"], "PASS_TASK048_LOA_SCOPED_SILVER_V2_CANDIDATE_REVIEW")
        self.assertEqual(result["candidate_sha256"], CANDIDATE_SHA)
        self.assertFalse(result["remote_write_authorized"])
        self.assertEqual(result["eiti_financial_identity"], "EVIDENCIA_INSUFICIENTE")
        self.assertFalse(result["gold_authorized"])

    def test_2720_visual_amount_drift_cannot_be_erased(self) -> None:
        e = copy.deepcopy(self.e48)
        e["candidate_payload"]["material_text_visual_divergence"]["observed"] = False
        with self.assertRaises(Task048Error):
            self.validate(evidence=e)

    def test_2720_cannot_use_text_layer_29m_as_canonical_amount(self) -> None:
        e = copy.deepcopy(self.e48)
        rows = e["candidate_payload"]["validated_action_records"]
        next(r for r in rows if r["action_code"] == "12.306.2001.2720")["appropriation_brl"] = 29000000
        with self.assertRaises(Task048Error):
            self.validate(evidence=e)

    def test_missing_expense_nature_cannot_be_inferred(self) -> None:
        e = copy.deepcopy(self.e48)
        e["candidate_payload"]["validated_action_records"][0]["expense_nature"] = "3.3.90.39"
        with self.assertRaises(Task048Error):
            self.validate(evidence=e)

    def test_generic_action_cannot_be_attributed_to_eiti(self) -> None:
        e = copy.deepcopy(self.e48)
        e["candidate_payload"]["validated_action_records"][0]["eiti_specific"] = True
        with self.assertRaises(Task048Error):
            self.validate(evidence=e)

    def test_gold_cannot_be_preauthorized(self) -> None:
        e = copy.deepcopy(self.e48)
        e["candidate_payload"]["guardrails"]["gold_authorized"] = True
        with self.assertRaises(Task048Error):
            self.validate(evidence=e)

    def test_remote_write_cannot_be_preauthorized(self) -> None:
        e = copy.deepcopy(self.e48)
        e["readiness"]["remote_write_authorized"] = True
        with self.assertRaises(Task048Error):
            self.validate(evidence=e)


if __name__ == "__main__":
    unittest.main()
