import json
import unittest
from pathlib import Path

from robo_dados_publicos.research.task167_pncp_stable_id_direct_json import (
    Task167Stop,
    build_url,
    load_config,
    sanitize_payload,
    validate_detail_identity,
)


def config():
    return load_config(Path("config/task167_pncp_stable_id_direct_json_traversal.v1.json"))


class TestTask167PncpStableIdDirectJson(unittest.TestCase):
    def test_config_and_urls_are_pinned(self):
        c = config()
        self.assertEqual(len(c["targets"]), 2)
        self.assertEqual(len(c["routes"]), 5)
        url = build_url(c, c["targets"][0], c["routes"][0])
        self.assertEqual(
            url,
            "https://pncp.gov.br/api/pncp/v1/orgaos/45132495000140/compras/2026/368",
        )

    def test_detail_identity_passes_exact_target(self):
        c = config()
        target = c["targets"][0]
        payload = {
            "anoCompra": 2026,
            "sequencialCompra": 368,
            "numeroControlePNCP": "45132495000140-1-000368/2026",
            "processo": "I00055",
            "orgaoEntidade": {"cnpj": "45132495000140"},
        }
        validate_detail_identity(payload, target, c["source"]["cnpj"])

    def test_detail_identity_fails_closed_on_weak_join(self):
        c = config()
        target = c["targets"][0]
        payload = {
            "anoCompra": 2026,
            "sequencialCompra": 368,
            "numeroControlePNCP": "45132495000140-1-000999/2026",
            "processo": "I00055",
            "orgaoEntidade": {"cnpj": "45132495000140"},
        }
        with self.assertRaises(Task167Stop):
            validate_detail_identity(payload, target, c["source"]["cnpj"])

    def test_budget_source_sanitizer_extracts_candidate_not_proven(self):
        payload = [{
            "codigoFonte": "05",
            "descricaoFonte": "Transferencias",
            "dotacao": "10.00.00.12.361.2001",
            "irrelevantRawBlob": {"secretish": "not copied"},
        }]
        sanitized = sanitize_payload("BUDGET_SOURCES", payload)
        self.assertEqual(sanitized["count"], 1)
        signals = sanitized["budget_accounting_signals"]
        self.assertTrue(any(x["path"].endswith("codigoFonte") for x in signals))
        self.assertTrue(all(x["status"] == "CANDIDATE_NOT_PROVEN" for x in signals))
        self.assertNotIn("secretish", json.dumps(sanitized))

    def test_linked_contracts_do_not_create_payment_claim(self):
        payload = [{
            "numeroControlePNCP": "x",
            "numeroContratoEmpenho": "170/2024",
            "valorInicial": 100,
            "fornecedor": {"cnpj": "00000000000000"},
        }]
        sanitized = sanitize_payload("LINKED_CONTRACTS", payload)
        self.assertEqual(sanitized["count"], 1)
        self.assertEqual(
            sanitized["selected"][0]["numeroContratoEmpenho"],
            "170/2024",
        )
        self.assertNotIn("pagamento", json.dumps(sanitized).lower())


if __name__ == "__main__":
    unittest.main()
