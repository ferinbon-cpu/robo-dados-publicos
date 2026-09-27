from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/github_task_045_f01_bounded_existing_custody_readonly_review_gate.py"


class Task045GateEntrypointTests(unittest.TestCase):
    def test_gate_entrypoint_passes(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(
            "TASK045_STATUS=STOP_TASK045_EITI_FINANCIAL_IDENTITY_CHAIN_STILL_INCOMPLETE_AFTER_BOUNDED_READONLY_REVIEW",
            proc.stdout,
        )
        self.assertIn("TASK045_PPA2690_RESOLVED=true", proc.stdout)
        self.assertIn("TASK045_EITI_FINANCIAL_IDENTITY=EVIDENCIA_INSUFICIENTE", proc.stdout)
        self.assertIn("TASK045_NEW_REMOTE_WRITE=false", proc.stdout)


if __name__ == "__main__":
    unittest.main()
