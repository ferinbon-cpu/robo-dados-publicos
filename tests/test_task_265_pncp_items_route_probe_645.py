import unittest
from pathlib import Path
from robo_dados_publicos.research.task265_pncp_items_route_probe_645 import *
ROOT=Path(__file__).resolve().parents[1]
class T(unittest.TestCase):
 def setUp(self):self.c=load_config(ROOT/"config/task265_pncp_items_route_probe_645.v1.json");self.e=load_evidence(ROOT/"docs/evidence/TASK_265_PRELIVE_ITEMS_ROUTE_645_0.8.0.json")
 def test_list(self):
  def g(url,**k):return {"requested_url":url,"remote_get_count":1,"raw_body_persisted":False,"url_effective":url,"http_code":200,"content_type":"application/json","curl_exit_code":0,"curl_error":None,"body_bytes":20,"body_sha256":"a"*64,"json_error":None,"json_shape":"LIST","item_count":1,"selected_items":[{"numeroItem":1,"descricao":"x"}],"diagnostic_scalars":{}}
  r=execute(self.c,self.e,getter=g,offline_test_mode=True);self.assertEqual(r["outcome"],"DOCUMENTED_ITEMS_ROUTE_HTTP200_LIST");self.assertEqual(r["item_count"],1)
 def test_no_silent_migration(self):self.assertFalse(self.e["adjudication"]["silent_detail_route_migration_applied_to_items"])
 def test_allowlist(self):self.assertIn("numeroItem",ITEM_ALLOW);self.assertIn("valorTotal",ITEM_ALLOW)
if __name__=="__main__":unittest.main()
