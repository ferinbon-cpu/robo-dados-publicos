import unittest
from pathlib import Path
from robo_dados_publicos.research.task258_task257_json301_body import *
ROOT=Path(__file__).resolve().parents[1]
class F:
 def __init__(self,m):self.m=m
 def get(self,*a,**k):return dict(self.m)
class T(unittest.TestCase):
 def setUp(self):self.c=load_config(ROOT/"config/task258_task257_json301_body.v1.json");self.e=load_evidence(ROOT/"docs/evidence/TASK_258_TASK257_HTTP301_NO_LOCATION_CANONICAL_0.8.0.json")
 def test_projection(self):self.assertEqual(project({"a":"x"*600})["a"],"x"*512)
 def test_parsed(self):
  p=self.c["probe"];m={"requested_url":p["requested_url"],"curl_exit_code":0,"curl_error":None,"http_code":301,"url_effective":p["requested_url"],"content_type":"application/json","body_bytes":20,"body_sha256":"a"*64,"json_parse_error":None,"json_projection":{"message":"moved"},"remote_get_count":1,"raw_body_persisted":False}
  r=execute(self.c,self.e,transport=F(m),authorization=None,expected_implementation_sha="0"*40,offline_test_mode=True);self.assertEqual(r["outcome"],"JSON_BODY_PARSED");self.assertFalse(r["raw_body_persisted"])
if __name__=="__main__":unittest.main()
