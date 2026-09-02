from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f01_next_evidence_readonly_gate_design import (
    Task044Error,
    validate_task044_design,
)

ROOT = Path(__file__).resolve().parents[1]
E44 = ROOT / "docs/evidence/TASK_044_F01_NEXT_EVIDENCE_READONLY_GATE_DESIGN_0.8.0.json"
E43 = ROOT / "docs/evidence/TASK_043_F01_BUDGET_LAWS_SCOPED_RECONCILIATION_0.8.0.json"


class Task044NextEvidenceDesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.e44 = json.loads(E44.read_text(encoding="utf-8"))
        self.e43 = json.loads(E43.read_text(encoding="utf-8"))

    def validate(self, evidence=None, task043=None):
        return validate_task044_design(evidence or self.e44, task043 or self.e43)

    def test_canonical_design_passes(self) -> None:
        result = self.validate()
        self.assertEqual(result["status"], "PASS_TASK044_NEXT_EVIDENCE_READONLY_GATE_DESIGN_REVIEW")
        self.assertEqual(result["selected_pages"], 12)
        self.assertTrue(result["authorization_required"])
        self.assertFalse(result["authorization_granted"])
        self.assertFalse(result["gold_authorized"])

    def test_preauthorization_stops(self) -> None:
        e = copy.deepcopy(self.e44)
        e["future_readonly_contract"]["authorization_granted"] = True
        with self.assertRaises(Task044Error):
            self.validate(evidence=e)

    def test_extra_page_stops(self) -> None:
        e = copy.deepcopy(self.e44)
        e["evidence_minimization"]["loa_pages"].append(176)
        e["future_readonly_contract"]["drive_files"][1]["pages"].append(176)
        e["evidence_minimization"]["max_selected_pages"] = 13
        with self.assertRaises(Task044Error):
            self.validate(evidence=e)

    def test_source_network_stops(self) -> None:
        e = copy.deepcopy(self.e44)
        e["future_readonly_contract"]["source_network"] = True
        with self.assertRaises(Task044Error):
            self.validate(evidence=e)

    def test_drive_write_stops(self) -> None:
        e = copy.deepcopy(self.e44)
        e["future_readonly_contract"]["drive_write"] = True
        with self.assertRaises(Task044Error):
            self.validate(evidence=e)

    def test_ocr_preauthorization_stops(self) -> None:
        e = copy.deepcopy(self.e44)
        e["future_readonly_contract"]["ocr"] = True
        with self.assertRaises(Task044Error):
            self.validate(evidence=e)

    def test_missing_field_inference_stops(self) -> None:
        e = copy.deepcopy(self.e44)
        e["promotion_policy"]["missing_field_behavior"] = "BEST_GUESS"
        with self.assertRaises(Task044Error):
            self.validate(evidence=e)

    def test_financial_identity_from_alignment_stops(self) -> None:
        e = copy.deepcopy(self.e44)
        e["promotion_policy"]["financial_identity_from_same_code_label_or_amount"] = True
        with self.assertRaises(Task044Error):
            self.validate(evidence=e)

    def test_task043_eiti_status_is_required(self) -> None:
        t = copy.deepcopy(self.e43)
        t["promotion"]["eiti_financial_identity"] = "PROVEN"
        with self.assertRaises(Task044Error):
            self.validate(task043=t)


if __name__ == "__main__":
    unittest.main()
