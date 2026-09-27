from __future__ import annotations

import json
from pathlib import Path
import unittest

from robo_dados_publicos.sources.siope_artifact_metadata_route_verification import (
    MetadataResponse,
    SiopeArtifactMetadataVerificationError,
    load_artifact_metadata_verification_config,
    summarize_metadata_payload,
    verify_artifact_metadata_route,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "source_expansion.siope_artifact_metadata_route_verification_gate.json"
WORKFLOW = ROOT / ".github" / "workflows" / "siope-artifact-metadata-route-verification-gate.yml"
SCRIPT = ROOT / "scripts" / "github_siope_artifact_metadata_route_verification_gate.py"


class FakeClient:
    def __init__(self, payload, *, content_type="application/json", byte_count=512):
        self.payload = payload
        self.content_type = content_type
        self.byte_count = byte_count
        self.calls = []

    def get_json(self, url, *, max_bytes, allowed_content_types):
        self.calls.append((url, max_bytes, tuple(allowed_content_types)))
        return MetadataResponse(url, 200, self.content_type, self.byte_count, self.payload)


class TestM7SiopeArtifactMetadataRouteVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_artifact_metadata_verification_config(CONFIG)

    def test_config_is_exact_and_keeps_collection_closed(self):
        c = self.config
        self.assertEqual(
            c["metadata_url"],
            "https://www.fnde.gov.br/plataforma-antonieta-de-barros-api/products/data-products/20/artifact-metadata",
        )
        self.assertEqual(c["network"], "ONE_READ_ONLY_GET_EXACT_METADATA_ROUTE")
        self.assertEqual(c["allowed_method"], "GET")
        self.assertEqual(c["allowed_hosts"], ["www.fnde.gov.br"])
        self.assertEqual(c["artifact_download"], "PROHIBITED")
        self.assertEqual(c["download_candidate_request"], "PROHIBITED")
        self.assertEqual(c["source_collection"], "PROHIBITED")
        self.assertEqual(c["source_processing"], "PROHIBITED")
        self.assertEqual(c["recurrence"], "PROHIBITED")
        self.assertEqual(c["schedule"], "DISABLED")

    def test_success_sanitizes_signed_url_and_never_calls_it(self):
        payload = {
            "productId": 20,
            "artifact": {
                "path": "exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz",
                "downloadUrl": "https://www.fnde.gov.br/files/SIOPE_DADOS_GERAIS_SIOPE.txt.gz?token=SECRET&expires=999",
            },
        }
        client = FakeClient(payload)
        result = verify_artifact_metadata_route(self.config, client=client)
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0][0], self.config["metadata_url"])
        self.assertEqual(result["metadata_route_status"], "VERIFIED_200_JSON_EXACT_OBSERVED_ROUTE")
        self.assertTrue(result["artifact_path_observed"])
        self.assertTrue(result["product_id_observed"])
        self.assertFalse(result["download_candidate_requested"])
        self.assertFalse(result["artifact_downloaded"])
        dumped = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("SECRET", dumped)
        urls = [item for item in result["observed_candidates"] if item["value_kind"] == "ABSOLUTE_URL"]
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0]["query_keys"], ["expires", "token"])
        self.assertTrue(urls[0]["query_present"])
        self.assertNotIn("?", urls[0]["route_without_query"])

    def test_cross_origin_url_is_observed_but_not_authorized(self):
        payload = {
            "downloadUrl": "https://cdn.example.invalid/file.txt.gz?signature=SECRET",
            "artifactPath": "exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz",
        }
        result = verify_artifact_metadata_route(self.config, client=FakeClient(payload))
        item = next(x for x in result["observed_candidates"] if x["value_kind"] == "ABSOLUTE_URL")
        self.assertEqual(item["host"], "cdn.example.invalid")
        self.assertFalse(item["allowed_host"])
        self.assertFalse(result["download_candidate_requested"])
        self.assertNotIn("SECRET", json.dumps(result))

    def test_general_string_values_are_not_persisted(self):
        payload = {
            "name": "Highly sensitive-looking but irrelevant string",
            "description": "Do not persist this free text",
            "artifact": {"status": "ready"},
        }
        summary = summarize_metadata_payload(payload, self.config)
        dumped = json.dumps(summary)
        self.assertNotIn("Highly sensitive-looking", dumped)
        self.assertNotIn("Do not persist", dumped)
        self.assertNotIn('"ready"', dumped)

    def test_summary_depth_or_node_overflow_fails_closed(self):
        payload = current = {}
        for i in range(12):
            nxt = {}
            current[f"level{i}"] = nxt
            current = nxt
        with self.assertRaisesRegex(SiopeArtifactMetadataVerificationError, "SUMMARY_TRUNCATED"):
            summarize_metadata_payload(payload, self.config)

    def test_no_observed_download_candidate_routes_to_schema_review(self):
        payload = {"productId": 20, "artifact": {"size": 123, "state": "ready"}}
        result = verify_artifact_metadata_route(self.config, client=FakeClient(payload))
        self.assertEqual(result["observed_candidate_count"], 0)
        self.assertEqual(result["next_gate"], "M7_SIOPE_ARTIFACT_METADATA_SCHEMA_REVIEW_0_8_0")

    def test_workflow_is_manual_read_only_and_runs_full_qa_before_live(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_artifact_metadata_route_verification", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("schedule:", text)
        live = text.index("Verificação ao vivo do endpoint exato de metadata")
        for marker in (
            "Preflight offline da candidata",
            "Gate M7 de desenho da expansão",
            "Dry-run da verificação de metadata sem rede",
            "Compilar",
            "Testes unitários",
            "Regressão histórica",
        ):
            self.assertLess(text.index(marker), live)

    def test_workflow_uploads_only_sanitized_result_and_has_no_download_tools(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("siope-artifact-metadata-route-verification-evidence/result.json", text)
        lower = text.lower()
        for forbidden in ("curl ", "wget ", "gcloud ", "drive oauth", "browser.setdownloadbehavior", "head "):
            self.assertNotIn(forbidden, lower)

    def test_gate_script_dry_run_contract_has_no_network(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("PASS_M7_SIOPE_ARTIFACT_METADATA_ROUTE_VERIFICATION_DRY_RUN", text)
        self.assertIn('"network_called": False', text)
        self.assertIn('"download_candidate_requested": False', text)
        self.assertIn('"collection_authorized": False', text)


if __name__ == "__main__":
    unittest.main()
