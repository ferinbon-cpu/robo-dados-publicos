from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.task055_f01_selected_granular_source_bounded_content_read import (
    RESULT,
    Task055Error,
    validate_task055_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E55 = ROOT / "docs/evidence/TASK_055_F01_SELECTED_GRANULAR_SOURCE_BOUNDED_CONTENT_READ_0.8.0.json"
E54 = ROOT / "docs/evidence/TASK_054_METADATA_SAFE_EXISTING_CUSTODY_INVENTORY_EXECUTION_0.8.0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Task055SelectedSourceReadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.e55 = load(E55)
        self.e54 = load(E54)

    def test_canonical_evidence_passes_negative_granularity_result(self) -> None:
        result = validate_task055_evidence(self.e55, self.e54)
        self.assertEqual(result["status"], RESULT)
        self.assertEqual(result["source_content_reads"], 1)
        self.assertFalse(result["selected_source_proves_eiti_financial_identity"])
        self.assertEqual(result["eiti_financial_identity"], "EVIDENCIA_INSUFICIENTE")

    def test_second_source_read_is_forbidden(self) -> None:
        e = copy.deepcopy(self.e55)
        e["effects"]["other_source_content_reads"] = 1
        with self.assertRaises(Task055Error):
            validate_task055_evidence(e, self.e54)

    def test_false_positive_eiti_identity_is_forbidden(self) -> None:
        e = copy.deepcopy(self.e55)
        e["promotion"]["selected_source_proves_eiti_financial_identity"] = True
        with self.assertRaises(Task055Error):
            validate_task055_evidence(e, self.e54)

    def test_liquidado_cannot_be_claimed_when_not_observed(self) -> None:
        e = copy.deepcopy(self.e55)
        e["eiti_granularity_checks"]["liquidado_marker_found"] = True
        with self.assertRaises(Task055Error):
            validate_task055_evidence(e, self.e54)

    def test_next_source_still_requires_fresh_authorization(self) -> None:
        e = copy.deepcopy(self.e55)
        e["next_bounded_gate"]["fresh_owner_authorization_required"] = False
        with self.assertRaises(Task055Error):
            validate_task055_evidence(e, self.e54)


if __name__ == "__main__":
    unittest.main()
