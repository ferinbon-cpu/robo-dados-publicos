from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from robo_dados_publicos.sources.siope_artifact_download_dom_intent_diagnostics import (
    diagnose_artifact_download_dom_intent,
    sanitize_dom_snapshot,
)
from robo_dados_publicos.sources.siope_artifact_download_runtime_route_probe import (
    load_artifact_download_runtime_route_probe_config,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_artifact_download_runtime_route_probe_gate.json"
SOURCE = ROOT / "robo_dados_publicos" / "sources" / "siope_artifact_download_dom_intent_diagnostics.py"
SCRIPT = ROOT / "scripts" / "github_siope_artifact_download_dom_intent_diagnostics_gate.py"
WORKFLOW = ROOT / ".github" / "workflows" / "siope-artifact-download-dom-intent-diagnostics-gate.yml"


class FakeRuntime:
    def __init__(self, *, before=None, after=None):
        self.before = before or {"controls": [], "dialogs": []}
        self.after = after or {"controls": [], "dialogs": []}

    def run_probe(self, config):
        return {
            "page_verified": True,
            "artifact_declared": True,
            "export_control_found": True,
            "click_executed": True,
            "browser_download_denied": True,
            "verified_metadata_network_sent": True,
            "verified_metadata_request_count": 1,
            "blocked_request_count": 1,
            "dom_before": self.before,
            "dom_after": self.after,
            "candidate_route_network_sent": False,
            "artifact_downloaded": False,
        }


class TestM7SiopeArtifactDownloadDomIntentDiagnostics(unittest.TestCase):
    def setUp(self):
        self.config = load_artifact_download_runtime_route_probe_config(CONFIG)

    def test_new_dialog_and_control_are_reported_without_query_values(self):
        before = {"controls": [{"tag": "button", "role": "", "text": "Exportar artefato", "href": None, "disabled": False}], "dialogs": []}
        after = {
            "controls": [
                before["controls"][0],
                {"tag": "a", "role": "button", "text": "Confirmar exportação", "href": {"scheme": "https", "host": "www.fnde.gov.br", "path": "/download", "query_keys": ["token", "id"]}, "disabled": False},
            ],
            "dialogs": [{"tag": "div", "role": "dialog", "text": "Deseja exportar o artefato?"}],
        }
        result = diagnose_artifact_download_dom_intent(self.config, runtime=FakeRuntime(before=before, after=after))
        self.assertEqual(result["diagnostic_status"], "DOM_INTENT_CHANGE_OBSERVED")
        self.assertEqual(result["dom_change"]["new_control_count"], 1)
        href = result["dom_change"]["new_controls"][0]["href"]
        self.assertEqual(href["query_keys"], ["id", "token"])
        self.assertNotIn("query", href)
        self.assertFalse(result["second_click_executed"])
        self.assertFalse(result["artifact_downloaded"])

    def test_no_change_is_explicit(self):
        snap = {"controls": [{"tag": "button", "role": "", "text": "Exportar artefato", "href": None, "disabled": False}], "dialogs": []}
        result = diagnose_artifact_download_dom_intent(self.config, runtime=FakeRuntime(before=snap, after=snap))
        self.assertEqual(result["diagnostic_status"], "NO_DOM_INTENT_CHANGE_OBSERVED")
        self.assertEqual(result["dom_change"]["new_control_count"], 0)

    def test_sanitizer_caps_and_allowlists_fields(self):
        raw = {
            "controls": [{"tag": "a", "role": "link", "text": "x" * 500, "href": {"scheme": "https", "host": "www.fnde.gov.br", "path": "/x", "query_keys": ["safe"], "secret": "NO"}, "disabled": False, "outerHTML": "NO"}],
            "dialogs": [{"tag": "div", "role": "dialog", "text": "y" * 500, "html": "NO"}],
        }
        clean = sanitize_dom_snapshot(raw)
        self.assertLessEqual(len(clean["controls"][0]["text"]), 160)
        self.assertNotIn("outerHTML", clean["controls"][0])
        self.assertNotIn("secret", clean["controls"][0]["href"])
        self.assertNotIn("html", clean["dialogs"][0])

    def test_source_has_one_click_and_no_input_value_or_html_capture(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('"behavior": "deny"', source)
        self.assertEqual(source.count("e.click();"), 1)
        self.assertNotIn("outerHTML", source)
        self.assertNotIn("document.querySelectorAll('input", source)
        self.assertNotIn(".value", source)
        self.assertIn("searchParams.keys()", source)

    def test_direct_dry_run_bootstraps_without_network(self):
        proc = subprocess.run([sys.executable, str(SCRIPT), "--dry-run"], cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], "PASS_M7_SIOPE_ARTIFACT_DOWNLOAD_DOM_INTENT_DIAGNOSTICS_DRY_RUN")
        self.assertFalse(payload["second_click_executed"])
        self.assertFalse(payload["candidate_route_network_sent"])
        self.assertFalse(payload["artifact_downloaded"])

    def test_workflow_is_manual_read_only_and_runs_full_qa_before_live(self):
        wf = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", wf)
        self.assertNotIn("schedule:", wf)
        self.assertIn("contents: read", wf)
        self.assertIn("confirm_artifact_download_dom_intent_diagnostics", wf)
        self.assertIn("persist-credentials: false", wf)
        self.assertIn("python -m unittest discover -s tests -v", wf)
        self.assertIn("python main.py selftest", wf)
        self.assertLess(wf.index("python -m unittest discover -s tests -v"), wf.index("Diagnóstico DOM ao vivo após clique único"))
        self.assertLess(wf.index("python main.py selftest"), wf.index("Diagnóstico DOM ao vivo após clique único"))
        self.assertNotIn("curl ", wf)
        self.assertNotIn("wget ", wf)
        self.assertNotIn("drive", wf.lower())


if __name__ == "__main__":
    unittest.main()
