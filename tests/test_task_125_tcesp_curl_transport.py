from copy import deepcopy
from pathlib import Path
import unittest
from robo_dados_publicos.research.task125_tcesp_curl_transport import Task125Stop,load_task125_contract,validate_task125_contract
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task125_tcesp_curl_transport.v1.json"
class TestTask125(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.c=load_task125_contract(P)
 def test_one_get_no_head_no_redirect(self):
  c=self.c["curl_contract"]; self.assertEqual(1,c["get_requests_max"]); self.assertEqual(0,c["head_requests"]); self.assertEqual(0,c["max_redirs"]); self.assertEqual(0,c["retry"])
 def test_secondary_role_and_primary_verify(self):
  self.assertEqual("SECONDARY_AGGREGATOR",self.c["semantics"]["source_role"]); self.assertTrue(self.c["semantics"]["primary_municipal_verification_required"])
 def test_no_fuzzy(self): self.assertFalse(self.c["local_processing"]["fuzzy_matching"])
 def test_retry_or_redirect_widening_fails(self):
  for k,v in (("retry",1),("max_redirs",1)):
   x=deepcopy(self.c); x["curl_contract"][k]=v
   with self.assertRaises(Task125Stop): validate_task125_contract(x)
 def test_promotion_fails(self):
  x=deepcopy(self.c); x["semantics"]["automatic_transaction_identity"]=True
  with self.assertRaises(Task125Stop): validate_task125_contract(x)
if __name__=="__main__": unittest.main()
