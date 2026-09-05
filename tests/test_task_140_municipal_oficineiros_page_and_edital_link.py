from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task140_municipal_oficineiros_page_and_edital_link.v1.json"

class TestTask140(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(P.read_text(encoding="utf-8"))

    def test_unit5_bounds(self):
        a=self.c["authorization"]
        self.assertEqual(5,a["authorization_unit_index"])
        self.assertEqual(1,a["search_invocations_max"])
        self.assertEqual(1,a["open_invocations_max"])
        self.assertEqual(1,a["click_invocations_max"])

    def test_exact_known_page_is_pinned(self):
        s=self.c["search"]
        self.assertEqual(["limeira.sp.gov.br"],s["official_domains"])
        self.assertIn("programa-de-educacao-integral",s["exact_target_url"])
        self.assertEqual(1,s["search_invocations_max"])
        self.assertEqual(0,s["retry"])

    def test_open_and_click_are_fail_closed(self):
        self.assertTrue(self.c["conditional_open"]["open_only_if_exact_target_url_returned"])
        cl=self.c["conditional_click"]
        self.assertTrue(cl["allowed_only_if_opened_primary_page_exposes_explicit_edital_credenciamento_or_processo_link"])
        self.assertEqual(1,cl["click_invocations_max"])
        self.assertEqual(0,cl["followup_opens"])
        self.assertEqual(0,cl["followup_searches"])

    def test_no_negative_or_financial_promotion(self):
        e=self.c["epistemic_semantics"]
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])
        self.assertFalse(e["automatic_supplier_linkage"])
        self.assertFalse(self.c["followup_procurement_or_financial_endpoints_authorized"])

    def test_design_has_no_remote_effects(self):
        self.assertTrue(all(v is False for v in self.c["remote_effects_in_task140_design"].values()))

if __name__=="__main__":
    unittest.main()
