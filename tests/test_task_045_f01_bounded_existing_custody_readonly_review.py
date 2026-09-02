from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f01_bounded_existing_custody_readonly_review import (
    RESULT,
    Task045Error,
    validate_task045_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E45 = ROOT / "docs/evidence/TASK_045_F01_BOUNDED_EXISTING_CUSTODY_READONLY_REVIEW_0.8.0.json"
E44 = ROOT / "docs/evidence/TASK_044_F01_NEXT_EVIDENCE_READONLY_GATE_DESIGN_0.8.0.json"
E43 = ROOT / "docs/evidence/TASK_043_F01_BUDGET_LAWS_SCOPED_RECONCILIATION_0.8.0.json"


class Task045BoundedExistingCustodyReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.e45 = json.loads(E45.read_text(encoding="utf-8"))
        self.e44 = json.loads(E44.read_text(encoding="utf-8"))
        self.e43 = json.loads(E43.read_text(encoding="utf-8"))

    def validate(self, evidence=None, task044=None, task043=None):
        return validate_task045_evidence(
            evidence or self.e45,
            task044 or self.e44,
            task043 or self.e43,
        )

    def test_canonical_evidence_stops_fail_closed_after_useful_resolution(self) -> None:
        result = self.validate()
        self.assertEqual(result["status"], RESULT)
        self.assertTrue(result["ppa_2690_resolved"])
        self.assertEqual(result["ppa_2690_2026_brl"], 16020000)
        self.assertEqual(result["loa_2690_2026_brl"], 6152000)
        self.assertEqual(result["loa_2720_2026_brl"], 28000000)
        self.assertEqual(result["eiti_financial_identity"], "EVIDENCIA_INSUFICIENTE")
        self.assertFalse(result["new_remote_write"])

    def test_auth_must_be_pinned_to_reviewed_main(self) -> None:
        e = copy.deepcopy(self.e45)
        e["authorization"]["authorized_against_sha"] = "0" * 40
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)

    def test_page_scope_cannot_expand(self) -> None:
        e = copy.deepcopy(self.e45)
        e["scope"]["loa_pages"].append(176)
        e["scope"]["selected_pages_total"] = 13
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)

    def test_source_hash_drift_stops(self) -> None:
        e = copy.deepcopy(self.e45)
        e["source_verification"]["loa"]["sha256"] = "0" * 64
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)

    def test_ocr_is_forbidden(self) -> None:
        e = copy.deepcopy(self.e45)
        e["render_review"]["ocr_used"] = True
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)

    def test_ppa_2690_value_drift_stops(self) -> None:
        e = copy.deepcopy(self.e45)
        e["ppa_2690_resolution"]["year_values"]["2026"] = 6152
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)

    def test_2690_amount_divergence_cannot_be_hidden(self) -> None:
        e = copy.deepcopy(self.e45)
        e["reconciliation"]["2690"]["exact_amount_alignment"] = True
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)

    def test_2720_visual_amount_cannot_be_replaced_by_bad_text_layer(self) -> None:
        e = copy.deepcopy(self.e45)
        e["loa_explicit_fields"]["12.306.2001.2720"]["appropriation_brl"] = 29000000
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)

    def test_material_text_visual_divergence_must_be_preserved(self) -> None:
        e = copy.deepcopy(self.e45)
        e["material_text_visual_divergence"]["observed"] = False
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)

    def test_expense_nature_cannot_be_inferred(self) -> None:
        e = copy.deepcopy(self.e45)
        e["loa_explicit_fields"]["12.362.2001.2690"]["expense_nature"] = "3.3.90.39"
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)

    def test_execution_stage_cannot_be_inferred_from_loa(self) -> None:
        e = copy.deepcopy(self.e45)
        e["loa_explicit_fields"]["12.306.2001.2720"]["execution_stage"] = "PAID"
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)

    def test_silver_write_remains_unauthorized(self) -> None:
        e = copy.deepcopy(self.e45)
        e["promotion"]["silver_write"] = True
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)

    def test_gold_remains_unauthorized(self) -> None:
        e = copy.deepcopy(self.e45)
        e["promotion"]["gold"] = True
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)

    def test_eiti_identity_cannot_be_promoted(self) -> None:
        e = copy.deepcopy(self.e45)
        e["promotion"]["eiti_financial_identity"] = "PROVEN"
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)

    def test_result_must_remain_controlled_stop(self) -> None:
        e = copy.deepcopy(self.e45)
        e["result"] = "PASS_PROMOTED"
        with self.assertRaises(Task045Error):
            self.validate(evidence=e)


if __name__ == "__main__":
    unittest.main()
