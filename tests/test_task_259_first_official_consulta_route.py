import unittest
from pathlib import Path
from robo_dados_publicos.research.task259_first_official_consulta_route import *
ROOT=Path(__file__).resolve().parents[1]
class F:
 def __init__(self,m):self.m=m
 def get(self,*a,**k):return dict(self.m)
class T(unittest.TestCase):
 def setUp(self):self.c=load_config(ROOT/"config/task259_first_official_consulta_route.v1.json");self.e=load_evidence(ROOT/"docs/evidence/TASK_259_PNCP_ROUTE_MIGRATION_CANONICAL_0.8.0.json")
 def test_exact(self):
  t=self.c["target"];m={"requested_url":t["url"],"curl_exit_code":0,"curl_error":None,"http_code":200,"content_type":"application/json","url_effective":t["url"],"body_bytes":10,"body_sha256":"a"*64,"json_error":None,"top_level_keys":["numeroControlePNCP"],"selected":{"numeroControlePNCP":t["control"]},"remote_get_count":1,"raw_body_persisted":False}
  r=execute(self.c,self.e,transport=F(m),authorization=None,expected_implementation_sha="0"*40,offline_test_mode=True);self.assertEqual(r["outcome"],"EXACT_CONTROL_RESOLVED")
if __name__=="__main__":unittest.main()
