from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "robo_dados_publicos" / "sources" / "siope_artifact_download_dom_intent_diagnostics.py"
SCRIPT = ROOT / "scripts" / "github_siope_artifact_download_dom_intent_diagnostics_gate.py"


class TestM7SiopeArtifactDownloadDomCleanupHotfix(unittest.TestCase):
    def test_source_waits_after_kill_and_cleanup_cannot_destroy_result(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("ignore_cleanup_errors=True", source)
        self.assertIn("process.kill()", source)
        self.assertIn("process.wait(timeout=2)", source)
        self.assertNotIn("artifact_download = \"ALLOW\"", source)

    def test_runner_emits_sanitized_fallback_for_unexpected_exception(self) -> None:
        spec = importlib.util.spec_from_file_location("dom_gate_hotfix_test", SCRIPT)
        self.assertIsNotNone(spec)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.json"
            stdout = io.StringIO()
            argv = [str(SCRIPT), "--output", str(output)]
            with patch.object(sys, "argv", argv), patch.object(
                module,
                "diagnose_artifact_download_dom_intent",
                side_effect=OSError(39, "Directory not empty", "/tmp/private-profile"),
            ), contextlib.redirect_stdout(stdout):
                code = module.main()

            self.assertEqual(code, 33)
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "STOP_M7_SIOPE_ARTIFACT_DOWNLOAD_DOM_INTENT_DIAGNOSTICS_GATE")
            self.assertEqual(payload["stop_reason"], "UNEXPECTED_RUNTIME_ERROR")
            self.assertFalse(payload["artifact_downloaded"])
            self.assertFalse(payload["candidate_route_network_sent"])
            self.assertFalse(payload["collection_authorized"])
            serialized = json.dumps(payload, sort_keys=True)
            self.assertNotIn("private-profile", serialized)
            self.assertNotIn("Directory not empty", serialized)


if __name__ == "__main__":
    unittest.main()
