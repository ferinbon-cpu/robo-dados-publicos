from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f01_budget_law_scoped_reconciliation import (
    Task043Error,
    validate_task043_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E43 = ROOT / "docs/evidence/TASK_043_F01_BUDGET_LAWS_SCOPED_RECONCILIATION_0.8.0.json"
E39 = ROOT / "docs/evidence/TASK_039_LOA_SCOPED_SILVER_CANDIDATE_REVIEW_0.8.0.json"
E41 = ROOT / "docs/evidence/TASK_041_F01_JOM_NATIVE_PPA_LDO_READINESS_REVIEW_0.8.0.json"
E42 = ROOT / "docs/evidence/TASK_042_F01_PPA_LDO_SCOPED_SILVER_CREATE_ONLY_READBACK_0.8.0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Task043ScopedReconciliationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.e43 = _load(E43)
        self.e39 = _load(E39)
        self.e41 = _load(E41)
        self.e42 = _load(E42)

    def validate(self, evidence=None, t39=None, t41=None, t42=None):
        return validate_task043_evidence(
            evidence or self.e43,
            t39 or self.e39,
            t41 or self.e41,
            t42 or self.e42,
        )

    def relation(self, evidence, relation_id):
        return next(r for r in evidence["reconciliation_ledger"] if r["relation_id"] == relation_id)

    def test_canonical_evidence_passes(self) -> None:
        result = self.validate()
        self.assertEqual(result["status"], "PASS_TASK043_SCOPED_BUDGET_LAW_RECONCILIATION_REVIEW")
        self.assertEqual(result["action_2690"], "REVIEW_REQUIRED_BLOCKED")
        self.assertEqual(result["eiti_financial_identity"], "EVIDENCIA_INSUFICIENTE")
        self.assertFalse(result["gold_authorized"])

    def test_2720_financial_identity_promotion_stops(self) -> None:
        e = copy.deepcopy(self.e43)
        self.relation(e, "F01_PPA_LOA_PROGRAM2001_ACTION2720_12_306")["financial_identity"] = True
        with self.assertRaises(Task043Error):
            self.validate(evidence=e)

    def test_2720_scaled_amount_identity_permission_stops(self) -> None:
        e = copy.deepcopy(self.e43)
        self.relation(e, "F01_PPA_LOA_PROGRAM2001_ACTION2720_12_306")["amount_diagnostic"]["identity_inference_allowed"] = True
        with self.assertRaises(Task043Error):
            self.validate(evidence=e)

    def test_2690_review_row_promotion_stops(self) -> None:
        e = copy.deepcopy(self.e43)
        r = self.relation(e, "F01_PPA_LOA_PROGRAM2001_ACTION2690_12_362")
        r["from"]["ppa_row_promoted"] = True
        r["promoted"] = True
        with self.assertRaises(Task043Error):
            self.validate(evidence=e)

    def test_eiti_identity_promotion_stops(self) -> None:
        e = copy.deepcopy(self.e43)
        self.relation(e, "F01_EITI_FINANCIAL_IDENTITY")["classification"] = "PROVEN"
        with self.assertRaises(Task043Error):
            self.validate(evidence=e)

    def test_program_total_attribution_stops(self) -> None:
        e = copy.deepcopy(self.e43)
        e["guardrails"]["program_2001_total_attribution_to_eiti"] = True
        with self.assertRaises(Task043Error):
            self.validate(evidence=e)

    def test_global_fiscal_table_eiti_attribution_stops(self) -> None:
        e = copy.deepcopy(self.e43)
        e["global_loa_tables"]["eiti_attribution_allowed"] = True
        with self.assertRaises(Task043Error):
            self.validate(evidence=e)

    def test_gold_promotion_stops(self) -> None:
        e = copy.deepcopy(self.e43)
        e["promotion"]["gold"] = True
        with self.assertRaises(Task043Error):
            self.validate(evidence=e)

    def test_remote_effect_stops(self) -> None:
        e = copy.deepcopy(self.e43)
        e["effects"]["drive_write"] = 1
        with self.assertRaises(Task043Error):
            self.validate(evidence=e)

    def test_task041_unpromoted_2690_row_is_required(self) -> None:
        t = copy.deepcopy(self.e41)
        t["ppa_candidate"]["program_2001"]["excluded_review_rows"][0]["promoted"] = True
        with self.assertRaises(Task043Error):
            self.validate(t41=t)

    def test_task042_byte_readback_is_required(self) -> None:
        t = copy.deepcopy(self.e42)
        t["ppa"]["readback"]["byte_identity"] = False
        with self.assertRaises(Task043Error):
            self.validate(t42=t)


if __name__ == "__main__":
    unittest.main()
