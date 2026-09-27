import unittest
from pathlib import Path
from robo_dados_publicos.research.task272_seven_history_v26_safe import *
ROOT=Path(__file__).resolve().parents[1]
class T(unittest.TestCase):
 def setUp(self): self.c=load_config(ROOT/"config/task272_seven_history_v26_safe.v1.json");self.e=load_evidence(ROOT/"docs/evidence/TASK_272_PRELIVE_SEVEN_HISTORY_V26_SAFE_0.8.0.json")
 def test_fixed_targets(self): self.assertEqual([x["sequencial"] for x in self.c["targets"]],[646,639,648,655,653,654,69])
 def test_privacy(self): self.assertNotIn("usuarioNome",self.c["safe_projection"])
 def test_offline_all_resolved(self):
  def g(t,c): return {"control":t["control"],"sequencial":t["sequencial"],"requested_url":t["url"],"http_code":200,"content_type":"application/json","url_effective":t["url"],"curl_exit_code":0,"curl_error":None,"body_bytes":1,"body_sha256":"a"*64,"json_error":None,"json_shape":"LIST","event_count":1,"event_keys":["compraSequencial"],"identity_valid":True,"safe_events":[{"compraSequencial":t["sequencial"]}],"safe_projection_sha256":"b"*64,"resolved":True,"outcome":"HISTORY_V26_SAFE_HTTP200_LIST","remote_get_count":1,"raw_body_persisted":False}
  r=execute(self.c,self.e,getter=g,offline_test_mode=True);self.assertEqual(r["resolved_count"],7);self.assertEqual(r["source_get_count"],7)
 def test_no_auth(self): self.assertEqual(execute(self.c,self.e,authorization=None,expected_implementation_sha="0"*40)["source_get_count"],0)
if __name__=="__main__":unittest.main()
