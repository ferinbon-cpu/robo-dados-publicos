import unittest
from robo_dados_publicos.research.task281_pncp_items645_recovery import *
class T(unittest.TestCase):
 def test_classify(self):
  self.assertEqual(classify({"http_code":200,"json_shape":"LIST"}),"PNCP_ITEMS_645_RECOVERED_HTTP200_LIST")
  self.assertEqual(classify({"http_code":503,"json_shape":"OTHER"}),"PNCP_ITEMS_645_STILL_UNAVAILABLE")
 def test_no_auth(self):
  c=load_config();e=load_evidence();self.assertEqual(execute(c,e,authorization=None,expected_implementation_sha="0"*40)["source_get_count"],0)
if __name__=="__main__":unittest.main()
