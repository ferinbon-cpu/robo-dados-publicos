from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestBI004GateEntrypoint(unittest.TestCase):
    def test_gate_entrypoint_passes_offline(self):
        result = subprocess.run(
            [sys.executable, "scripts/github_bi_004_serving_executor_gate.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertIn(
            "PASS_BI_004_BOUNDED_FIRST_SERVING_EXECUTOR_OFFLINE",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
