from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.automation.f02_fundeb_monthly_policy_finalization import (
    F02FundebMonthlyPolicyFinalizationStop,
    load_json,
    validate_finalization,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config/automation_policy.v1.json"
MERGE_SHA = "48c2f7624dba3f46b61f09659f15d798b836c0ef"


def evidence():
    return {
        "schema": "F02_FUNDEB_MONTHLY_CASH_POLICY_FINALIZATION_V2",
        "status": "READY_FOR_MANUAL_RUNTIME_AUTHORIZATION_ONLY",
        "implementation_pr": 376,
        "implementation_merge_sha": MERGE_SHA,
        "verification_contract": {
            "method": "LOCAL_GIT_OBJECT_AND_ANCESTRY_PLUS_CROSS_FILE_PIN_EQUALITY",
            "full_git_history_required": True,
            "network_required_after_checkout": False,
            "github_signature_claimed_by_this_evidence": False,
        },
        "gate_effects": {
            "auto_allowed": False,
            "workflow_trigger": False,
            "source_network": False,
            "drive_read": False,
            "drive_write": False,
            "publication": False,
            "schedule": False,
            "recurrence": False,
        },
        "still_forbidden": [
            "DELETE", "OVERWRITE", "SERVING", "LOOKER", "PUBLICATION", "SITE",
            "SCHEDULE", "RECURRENCE", "GOLD_PROMOTION",
            "FINANCIAL_CLAIM_PROMOTION_WITHOUT_EVIDENCE",
        ],
    }


def execution_gate():
    return {
        "id": "F02_FUNDEB_MONTHLY_CASH_OFFLINE",
        "tier": "T0_OFFLINE",
        "auto_allowed": False,
        "manual_execution_required": True,
        "no_workflow_trigger": True,
        "current_triggers": [],
        "effects": {
            "source_network": False,
            "drive_reads": False,
            "drive_writes": False,
            "publication": False,
        },
        "implementation_pr_required": 376,
        "implementation_pr_merged": 376,
        "implementation_merge_sha": MERGE_SHA,
        "implementation_merge_required_before_manual_execution": False,
        "blockers": [
            "EXPLICIT_OWNER_RUNTIME_AUTHORIZATION_REQUIRED",
            "LOCAL_SNAPSHOT_MATERIALIZATION_MUST_BE_BOUNDED",
            "SILVER_PERSISTENCE_REQUIRES_SEPARATE_CREATE_ONLY_EXECUTION",
        ],
    }


def policy():
    return {
        "schema": "ROBO_DADOS_PUBLICOS_AUTOMATION_POLICY_V1",
        "gates": [execution_gate()],
    }


def gate_contract():
    gate = execution_gate()
    gate.update({
        "schema": "F02_FUNDEB_MONTHLY_CASH_GATE_V1",
        "status": "REGISTERED_MANUAL_T0_REMOTE_CLOSED",
    })
    return gate


class F02FundebMonthlyPolicyFinalizationValidatorTests(unittest.TestCase):
    def test_synthetic_finalization_passes_only_with_ancestor_proof(self):
        result = validate_finalization(
            evidence(), policy(), gate_contract(), implementation_ancestor_verified=True
        )
        self.assertEqual(result["status"], "PASS_F02_FUNDEB_MONTHLY_POLICY_FINALIZATION")
        self.assertTrue(result["implementation_ancestor_verified"])
        self.assertFalse(result["auto_allowed"])
        self.assertEqual(result["remote_effects"], 0)

        with self.assertRaisesRegex(
            F02FundebMonthlyPolicyFinalizationStop,
            "IMPLEMENTATION_ANCESTRY_NOT_VERIFIED",
        ):
            validate_finalization(
                evidence(), policy(), gate_contract(), implementation_ancestor_verified=False
            )

    def test_pin_auto_and_remote_drift_fail_closed(self):
        bad_gate = gate_contract()
        bad_gate["implementation_merge_sha"] = "0" * 40
        with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "IMPLEMENTATION_SHA_PIN_DRIFT"):
            validate_finalization(evidence(), policy(), bad_gate, implementation_ancestor_verified=True)

        bad_policy = policy()
        bad_policy["gates"][0]["auto_allowed"] = True
        with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "AUTO_ENABLED"):
            validate_finalization(evidence(), bad_policy, gate_contract(), implementation_ancestor_verified=True)

        bad_policy = policy()
        bad_policy["gates"][0]["effects"]["drive_writes"] = True
        with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "REMOTE_EFFECT_ENABLED"):
            validate_finalization(evidence(), bad_policy, gate_contract(), implementation_ancestor_verified=True)

    def test_missing_or_invalid_json_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing.json"
            with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "JSON_READ"):
                load_json(missing)
            invalid = Path(td) / "invalid.json"
            invalid.write_text("{bad", encoding="utf-8")
            with self.assertRaisesRegex(F02FundebMonthlyPolicyFinalizationStop, "JSON_READ"):
                load_json(invalid)

    def test_new_workflow_is_registered_as_auto_t0_remote_closed(self):
        raw = json.loads(POLICY.read_text(encoding="utf-8"))
        matches = [
            row for row in raw["gates"]
            if row.get("id") == "F02_FUNDEB_MONTHLY_POLICY_FINALIZATION_EVIDENCE_CI"
        ]
        self.assertEqual(len(matches), 1)
        gate = matches[0]
        self.assertEqual(gate["tier"], "T0_OFFLINE")
        self.assertTrue(gate["auto_allowed"])
        self.assertEqual(gate["credential_capability"], "NONE")
        self.assertTrue(all(value is False for value in gate["effects"].values()))
        self.assertEqual(
            gate["workflow"],
            ".github/workflows/f02-fundeb-monthly-policy-finalization-evidence.yml",
        )
        self.assertEqual(gate["permissions"], {"contents": "read"})
        self.assertFalse(gate["persist_credentials"])
        self.assertEqual(gate["secrets"], [])


if __name__ == "__main__":
    unittest.main()
