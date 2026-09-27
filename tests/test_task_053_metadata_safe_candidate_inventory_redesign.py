from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.task053_metadata_safe_candidate_inventory_redesign import (
    RESULT,
    Task053Error,
    validate_task053_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E53 = ROOT / "docs/evidence/TASK_053_METADATA_SAFE_CANDIDATE_INVENTORY_REDESIGN_0.8.0.json"
E52 = ROOT / "docs/evidence/TASK_052_EXISTING_CUSTODY_GRANULAR_SOURCE_INVENTORY_0.8.0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Task053RedesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.e53 = load(E53)
        self.e52 = load(E52)

    def test_canonical_evidence_passes_offline_redesign(self) -> None:
        result = validate_task053_evidence(self.e53, self.e52)
        self.assertEqual(result["status"], RESULT)
        self.assertEqual(result["max_candidate_records"], 25)
        self.assertEqual(result["source_content_reads"], 0)
        self.assertFalse(result["new_remote_data_write"])
        self.assertEqual(result["future_gate"], "TASK_054_METADATA_SAFE_EXISTING_CUSTODY_INVENTORY_EXECUTION")
        self.assertEqual(result["eiti_financial_identity"], "EVIDENCIA_INSUFICIENTE")

    def test_drive_fetch_must_remain_forbidden(self) -> None:
        e = copy.deepcopy(self.e53)
        e["redesigned_inventory_contract"]["forbidden_operations"].remove("DRIVE_FETCH")
        with self.assertRaises(Task053Error):
            validate_task053_evidence(e, self.e52)

    def test_any_source_read_breaks_t0_contract(self) -> None:
        e = copy.deepcopy(self.e53)
        e["effects"]["source_content_reads"] = 1
        with self.assertRaises(Task053Error):
            validate_task053_evidence(e, self.e52)

    def test_hydrated_task052_content_cannot_be_reused(self) -> None:
        e = copy.deepcopy(self.e53)
        e["upstream"]["hydrated_content_reuse_allowed"] = True
        with self.assertRaises(Task053Error):
            validate_task053_evidence(e, self.e52)

    def test_future_source_read_requires_fresh_authorization(self) -> None:
        e = copy.deepcopy(self.e53)
        e["execution_plan"]["fresh_owner_authorization_required_before_any_source_content_read"] = False
        with self.assertRaises(Task053Error):
            validate_task053_evidence(e, self.e52)

    def test_redesign_cannot_claim_inventory_execution(self) -> None:
        e = copy.deepcopy(self.e53)
        e["promotion"]["candidate_inventory_executed"] = True
        with self.assertRaises(Task053Error):
            validate_task053_evidence(e, self.e52)


if __name__ == "__main__":
    unittest.main()
