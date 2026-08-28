from pathlib import Path
import json
import subprocess
import sys
import unittest

from robo_dados_publicos.automation.policy import load_policy
from robo_dados_publicos.automation.trust_boundary import TrustBoundaryError, evaluate_m8_t1_trust_boundary


ROOT = Path(__file__).resolve().parents[1]


class TestM8T1NoClickTrustBoundary(unittest.TestCase):
    def setUp(self):
        self.policy = load_policy(ROOT)
        self.good = dict(
            repository="ferinbon-cpu/robo-dados-publicos",
            ref="refs/heads/main",
            event_name="push",
            ref_protected=True,
            repository_private=False,
        )

    def test_trusted_public_protected_main_passes(self):
        result = evaluate_m8_t1_trust_boundary(self.policy, **self.good)
        self.assertEqual("PASS_M8_T1_TRUST_BOUNDARY", result["status"])
        self.assertEqual("AUTO_ALLOWED", result["policy_decision"])
        self.assertEqual("T1_REMOTE_READONLY", result["tier"])
        self.assertEqual("READ_ONLY_PROVEN", result["credential_capability"])
        self.assertEqual(21728151, result["ruleset_id"])
        self.assertEqual(0, result["drive_write_count"])
        self.assertFalse(result["publication_authorized"])

    def test_wrong_repository_fails_closed(self):
        kwargs = dict(self.good, repository="fork/example")
        with self.assertRaisesRegex(TrustBoundaryError, "STOP_M8_T1_UNTRUSTED_REPOSITORY"):
            evaluate_m8_t1_trust_boundary(self.policy, **kwargs)

    def test_non_push_fails_closed(self):
        kwargs = dict(self.good, event_name="pull_request")
        with self.assertRaisesRegex(TrustBoundaryError, "STOP_M8_T1_UNTRUSTED_EVENT"):
            evaluate_m8_t1_trust_boundary(self.policy, **kwargs)

    def test_non_main_fails_closed(self):
        kwargs = dict(self.good, ref="refs/heads/feature")
        with self.assertRaisesRegex(TrustBoundaryError, "STOP_M8_T1_UNTRUSTED_REF"):
            evaluate_m8_t1_trust_boundary(self.policy, **kwargs)

    def test_unprotected_main_fails_closed(self):
        kwargs = dict(self.good, ref_protected=False)
        with self.assertRaisesRegex(TrustBoundaryError, "STOP_M8_T1_MAIN_NOT_PROTECTED"):
            evaluate_m8_t1_trust_boundary(self.policy, **kwargs)

    def test_private_repository_fails_closed(self):
        kwargs = dict(self.good, repository_private=True)
        with self.assertRaisesRegex(TrustBoundaryError, "STOP_M8_T1_REPOSITORY_NOT_PUBLIC"):
            evaluate_m8_t1_trust_boundary(self.policy, **kwargs)

    def test_cli_dry_run_passes_without_network_or_secrets(self):
        cp = subprocess.run(
            [sys.executable, str(ROOT / "scripts/github_m8_t1_no_click_trust_boundary_gate.py"), "--dry-run"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, cp.returncode, cp.stderr or cp.stdout)
        result = json.loads(cp.stdout.strip())
        self.assertEqual("PASS_M8_T1_TRUST_BOUNDARY", result["status"])
        self.assertEqual(0, result["source_get_count"])
        self.assertEqual(0, result["drive_write_count"])
        self.assertFalse(result["publication_authorized"])


if __name__ == "__main__":
    unittest.main()
