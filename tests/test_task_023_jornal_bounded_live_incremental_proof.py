from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.journal.bounded_live_proof import (
    EXPECTED_INTEGRITY,
    evaluate_discovery,
    load_pinned_checkpoint,
    request_prohibited_effects,
    run_proof,
    validate_live_authorization,
)
from robo_dados_publicos.journal.real_checkpoint import validate_real_checkpoint

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = ROOT / "docs/evidence/TASK_018_JORNAL_COMPLETED_CANONICAL_CHECKPOINT_0.8.0.json"


def new_item(edition: int) -> dict:
    return {
        "edition": edition,
        "publication_date": f"2026-09-{edition - 7315:02d}",
        "document_url": f"https://ecrie.com.br/test/task023/{edition}.pdf",
        "source_id": f"LIMEIRA_JO_{edition:05d}",
        "logical_key": f"limeira/jornal_oficial/edicao/{edition}",
    }


class FakeTransport:
    network_capable = False

    def __init__(self, result: dict):
        self.result = result
        self.calls = 0

    def discover(self) -> dict:
        self.calls += 1
        return copy.deepcopy(self.result)


class Task023Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))

    def discovery(self, items=None, **overrides):
        result = {"status": "PASS_DISCOVERY", "complete": True, "pages_requested": 1, "request_count": 1,
                  "automatic_retry": False, "items": copy.deepcopy(items or self.checkpoint["items"])}
        result.update(overrides)
        return result

    def test_real_checkpoint_loads_and_has_exact_integrity(self):
        snapshot, result = load_pinned_checkpoint(CHECKPOINT)
        self.assertIsNotNone(snapshot)
        self.assertEqual(result["status"], "PASS_REAL_CHECKPOINT_PINNED")
        self.assertEqual(result["canonical_payload_sha256"], EXPECTED_INTEGRITY)

    def test_missing_checkpoint_stops(self):
        _, result = load_pinned_checkpoint(ROOT / "does-not-exist.json")
        self.assertEqual(result["status"], "STOP_CHECKPOINT_MISSING")

    def test_any_baseline_identity_change_and_hash_change_stop(self):
        changed = copy.deepcopy(self.checkpoint); changed["items"][0]["document_url"] += "?drift"
        self.assertEqual(validate_real_checkpoint(changed)["status"], "STOP_INTEGRITY_MISMATCH")
        changed = copy.deepcopy(self.checkpoint); changed["integrity"]["canonical_payload_sha256"] = "0" * 64
        self.assertEqual(validate_real_checkpoint(changed)["status"], "STOP_INTEGRITY_MISMATCH")

    def test_wrong_baseline_counts_stop(self):
        for count in (11, 13):
            changed = copy.deepcopy(self.checkpoint)
            changed["items"] = changed["items"][:count]
            if count == 13:
                changed["items"].append(new_item(7316))
            changed["item_count"] = count
            self.assertEqual(validate_real_checkpoint(changed)["status"], "STOP_ITEM_COUNT_NOT_EXACTLY_12")

    def test_no_change_and_append_only_bounds(self):
        no_change = evaluate_discovery(checkpoint=self.checkpoint, discovery=self.discovery())
        self.assertEqual(no_change["status"], "NO_CHANGE_IDEMPOTENT")
        self.assertEqual(no_change["boundary_outcome"], "PASS_LIVE_INCREMENTAL_NO_CHANGE_IDEMPOTENT")
        for count in (1, 3, 8):
            items = self.checkpoint["items"] + [new_item(7316 + i) for i in range(count)]
            result = evaluate_discovery(checkpoint=self.checkpoint, discovery=self.discovery(items))
            self.assertEqual(result["status"], "NEW_ITEMS_APPEND_ONLY")
            self.assertEqual(result["new_item_count"], count)
            self.assertFalse(result["checkpoint_advance_authorized"])
        items = self.checkpoint["items"] + [new_item(7316 + i) for i in range(9)]
        self.assertEqual(evaluate_discovery(checkpoint=self.checkpoint, discovery=self.discovery(items))["status"], "STOP_NEW_ITEM_BOUND_EXCEEDED")

    def test_missing_drift_duplicate_and_non_monotonic_stop(self):
        cases = []
        cases.append((self.checkpoint["items"][1:], "STOP_KNOWN_ITEM_MISSING"))
        drift = copy.deepcopy(self.checkpoint["items"]); drift[0]["publication_date"] = "2026-08-13"
        cases.append((drift, "STOP_KNOWN_ITEM_DRIFT"))
        cases.append((self.checkpoint["items"] + [copy.deepcopy(self.checkpoint["items"][-1])], "STOP_DUPLICATE_EDITION"))
        cases.append((self.checkpoint["items"] + [new_item(7310)], "STOP_DUPLICATE_EDITION"))
        older = new_item(7303); older["publication_date"] = "2026-08-13"
        cases.append((self.checkpoint["items"] + [older], "STOP_NON_MONOTONIC_NEW_ITEM"))
        for items, expected in cases:
            self.assertEqual(evaluate_discovery(checkpoint=self.checkpoint, discovery=self.discovery(items))["status"], expected)

    def test_duplicate_source_and_logical_key_stop(self):
        for field, expected in (("source_id", "STOP_DUPLICATE_SOURCE_ID"), ("logical_key", "STOP_DUPLICATE_LOGICAL_KEY")):
            extra = new_item(7316); extra[field] = self.checkpoint["items"][0][field]
            result = evaluate_discovery(checkpoint=self.checkpoint, discovery=self.discovery(self.checkpoint["items"] + [extra]))
            self.assertEqual(result["status"], expected)

    def test_malformed_identity_variants_stop(self):
        variants = [
            ("source_id", "WRONG", "STOP_SOURCE_ID_EDITION_MISMATCH"),
            ("logical_key", "WRONG", "STOP_LOGICAL_KEY_EDITION_MISMATCH"),
            ("document_url", "http://ecrie.com.br/x.pdf", "STOP_DOCUMENT_URL_NOT_HTTPS"),
            ("document_url", "https://example.com/x.pdf", "STOP_DOCUMENT_HOST_NOT_ALLOWED"),
            ("publication_date", "not-a-date", "STOP_BAD_ITEM_CONTRACT"),
        ]
        for field, value, expected in variants:
            extra = new_item(7316); extra[field] = value
            result = evaluate_discovery(checkpoint=self.checkpoint, discovery=self.discovery(self.checkpoint["items"] + [extra]))
            self.assertEqual(result["status"], expected)

    def test_incomplete_unknown_pagination_and_retry_stop(self):
        self.assertEqual(evaluate_discovery(checkpoint=self.checkpoint, discovery=self.discovery(complete=False))["status"], "STOP_DISCOVERY_INCOMPLETE")
        self.assertEqual(evaluate_discovery(checkpoint=self.checkpoint, discovery=self.discovery(status="UNKNOWN"))["status"], "STOP_DISCOVERY_NOT_COMPLETE")
        self.assertEqual(evaluate_discovery(checkpoint=self.checkpoint, discovery=self.discovery(pages_requested=9))["status"], "STOP_PAGINATION_BOUNDARY_EXCEEDED")
        self.assertEqual(evaluate_discovery(checkpoint=self.checkpoint, discovery=self.discovery(request_count=9))["status"], "STOP_REQUEST_BUDGET_EXCEEDED")
        self.assertEqual(evaluate_discovery(checkpoint=self.checkpoint, discovery=self.discovery(automatic_retry=True))["status"], "STOP_AUTOMATIC_RETRY_PROHIBITED")

    def test_authorization_is_separate_exact_and_synthetic_never_operational(self):
        self.assertEqual(validate_live_authorization(None, expected_sha="a" * 40)["status"], "STOP_LIVE_PROOF_NOT_AUTHORIZED")
        self.assertEqual(validate_live_authorization({"task": "TASK_018"}, expected_sha="a" * 40)["status"], "STOP_TASK_018_AUTHORIZATION_REUSE")
        self.assertEqual(validate_live_authorization({"synthetic_test_only": True}, expected_sha="a" * 40)["status"], "STOP_SYNTHETIC_AUTHORIZATION_NOT_OPERATIONAL")
        self.assertEqual(validate_live_authorization({"owner_authorized": True, "implementation_sha": "b" * 40}, expected_sha="a" * 40)["status"], "STOP_LIVE_AUTHORIZATION_CONTRACT_MISMATCH")

    def test_unauthorized_run_never_calls_transport_and_fake_transport_is_offline(self):
        fake = FakeTransport(self.discovery())
        result = run_proof(checkpoint=self.checkpoint, transport=fake, authorization=None, expected_sha="a" * 40)
        self.assertEqual(result["status"], "STOP_LIVE_PROOF_NOT_AUTHORIZED")
        self.assertEqual(fake.calls, 0)
        result = run_proof(checkpoint=self.checkpoint, transport=fake,
                           authorization={"synthetic_test_only": True}, expected_sha="a" * 40,
                           offline_test_mode=True)
        self.assertEqual(result["status"], "NO_CHANGE_IDEMPOTENT")
        self.assertEqual(fake.calls, 1)

    def test_bad_checkpoint_stops_before_transport(self):
        fake = FakeTransport(self.discovery())
        checkpoint = copy.deepcopy(self.checkpoint); checkpoint["item_count"] = 11
        result = run_proof(checkpoint=checkpoint, transport=fake,
                           authorization={"synthetic_test_only": True}, expected_sha="a" * 40,
                           offline_test_mode=True)
        self.assertEqual(result["status"], "STOP_ITEM_COUNT_NOT_EXACTLY_12")
        self.assertEqual(fake.calls, 0)

    def test_all_operational_effect_requests_stop(self):
        cases = (({"downstream": True}, "STOP_DOWNSTREAM_EXECUTION_NOT_AUTHORIZED"),
                 ({"checkpoint_advance": True}, "STOP_CHECKPOINT_ADVANCE_NOT_AUTHORIZED"),
                 ({"schedule": True}, "STOP_SCHEDULE_NOT_AUTHORIZED"),
                 ({"recurrence": True}, "STOP_RECURRENCE_NOT_AUTHORIZED"))
        for kwargs, expected in cases:
            self.assertEqual(request_prohibited_effects(**kwargs)["status"], expected)

    def test_contract_fixture_and_gate(self):
        config = json.loads((ROOT / "config/jornal_bounded_live_incremental_proof.v1.json").read_text())
        fixture = json.loads((ROOT / "tests/fixtures/task_023_synthetic_scenarios.json").read_text())
        self.assertEqual(config["tier"], "T0_OFFLINE")
        self.assertFalse(config["authorization"]["live_incremental_proof_authorized"])
        self.assertTrue(fixture["synthetic_test_only"])
        self.assertFalse(fixture["operational_authority"])
        proc = subprocess.run([sys.executable, "scripts/github_task_023_jornal_bounded_live_incremental_proof_implementation_review_gate.py"], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
