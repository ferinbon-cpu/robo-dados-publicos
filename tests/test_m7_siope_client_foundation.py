from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from urllib.error import URLError

from robo_dados_publicos.sources.siope_client import SiopeClient, SiopeClientError, SiopeClientPolicy, build_dados_gerais_url
from robo_dados_publicos.sources.siope_client_foundation_design import run_design
from robo_dados_publicos.sources.siope_client_limeira_live_validation import SiopeClientLimeiraLiveValidationError, run_validation, validate_config
from robo_dados_publicos.sources.siope_official_olinda_limeira_pilot_readonly_get_review import load_json, run_review

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_limeira_pilot_readonly_get_review.json"
DESIGN_CONFIG = ROOT / "config/source_expansion.siope_client_foundation_design.json"
VALIDATION_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_live_validation.json"
PROVEN_URL = "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)?@Ano_Consulta=2024&@Num_Peri=6&@Sig_UF='SP'&$filter=COD_MUNI%20eq%20352690&$select=COD_MUNI,NOM_MUNI,NUM_ANO,NUM_PERI,SIG_UF&$format=json"


class FakeResponse:
    def __init__(self, payload: dict, *, url: str = PROVEN_URL, content_type: str = "application/json", status: int = 200):
        self._raw = json.dumps(payload).encode("utf-8")
        self.url = url
        self.status = status
        self.headers = {"Content-Type": content_type}
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb): return False
    def geturl(self): return self.url
    def getcode(self): return self.status
    def read(self, n: int = -1): return self._raw if n < 0 else self._raw[:n]


def good_payload() -> dict:
    return {"@odata.context": "sanitized-test-context", "value": [{"COD_MUNI": 352690, "NOM_MUNI": "Limeira", "NUM_ANO": 2024, "NUM_PERI": 6, "SIG_UF": "SP"}]}


class SiopeClientFoundationTests(unittest.TestCase):
    def test_pinned_limeira_pilot_review_passes_offline(self):
        cfg = load_json(REVIEW_CONFIG); evidence_path = ROOT / cfg["pinned_evidence_path"]
        result = run_review(cfg, load_json(evidence_path), evidence_path=evidence_path)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_REVIEW")
        self.assertEqual(result["municipal_identity_status"], "PROVEN_LIMEIRA_352690_SP_2024_6")
        self.assertFalse(result["collection_authorized"])

    def test_client_builder_reproduces_proven_pilot_url_exactly(self):
        url = build_dados_gerais_url(ano=2024, periodo=6, uf="SP", municipality_code=352690, select_fields=("COD_MUNI", "NOM_MUNI", "NUM_ANO", "NUM_PERI", "SIG_UF"))
        self.assertEqual(url, PROVEN_URL); self.assertIn("%20", url); self.assertNotIn("+", url)

    def test_builder_rejects_unproven_field(self):
        with self.assertRaises(SiopeClientError):
            build_dados_gerais_url(ano=2024, periodo=6, uf="SP", municipality_code=352690, select_fields=("COD_MUNI", "CAMPO_INVENTADO"))

    def test_policy_keeps_retry_redirect_and_pagination_closed(self):
        for policy in (SiopeClientPolicy(max_attempts=2), SiopeClientPolicy(follow_redirects=True), SiopeClientPolicy(follow_nextlink=True)):
            with self.assertRaises(SiopeClientError): policy.validate()

    def test_foundation_design_passes_without_network(self):
        result = run_design(json.loads(DESIGN_CONFIG.read_text(encoding="utf-8")))
        self.assertTrue(result["builder_reproduces_proven_limeira_url"]); self.assertEqual(result["resource_allowlist_count"], 1); self.assertFalse(result["pagination_follow_allowed"])

    def test_generic_client_mocked_success(self):
        client = SiopeClient(opener=lambda req, timeout: FakeResponse(good_payload(), url=req.full_url))
        page = client.get_dados_gerais_page(ano=2024, periodo=6, uf="SP", municipality_code=352690, select_fields=("COD_MUNI", "NOM_MUNI", "NUM_ANO", "NUM_PERI", "SIG_UF"))
        self.assertEqual(page.status, 200); self.assertEqual(len(page.records), 1); self.assertEqual(page.request_count, 1); self.assertFalse(page.nextlink_present)

    def test_nextlink_stops_until_future_authorization(self):
        payload = good_payload(); payload["@odata.nextLink"] = "https://www.fnde.gov.br/next"
        client = SiopeClient(opener=lambda req, timeout: FakeResponse(payload, url=req.full_url))
        with self.assertRaisesRegex(SiopeClientError, "NEXTLINK_REQUIRES_FUTURE_AUTHORIZATION"):
            client.get_dados_gerais_page(ano=2024, periodo=6, uf="SP", municipality_code=352690, select_fields=("COD_MUNI",))

    def test_timeout_is_classified_and_not_retried(self):
        calls = {"n": 0}
        def opener(req, timeout):
            calls["n"] += 1; raise URLError(TimeoutError("timed out"))
        client = SiopeClient(opener=opener)
        with self.assertRaisesRegex(SiopeClientError, "TIMEOUT"):
            client.get_dados_gerais_page(ano=2024, periodo=6, uf="SP", municipality_code=352690, select_fields=("COD_MUNI",))
        self.assertEqual(calls["n"], 1)

    def test_live_validation_mocked_success_is_sanitized(self):
        cfg = json.loads(VALIDATION_CONFIG.read_text(encoding="utf-8")); result = run_validation(cfg, opener=lambda req, timeout: FakeResponse(good_payload(), url=req.full_url))
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION"); self.assertTrue(result["generic_client_used"]); self.assertEqual(result["value_count"], 1); self.assertFalse(result["record_values_persisted"]); self.assertFalse(result["query_values_persisted_in_result"]); self.assertFalse(result["collection_authorized"])

    def test_live_validation_identity_mismatch_fails_closed(self):
        cfg = json.loads(VALIDATION_CONFIG.read_text(encoding="utf-8")); payload = good_payload(); payload["value"][0]["COD_MUNI"] = 1
        with self.assertRaises(SiopeClientLimeiraLiveValidationError): run_validation(cfg, opener=lambda req, timeout: FakeResponse(payload, url=req.full_url))

    def test_live_validation_dry_design_has_zero_network(self):
        result = validate_config(json.loads(VALIDATION_CONFIG.read_text(encoding="utf-8"))); self.assertFalse(result["network_called"]); self.assertEqual(result["request_count"], 0)

    def test_gate_scripts_run_directly_from_repo_root(self):
        commands = [[sys.executable, "scripts/github_siope_official_olinda_limeira_pilot_readonly_get_review_gate.py"], [sys.executable, "scripts/github_siope_client_foundation_design_gate.py"], [sys.executable, "scripts/github_siope_client_limeira_live_validation_gate.py", "--dry-run"]]
        for command in commands:
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False); self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_workflow_is_manual_readonly_full_qa_and_sanitized(self):
        text = (ROOT / ".github/workflows/siope-client-limeira-live-validation-gate.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text); self.assertIn("confirm_siope_client_limeira_live_validation", text); self.assertIn("contents: read", text); self.assertIn("python -m unittest discover -s tests -v", text); self.assertIn("python main.py selftest", text); self.assertIn("continue-on-error: true", text); self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", text); self.assertNotIn("schedule:", text); self.assertNotIn("rerun", text.lower())


if __name__ == "__main__":
    unittest.main()
