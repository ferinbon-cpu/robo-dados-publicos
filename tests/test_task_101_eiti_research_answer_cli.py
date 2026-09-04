from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/render_eiti_research_answer_offline.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


class TestTask101EitiResearchAnswerCli(unittest.TestCase):
    def test_default_cli_prints_researcher_facing_markdown(self):
        result = run_cli()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertTrue(result.stdout.startswith("# Research answer — "))
        self.assertIn("Política Municipal de Educação Integral em Tempo Integral de Limeira", result.stdout)
        self.assertIn("### CLAIM:EITI_FINANCIAL_IDENTITY", result.stdout)
        self.assertIn("**Status:** UNKNOWN", result.stdout)
        self.assertIn("**budgetary_policy_identity** — UNKNOWN", result.stdout)
        self.assertIn("**transaction_execution_identity** — UNKNOWN", result.stdout)
        self.assertIn("**outcome_effect** — UNKNOWN", result.stdout)
        self.assertIn("### 2018-2021", result.stdout)
        self.assertIn("### 2022-2025", result.stdout)

    def test_cli_is_deterministic(self):
        first = run_cli()
        second = run_cli()
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_claim_audit_omits_matrix_and_historical_payloads(self):
        result = run_cli("--query-type", "CLAIM_AUDIT")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(
            "Nenhuma dimensão de institucionalização incluída neste tipo de consulta.",
            result.stdout,
        )
        self.assertIn(
            "Nenhuma lacuna histórica de aquisição incluída neste pacote.",
            result.stdout,
        )

    def test_no_evidence_keeps_ids_but_omits_expanded_evidence(self):
        result = run_cli("--no-evidence")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("**Evidence IDs:**", result.stdout)
        self.assertNotIn("**Evidências:**", result.stdout)

    def test_no_unknown_gaps_omits_matrix_gap_list_only(self):
        result = run_cli("--no-unknown-gaps")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("**budgetary_policy_identity** — UNKNOWN", result.stdout)
        self.assertIn("Nenhuma lacuna de institucionalização incluída neste pacote.", result.stdout)

    def test_invalid_query_type_fails_before_execution(self):
        result = run_cli("--query-type", "INVENTED")
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)

    def test_script_has_no_remote_client_imports_or_persistence_calls(self):
        source = SCRIPT.read_text(encoding="utf-8")
        forbidden = (
            "requests",
            "urllib.request",
            "googleapiclient",
            "google.auth",
            "boto3",
            "socket",
            "drive_write",
            "state_registry",
            "queue_write",
            "publication",
        )
        for marker in forbidden:
            self.assertNotIn(marker, source)


if __name__ == "__main__":
    unittest.main()
