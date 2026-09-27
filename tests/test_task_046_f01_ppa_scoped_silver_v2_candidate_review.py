from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f01_ppa_scoped_silver_v2_candidate_review import (
    Task046Error,
    validate_task046_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E46 = ROOT / "docs/evidence/TASK_046_F01_PPA_SCOPED_SILVER_V2_CANDIDATE_REVIEW_0.8.0.json"
E45 = ROOT / "docs/evidence/TASK_045_F01_BOUNDED_EXISTING_CUSTODY_READONLY_REVIEW_0.8.0.json"
E42 = ROOT / "docs/evidence/TASK_042_F01_PPA_LDO_SCOPED_SILVER_CREATE_ONLY_READBACK_0.8.0.json"


class Task046PpaSilverV2CandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.e46 = json.loads(E46.read_text(encoding="utf-8"))
        self.e45 = json.loads(E45.read_text(encoding="utf-8"))
        self.e42 = json.loads(E42.read_text(encoding="utf-8"))

    def validate(self, evidence=None, task045=None, task042=None):
        return validate_task046_evidence(evidence or self.e46, task045 or self.e45, task042 or self.e42)

    def test_canonical_candidate_passes_without_write(self) -> None:
        result = self.validate()
        self.assertEqual(result["status"], "PASS_TASK046_PPA_SCOPED_SILVER_V2_CANDIDATE_REVIEW")
        self.assertEqual(result["candidate_sha256"], "1326c17b53b12064a04cc84123b0414ea77a3e80a8f62fe7cea0dc13eafdd280")
        self.assertFalse(result["remote_write_authorized"])
        self.assertEqual(result["eiti_financial_identity"], "EVIDENCIA_INSUFICIENTE")

    def test_v1_persistence_is_required(self) -> None:
        t = copy.deepcopy(self.e42)
        t["ppa"]["readback"]["verified"] = False
        with self.assertRaises(Task046Error):
            self.validate(task042=t)

    def test_task045_resolution_is_required(self) -> None:
        t = copy.deepcopy(self.e45)
        t["promotion"]["ppa_review_row_resolved"] = False
        with self.assertRaises(Task046Error):
            self.validate(task045=t)

    def test_resolved_2690_value_drift_stops(self) -> None:
        e = copy.deepcopy(self.e46)
        action = next(a for a in e["candidate"]["program_2001"]["selected_actions"] if a["education_level"] == "ENSINO MEDIO E SUPERIOR")
        action["2026"] = 6152
        with self.assertRaises(Task046Error):
            self.validate(evidence=e)

    def test_resolved_row_cannot_remain_excluded(self) -> None:
        e = copy.deepcopy(self.e46)
        e["candidate"]["program_2001"]["excluded_review_rows"] = [{"action_code":"2690"}]
        with self.assertRaises(Task046Error):
            self.validate(evidence=e)

    def test_candidate_hash_drift_stops(self) -> None:
        e = copy.deepcopy(self.e46)
        e["candidate"]["program_2001"]["indicator"]["2029"] = 60
        with self.assertRaises(Task046Error):
            self.validate(evidence=e)

    def test_overwrite_is_forbidden(self) -> None:
        e = copy.deepcopy(self.e46)
        e["target"]["overwrite"] = True
        with self.assertRaises(Task046Error):
            self.validate(evidence=e)

    def test_remote_write_cannot_be_preauthorized(self) -> None:
        e = copy.deepcopy(self.e46)
        e["readiness"]["remote_write_authorized"] = True
        with self.assertRaises(Task046Error):
            self.validate(evidence=e)

    def test_silver_v2_cannot_be_marked_persisted(self) -> None:
        e = copy.deepcopy(self.e46)
        e["promotion"]["silver_v2"] = True
        with self.assertRaises(Task046Error):
            self.validate(evidence=e)

    def test_eiti_identity_remains_insufficient(self) -> None:
        e = copy.deepcopy(self.e46)
        e["candidate"]["guardrails"]["eiti_financial_identity"] = "PROVEN"
        with self.assertRaises(Task046Error):
            self.validate(evidence=e)


if __name__ == "__main__":
    unittest.main()
