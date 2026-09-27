from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"config/task144_transparency_eiti_procurement_search.v1.json"
S=ROOT/"docs/evidence/TASK_143_INDEXED_CHAMAMENTO_ROUTE_SEARCH_STOP_0.8.0.json"
class TestTask144(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=json.loads(C.read_text(encoding="utf-8")); cls.s=json.loads(S.read_text(encoding="utf-8"))
 def test_upstream_stop(self):
  self.assertEqual("STOP_INDEXED_CHAMAMENTO_NO_QUALIFIED_ROUTE_RESULT",self.s["result"]); self.assertEqual(1,self.s["search_invocations"]); self.assertEqual(0,self.s["open_invocations"]); self.assertFalse(self.s["negative_exhaustive_conclusion_created"])
 def test_unit9_bounds(self):
  a=self.c["authorization"]; self.assertEqual(9,a["authorization_unit_index"]); self.assertEqual(1,a["search_invocations_max"]); self.assertEqual(1,a["open_invocations_max"])
 def test_transparency_only(self):
  s=self.c["search"]; self.assertEqual("transparencia.limeira.sp.gov.br",s["official_domain"]); self.assertEqual(1,s["search_invocations_max"]); self.assertEqual(0,s["retry"])
 def test_fail_closed(self):
  o=self.c["conditional_open"]; self.assertTrue(o["official_transparency_result_only"]); self.assertEqual(1,o["open_invocations_max"]); self.assertEqual(0,o["followup_clicks"]); self.assertEqual(0,o["followup_searches"])
  e=self.c["epistemic_semantics"]; self.assertFalse(e["negative_exhaustive_conclusion_allowed"]); self.assertFalse(e["automatic_financial_identity"]); self.assertFalse(e["automatic_transaction_identity"]); self.assertFalse(e["automatic_supplier_linkage"])
if __name__=="__main__": unittest.main()
