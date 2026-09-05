from copy import deepcopy
from pathlib import Path
import unittest
from robo_dados_publicos.research.task127_jom_eiti_accounting_field_scan import Task127Stop,load_task127_contract,validate_task127_contract
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task127_jom_eiti_accounting_field_scan.v1.json"
class TestTask127(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.c=load_task127_contract(P)
 def test_one_exact_get(self):
  t=self.c["transport"]; self.assertEqual(1,t["get_requests_max"]); self.assertEqual(0,t["redirects_max"]); self.assertEqual(0,t["retry"]); self.assertTrue(t["exact_url_only"])
 def test_no_ocr(self): self.assertFalse(self.c["processing"]["ocr"])
 def test_accounting_terms_complete(self):
  self.assertEqual(10,len(self.c["processing"]["normalized_terms"]))
 def test_weak_promotion_guards(self):
  s=self.c["semantics"]; self.assertFalse(s["r30_hour_is_execution_event"]); self.assertFalse(s["monthly_payment_wording_is_execution_event"]); self.assertFalse(s["automatic_promotion"])
 def test_scope_widening_fails(self):
  x=deepcopy(self.c); x["transport"]["get_requests_max"]=2
  with self.assertRaisesRegex(Task127Stop,"TASK127_GET"): validate_task127_contract(x)
  x=deepcopy(self.c); x["processing"]["ocr"]=True
  with self.assertRaisesRegex(Task127Stop,"TASK127_OCR"): validate_task127_contract(x)
if __name__=="__main__": unittest.main()
