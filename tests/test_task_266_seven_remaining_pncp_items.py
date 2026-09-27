import unittest
from pathlib import Path
from robo_dados_publicos.research.task266_seven_remaining_pncp_items import *
ROOT=Path(__file__).resolve().parents[1]
class T(unittest.TestCase):
 def test_all(self):
  c=load_config(ROOT/"config/task266_seven_remaining_pncp_items.v1.json");e=load_evidence(ROOT/"docs/evidence/TASK_266_TASK265_ITEMS_ROUTE_CANONICAL_0.8.0.json")
  def g(url,**k):return {"http_code":200,"json_shape":"LIST","curl_exit_code":0,"curl_error":None,"content_type":"application/json","body_bytes":10,"body_sha256":"a"*64,"json_error":None,"item_count":1,"selected_items":[{"numeroItem":1}],"diagnostic_scalars":{}}
  r=execute(c,e,getter=g,offline_test_mode=True);self.assertEqual(r["resolved_count"],7);self.assertEqual(r["source_get_count"],7)
if __name__=="__main__":unittest.main()
