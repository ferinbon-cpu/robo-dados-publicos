from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.task052_existing_custody_granular_source_inventory import (
    RESULT,
    Task052Error,
    validate_task052_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E52 = ROOT / "docs/evidence/TASK_052_EXISTING_CUSTODY_GRANULAR_SOURCE_INVENTORY_0.8.0.json"
E51 = ROOT / "docs/evidence/TASK_051_F01_EITI_GRANULAR_EXECUTION_SOURCE_SELECTION_0.8.0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Task052InventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.e52 = load(E52)
        self.e51 = load(E51)

    def test_canonical_evidence_stops_fail_closed(self) -> None:
        result = validate_task052_evidence(self.e52, self.e51)
        self.assertEqual(result["status"], RESULT)
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["source_content_reads"], 1)
        self.assertFalse(result["new_remote_data_write"])
        self.assertEqual(result["eiti_financial_identity"], "EVIDENCIA_INSUFICIENTE")

    def test_boundary_breach_cannot_be_marked_pass(self) -> None:
        e = copy.deepcopy(self.e52)
        e["promotion"]["candidate_inventory_passed"] = True
        with self.assertRaises(Task052Error):
            validate_task052_evidence(e, self.e51)

    def test_hydrated_content_cannot_be_used_for_classification(self) -> None:
        e = copy.deepcopy(self.e52)
        e["candidate_records"][0]["content_used_for_candidate_classification"] = True
        with self.assertRaises(Task052Error):
            validate_task052_evidence(e, self.e51)

    def test_drive_write_remains_forbidden(self) -> None:
        e = copy.deepcopy(self.e52)
        e["effects"]["drive_write"] = 1
        with self.assertRaises(Task052Error):
            validate_task052_evidence(e, self.e51)

    def test_candidate_bound_remains_25(self) -> None:
        e = copy.deepcopy(self.e52)
        e["inventory_contract"]["max_candidate_records"] = 26
        with self.assertRaises(Task052Error):
            validate_task052_evidence(e, self.e51)


if __name__ == "__main__":
    unittest.main()
