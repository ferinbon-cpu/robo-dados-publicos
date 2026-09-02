from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.loa_scoped_silver_persistence_review import (
    Task040ReviewError,
    validate_task040_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_040_LOA_SCOPED_SILVER_CREATE_ONLY_READBACK_0.8.0.json"


class Task040ScopedSilverPersistenceReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_canonical_evidence_passes(self):
        result = validate_task040_evidence(copy.deepcopy(self.evidence))
        self.assertEqual(result["status"], "PASS_TASK040_SCOPED_SILVER_PERSISTENCE_REVIEW")
        self.assertEqual(result["f01_status"], "SILVER_SCOPED_PARTIAL_VALIDATED")
        self.assertFalse(result["gold_authorized"])
        self.assertFalse(result["future_blanket_authorizations_accepted"])

    def test_rejects_unpinned_authorization(self):
        e = copy.deepcopy(self.evidence)
        e["authorization"]["authorized_against_sha"] = "0" * 40
        with self.assertRaises(Task040ReviewError):
            validate_task040_evidence(e)

    def test_rejects_banked_future_authorizations(self):
        e = copy.deepcopy(self.evidence)
        e["authorization"]["future_blanket_authorizations_accepted"] = True
        with self.assertRaises(Task040ReviewError):
            validate_task040_evidence(e)

    def test_rejects_extra_drive_create(self):
        e = copy.deepcopy(self.evidence)
        e["effects"]["drive_creates"] = 2
        with self.assertRaises(Task040ReviewError):
            validate_task040_evidence(e)

    def test_rejects_missing_readback(self):
        e = copy.deepcopy(self.evidence)
        e["readback"]["verified"] = False
        with self.assertRaises(Task040ReviewError):
            validate_task040_evidence(e)

    def test_rejects_complete_loa_claim(self):
        e = copy.deepcopy(self.evidence)
        e["candidate"]["complete_loa_claim"] = True
        with self.assertRaises(Task040ReviewError):
            validate_task040_evidence(e)

    def test_rejects_gold_promotion(self):
        e = copy.deepcopy(self.evidence)
        e["promotion"]["gold"] = True
        with self.assertRaises(Task040ReviewError):
            validate_task040_evidence(e)


if __name__ == "__main__":
    unittest.main()
