from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/render_research_answer_offline.py"
TASK101 = ROOT / "scripts/render_eiti_research_answer_offline.py"

_SPEC = importlib.util.spec_from_file_location("task102_cli", SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_CLI = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CLI)


def run_script(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )


class TestTask102GenericResearchQuerySpec(unittest.TestCase):
    def test_default_generic_cli_matches_task101_default_output(self):
        generic = run_script(SCRIPT)
        specific = run_script(TASK101)
        self.assertEqual(0, generic.returncode, generic.stderr)
        self.assertEqual(0, specific.returncode, specific.stderr)
        self.assertEqual(specific.stdout, generic.stdout)

    def test_generic_cli_is_deterministic(self):
        first = run_script(SCRIPT)
        second = run_script(SCRIPT)
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_default_output_preserves_known_eiti_gaps(self):
        result = run_script(SCRIPT)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("CLAIM:EITI_FINANCIAL_IDENTITY", result.stdout)
        self.assertIn("**budgetary_policy_identity** — UNKNOWN", result.stdout)
        self.assertIn("**transaction_execution_identity** — UNKNOWN", result.stdout)
        self.assertIn("**outcome_effect** — UNKNOWN", result.stdout)

    def test_cli_rejects_path_traversal_and_arbitrary_spec_paths(self):
        for candidate in ("../x.json", "../../config/research_query.v1.json", "sub/x.json", r"sub\\x.json"):
            result = run_script(SCRIPT, "--spec", candidate)
            self.assertEqual(2, result.returncode, candidate)
            self.assertEqual("", result.stdout)

    def test_unknown_spec_fails_closed(self):
        result = run_script(SCRIPT, "--spec", "does_not_exist.json")
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("STOP_TASK102:", result.stderr)

    def test_registry_is_t0_remote_effect_free(self):
        registry = _CLI._load_registry()
        self.assertEqual("RESEARCH_DATASET_REGISTRY_V1", registry["schema"])
        self.assertTrue(all(value is False for value in registry["remote_effects"].values()))
        self.assertEqual(1, len(registry["datasets"]))

    def test_registry_subject_and_query_types_are_bounded(self):
        registry = _CLI._load_registry()
        dataset = registry["datasets"][0]
        self.assertEqual("POLICY:EITI_LIMEIRA", dataset["subject_id"])
        self.assertEqual(list(_CLI.QUERY_TYPES), dataset["allowed_query_types"])

    def test_spec_cannot_supply_sources_urls_or_free_form_prompt(self):
        valid = {
            "version": 1,
            "schema": "RESEARCH_QUERY_SPEC_V1",
            "spec_id": "SPEC:X",
            "dataset_id": "DATASET:X",
            "query_id": "Q:X",
            "query_type": "CLAIM_AUDIT",
            "subject_id": "POLICY:X",
            "include_evidence": True,
            "include_unknown_gaps": True,
            "output_format": "MARKDOWN",
            "output_channel": "STDOUT",
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with mock.patch.object(_CLI, "QUERY_SPEC_DIR", root):
                for field, value in (
                    ("source_path", "config/x.json"),
                    ("source_url", "https://example.invalid/x"),
                    ("prompt", "interpret freely"),
                    ("question", "what happened?"),
                    ("free_form", True),
                ):
                    payload = dict(valid)
                    payload[field] = value
                    (root / "x.json").write_text(json.dumps(payload), encoding="utf-8")
                    with self.assertRaisesRegex(_CLI.ResearchAnswerCliStop, "FORBIDDEN_FIELD"):
                        _CLI._load_query_spec("x.json")

    def test_subject_mismatch_fails_before_query_execution(self):
        spec = _CLI._load_query_spec(_CLI.DEFAULT_SPEC)
        altered = dict(spec)
        altered["subject_id"] = "POLICY:OTHER"
        with mock.patch.object(_CLI, "_load_query_spec", return_value=altered):
            with self.assertRaisesRegex(_CLI.ResearchAnswerCliStop, "SUBJECT_MISMATCH"):
                _CLI.build_research_answer()

    def test_sha256_verification_fails_closed_on_tampered_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "payload.json"
            path.write_text('{"ok":true}', encoding="utf-8")
            expected = sha256(path.read_bytes()).hexdigest()
            self.assertEqual({"ok": True}, _CLI._read_json(path, expected_sha256=expected))
            path.write_text('{"ok":false}', encoding="utf-8")
            with self.assertRaisesRegex(_CLI.ResearchAnswerCliStop, "SHA256_MISMATCH"):
                _CLI._read_json(path, expected_sha256=expected)

    def test_registry_rejects_paths_outside_config(self):
        registry = _CLI._load_registry()
        altered = json.loads(json.dumps(registry))
        altered["datasets"][0]["research_source"]["path"] = "../secret.json"
        with self.assertRaises(_CLI.ResearchAnswerCliStop):
            _CLI._validate_registry(altered)

    def test_script_has_no_remote_or_llm_client_imports(self):
        source = SCRIPT.read_text(encoding="utf-8")
        forbidden = (
            "requests",
            "urllib.request",
            "googleapiclient",
            "google.auth",
            "boto3",
            "socket",
            "openai",
            "anthropic",
        )
        for marker in forbidden:
            self.assertNotIn(marker, source)


if __name__ == "__main__":
    unittest.main()
