from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.automation.policy import evaluate_gate, validate_policy
from robo_dados_publicos.manual_ingest.f02_fundeb_monthly_cash import (
    F02FundebMonthlyCashStop,
    load_pinned_authorization,
    validate_global_policy_registration,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config/automation_policy.v1.json"
GATE = ROOT / "config/f02_fundeb_monthly_cash_gate.v1.json"
CUSTODY = ROOT / "docs/evidence/f02_fundeb_monthly_cash/F02_FUNDEB_MONTHLY_2026_JAN_MAR_SOURCE_CUSTODY.json"
POLICY_AUTH = ROOT / "docs/evidence/F02_FUNDEB_MONTHLY_CASH_POLICY_OWNER_AUTHORIZATION_0.8.0.json"


def synthetic_authorization() -> dict[str, object]:
    return {
        "schema":"F02_FUNDEB_MONTHLY_CASH_RUNTIME_AUTHORIZATION_V1",
        "authorization_id":"TEST_ONLY_EXAMPLE_DO_NOT_USE_OPERATIONALLY",
        "scope":"F02_FUNDEB_MONTHLY_CASH_LOCAL_SNAPSHOT_READ",
        "batch_id":"F02_FUNDEB_MONTHLY_CASH_2026_JAN_MAR",
        "authorized":True,
        "owner_instruction_verbatim":"SYNTHETIC TEST ONLY - NOT AN OWNER AUTHORIZATION",
        "forbidden_effects":[
            "DELETE","OVERWRITE","SERVING","LOOKER","PUBLICATION","SITE",
            "SCHEDULE","RECURRENCE","GOLD_PROMOTION",
            "FINANCIAL_CLAIM_PROMOTION_WITHOUT_EVIDENCE",
        ],
    }


class F02FundebMonthlyCashPolicyActivationTests(unittest.TestCase):
    def test_global_policy_registers_exactly_one_manual_t0_gate_and_auto_evaluator_blocks(self):
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        validate_policy(policy)
        gate = validate_global_policy_registration(policy)
        self.assertEqual(gate["id"], "F02_FUNDEB_MONTHLY_CASH_OFFLINE")
        self.assertEqual(gate["tier"], "T0_OFFLINE")
        self.assertFalse(gate["auto_allowed"])
        self.assertTrue(gate["manual_execution_required"])
        self.assertTrue(gate["no_workflow_trigger"])
        self.assertEqual(gate["current_triggers"], [])
        self.assertFalse(gate["effects"]["source_network"])
        self.assertFalse(gate["effects"]["drive_reads"])
        self.assertFalse(gate["effects"]["drive_writes"])
        self.assertFalse(gate["effects"]["publication"])
        decision = evaluate_gate(policy, gate["id"])
        self.assertEqual(decision["decision"], "BLOCK")
        self.assertEqual(decision["reason"], "POLICY_AUTO_ALLOWED_FALSE")

    def test_gate_contract_is_operational_only_as_registered_manual_t0(self):
        gate = json.loads(GATE.read_text(encoding="utf-8"))
        self.assertEqual(gate["schema"], "F02_FUNDEB_MONTHLY_CASH_GATE_V1")
        self.assertEqual(gate["tier"], "T0")
        self.assertTrue(gate["operational"])
        self.assertTrue(gate["global_policy_registration_required"])
        self.assertEqual(gate["status"], "REGISTERED_MANUAL_T0_REMOTE_CLOSED")
        self.assertFalse(gate["implementation_merge_required_before_manual_execution"])
        self.assertEqual(gate["implementation_pr_merged"], 376)
        self.assertEqual(gate["implementation_merge_sha"], "48c2f7624dba3f46b61f09659f15d798b836c0ef")
        self.assertFalse(gate["remote_drive_read_authorized"])
        self.assertTrue(gate["runtime_authorization_required"])
        self.assertTrue(all(gate["blocked_remote_effects"].values()))
        self.assertTrue(all(gate["semantic_blocks"].values()))

    def test_policy_change_authorization_is_durable_but_not_runtime_authorization(self):
        auth = json.loads(POLICY_AUTH.read_text(encoding="utf-8"))
        self.assertEqual(
            auth["schema"],
            "F02_FUNDEB_MONTHLY_CASH_POLICY_OWNER_AUTHORIZATION_V1",
        )
        self.assertEqual(auth["status"], "AUTHORIZED_POLICY_CHANGE")
        self.assertTrue(auth["authorized"])
        self.assertTrue(auth["runtime_authorization_is_separate"])
        self.assertTrue(auth["runtime_authorization_must_be_ephemeral_and_exact_sha_pinned"])
        forbidden = set(auth["explicitly_not_authorized"])
        for effect in (
            "AUTO_EXECUTION","REMOTE_DRIVE_MATERIALIZATION","BRONZE_WRITE",
            "SILVER_WRITE_BY_THIS_POLICY_CHANGE","GOLD_WRITE","SERVING","LOOKER",
            "PUBLICATION","SITE","OVERWRITE","DELETE","SCHEDULE","RECURRENCE",
            "FINANCIAL_CLAIM_PROMOTION_WITHOUT_EVIDENCE",
        ):
            self.assertIn(effect, forbidden)

    def test_source_custody_remains_primary_only(self):
        custody = json.loads(CUSTODY.read_text(encoding="utf-8"))
        self.assertEqual(
            [x["month"] for x in custody["sources"]],
            ["2026-01", "2026-02", "2026-03"],
        )
        self.assertTrue(custody["evidence_boundary"]["primary_source_manifest_only"])
        self.assertTrue(
            custody["evidence_boundary"]["legacy_derived_artifacts_not_used_for_validation"]
        )

    def test_synthetic_authorization_remains_transient_and_tests_path_is_rejected(self):
        payload = (json.dumps(synthetic_authorization(), sort_keys=True) + "\n").encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as td:
            path = Path(td) / "synthetic-authorization.json"
            path.write_bytes(payload)
            with self.assertRaisesRegex(
                F02FundebMonthlyCashStop,
                "AUTHORIZATION_TEST_FIXTURE_FORBIDDEN_OPERATIONALLY",
            ):
                load_pinned_authorization(
                    root=ROOT,
                    relative_path=path.relative_to(ROOT),
                    expected_sha256=digest,
                )


if __name__ == "__main__":
    unittest.main()
