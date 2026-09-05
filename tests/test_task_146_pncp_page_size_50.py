from copy import deepcopy
from pathlib import Path
import unittest

from robo_dados_publicos.research.task146_pncp_page_size_50 import (
    Task146Stop,
    load,
    validate_task146_contract,
)

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task146_pncp_page_size_50.v1.json"

class TestTask146(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=load(P)

    def test_corrected_exact_url_uses_50(self):
        self.assertEqual(50,self.c["source"]["page_size"])
        self.assertTrue(self.c["source"]["exact_url"].endswith("tamanhoPagina=50"))

    def test_historical_500_is_not_rewritten(self):
        h=self.c["historical_correction"]
        self.assertEqual(500,h["prior_page_size"])
        self.assertEqual(400,h["prior_user_observed_response_status"])
        self.assertFalse(h["historical_artifacts_rewritten"])

    def test_execution_is_one_open_only(self):
        w=self.c["managed_web_execution"]
        self.assertEqual(1,w["open_invocations_max"])
        self.assertEqual(0,w["search_queries"])
        self.assertEqual(0,w["clicks"])
        self.assertEqual(0,w["retry"])
        self.assertEqual(0,w["followup_opens"])

    def test_scope_widening_fails(self):
        x=deepcopy(self.c)
        x["source"]["page_size"]=500
        with self.assertRaisesRegex(Task146Stop,"TASK146_PAGE"):
            validate_task146_contract(x)

    def test_negative_and_identity_promotions_blocked(self):
        e=self.c["epistemic_semantics"]
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["pncp_no_match_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])
        self.assertFalse(e["automatic_supplier_linkage"])

if __name__=="__main__":
    unittest.main()
