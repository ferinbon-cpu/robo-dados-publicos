import unittest
from robo_dados_publicos.research.task279_paired_pncp_health_645 import *
class T(unittest.TestCase):
 def test_classify_5xx(self):
  h={"http_code":200,"json_shape":"LIST"};t={"http_code":503,"json_shape":"OTHER","page_contract_valid":False}
  self.assertEqual(classify(h,t),"PNCP_ITEMS_HEALTHY_LINKED_CONTRACT_ROUTE_UNAVAILABLE")
 def test_classify_404(self):
  h={"http_code":200,"json_shape":"LIST"};t={"http_code":404,"json_shape":"OBJECT","page_contract_valid":False}
  self.assertEqual(classify(h,t),"PNCP_ITEMS_HEALTHY_LINKED_CONTRACT_HTTP404_CONTEXT")
 def test_no_auth(self):
  c=load_config();e=load_evidence();self.assertEqual(execute(c,e,authorization=None,expected_implementation_sha="0"*40)["source_get_count"],0)
if __name__=="__main__":unittest.main()
