from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task139_limeira_primary_procurement_search.v1.json"

class TestTask139(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=json.loads(P.read_text(encoding="utf-8"))

    def test_unit4_and_bounds(self):
        a=self.c["authorization"]
        self.assertEqual(10,a["owner_authorization_units_granted"])
        self.assertEqual(4,a["authorization_unit_index"])
        self.assertEqual(1,a["search_invocations_max"])
        self.assertEqual(1,a["open_invocations_max"])

    def test_search_is_municipal_primary_only(self):
        s=self.c["search"]
        self.assertEqual(["limeira.sp.gov.br"],s["domains"])
        self.assertEqual(1,s["search_invocations_max"])
        self.assertEqual(0,s["retry"])
        self.assertIn("credenciamento",s["query"])
        self.assertIn("tempo integral",s["query"])

    def test_open_is_fail_closed(self):
        o=self.c["conditional_open"]
        self.assertTrue(o["allowed_only_for_official_limeira_result"])
        self.assertEqual("limeira.sp.gov.br",o["allowed_domain_suffix"])
        self.assertEqual(1,o["open_most_probative_result_max"])
        self.assertTrue(o["require_policy_and_procurement_context_in_search_result"])
        self.assertEqual(0,o["followup_clicks"])
        self.assertEqual(0,o["followup_searches"])

    def test_no_weak_or_financial_promotion(self):
        self.assertFalse(self.c["matching"]["weak_context_alone_qualifies"])
        e=self.c["epistemic_semantics"]
        self.assertFalse(e["negative_exhaustive_conclusion_allowed"])
        self.assertFalse(e["global_no_match_allowed"])
        self.assertFalse(e["automatic_financial_identity"])
        self.assertFalse(e["automatic_transaction_identity"])
        self.assertFalse(e["automatic_supplier_linkage"])
        self.assertFalse(self.c["followup_procurement_or_financial_endpoints_authorized"])

    def test_design_has_no_remote_effects(self):
        self.assertTrue(all(v is False for v in self.c["remote_effects_in_task139_design"].values()))

if __name__=="__main__":
    unittest.main()
