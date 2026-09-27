from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/github_task_046_f01_ppa_scoped_silver_v2_candidate_review_gate.py"


class Task046GateEntrypointTests(unittest.TestCase):
    def test_gate_entrypoint_passes(self) -> None:
        proc = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("TASK046_STATUS=PASS_TASK046_PPA_SCOPED_SILVER_V2_CANDIDATE_REVIEW", proc.stdout)
        self.assertIn("TASK046_REMOTE_WRITE_AUTHORIZED=false", proc.stdout)
        self.assertIn("TASK046_EITI_FINANCIAL_IDENTITY=EVIDENCIA_INSUFICIENTE", proc.stdout)


if __name__ == "__main__":
    unittest.main()
