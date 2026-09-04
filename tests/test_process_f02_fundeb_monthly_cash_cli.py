from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/process_f02_fundeb_monthly_cash.py"
MANIFEST = "docs/evidence/f02_fundeb_monthly_cash/F02_FUNDEB_MONTHLY_2026_JAN_MAR_SOURCE_CUSTODY.json"


def test_auth():
    return {
        "schema":"F02_FUNDEB_MONTHLY_CASH_RUNTIME_AUTHORIZATION_V1",
        "authorization_id":"CLI_TEST",
        "scope":"F02_FUNDEB_MONTHLY_CASH_LOCAL_SNAPSHOT_READ",
        "batch_id":"F02_FUNDEB_MONTHLY_CASH_2026_JAN_MAR",
        "authorized":True,
        "owner_instruction_verbatim":"synthetic CLI test",
        "forbidden_effects":[
            "DELETE","OVERWRITE","SERVING","LOOKER","PUBLICATION","SITE",
            "SCHEDULE","RECURRENCE","GOLD_PROMOTION",
            "FINANCIAL_CLAIM_PROMOTION_WITHOUT_EVIDENCE",
        ],
    }


class ProcessF02FundebMonthlyCashCliTests(unittest.TestCase):
    def test_missing_required_arguments_is_nonzero(self):
        cp = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("--manifest", cp.stderr)
        self.assertIn("--authorization", cp.stderr)

    def test_bad_authorization_sha_pin_is_nonzero_before_snapshot_read(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            auth_path = Path(td) / "auth.json"
            auth_path.write_text(json.dumps(test_auth()), encoding="utf-8")
            rel_auth = auth_path.relative_to(ROOT)
            cp = subprocess.run(
                [
                    sys.executable, str(SCRIPT),
                    "--manifest", MANIFEST,
                    "--authorization", str(rel_auth),
                    "--authorization-sha256", "not-a-sha",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("STOP_F02_FUNDEB_MONTHLY_AUTHORIZATION_PIN", cp.stderr)

    def test_authorization_sha_drift_is_nonzero_before_snapshot_read(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            auth_path = Path(td) / "auth.json"
            auth_path.write_text(json.dumps(test_auth()), encoding="utf-8")
            rel_auth = auth_path.relative_to(ROOT)
            cp = subprocess.run(
                [
                    sys.executable, str(SCRIPT),
                    "--manifest", MANIFEST,
                    "--authorization", str(rel_auth),
                    "--authorization-sha256", "0" * 64,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("STOP_F02_FUNDEB_MONTHLY_AUTHORIZATION_SHA_DRIFT", cp.stderr)

    def test_invalid_manifest_json_is_nonzero(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            bad_manifest = Path(td) / "bad.json"
            bad_manifest.write_text("{bad-json", encoding="utf-8")
            auth_path = Path(td) / "auth.json"
            auth_bytes = json.dumps(test_auth()).encode("utf-8")
            auth_path.write_bytes(auth_bytes)
            cp = subprocess.run(
                [
                    sys.executable, str(SCRIPT),
                    "--manifest", str(bad_manifest.relative_to(ROOT)),
                    "--authorization", str(auth_path.relative_to(ROOT)),
                    "--authorization-sha256", hashlib.sha256(auth_bytes).hexdigest(),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(cp.returncode, 0)
        self.assertIn("STOP_F02_FUNDEB_MONTHLY_MANIFEST_INVALID_JSON", cp.stderr)


if __name__ == "__main__":
    unittest.main()
