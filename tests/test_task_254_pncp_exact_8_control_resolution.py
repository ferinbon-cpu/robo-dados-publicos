from __future__ import annotations

import copy
import unittest
from pathlib import Path

from robo_dados_publicos.research.task254_pncp_exact_8_control_resolution import (
    EXPECTED_REPOSITORY,
    EXPECTED_SOURCE,
    build_url,
    execute_exact_resolution,
    load_config,
    parse_control,
    validate_live_authorization,
    validate_task253_inputs,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/task254_pncp_exact_8_control_resolution.v1.json"
IMPL = "4c3013eba2a091c294fcdea44705077e95c7302d"


class FakeSource:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def get(self, url, *, timeout, max_bytes):
        self.calls.append((url, timeout, max_bytes))
        return self.responses[url]


def detail_payload(target):
    return {
        "numeroControlePNCP": target["control"],
        "anoCompra": target["ano"],
        "sequencialCompra": target["sequencial"],
        "numeroCompra": f"{target['sequencial']}/2026",
        "processo": "PROCESSO-TESTE",
        "objetoCompra": "OBJETO SANITIZADO DE TESTE",
        "valorTotalEstimado": 123.45,
        "dataPublicacaoPncp": "2026-09-01T00:00:00",
        "modalidadeId": 6,
        "modalidadeNome": "Pregão eletrônico",
        "situacaoCompraId": 1,
        "situacaoCompraNome": "Divulgada no PNCP",
        "orgaoEntidade": {
            "cnpj": target["cnpj"],
            "razaoSocial": "MUNICIPIO DE LIMEIRA",
            "poderId": "E",
            "esferaId": "M",
        },
        "unidadeOrgao": {
            "codigoUnidade": "1",
            "nomeUnidade": "PREFEITURA",
            "municipioNome": "Limeira",
            "ufSigla": "SP",
        },
    }


def success_meta(url, n=128):
    return {
        "url": url,
        "requested_url": url,
        "http_status": 200,
        "content_type": "application/json",
        "bytes_received": n,
        "sha256": "a" * 64,
        "transport_error": None,
        "remote_get_count": 1,
    }


def live_auth(cfg, impl=IMPL):
    return {
        "task": "TASK_254_LIVE_AUTHORIZATION",
        "repository": EXPECTED_REPOSITORY,
        "implementation_branch": "main",
        "runtime_branch": cfg["runtime"]["branch"],
        "implementation_sha": impl,
        "source": EXPECTED_SOURCE,
        "operation": "EXACT_8_TASK253_PNCP_PURCHASE_CONTROL_DETAIL_RESOLUTION",
        "controls": [t["control"] for t in cfg["targets"]],
        "target_count": 8,
        "max_detail_get_count": 8,
        "max_total_remote_get_count": 8,
        "max_gets_per_target": 1,
        "attempt_count": 1,
        "owner_authorized": True,
        "source_network_authorized": True,
        "pncp_detail_gets_authorized": True,
        "rediscovery_authorized": False,
        "publication_search_authorized": False,
        "other_pncp_routes_authorized": False,
        "automatic_retry": False,
        "redirects": False,
        "alternate_url_discovery": False,
        "prior_authorization_reused": False,
        "drive_write_authorized": False,
        "serving_authorized": False,
        "publication_authorized": False,
        "promotion_authorized": False,
        "recurrence_authorized": False,
        "schedule_authorized": False,
        "consumed": False,
    }


class Task254CarrierTest(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(CONFIG)
        validate_task253_inputs(self.cfg)

    def test_exact_controls_map_to_exact_detail_urls(self):
        expected_sequences = [646, 639, 645, 648, 655, 653, 654, 69]
        self.assertEqual([t["sequencial"] for t in self.cfg["targets"]], expected_sequences)
        for target in self.cfg["targets"]:
            parsed = parse_control(target["control"])
            self.assertEqual(parsed["sequencial"], target["sequencial"])
            self.assertEqual(
                build_url(self.cfg, target),
                f"https://pncp.gov.br/api/pncp/v1/orgaos/45132495000140/compras/2026/{target['sequencial']}",
            )

    def test_missing_live_authorization_stops(self):
        result = validate_live_authorization(None, expected_implementation_sha=IMPL, config=self.cfg)
        self.assertEqual(result["status"], "STOP_TASK254_LIVE_NOT_AUTHORIZED")

    def test_exact_live_authorization_passes(self):
        result = validate_live_authorization(live_auth(self.cfg), expected_implementation_sha=IMPL, config=self.cfg)
        self.assertEqual(result, {"status": "PASS_TASK254_LIVE_AUTHORIZATION"})

    def test_authorization_control_drift_stops(self):
        auth = live_auth(self.cfg)
        auth["controls"] = auth["controls"][:-1]
        result = validate_live_authorization(auth, expected_implementation_sha=IMPL, config=self.cfg)
        self.assertEqual(result["status"], "STOP_TASK254_AUTHORIZATION_CONTRACT_MISMATCH")

    def test_all_eight_exact_details_resolve(self):
        responses = {}
        for target in self.cfg["targets"]:
            url = build_url(self.cfg, target)
            responses[url] = (success_meta(url), detail_payload(target))
        source = FakeSource(responses)
        result = execute_exact_resolution(
            self.cfg,
            source=source,
            authorization=None,
            expected_implementation_sha=IMPL,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "PASS_BOUNDED_EXACT_8_PNCP_DETAIL_OBSERVATION")
        self.assertTrue(result["complete_observation_scope"])
        self.assertEqual(result["source_get_count"], 8)
        self.assertEqual(result["resolved_count"], 8)
        self.assertEqual(result["unresolved_count"], 0)
        self.assertEqual(len(source.calls), 8)
        self.assertFalse(result["raw_payload_persisted"])
        self.assertFalse(result["absence_inference_allowed"])

    def test_503_is_unresolved_not_no_data_or_absence(self):
        responses = {}
        for idx, target in enumerate(self.cfg["targets"]):
            url = build_url(self.cfg, target)
            if idx == 0:
                responses[url] = ({
                    "url": url,
                    "requested_url": url,
                    "http_status": 503,
                    "content_type": None,
                    "bytes_received": 0,
                    "sha256": None,
                    "transport_error": "HTTP_ERROR_503",
                    "remote_get_count": 1,
                }, None)
            else:
                responses[url] = (success_meta(url), detail_payload(target))
        result = execute_exact_resolution(
            self.cfg,
            source=FakeSource(responses),
            authorization=None,
            expected_implementation_sha=IMPL,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "PASS_BOUNDED_EXACT_8_PNCP_DETAIL_OBSERVATION")
        self.assertEqual(result["resolved_count"], 7)
        self.assertEqual(result["unresolved_count"], 1)
        self.assertEqual(result["observations"][0]["status"], "UNRESOLVED_SOURCE_OBSERVATION")
        self.assertFalse(result["global_pncp_absence_conclusion"])
        self.assertFalse(result["observations"][0]["absence_inference_allowed"])

    def test_http_200_control_identity_drift_stops(self):
        responses = {}
        for target in self.cfg["targets"]:
            url = build_url(self.cfg, target)
            payload = detail_payload(target)
            responses[url] = (success_meta(url), payload)
        first = self.cfg["targets"][0]
        bad = detail_payload(first)
        bad["numeroControlePNCP"] = "45132495000140-1-999999/2026"
        responses[build_url(self.cfg, first)] = (success_meta(build_url(self.cfg, first)), bad)
        result = execute_exact_resolution(
            self.cfg,
            source=FakeSource(responses),
            authorization=None,
            expected_implementation_sha=IMPL,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "STOP_TASK254_FAIL_CLOSED")
        self.assertEqual(result["stop_code"], "TASK254_DETAIL_CONTROL_IDENTITY_MISMATCH")

    def test_http_200_non_json_stops(self):
        responses = {}
        for target in self.cfg["targets"]:
            url = build_url(self.cfg, target)
            responses[url] = (success_meta(url), detail_payload(target))
        first = self.cfg["targets"][0]
        url = build_url(self.cfg, first)
        meta = success_meta(url)
        meta["content_type"] = "text/html"
        responses[url] = (meta, detail_payload(first))
        result = execute_exact_resolution(
            self.cfg,
            source=FakeSource(responses),
            authorization=None,
            expected_implementation_sha=IMPL,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "STOP_TASK254_FAIL_CLOSED")
        self.assertEqual(result["stop_code"], "TASK254_HTTP_200_CONTENT_TYPE")

    def test_http_200_cnpj_identity_drift_stops(self):
        responses = {}
        for target in self.cfg["targets"]:
            url = build_url(self.cfg, target)
            responses[url] = (success_meta(url), detail_payload(target))
        first = self.cfg["targets"][0]
        bad = detail_payload(first)
        bad["orgaoEntidade"]["cnpj"] = "00000000000000"
        responses[build_url(self.cfg, first)] = (success_meta(build_url(self.cfg, first)), bad)
        result = execute_exact_resolution(
            self.cfg,
            source=FakeSource(responses),
            authorization=None,
            expected_implementation_sha=IMPL,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "STOP_TASK254_FAIL_CLOSED")
        self.assertEqual(result["stop_code"], "TASK254_DETAIL_CNPJ_IDENTITY_MISMATCH")

    def test_redirect_status_stops_without_following(self):
        responses = {}
        for target in self.cfg["targets"]:
            url = build_url(self.cfg, target)
            responses[url] = (success_meta(url), detail_payload(target))
        first = self.cfg["targets"][0]
        url = build_url(self.cfg, first)
        responses[url] = ({
            "url": url,
            "requested_url": url,
            "http_status": 302,
            "content_type": None,
            "bytes_received": 0,
            "sha256": None,
            "transport_error": "HTTP_ERROR_302",
            "remote_get_count": 1,
        }, None)
        result = execute_exact_resolution(
            self.cfg,
            source=FakeSource(responses),
            authorization=None,
            expected_implementation_sha=IMPL,
            offline_test_mode=True,
        )
        self.assertEqual(result["status"], "STOP_TASK254_FAIL_CLOSED")
        self.assertEqual(result["stop_code"], "TASK254_REDIRECT_STATUS_OBSERVED")

    def test_main_carrier_has_no_live_effect_by_default(self):
        self.assertFalse(any(self.cfg["pre_authorization_remote_effects"].values()))
        self.assertFalse(self.cfg["authorization"]["source_network_authorized_by_default"])
        self.assertFalse(self.cfg["authorization"]["pncp_detail_gets_authorized_by_default"])
        self.assertFalse(self.cfg["persistence"]["drive_write"])
        self.assertFalse(self.cfg["persistence"]["publication"])


if __name__ == "__main__":
    unittest.main()
