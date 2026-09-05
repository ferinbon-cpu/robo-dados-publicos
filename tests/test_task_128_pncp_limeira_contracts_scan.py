from copy import deepcopy
from pathlib import Path
import unittest

from robo_dados_publicos.research.task128_pncp_limeira_contracts_scan import (
    Task128Stop,
    load_task128_contract,
    scan_pncp_payload,
    validate_task128_contract,
)

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task128_pncp_limeira_contracts_page1.v1.json"


class TestTask128(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=load_task128_contract(P)

    def test_one_exact_page_one_get(self):
        self.assertEqual(1,self.c["transport"]["get_requests_max"])
        self.assertEqual(0,self.c["transport"]["retry"])
        self.assertEqual(0,self.c["transport"]["redirects_max"])
        self.assertEqual(1,self.c["source"]["pagina"])
        self.assertEqual(500,self.c["source"]["tamanho_pagina"])

    def test_secondary_role_caps_promotion(self):
        sem=self.c["epistemic_semantics"]
        self.assertEqual("SECONDARY_AGGREGATOR",sem["source_role"])
        self.assertEqual("CORROBORATED",sem["accounting_execution_max_status"])
        self.assertFalse(sem["automatic_financial_identity"])
        self.assertFalse(sem["automatic_transaction_identity"])
        self.assertTrue(sem["municipal_primary_verification_required"])

    def test_explicit_policy_marker_qualifies_candidate(self):
        payload={
            "data":[{
                "numeroControlePNCP":"45132495000140-2-000001/2026",
                "numeroContratoEmpenho":"123",
                "processo":"99/2026",
                "niFornecedor":"12345678000199",
                "nomeRazaoSocialFornecedor":"OFICINEIRO TESTE",
                "objetoContrato":"Contratação para o Programa Escola em Tempo Integral - oficinas culturais",
                "informacaoComplementar":"",
                "valorGlobal":12000.0
            }],
            "totalRegistros":1,
            "totalPaginas":1,
            "numeroPagina":1,
            "paginasRestantes":0,
            "empty":False,
        }
        r=scan_pncp_payload(payload,deepcopy(self.c))
        self.assertEqual("CANDIDATE_MATCH_WITHIN_PNCP_CNPJ_DATE_SCOPE",r["status"])
        self.assertEqual(1,r["candidate_count"])
        self.assertIn("PROGRAMA ESCOLA EM TEMPO INTEGRAL",r["candidates"][0]["strong_policy_markers"])
        self.assertFalse(r["financial_identity_promoted"])

    def test_officina_only_does_not_qualify(self):
        payload={
            "data":[{
                "objetoContrato":"Contratação de oficinas culturais",
                "informacaoComplementar":"pagamento mensal"
            }],
            "totalRegistros":1,
            "totalPaginas":1,
            "numeroPagina":1,
            "paginasRestantes":0,
            "empty":False,
        }
        r=scan_pncp_payload(payload,deepcopy(self.c))
        self.assertEqual(0,r["candidate_count"])
        self.assertEqual("NO_MATCH_WITHIN_PNCP_CNPJ_DATE_SCOPE_ONLY",r["status"])

    def test_page_one_partial_never_claims_exhaustive_no_match(self):
        payload={
            "data":[{"objetoContrato":"material escolar","informacaoComplementar":""}],
            "totalRegistros":700,
            "totalPaginas":2,
            "numeroPagina":1,
            "paginasRestantes":1,
            "empty":False,
        }
        r=scan_pncp_payload(payload,deepcopy(self.c))
        self.assertEqual("PARTIAL_PAGE1_REQUIRES_FRESH_PAGING_GATE",r["status"])
        self.assertFalse(r["coverage"]["exhaustive_within_query_scope"])
        self.assertTrue(r["coverage"]["fresh_paging_gate_required"])

    def test_empty_valid_response_is_bounded_no_match(self):
        payload={
            "data":[],
            "totalRegistros":0,
            "totalPaginas":0,
            "numeroPagina":1,
            "paginasRestantes":0,
            "empty":True,
        }
        r=scan_pncp_payload(payload,deepcopy(self.c))
        self.assertEqual("NO_MATCH_WITHIN_PNCP_CNPJ_DATE_SCOPE_ONLY",r["status"])
        self.assertTrue(r["coverage"]["exhaustive_within_query_scope"])

    def test_malformed_pagination_fails_closed(self):
        payload={"data":[],"totalRegistros":1,"totalPaginas":1,"numeroPagina":1}
        with self.assertRaisesRegex(Task128Stop,"TOTAL_LT_PAGE|ZERO_PAGES|PAYLOAD"):
            scan_pncp_payload(payload,deepcopy(self.c))

    def test_scope_widening_fails(self):
        x=deepcopy(self.c); x["transport"]["get_requests_max"]=2
        with self.assertRaisesRegex(Task128Stop,"TASK128_GET"):
            validate_task128_contract(x)
        x=deepcopy(self.c); x["future_paging_authorized"]=True
        with self.assertRaisesRegex(Task128Stop,"TASK128_FUTURE_PAGING"):
            validate_task128_contract(x)


if __name__=="__main__":
    unittest.main()
