from __future__ import annotations

from hashlib import sha256
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/render_eiti_research_answer_offline.py"

_SPEC = importlib.util.spec_from_file_location("task101_cli", SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_CLI = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CLI)


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
        self.assertIn("Nenhuma lacuna histórica de aquisição incluída neste pacote.", result.stdout)
        self.assertIn("## Evidência histórica negativa bounded", result.stdout)
        self.assertIn("### 2018-2021", result.stdout)
        self.assertIn("**Status:** BOUNDED_NO_CANDIDATES", result.stdout)

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
        self.assertIn(
            "Nenhuma evidência histórica negativa bounded incluída neste pacote.",
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

    def test_build_function_invalid_query_type_fails_closed(self):
        with self.assertRaisesRegex(_CLI.EitiResearchAnswerCliStop, "TASK101_QUERY_TYPE"):
            _CLI.build_eiti_research_answer(query_type="INVENTED")

    def test_build_function_fails_closed_on_missing_or_tampered_canonical_input(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            missing = root / _CLI.EITI_PATH.name
            with mock.patch.object(_CLI, "EITI_PATH", missing):
                with self.assertRaisesRegex(_CLI.EitiResearchAnswerCliStop, "INPUT_READ"):
                    _CLI.build_eiti_research_answer()

            tampered = root / _CLI.EITI_PATH.name
            tampered.write_text('{"research_bundle":{},"institutionalization_matrix":{}}', encoding="utf-8")
            with mock.patch.object(_CLI, "EITI_PATH", tampered):
                with self.assertRaisesRegex(_CLI.EitiResearchAnswerCliStop, "INPUT_SHA256_MISMATCH"):
                    _CLI.build_eiti_research_answer()

    def test_claim_audit_with_no_unknown_gaps_remains_well_formed(self):
        result = run_cli("--query-type", "CLAIM_AUDIT", "--no-unknown-gaps")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(
            "Nenhuma dimensão de institucionalização incluída neste tipo de consulta.",
            result.stdout,
        )
        self.assertIn(
            "Nenhuma lacuna de institucionalização incluída neste pacote.",
            result.stdout,
        )

    def test_load_json_fails_closed_on_missing_malformed_and_tampered_input(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            missing = root / "missing.json"
            with self.assertRaisesRegex(_CLI.EitiResearchAnswerCliStop, "INPUT_READ"):
                _CLI._load_json(missing, expected_sha256="0" * 64)

            malformed = root / "malformed.json"
            malformed.write_bytes(b"{not-json")
            malformed_sha = sha256(malformed.read_bytes()).hexdigest()
            with self.assertRaisesRegex(_CLI.EitiResearchAnswerCliStop, "INPUT_JSON"):
                _CLI._load_json(malformed, expected_sha256=malformed_sha)

            tampered = root / "tampered.json"
            tampered.write_text('{"ok":true}', encoding="utf-8")
            with self.assertRaisesRegex(_CLI.EitiResearchAnswerCliStop, "INPUT_SHA256_MISMATCH"):
                _CLI._load_json(tampered, expected_sha256="0" * 64)

    def test_pinned_input_hashes_match_current_versioned_configs(self):
        for path in (_CLI.EITI_PATH, _CLI.HISTORICAL_PATH):
            observed = sha256(path.read_bytes()).hexdigest()
            self.assertEqual(_CLI.EXPECTED_INPUT_SHA256[path.name], observed)

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
