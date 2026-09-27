from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.journal.incremental_live_proof import (
    evaluate_live_proof_design,
    request_downstream_execution,
    request_live_proof_execution,
)
from robo_dados_publicos.journal.incremental_readiness import plan_incremental_readiness

ROOT = Path(__file__).resolve().parents[1]


def item(edition: int) -> dict:
    return {"edition": edition, "publication_date": f"2026-08-{edition-7300:02d}", "document_url": f"https://www.limeira.sp.gov.br/jornaloficial/edicao/{edition}.pdf", "source_id": f"LIMEIRA_JO_{edition:05d}", "logical_key": f"limeira/jornal_oficial/edicao/{edition}"}


class Task021Tests(unittest.TestCase):
    def setUp(self):
        self.checkpoint = [item(7310), item(7311)]

    def evaluate(self, discovery, status="PASS_DISCOVERY"):
        return evaluate_live_proof_design(checkpoint_status="COMPLETE", checkpoint_items=self.checkpoint, checkpoint_real_snapshot_pinned=True, discovery_status=status, discovered_items=discovery)

    def test_no_change_zero_effects(self):
        result = self.evaluate(self.checkpoint)
        self.assertEqual(result["status"], "NO_CHANGE_IDEMPOTENT")
        self.assertEqual(result["remote_effects"], 0)
        self.assertFalse(result["downstream_execution"])

    def test_append_only_is_detection_not_execution(self):
        result = self.evaluate(self.checkpoint + [item(7312)])
        self.assertEqual(result["status"], "NEW_ITEMS_APPEND_ONLY")
        self.assertEqual(result["boundary_outcome"], "NEW_ITEMS_DETECTED_EXECUTION_NOT_AUTHORIZED")
        self.assertFalse(result["collection_authorized"])
        self.assertFalse(result["persistence_authorized"])
        self.assertFalse(result["checkpoint_advance_authorized"])

    def test_task020_required_stops(self):
        cases = []
        cases.append(self.evaluate(self.checkpoint, "PARTIAL"))
        cases.append(self.evaluate(self.checkpoint[1:]))
        drift = [dict(x) for x in self.checkpoint]; drift[0]["document_url"] += "?drift=1"; cases.append(self.evaluate(drift))
        cases.append(self.evaluate(self.checkpoint + [dict(self.checkpoint[-1])]))
        cases.append(self.evaluate([item(7309)] + self.checkpoint))
        cases.append(self.evaluate(self.checkpoint + [item(n) for n in range(7312, 7321)]))
        bad = self.checkpoint + [item(7312)]; bad[-1]["logical_key"] = "bad"; cases.append(self.evaluate(bad))
        self.assertEqual([x["status"] for x in cases], ["STOP_DISCOVERY_NOT_COMPLETE", "STOP_KNOWN_ITEM_MISSING", "STOP_KNOWN_ITEM_DRIFT", "STOP_DUPLICATE_EDITION", "STOP_NON_MONOTONIC_NEW_ITEM", "STOP_NEW_ITEM_BOUND_EXCEEDED", "STOP_BAD_ITEM_CONTRACT"])

    def test_unpinned_real_checkpoint_never_falls_back(self):
        fixture = json.loads((ROOT / "tests/fixtures/task_021_synthetic_checkpoint.json").read_text())
        result = evaluate_live_proof_design(checkpoint_status=fixture["status"], checkpoint_items=fixture["items"], checkpoint_real_snapshot_pinned=False, discovery_status="PASS_DISCOVERY", discovered_items=fixture["items"])
        self.assertEqual(result["status"], "STOP_REAL_CHECKPOINT_NOT_PINNED")

    def test_live_downstream_schedule_recurrence_and_task018_reuse_blocked(self):
        self.assertEqual(request_live_proof_execution(authorization=None)["status"], "STOP_LIVE_PROOF_NOT_AUTHORIZED")
        self.assertEqual(request_live_proof_execution(authorization={"task_018_authorization_reused": True})["status"], "STOP_TASK_018_AUTHORIZATION_REUSE")
        self.assertEqual(request_downstream_execution(planner_status="NEW_ITEMS_APPEND_ONLY")["status"], "STOP_DOWNSTREAM_EXECUTION_NOT_AUTHORIZED")
        contract = json.loads((ROOT / "config/jornal_incremental_live_proof_gate.v1.json").read_text())
        auth = contract["authorizations"]
        self.assertFalse(auth["schedule_authorized"])
        self.assertFalse(auth["recurrence_authorized"])
        self.assertFalse(auth["workflow_dispatch_authorized"])

    def test_gate_passes(self):
        proc = subprocess.run([sys.executable, "scripts/github_task_021_jornal_incremental_live_proof_gate_design.py"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
