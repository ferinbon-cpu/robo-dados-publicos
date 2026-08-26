from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW_SCRIPT = ROOT / "scripts/github_siope_official_olinda_exact_contract_corroboration_review_gate.py"
MINIMAL_GET_SCRIPT = ROOT / "scripts/github_siope_official_olinda_minimal_readonly_get_gate.py"


class MinimalReadonlyGetScriptBootstrapTests(unittest.TestCase):
    def _run(self, *args: str) -> dict:
        completed = subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        return json.loads(completed.stdout)

    def test_review_script_runs_directly_from_repo_root(self):
        result = self._run(str(REVIEW_SCRIPT))
        self.assertEqual(
            result["status"],
            "PASS_M7_SIOPE_OFFICIAL_OLINDA_EXACT_CONTRACT_CORROBORATION_REVIEW",
        )
        self.assertFalse(result["network_called"])
        self.assertFalse(result["resource_get_authorized"])

    def test_minimal_get_dry_run_script_runs_directly_from_repo_root(self):
        result = self._run(str(MINIMAL_GET_SCRIPT), "--dry-run")
        self.assertEqual(
            result["status"],
            "PASS_M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_DESIGN",
        )
        self.assertFalse(result["network_called"])
        self.assertEqual(result["request_count"], 0)


if __name__ == "__main__":
    unittest.main()
