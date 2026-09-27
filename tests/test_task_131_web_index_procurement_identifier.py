from copy import deepcopy
from pathlib import Path
import unittest

from robo_dados_publicos.research.task131_web_index_procurement_identifier import (
    Task131Stop,load_task131_contract,validate_task131_contract
)

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task131_web_index_procurement_identifier.v1.json"

class TestTask131(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=load_task131_contract(P,root=ROOT)

    def test_bounded_index_scope(self):
        s=self.c["search"]
        self.assertEqual(8,s["query_family_count_max"])
        self.assertEqual(16,s["search_query_count_max"])
        self.assertEqual(0,s["raw_pdf_requests"])
        self.assertEqual(0,s["pncp_requests"])
        self.assertEqual(0,s["retry"])

    def test_index_identifier_is_candidate_only(self):
        sem=self.c["evidence_semantics"]
        self.assertEqual("CANDIDATE",sem["search_index_snippet_max_status"])
        self.assertTrue(sem["may_select_future_primary_lookup"])
        self.assertFalse(sem["financial_identity"])
        self.assertFalse(sem["transaction_identity"])
        self.assertFalse(sem["weak_term_contract_join"])

    def test_pdf_retry_or_pncp_request_fails_closed(self):
        for key in ("direct_pdf_open_requests","raw_pdf_requests","pncp_requests"):
            x=deepcopy(self.c); x["search"][key]=1
            with self.assertRaises(Task131Stop):
                validate_task131_contract(x,root=ROOT)

    def test_primary_read_cannot_be_pre_authorized(self):
        x=deepcopy(self.c); x["future_primary_read_authorized"]=True
        with self.assertRaisesRegex(Task131Stop,"FUTURE_PRIMARY"):
            validate_task131_contract(x,root=ROOT)

    def test_weak_join_cannot_be_enabled(self):
        x=deepcopy(self.c); x["evidence_semantics"]["weak_term_contract_join"]=True
        with self.assertRaisesRegex(Task131Stop,"WEAK_TERM_CONTRACT_JOIN"):
            validate_task131_contract(x,root=ROOT)

if __name__=="__main__": unittest.main()
