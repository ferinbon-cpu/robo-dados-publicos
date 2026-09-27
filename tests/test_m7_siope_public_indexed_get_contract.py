from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from robo_dados_publicos.sources.siope_download_route_discovery import TextResponse
from robo_dados_publicos.sources.siope_public_indexed_get_contract import (
    SiopePublicIndexedGetContractError,
    load_public_indexed_get_contract_config,
    verify_public_indexed_get_contract,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_public_indexed_get_contract_gate.json"
DECISION = ROOT / "config" / "source_expansion.siope_public_report_human_challenge_decision.json"
SCRIPT = ROOT / "scripts" / "github_siope_public_indexed_get_contract_gate.py"
WORKFLOW = ROOT / ".github" / "workflows" / "siope-public-indexed-get-contract-gate.yml"


class FakeClient:
    def __init__(self, body: str):
        self.body = body
        self.calls: list[str] = []

    def get_text(self, url: str, *, max_bytes: int, allowed_content_types: tuple[str, ...]):
        self.calls.append(url)
        return TextResponse(
            url=url,
            status=200,
            content_type="text/html",
            body=self.body,
            byte_count=len(self.body.encode("utf-8")),
        )


class TestM7SiopePublicIndexedGetContract(unittest.TestCase):
    def setUp(self):
        self.cfg = load_public_indexed_get_contract_config(CONFIG)

    def test_human_challenge_decision_blocks_post_and_bypass(self):
        decision = json.loads(DECISION.read_text(encoding="utf-8"))
        self.assertEqual(decision["human_challenge_status"], "PROVEN_PRESENT")
        self.assertEqual(decision["decision"], "BLOCK_UNATTENDED_FORM_SUBMISSION")
        policy = decision["policy"]
        self.assertFalse(policy["submit_post_form"])
        self.assertFalse(policy["bypass_captcha"])
        self.assertFalse(policy["solve_captcha_automatically"])
        self.assertFalse(policy["capture_captcha_material"])
        self.assertFalse(policy["reuse_personal_session"])
        self.assertFalse(policy["collection_authorized"])
        self.assertEqual(decision["next_gate"], "M7_SIOPE_PUBLIC_INDEXED_GET_CONTRACT_GATE_0_8_0")

    def test_config_uses_exact_public_example_and_never_pilot_limeira(self):
        self.assertIn("cod_muni=292430", self.cfg["public_indexed_example_url"])
        self.assertNotIn("352690", self.cfg["public_indexed_example_url"])
        self.assertTrue(self.cfg["verification_rules"]["send_exact_indexed_example_only"])
        self.assertFalse(self.cfg["verification_rules"]["send_pilot_limeira_values"])
        self.assertEqual(self.cfg["verification_rules"]["methods"], ["GET"])
        self.assertEqual(self.cfg["human_challenge_required_markers"], ["validar o captcha"])

    def test_no_captcha_passes_to_runtime_route_diagnostics_without_query_values_in_evidence(self):
        body = "<h1>Dados Informados pelos Municípios</h1>Buscando planilhas... por favor aguarde! Buscando dados... por favor aguarde!"
        fake = FakeClient(body)
        result = verify_public_indexed_get_contract(self.cfg, client=fake)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_INDEXED_GET_CONTRACT_GATE")
        self.assertEqual(result["surface_verified_by"], "EXACT_HEADING")
        self.assertFalse(result["captcha_component_present"])
        self.assertFalse(result["human_challenge_active"])
        self.assertEqual(result["next_gate"], "M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0")
        self.assertTrue(result["indexed_example_query_sent"])
        self.assertFalse(result["pilot_limeira_values_sent"])
        payload = json.dumps(result, ensure_ascii=False)
        for secret_like_public_value in ("292430", "2024", "num_peri=6", "admin=3"):
            self.assertNotIn(secret_like_public_value, payload)
        self.assertEqual(fake.calls, [self.cfg["public_indexed_example_url"]])

    def test_legacy_encoding_mojibake_heading_passes_only_with_both_ascii_loading_markers(self):
        body = "<h1>Dados Informados pelos Munic�pios</h1>Buscando planilhas... por favor aguarde! Buscando dados... por favor aguarde!"
        result = verify_public_indexed_get_contract(self.cfg, client=FakeClient(body))
        self.assertFalse(result["expected_heading_present"])
        self.assertEqual(result["surface_verified_by"], "ASCII_LOADING_MARKERS")
        self.assertTrue(all(result["loading_markers_present"].values()))
        self.assertTrue(result["indexed_example_query_sent"])

    def test_mojibake_heading_without_complete_ascii_contract_stops_after_response(self):
        body = "<h1>Dados Informados pelos Munic�pios</h1>Buscando dados... por favor aguarde!"
        with self.assertRaises(SiopePublicIndexedGetContractError) as ctx:
            verify_public_indexed_get_contract(self.cfg, client=FakeClient(body))
        exc = ctx.exception
        self.assertEqual(str(exc), "STOP_SIOPE_PUBLIC_INDEXED_GET_CONTRACT_UNEXPECTED_SURFACE")
        self.assertTrue(exc.network_called)
        self.assertTrue(exc.indexed_example_query_sent)
        self.assertFalse(exc.diagnostics["expected_heading_present"])
        self.assertFalse(all(exc.diagnostics["loading_markers_present"].values()))

    def test_captcha_component_without_required_message_does_not_false_stop(self):
        body = "<h1>Dados Informados pelos Municípios</h1><div class='g-recaptcha'></div>Buscando dados..."
        result = verify_public_indexed_get_contract(self.cfg, client=FakeClient(body))
        self.assertTrue(result["captcha_component_present"])
        self.assertFalse(result["human_challenge_required_message_present"])
        self.assertFalse(result["human_challenge_active"])
        self.assertEqual(result["next_gate"], "M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0")

    def test_active_human_challenge_is_observed_even_when_accented_prefix_is_mojibake(self):
        body = "<h1>Dados Informados pelos Municípios</h1>� necess�rio validar o captcha"
        result = verify_public_indexed_get_contract(self.cfg, client=FakeClient(body))
        self.assertTrue(result["captcha_component_present"])
        self.assertTrue(result["human_challenge_required_message_present"])
        self.assertTrue(result["human_challenge_active"])
        self.assertFalse(result["captcha_bypass"])
        self.assertFalse(result["form_submission"])
        self.assertEqual(result["next_gate"], "M7_SIOPE_MANUAL_ASSISTED_ACQUISITION_DESIGN_0_8_0")

    def test_result_persists_only_query_key_names(self):
        body = "<h1>Dados Informados pelos Municípios</h1>"
        result = verify_public_indexed_get_contract(self.cfg, client=FakeClient(body))
        self.assertEqual(result["final_surface"]["query_keys"], self.cfg["expected_query_keys"])
        self.assertTrue(result["final_surface"]["query_present"])
        self.assertFalse(result["query_values_persisted"])
        self.assertFalse(result["response_body_persisted"])
        self.assertFalse(result["artifact_downloaded"])
        self.assertFalse(result["head_request_performed"])

    def test_direct_dry_run_calls_no_network(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_PUBLIC_INDEXED_GET_CONTRACT_DRY_RUN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["indexed_example_query_sent"])
        self.assertFalse(result["pilot_limeira_values_sent"])
        self.assertFalse(result["collection_authorized"])

    def test_workflow_is_manual_read_only_full_qa_and_no_post_tools(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_public_indexed_get_contract", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        self.assertIn("siope-public-indexed-get-contract-evidence/result.json", text)
        lower = text.lower()
        self.assertNotIn("schedule:", lower)
        self.assertNotIn("curl ", lower)
        self.assertNotIn("wget ", lower)
        self.assertNotIn("--head", lower)


if __name__ == "__main__":
    unittest.main()
