import unittest
from pathlib import Path
from robo_dados_publicos.research.task270_pncp_history_v26_safe_645 import *
ROOT=Path(__file__).resolve().parents[1]
class T(unittest.TestCase):
 def setUp(self):
  self.c=load_config(ROOT/"config/task270_pncp_history_v26_safe_645.v1.json");self.e=load_evidence(ROOT/"docs/evidence/TASK_270_PRELIVE_HISTORY_V26_SAFE_645_0.8.0.json")
 def test_safe_projection(self):
  self.assertNotIn("usuarioNome",self.c["safe_projection"])
 def test_projection_drops_user(self):
  row={"compraAno":2026,"compraSequencial":645,"compraOrgaoCnpj":"45132495000140","tipoLogManutencaoNome":"Inclusão","usuarioNome":"Pessoa"}
  out=project(row,self.c["safe_projection"]);self.assertNotIn("usuarioNome",out);self.assertEqual(out["tipoLogManutencaoNome"],"Inclusão")
 def test_offline_execute(self):
  def g(url,**kw):return {"requested_url":url,"remote_get_count":1,"raw_body_persisted":False,"url_effective":url,"http_code":200,"content_type":"application/json","curl_exit_code":0,"curl_error":None,"body_bytes":10,"body_sha256":"a"*64,"json_error":None,"json_shape":"LIST","event_count":1,"event_keys":["compraAno","tipoLogManutencaoNome","usuarioNome"],"safe_events":[{"compraAno":2026,"tipoLogManutencaoNome":"Inclusão"}],"diagnostic_scalars":{}}
  r=execute(self.c,self.e,getter=g,offline_test_mode=True);self.assertEqual(r["event_count"],1);self.assertNotIn("usuarioNome",r["safe_events"][0])
 def test_no_auth(self):
  r=execute(self.c,self.e,authorization=None,expected_implementation_sha="0"*40);self.assertEqual(r["source_get_count"],0)
if __name__=="__main__":unittest.main()
