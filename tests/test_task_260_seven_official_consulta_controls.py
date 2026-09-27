import unittest
from pathlib import Path
from robo_dados_publicos.research.task260_seven_official_consulta_controls import *
ROOT=Path(__file__).resolve().parents[1]
class F:
 def get(self,url,**k):
  seq=int(url.rsplit("/",1)[-1]);ctl=f"45132495000140-1-{seq:06d}/2026"
  return {"http_code":200,"curl_exit_code":0,"curl_error":None,"body_bytes":1,"body_sha256":"a"*64,"json_error":None,"selected":{"numeroControlePNCP":ctl},"raw_body_persisted":False}
class T(unittest.TestCase):
 def test_all(self):
  c=load_config(ROOT/"config/task260_seven_official_consulta_controls.v1.json");e=load_evidence(ROOT/"docs/evidence/TASK_260_TASK259_FIRST_CONTROL_CANONICAL_0.8.0.json")
  r=execute(c,e,transport=F(),authorization=None,expected_implementation_sha="0"*40,offline_test_mode=True);self.assertEqual(r["resolved_count"],7);self.assertEqual(r["source_get_count"],7)
if __name__=="__main__":unittest.main()
