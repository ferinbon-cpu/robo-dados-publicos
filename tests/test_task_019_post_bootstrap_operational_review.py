from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Task019PostBootstrapOperationalReviewTests(unittest.TestCase):
    def test_gate_passes_on_pinned_repository_state(self):
        proc = subprocess.run(
            [sys.executable, "scripts/github_task_019_post_bootstrap_operational_review_gate.py"],
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

    def test_review_does_not_promote_recurrence_or_release(self):
        review = json.loads(
            (
                ROOT
                / "docs/evidence/TASK_019_POST_BOOTSTRAP_OPERATIONAL_REVIEW_0.8.0.json"
            ).read_text(encoding="utf-8")
        )
        conclusions = review["operational_conclusions"]
        release = review["release_boundary"]
        effects = review["effects_of_task_019"]

        self.assertEqual(conclusions["recurrence_eligibility"], "NOT_PROMOTED_BY_TASK_019")
        self.assertFalse(conclusions["schedule_authorization"])
        self.assertFalse(conclusions["recurrence_authorization"])
        self.assertFalse(conclusions["future_batch_execution_authorized"])
        self.assertEqual(release["active"], "0.7.0")
        self.assertEqual(release["candidate"], "0.8.0")
        self.assertFalse(release["release_promotion_performed"])
        self.assertEqual(release["B1"], "PENDING")
        self.assertEqual(release["B2"], "PENDING")
        self.assertEqual(release["B3"], "PENDING")
        self.assertTrue(all(value == 0 for value in effects.values()))

    def test_next_engineering_task_is_offline_only(self):
        review = json.loads(
            (
                ROOT
                / "docs/evidence/TASK_019_POST_BOOTSTRAP_OPERATIONAL_REVIEW_0.8.0.json"
            ).read_text(encoding="utf-8")
        )
        actions = review["next_actions"]
        self.assertEqual(
            actions["engineering_track"],
            "TASK_020_T0_JORNAL_INCREMENTAL_RECURRENCE_READINESS_DESIGN",
        )
        self.assertFalse(actions["task_020_remote_effects_authorized"])


if __name__ == "__main__":
    unittest.main()
