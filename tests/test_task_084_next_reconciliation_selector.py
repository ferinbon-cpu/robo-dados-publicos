from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import unittest

from robo_dados_publicos.reconciliation.rollout import (
    ReconciliationRolloutError,
    parse_pinned_plan,
    select_next_ready_task,
)

ROOT = Path(__file__).resolve().parents[1]


def task(task_id: str, *, event: str, target: str = "LIMEIRA_CONTRATOS", status: str = "READY_SEARCH", priority: int = 100) -> dict:
    return {
        "task_id": task_id,
        "origin_event_id": event,
        "origin_source_id": "LIMEIRA_JO_TEST",
        "target_source": target,
        "task_type": "FIND_CONTRACT_RECORD",
        "status": status,
        "priority": priority,
        "rationale": "test",
        "match_keys": {"year": 2025, "contract_number": "1/2025"},
        "search_hints": {},
        "minimum_link_confidence": "A",
        "identity_rule": "candidate only",
    }


def raw_plan(rows: list[dict]) -> tuple[bytes, str]:
    raw = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows).encode("utf-8")
    return raw, sha256(raw).hexdigest()


class TestTask084NextReconciliationSelector(unittest.TestCase):
    def setUp(self):
        self.first = task("RECTASK_first", event="JOEV_001")
        self.second = task("RECTASK_second", event="JOEV_002")
        self.other_target = task("RECTASK_other", event="JOEV_003", target="SIAVE_LIMEIRA", priority=70)
        self.rows = [self.first, self.second, self.other_target]
        self.raw, self.digest = raw_plan(self.rows)

    def test_selects_first_remaining_ready_target_task_after_consumed_exclusion(self):
        result = select_next_ready_task(
            self.raw,
            expected_sha256=self.digest,
            target_source="LIMEIRA_CONTRATOS",
            consumed_task_ids=["RECTASK_first"],
        )
        self.assertEqual("PASS_RECONCILIATION_NEXT_TASK_SELECTED", result["status"])
        self.assertEqual("RECTASK_second", result["selected_task_id"])
        self.assertEqual(2, result["eligible_ready_tasks"])
        self.assertEqual(1, result["remaining_ready_tasks"])
        self.assertEqual(0, sum(result["remote_effects"].values()))

    def test_exact_plan_sha_is_mandatory(self):
        with self.assertRaisesRegex(ReconciliationRolloutError, "STOP_ROLLOUT_PLAN_SHA256_MISMATCH"):
            parse_pinned_plan(self.raw, expected_sha256="0" * 64)

    def test_non_utf8_plan_fails_closed_after_exact_hash_check(self):
        raw = b"\xff\xfe\xfd"
        digest = sha256(raw).hexdigest()
        with self.assertRaisesRegex(ReconciliationRolloutError, "STOP_ROLLOUT_PLAN_NOT_UTF8"):
            parse_pinned_plan(raw, expected_sha256=digest)

    def test_non_object_jsonl_line_fails_closed(self):
        raw = b"[]\n"
        digest = sha256(raw).hexdigest()
        with self.assertRaisesRegex(ReconciliationRolloutError, "STOP_ROLLOUT_NON_OBJECT_LINE_1"):
            parse_pinned_plan(raw, expected_sha256=digest)

    def test_empty_plan_fails_closed(self):
        raw = b"\n"
        digest = sha256(raw).hexdigest()
        with self.assertRaisesRegex(ReconciliationRolloutError, "STOP_ROLLOUT_EMPTY_PLAN"):
            parse_pinned_plan(raw, expected_sha256=digest)

    def test_missing_priority_fails_closed(self):
        row = dict(self.first)
        row.pop("priority")
        raw, digest = raw_plan([row])
        with self.assertRaisesRegex(ReconciliationRolloutError, "STOP_ROLLOUT_INVALID_PRIORITY"):
            parse_pinned_plan(raw, expected_sha256=digest)

    def test_missing_required_sort_field_fails_closed(self):
        row = dict(self.first)
        row.pop("origin_event_id")
        raw, digest = raw_plan([row])
        with self.assertRaisesRegex(ReconciliationRolloutError, "STOP_ROLLOUT_INVALID_ORIGIN_EVENT_ID"):
            parse_pinned_plan(raw, expected_sha256=digest)

    def test_duplicate_task_id_fails_closed(self):
        raw, digest = raw_plan([self.first, self.first])
        with self.assertRaisesRegex(ReconciliationRolloutError, "STOP_ROLLOUT_DUPLICATE_TASK_ID"):
            parse_pinned_plan(raw, expected_sha256=digest)

    def test_noncanonical_plan_order_fails_closed(self):
        raw, digest = raw_plan([self.second, self.first, self.other_target])
        with self.assertRaisesRegex(ReconciliationRolloutError, "STOP_ROLLOUT_PLAN_NOT_CANONICAL_ORDER"):
            parse_pinned_plan(raw, expected_sha256=digest)

    def test_noncanonical_target_source_tiebreaker_fails_closed(self):
        contract = task("RECTASK_contract", event="JOEV_same", target="LIMEIRA_CONTRATOS")
        siave = task("RECTASK_siave", event="JOEV_same", target="SIAVE_LIMEIRA")
        raw, digest = raw_plan([siave, contract])
        with self.assertRaisesRegex(ReconciliationRolloutError, "STOP_ROLLOUT_PLAN_NOT_CANONICAL_ORDER"):
            parse_pinned_plan(raw, expected_sha256=digest)

    def test_unknown_consumed_task_fails_closed(self):
        with self.assertRaisesRegex(ReconciliationRolloutError, "STOP_ROLLOUT_CONSUMED_TASK_NOT_IN_PINNED_PLAN"):
            select_next_ready_task(
                self.raw,
                expected_sha256=self.digest,
                target_source="LIMEIRA_CONTRATOS",
                consumed_task_ids=["RECTASK_missing"],
            )

    def test_no_remaining_target_task_fails_closed(self):
        with self.assertRaisesRegex(ReconciliationRolloutError, "STOP_ROLLOUT_NO_REMAINING_READY_TASK"):
            select_next_ready_task(
                self.raw,
                expected_sha256=self.digest,
                target_source="LIMEIRA_CONTRATOS",
                consumed_task_ids=["RECTASK_first", "RECTASK_second"],
            )

    def test_blocked_task_is_never_selected(self):
        blocked = task("RECTASK_blocked", event="JOEV_000", status="BLOCKED_CONNECTOR_DISCOVERY")
        raw, digest = raw_plan([blocked, self.first])
        result = select_next_ready_task(raw, expected_sha256=digest, target_source="LIMEIRA_CONTRATOS")
        self.assertEqual("RECTASK_first", result["selected_task_id"])

    def test_real_constants_match_prior_repository_evidence(self):
        task075 = json.loads((ROOT / "docs/evidence/TASK_075_PLAN_JOURNAL_RECONCILIATION_0.8.0.json").read_text(encoding="utf-8"))
        task077 = json.loads((ROOT / "docs/evidence/TASK_077_BOUNDED_CONTRACTS_RESOLVER_PILOT_0.8.0.json").read_text(encoding="utf-8"))
        task084 = json.loads((ROOT / "docs/evidence/TASK_084_NEXT_RECONCILIATION_SELECTOR_0.8.0.json").read_text(encoding="utf-8"))

        self.assertEqual(task075["plan"]["canonical_jsonl_sha256"], task084["source_plan"]["sha256"])
        self.assertEqual(task075["plan"]["canonical_jsonl_bytes"], task084["source_plan"]["bytes"])
        self.assertEqual(task075["plan"]["generated_tasks"], task084["source_plan"]["tasks"])
        self.assertEqual(task077["selection"]["task_id"], task084["consumed_contract_task"]["task_id"])


if __name__ == "__main__":
    unittest.main()
