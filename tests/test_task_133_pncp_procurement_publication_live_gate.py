from copy import deepcopy
from pathlib import Path
import unittest

from robo_dados_publicos.research.task133_pncp_procurement_publication_live_gate import (
    Task133Stop,
    interpret_future_payload,
    load_task133_contract,
    validate_task133_contract,
)

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "config/task133_pncp_procurement_publication_live_gate.v1.json"


class TestTask133(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = load_task133_contract(P)

    def test_design_is_offline_and_unautorized(self):
        self.assertEqual("T0_OFFLINE_LIVE_GATE_DESIGN_ONLY", self.c["mode"])
        self.assertFalse(self.c["authorization"]["authorized_now"])
        self.assertTrue(self.c["authorization"]["must_be_issued_after_gate_merge"])
        self.assertTrue(all(v is False for v in self.c["remote_effects_in_task133_design"].values()))

    def test_exact_one_get_scope_is_pinned(self):
        s = self.c["source"]
        t = self.c["transport"]
        self.assertEqual("45132495000140", s["cnpj_orgao"])
        self.assertEqual(12, s["codigo_modalidade_contratacao"])
        self.assertEqual(1, s["pagina"])
        self.assertEqual(500, s["tamanho_pagina"])
        self.assertEqual(1, t["get_requests_max"])
        self.assertEqual(0, t["redirects_max"])
        self.assertEqual(0, t["retry"])
        self.assertIn("/contratacoes/publicacao?", s["exact_url"])

    def test_live_enablement_inside_design_fails_closed(self):
        x = deepcopy(self.c)
        x["authorization"]["authorized_now"] = True
        with self.assertRaisesRegex(Task133Stop, "AUTH_MUST_BE_FALSE"):
            validate_task133_contract(x)

    def test_weak_context_alone_does_not_qualify(self):
        payload = {
            "data": [{
                "numeroControlePNCP": "weak",
                "objetoCompra": "Credenciamento de oficineiros para oficinas extracurriculares",
                "informacaoComplementar": "",
            }],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "numeroPagina": 1,
        }
        result = interpret_future_payload(payload, self.c)
        self.assertEqual("NO_MATCH_WITHIN_PNCP_CNPJ_MODALITY_DATE_SCOPE_ONLY", result["status"])
        self.assertEqual(0, result["candidate_count"])

    def test_strong_marker_yields_candidate_without_identity_promotion(self):
        payload = {
            "data": [{
                "numeroControlePNCP": "45132495000140-1-000001/2026",
                "anoCompra": 2026,
                "sequencialCompra": 1,
                "numeroCompra": "001/2026",
                "processo": "12345/2025",
                "objetoCompra": "Credenciamento para oficinas no Programa de Educação Integral",
                "informacaoComplementar": "Escola em Tempo Integral",
            }],
            "totalRegistros": 1,
            "totalPaginas": 1,
            "numeroPagina": 1,
        }
        result = interpret_future_payload(payload, self.c)
        self.assertEqual("CANDIDATE_ADMIN_IDENTIFIER_REQUIRES_PRIMARY_VERIFICATION", result["status"])
        self.assertEqual(1, result["candidate_count"])
        self.assertFalse(result["financial_identity_promoted"])
        self.assertFalse(result["transaction_identity_promoted"])
        self.assertTrue(result["primary_municipal_verification_required"])

    def test_partial_page_without_candidate_cannot_be_no_match(self):
        payload = {
            "data": [{"objetoCompra": "Outra contratação"}],
            "totalRegistros": 501,
            "totalPaginas": 2,
            "numeroPagina": 1,
        }
        result = interpret_future_payload(payload, self.c)
        self.assertEqual("PARTIAL_PAGE1_NO_CONCLUSION_FRESH_GATE_REQUIRED", result["status"])


if __name__ == "__main__":
    unittest.main()
