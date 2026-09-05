from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"docs/evidence/TASK_125_TCESP_CURL_TRANSPORT_0.8.0.json"
class TestTask125Closure(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.e=json.loads(P.read_text(encoding="utf-8"))
 def test_one_get_no_retry(self):
  x=self.e["live_execution"]; self.assertEqual(1,x["get_attempts"]); self.assertEqual(0,x["head_requests"]); self.assertFalse(x["retry_performed"])
 def test_dns_failure_zero_bytes(self):
  x=self.e["live_execution"]; self.assertEqual(6,x["curl_exit_code"]); self.assertEqual("000",x["http_code"]); self.assertEqual(0,x["size_download_bytes"]); self.assertEqual("DNS_RESOLUTION_FAILURE",x["failure_class"])
 def test_no_data_conclusion(self):
  i=self.e["interpretation"]; self.assertTrue(i["transport_failure_only"]); self.assertTrue(i["no_data_conclusion"]); self.assertFalse(i["no_match_claim"]); self.assertFalse(i["source_unavailable_claim"])
 def test_next_route_is_not_third_retry(self):
  n=self.e["next_action"]; self.assertEqual("USE_WEB_ACCESSIBLE_HTML_OR_SEARCH_SURFACE_NEW_GATE",n["status"]); self.assertFalse(n["third_transport_retry_in_same_task_allowed"])
if __name__=="__main__": unittest.main()
