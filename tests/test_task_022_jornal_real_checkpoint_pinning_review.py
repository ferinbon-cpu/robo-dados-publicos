from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.journal.real_checkpoint import (
    canonical_payload_sha256,
    validate_real_checkpoint,
    validate_t0_authorizations,
)

ROOT = Path(__file__).resolve().parents[1]


def item(edition: int, day: int) -> dict:
    return {
        "edition": edition,
        "publication_date": f"2026-08-{day:02d}",
        "document_url": f"https://ecrie.com.br/documento/{edition}.pdf",
        "source_id": f"LIMEIRA_JO_{edition:05d}",
        "logical_key": f"limeira/jornal_oficial/edicao/{edition}",
    }


def candidate() -> dict:
    items = [item(7300 + n, n) for n in range(1, 13)]
    return {
        "schema": "TASK_018_JORNAL_COMPLETED_CANONICAL_CHECKPOINT_V1",
        "source_id": "LIMEIRA_JORNAL_OFICIAL",
        "checkpoint_status": "COMPLETE",
        "origin_task": "TASK_018",
        "origin_run_id": 33392616951,
        "origin_batch_id": "BATCH-CBBF70ADCA619C9C",
        "origin_execution_head_sha": "81db1a28c4532bd299d5b21cf38e295f4c49eeec",
        "item_count": 12,
        "items": items,
        "provenance": {
            "authority": "TASK_018_HISTORICAL_SANITIZED_ARTIFACT",
            "artifact_name": "task-018-sanitized-operational-evidence",
            "artifact_id": 9758450652,
            "identities_observed_directly": True,
            "sequence_assumed": False,
            "synthetic_fixture": False,
        },
        "integrity": {"item_count": 12, "canonical_payload_sha256": canonical_payload_sha256(items)},
    }


class Task022Tests(unittest.TestCase):
    def assert_stop(self, snapshot: dict, expected: str | None = None):
        status = validate_real_checkpoint(snapshot)["status"]
        self.assertTrue(status.startswith("STOP_"), status)
        if expected:
            self.assertEqual(status, expected)

    def test_valid_12_item_candidate_passes_validator(self):
        result = validate_real_checkpoint(candidate())
        self.assertEqual(result["status"], "PASS_REAL_CHECKPOINT_PINNED")
        self.assertEqual(result["item_count"], 12)
        self.assertFalse(result["live_proof_authorized"])

    def test_11_and_13_items_stop(self):
        for size in (11, 13):
            snap = candidate()
            if size == 11:
                snap["items"].pop()
            else:
                snap["items"].append(item(7313, 13))
            snap["item_count"] = size
            self.assert_stop(snap, "STOP_ITEM_COUNT_NOT_EXACTLY_12")

    def test_duplicate_edition_source_id_and_logical_key_stop(self):
        for field in ("edition", "source_id", "logical_key"):
            snap = candidate()
            snap["items"][1][field] = snap["items"][0][field]
            self.assert_stop(snap)

    def test_canonical_identity_mismatches_stop(self):
        snap = candidate(); snap["items"][0]["source_id"] = "LIMEIRA_JO_99999"
        self.assert_stop(snap, "STOP_SOURCE_ID_EDITION_MISMATCH")
        snap = candidate(); snap["items"][0]["logical_key"] = "limeira/jornal_oficial/edicao/99999"
        self.assert_stop(snap, "STOP_LOGICAL_KEY_EDITION_MISMATCH")

    def test_bad_date_transport_and_host_stop(self):
        mutations = [
            ("publication_date", "2026-02-30", "STOP_BAD_PUBLICATION_DATE"),
            ("document_url", "http://ecrie.com.br/x.pdf", "STOP_DOCUMENT_URL_NOT_HTTPS"),
            ("document_url", "https://example.invalid/x.pdf", "STOP_DOCUMENT_HOST_NOT_ALLOWED"),
        ]
        for field, value, status in mutations:
            snap = candidate(); snap["items"][0][field] = value
            self.assert_stop(snap, status)

    def test_missing_synthetic_and_assumed_provenance_stop(self):
        snap = candidate(); del snap["provenance"]
        self.assert_stop(snap, "STOP_PROVENANCE_MISSING")
        snap = candidate(); snap["provenance"]["synthetic_fixture"] = True
        self.assert_stop(snap, "STOP_SYNTHETIC_FIXTURE_NOT_AUTHORITY")
        snap = candidate(); snap["provenance"]["sequence_assumed"] = True
        self.assert_stop(snap, "STOP_ASSUMED_SEQUENCE_PROHIBITED")

    def test_task018_batch_run_and_head_mismatch_stop(self):
        for field in ("origin_batch_id", "origin_run_id", "origin_execution_head_sha"):
            snap = candidate(); snap[field] = "wrong"
            self.assert_stop(snap, "STOP_TASK_018_ORIGIN_MISMATCH")

    def test_integrity_and_order_stop(self):
        snap = candidate(); snap["integrity"]["canonical_payload_sha256"] = "0" * 64
        self.assert_stop(snap, "STOP_INTEGRITY_MISMATCH")
        snap = candidate(); snap["items"].reverse(); snap["integrity"]["canonical_payload_sha256"] = canonical_payload_sha256(snap["items"])
        self.assert_stop(snap, "STOP_ITEMS_NOT_DETERMINISTICALLY_ORDERED")

    def test_live_schedule_and_recurrence_attempts_stop(self):
        auth = json.loads((ROOT / "config/jornal_real_checkpoint_pinning_review.v1.json").read_text())["authorizations"]
        self.assertEqual(validate_t0_authorizations(auth)["status"], "PASS_T0_AUTHORIZATIONS_BLOCKED")
        for field in ("live_proof_authorized", "schedule_authorized", "recurrence_authorized"):
            changed = copy.deepcopy(auth); changed[field] = True
            self.assertEqual(validate_t0_authorizations(changed)["status"], "STOP_T0_OPERATIONAL_AUTHORIZATION")

    def test_repository_result_is_truthful_blocked_and_task021_still_passes(self):
        evidence = json.loads((ROOT / "docs/evidence/TASK_022_JORNAL_REAL_CHECKPOINT_PINNING_REVIEW_0.8.0.json").read_text())
        self.assertEqual(evidence["status"], "STOP_REAL_CHECKPOINT_EVIDENCE_INSUFFICIENT")
        self.assertEqual(evidence["real_checkpoint_status"], "BLOCKED_NOT_PINNED")
        self.assertFalse((ROOT / "docs/evidence/TASK_018_JORNAL_COMPLETED_CANONICAL_CHECKPOINT_0.8.0.json").exists())
        proc = subprocess.run([sys.executable, "scripts/github_task_021_jornal_incremental_live_proof_gate_design.py"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_task022_gate_passes_blocked_review(self):
        proc = subprocess.run([sys.executable, "scripts/github_task_022_jornal_real_checkpoint_pinning_review_gate.py"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["status"], "PASS_TASK_022_BLOCKED_REVIEW")


if __name__ == "__main__":
    unittest.main()
