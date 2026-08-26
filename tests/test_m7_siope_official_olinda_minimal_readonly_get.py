from __future__ import annotations

import copy
import io
import json
import unittest
from pathlib import Path

from robo_dados_publicos.sources import siope_official_olinda_exact_contract_corroboration_review as review
from robo_dados_publicos.sources import siope_official_olinda_minimal_readonly_get as minimal

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_exact_contract_corroboration_review.json"
DESIGN_CONFIG = ROOT / "config/source_expansion.siope_official_olinda_minimal_readonly_get_design.json"
WORKFLOW = ROOT / ".github/workflows/siope-official-olinda-minimal-readonly-get-gate.yml"


class FakeHeaders(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class FakeResponse:
    def __init__(self, url: str, payload, *, status: int = 200, content_type: str = "application/json"):
        self.url = url
        self.status = status
        self.headers = FakeHeaders({"Content-Type": content_type})
        if isinstance(payload, bytes):
            self.raw = payload
        else:
            self.raw = json.dumps(payload).encode("utf-8")

    def geturl(self):
        return self.url

    def getcode(self):
        return self.status

    def read(self, amount: int):
        return self.raw[:amount]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeOpener:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls = []

    def __call__(self, request, timeout: int):
        self.calls.append((request, timeout))
        return self.response


def reviewed() -> dict:
    cfg = review.load_json(REVIEW_CONFIG)
    evidence_path = ROOT / cfg["pinned_evidence_path"]
    dossier_path = ROOT / cfg["pinned_corroboration_path"]
    return review.run_review(
        cfg,
        review.load_json(evidence_path),
        evidence_path=evidence_path,
        corroboration_path=dossier_path,
    )


class MinimalReadonlyGetTests(unittest.TestCase):
    def test_pinned_review_passes_offline_and_does_not_authorize_get(self):
        result = reviewed()
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_EXACT_CONTRACT_CORROBORATION_REVIEW")
        self.assertEqual(result["corroborator_count"], 6)
        self.assertFalse(result["network_called"])
        self.assertFalse(result["resource_get_authorized"])
        self.assertFalse(result["collection_authorized"])

    def test_pinned_review_rejects_tampered_evidence(self):
        cfg = review.load_json(REVIEW_CONFIG)
        evidence_path = ROOT / cfg["pinned_evidence_path"]
        dossier_path = ROOT / cfg["pinned_corroboration_path"]
        evidence = copy.deepcopy(review.load_json(evidence_path))
        evidence["location_hash_odata_side_counts"]["odata_nearest_right_65536_count"] = 1
        with self.assertRaises(review.SiopeOfficialOlindaExactContractCorroborationReviewError):
            review.run_review(cfg, evidence, evidence_path=evidence_path, corroboration_path=dossier_path)

    def test_design_is_exact_non_limeira_and_network_free(self):
        config = minimal.load_config(DESIGN_CONFIG)
        result = minimal.validate_design(config)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_DESIGN")
        self.assertTrue(result["fixed_non_limeira_example"])
        self.assertFalse(result["network_called"])
        self.assertEqual(result["request_count"], 0)
        self.assertFalse(result["redirects_allowed"])
        self.assertFalse(result["odata_nextlink_follow_allowed"])
        self.assertNotIn("Limeira", config["exact_url"])
        self.assertNotIn("352690", config["exact_url"])

    def test_design_rejects_any_limeira_value(self):
        config = minimal.load_config(DESIGN_CONFIG)
        bad = copy.deepcopy(config)
        bad["exact_url"] += "&municipio=Limeira"
        with self.assertRaises(minimal.SiopeOfficialOlindaMinimalReadonlyGetError):
            minimal.validate_design(bad)

    def test_mocked_live_success_is_one_get_and_sanitized(self):
        config = minimal.load_config(DESIGN_CONFIG)
        payload = {
            "@odata.context": "context-value-must-not-be-persisted",
            "@odata.nextLink": "https://example.invalid/secret-next-page",
            "value": [
                {"COD_MUNI": "000001", "MUNICIPIO": "SECRET VALUE", "VALOR": 123.45},
                {"COD_MUNI": "000002", "MUNICIPIO": "OTHER", "VALOR": 9.99},
            ],
        }
        opener = FakeOpener(FakeResponse(config["exact_url"], payload))
        result = minimal.run_minimal_get(config, opener=opener)
        self.assertEqual(result["status"], minimal.PASS)
        self.assertEqual(result["request_count"], 1)
        self.assertEqual(len(opener.calls), 1)
        request, timeout = opener.calls[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url, config["exact_url"])
        self.assertGreater(timeout, 0)
        self.assertEqual(result["value_count"], 2)
        self.assertEqual(result["first_record_schema_keys"], ["COD_MUNI", "MUNICIPIO", "VALOR"])
        self.assertTrue(result["odata_nextlink_present"])
        self.assertFalse(result["odata_nextlink_followed"])
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("SECRET VALUE", serialized)
        self.assertNotIn("secret-next-page", serialized)
        self.assertNotIn("000001", serialized)
        self.assertFalse(result["record_values_persisted"])
        self.assertFalse(result["response_body_persisted"])
        self.assertFalse(result["ongoing_resource_get_authorized"])
        self.assertTrue(result["manual_single_get_authorization_consumed"])

    def test_mocked_live_rejects_redirect_or_url_drift(self):
        config = minimal.load_config(DESIGN_CONFIG)
        opener = FakeOpener(FakeResponse(config["exact_url"] + "&redirected=1", {"value": [{}]}))
        with self.assertRaises(minimal.SiopeOfficialOlindaMinimalReadonlyGetError) as ctx:
            minimal.run_minimal_get(config, opener=opener)
        self.assertIn("REDIRECT_OR_URL_DRIFT", str(ctx.exception))
        self.assertEqual(len(opener.calls), 1)

    def test_mocked_live_rejects_non_json_content_type(self):
        config = minimal.load_config(DESIGN_CONFIG)
        opener = FakeOpener(FakeResponse(config["exact_url"], {"value": [{}]}, content_type="text/html"))
        with self.assertRaises(minimal.SiopeOfficialOlindaMinimalReadonlyGetError):
            minimal.run_minimal_get(config, opener=opener)

    def test_mocked_live_rejects_invalid_json(self):
        config = minimal.load_config(DESIGN_CONFIG)
        opener = FakeOpener(FakeResponse(config["exact_url"], b"not-json"))
        with self.assertRaises(minimal.SiopeOfficialOlindaMinimalReadonlyGetError):
            minimal.run_minimal_get(config, opener=opener)

    def test_mocked_live_rejects_missing_or_empty_value(self):
        config = minimal.load_config(DESIGN_CONFIG)
        for payload in ({}, {"value": []}, {"value": ["not-object"]}):
            with self.subTest(payload=payload):
                opener = FakeOpener(FakeResponse(config["exact_url"], payload))
                with self.assertRaises(minimal.SiopeOfficialOlindaMinimalReadonlyGetError):
                    minimal.run_minimal_get(config, opener=opener)
                self.assertEqual(len(opener.calls), 1)

    def test_schema_width_fails_closed(self):
        config = minimal.load_config(DESIGN_CONFIG)
        too_wide = {f"F{i:03d}": i for i in range(129)}
        opener = FakeOpener(FakeResponse(config["exact_url"], {"value": [too_wide]}))
        with self.assertRaises(minimal.SiopeOfficialOlindaMinimalReadonlyGetError):
            minimal.run_minimal_get(config, opener=opener)

    def test_workflow_is_manual_pinned_readonly_and_qa_precedes_live(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        live_name = "Executar um único GET mínimo SIOPE Olinda"
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_official_olinda_minimal_readonly_get", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd", text)
        self.assertIn("actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97", text)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", text)
        self.assertLess(text.index("python -m unittest discover -s tests -v"), text.index(live_name))
        self.assertLess(text.index("python main.py selftest"), text.index(live_name))
        self.assertNotIn("352690", text)
        self.assertNotIn("Limeira", text)
        for forbidden in ("curl ", "wget ", "requests.post", "git push", "schedule:"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
