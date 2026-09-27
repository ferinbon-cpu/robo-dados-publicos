from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.task054_metadata_safe_existing_custody_inventory_execution import (
    PRIMARY_ID,
    RESULT,
    Task054Error,
    validate_task054_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E54 = ROOT / "docs/evidence/TASK_054_METADATA_SAFE_EXISTING_CUSTODY_INVENTORY_EXECUTION_0.8.0.json"
E53 = ROOT / "docs/evidence/TASK_053_METADATA_SAFE_CANDIDATE_INVENTORY_REDESIGN_0.8.0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Task054MetadataSafeInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.e54 = load(E54)
        self.e53 = load(E53)

    def test_canonical_inventory_passes_without_source_read(self) -> None:
        result = validate_task054_evidence(self.e54, self.e53)
        self.assertEqual(result["status"], RESULT)
        self.assertEqual(result["candidate_count"], 5)
        self.assertEqual(result["primary_candidate_drive_file_id"], PRIMARY_ID)
        self.assertEqual(result["source_content_reads"], 0)
        self.assertFalse(result["new_remote_data_write"])
        self.assertEqual(result["eiti_financial_identity"], "EVIDENCIA_INSUFICIENTE")

    def test_content_hydration_is_fail_closed(self) -> None:
        e = copy.deepcopy(self.e54)
        e["execution"]["content_hydration_observed"] = True
        with self.assertRaises(Task054Error):
            validate_task054_evidence(e, self.e53)

    def test_best_effort_fetch_is_forbidden(self) -> None:
        e = copy.deepcopy(self.e54)
        e["execution"]["best_effort_fetch"] = True
        with self.assertRaises(Task054Error):
            validate_task054_evidence(e, self.e53)

    def test_candidate_basis_must_be_metadata_only(self) -> None:
        e = copy.deepcopy(self.e54)
        e["candidate_records"][1]["basis"] = "CONTENT_DERIVED"
        with self.assertRaises(Task054Error):
            validate_task054_evidence(e, self.e53)

    def test_candidate_bound_remains_25(self) -> None:
        e = copy.deepcopy(self.e54)
        prototype = copy.deepcopy(e["candidate_records"][-1])
        for index in range(21):
            candidate = copy.deepcopy(prototype)
            candidate["rank"] = len(e["candidate_records"]) + 1
            candidate["drive_file_id"] = f"synthetic-{index}"
            candidate["title"] = f"synthetic-{index}.pdf"
            e["candidate_records"].append(candidate)
        e["selection"]["candidate_count"] = len(e["candidate_records"])
        e["selection"]["secondary_candidate_count"] = len(e["candidate_records"]) - 1
        with self.assertRaises(Task054Error):
            validate_task054_evidence(e, self.e53)

    def test_source_read_cannot_be_preauthorized(self) -> None:
        e = copy.deepcopy(self.e54)
        e["next_bounded_gate"]["source_content_read_authorized"] = True
        with self.assertRaises(Task054Error):
            validate_task054_evidence(e, self.e53)

    def test_remote_write_or_promotion_remains_forbidden(self) -> None:
        for key in ("drive_write", "bronze", "silver", "gold", "serving", "publication"):
            with self.subTest(key=key):
                e = copy.deepcopy(self.e54)
                e["effects"][key] = 1
                with self.assertRaises(Task054Error):
                    validate_task054_evidence(e, self.e53)


if __name__ == "__main__":
    unittest.main()
