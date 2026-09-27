from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.journal.incremental_readiness import plan_incremental_readiness

ROOT = Path(__file__).resolve().parents[1]


def item(edition: int, day: int) -> dict:
    return {
        "edition": edition,
        "publication_date": f"2026-08-{day:02d}",
        "document_url": f"https://www.limeira.sp.gov.br/jornaloficial/edicao/{edition}.pdf",
        "source_id": f"LIMEIRA_JO_{edition:05d}",
        "logical_key": f"limeira/jornal_oficial/edicao/{edition}",
    }


class Task020JornalIncrementalReadinessTests(unittest.TestCase):
    def setUp(self):
        self.baseline = [item(7310, 10), item(7311, 11)]

    def plan(self, discovered, *, discovery_status="PASS_DISCOVERY", checkpoint_status="COMPLETE", max_new_items=8):
        return plan_incremental_readiness(
            checkpoint_status=checkpoint_status,
            checkpoint_items=self.baseline,
            discovery_status=discovery_status,
            discovered_items=discovered,
            max_new_items=max_new_items,
        )

    def test_no_change_is_idempotent_and_has_no_work(self):
        result = self.plan(self.baseline)
        self.assertEqual(result["status"], "NO_CHANGE_IDEMPOTENT")
        self.assertEqual(result["new_items"], [])
        self.assertEqual(result["new_item_count"], 0)
        self.assertFalse(result["remote_effects_authorized"])
        self.assertFalse(result["checkpoint_mutation_performed"])
        self.assertFalse(result["checkpoint_candidate"]["advance_allowed"])

    def test_append_only_delta_is_sorted_proposal_only(self):
        result = self.plan(self.baseline + [item(7313, 13), item(7312, 12)])
        self.assertEqual(result["status"], "NEW_ITEMS_APPEND_ONLY")
        self.assertEqual([row["edition"] for row in result["new_items"]], [7312, 7313])
        self.assertEqual(result["new_item_count"], 2)
        self.assertFalse(result["remote_effects_authorized"])
        self.assertFalse(result["checkpoint_candidate"]["advance_allowed"])
        self.assertEqual(
            result["checkpoint_candidate"]["advance_condition"],
            "ONLY_AFTER_ALL_PROPOSED_NEW_ITEMS_COMPLETE_DOWNSTREAM_AND_FINAL_READBACK",
        )

    def test_partial_discovery_stops(self):
        result = self.plan(self.baseline, discovery_status="PARTIAL_DISCOVERY_PAGINATION_UNRESOLVED")
        self.assertEqual(result["status"], "STOP_DISCOVERY_NOT_COMPLETE")

    def test_incomplete_checkpoint_stops(self):
        result = self.plan(self.baseline, checkpoint_status="PARTIAL")
        self.assertEqual(result["status"], "STOP_CHECKPOINT_NOT_COMPLETE")

    def test_missing_known_item_stops(self):
        result = self.plan([self.baseline[1]])
        self.assertEqual(result["status"], "STOP_KNOWN_ITEM_MISSING")

    def test_known_item_drift_stops(self):
        changed = [dict(row) for row in self.baseline]
        changed[0]["publication_date"] = "2026-08-09"
        result = self.plan(changed)
        self.assertEqual(result["status"], "STOP_KNOWN_ITEM_DRIFT")

    def test_duplicate_edition_stops_even_if_identical(self):
        result = self.plan(self.baseline + [dict(self.baseline[-1])])
        self.assertEqual(result["status"], "STOP_DUPLICATE_EDITION")

    def test_non_monotonic_new_item_stops(self):
        result = self.plan([item(7309, 9)] + self.baseline)
        self.assertEqual(result["status"], "STOP_NON_MONOTONIC_NEW_ITEM")

    def test_new_item_bound_stops(self):
        result = self.plan(self.baseline + [item(7312 + i, 12 + i) for i in range(9)])
        self.assertEqual(result["status"], "STOP_NEW_ITEM_BOUND_EXCEEDED")

    def test_bad_canonical_identity_stops(self):
        malformed = self.baseline + [item(7312, 12)]
        malformed[-1]["source_id"] = "WRONG"
        result = self.plan(malformed)
        self.assertEqual(result["status"], "STOP_BAD_ITEM_CONTRACT")

    def test_contract_does_not_authorize_recurrence(self):
        contract = json.loads(
            (ROOT / "config/jornal_incremental_recurrence_readiness.v1.json").read_text(encoding="utf-8")
        )
        activation = contract["recurrence_activation"]
        continuation = contract["continuation_semantics"]
        effects = contract["effects_of_task_020"]
        self.assertEqual(contract["tier"], "T0_OFFLINE")
        self.assertFalse(activation["recurrence_authorized"])
        self.assertFalse(activation["schedule_authorized"])
        self.assertFalse(activation["cadence_selected"])
        self.assertFalse(activation["future_batch_execution_authorized"])
        self.assertFalse(activation["automatic_t2_authorized"])
        self.assertFalse(activation["automatic_t3_authorized"])
        self.assertFalse(continuation["automatic_retry"])
        self.assertFalse(continuation["partial_checkpoint_commit"])
        self.assertTrue(all(value == 0 for value in effects.values()))

    def test_gate_passes_on_pinned_repository_state(self):
        proc = subprocess.run(
            [sys.executable, "scripts/github_task_020_jornal_incremental_recurrence_readiness_design_gate.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["failed_checks"], [])
        self.assertTrue(all(result["checks"].values()))


if __name__ == "__main__":
    unittest.main()
