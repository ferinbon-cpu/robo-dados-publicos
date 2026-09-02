from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f01_ppa_scoped_silver_v2_persistence_review import (
    Task047Error,
    validate_task047_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E47 = ROOT / "docs/evidence/TASK_047_F01_PPA_SCOPED_SILVER_V2_CREATE_ONLY_READBACK_0.8.0.json"
E46 = ROOT / "docs/evidence/TASK_046_F01_PPA_SCOPED_SILVER_V2_CANDIDATE_REVIEW_0.8.0.json"


class Task047PersistenceReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.e47 = json.loads(E47.read_text(encoding="utf-8"))
        self.e46 = json.loads(E46.read_text(encoding="utf-8"))

    def validate(self, e47=None, e46=None):
        return validate_task047_evidence(e47 or self.e47, e46 or self.e46)

    def test_canonical_evidence_passes(self):
        result = self.validate()
        self.assertEqual(result["status"], "PASS_TASK047_PPA_SCOPED_SILVER_V2_PERSISTENCE_REVIEW")
        self.assertFalse(result["gold"])

    def test_missing_authorization_stops(self):
        e = copy.deepcopy(self.e47)
        e["authorization"]["owner_authorized"] = False
        with self.assertRaises(Task047Error):
            self.validate(e47=e)

    def test_collision_stops(self):
        e = copy.deepcopy(self.e47)
        e["execution"]["target_name_collision_observed"] = True
        with self.assertRaises(Task047Error):
            self.validate(e47=e)

    def test_hash_drift_stops(self):
        e = copy.deepcopy(self.e47)
        e["ppa"]["sha256"] = "0" * 64
        with self.assertRaises(Task047Error):
            self.validate(e47=e)

    def test_readback_required(self):
        e = copy.deepcopy(self.e47)
        e["ppa"]["readback"]["verified"] = False
        with self.assertRaises(Task047Error):
            self.validate(e47=e)

    def test_overwrite_forbidden(self):
        e = copy.deepcopy(self.e47)
        e["effects"]["overwrite"] = 1
        with self.assertRaises(Task047Error):
            self.validate(e47=e)

    def test_gold_promotion_stops(self):
        e = copy.deepcopy(self.e47)
        e["promotion"]["gold"] = True
        with self.assertRaises(Task047Error):
            self.validate(e47=e)

    def test_eiti_identity_cannot_be_promoted(self):
        e = copy.deepcopy(self.e47)
        e["promotion"]["eiti_financial_identity"] = "PROVEN"
        with self.assertRaises(Task047Error):
            self.validate(e47=e)


if __name__ == "__main__":
    unittest.main()
