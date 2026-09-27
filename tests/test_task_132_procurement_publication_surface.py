from copy import deepcopy
from pathlib import Path
import unittest
from robo_dados_publicos.research.task132_procurement_publication_surface import (
    Task132Stop,load_task132_contract,validate_task132_contract
)
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task132_procurement_publication_surface.v1.json"

class TestTask132(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.c=load_task132_contract(P)

    def test_selects_pncp_procurement_not_contract_surface(self):
        s=self.c["selected_surface"]
        self.assertEqual("PNCP_PUBLIC_CONTRATACOES_BY_PUBLICATION",s["name"])
        self.assertIn("/contratacoes/publicacao",s["endpoint_template"])
        self.assertEqual(12,self.c["target"]["procurement_mode_code"])

    def test_initial_probe_is_exact_one_get_but_not_yet_authorized(self):
        p=self.c["initial_live_probe"]
        self.assertFalse(p["authorized_now"])
        self.assertEqual(1,p["get_requests_max"])
        self.assertEqual(0,p["retry"])
        self.assertEqual(500,p["tamanho_pagina"])
        self.assertIn("codigoModalidadeContratacao=12",p["exact_url"])

    def test_candidate_needs_strong_policy_marker(self):
        m=self.c["candidate_matching"]
        self.assertTrue(m["strong_policy_marker_required"])
        self.assertFalse(m["weak_context_alone_qualifies"])

    def test_followups_are_separately_gated(self):
        self.assertTrue(self.c["followup_if_candidate"]["each_followup_requires_separate_gate"])

    def test_no_auto_identity(self):
        s=self.c["epistemic_semantics"]
        self.assertFalse(s["automatic_financial_identity"])
        self.assertFalse(s["automatic_transaction_identity"])
        self.assertFalse(s["automatic_supplier_linkage"])

    def test_live_enablement_fails_closed(self):
        x=deepcopy(self.c); x["initial_live_probe"]["authorized_now"]=True
        with self.assertRaisesRegex(Task132Stop,"LIVE_NOT_AUTHORIZED"):
            validate_task132_contract(x)

    def test_scope_widening_fails_closed(self):
        x=deepcopy(self.c); x["initial_live_probe"]["cnpj"]="other"
        with self.assertRaisesRegex(Task132Stop,"PROBE_CNPJ"):
            validate_task132_contract(x)

if __name__=="__main__": unittest.main()
