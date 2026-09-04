from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.f02_fundeb_monthly_cash import (
    F02FundebMonthlyCashStop,
    load_pinned_authorization,
)

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "config/f02_fundeb_monthly_cash_gate.v1.json"
CUSTODY = ROOT / "docs/evidence/f02_fundeb_monthly_cash/F02_FUNDEB_MONTHLY_2026_JAN_MAR_SOURCE_CUSTODY.json"


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


class F02FundebMonthlyCashStandaloneGateTests(unittest.TestCase):
    def test_gate_is_design_only_remote_closed_until_global_policy_registration(self):
        gate = json.loads(GATE.read_text(encoding="utf-8"))
        self.assertEqual(gate["schema"], "F02_FUNDEB_MONTHLY_CASH_GATE_DESIGN_V1")
        self.assertEqual(gate["tier"], "T0")
        self.assertEqual(gate["mode"], "T0_OFFLINE_FUNDEB_MONTHLY_CASH")
        self.assertFalse(gate["operational"])
        self.assertTrue(gate["global_policy_registration_required"])
        self.assertEqual(gate["execution_before_global_policy_registration"], "STOP")
        self.assertEqual(
            gate["status"],
            "DESIGN_ONLY_NON_OPERATIONAL_UNTIL_GLOBAL_POLICY_REGISTRATION",
        )
        self.assertFalse(gate["remote_drive_read_authorized"])
        self.assertTrue(gate["runtime_authorization_required"])
        self.assertTrue(all(gate["blocked_remote_effects"].values()))
        self.assertTrue(all(gate["semantic_blocks"].values()))

    def test_source_custody_is_primary_only_and_pins_three_unique_months(self):
        custody = json.loads(CUSTODY.read_text(encoding="utf-8"))
        self.assertEqual(custody["family"], "FUNDEB_MONTHLY_CASH_LOCAL")
        self.assertEqual(
            [x["month"] for x in custody["sources"]],
            ["2026-01", "2026-02", "2026-03"],
        )
        self.assertEqual(len({x["drive_file_id"] for x in custody["sources"]}), 3)
        self.assertEqual(len({x["sha256"] for x in custody["sources"]}), 3)
        self.assertTrue(custody["evidence_boundary"]["primary_source_manifest_only"])
        self.assertTrue(
            custody["evidence_boundary"]["legacy_derived_artifacts_not_used_for_validation"]
        )

    def test_synthetic_authorization_is_generated_transiently_and_tests_fixture_path_is_rejected(self):
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
