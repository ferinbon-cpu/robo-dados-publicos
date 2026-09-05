from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"docs/evidence/TASK_124_TCESP_LIMEIRA_2026_EXPENSE_SCAN_0.8.0.json"
class TestTask124Closure(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.e=json.loads(P.read_text(encoding="utf-8"))
 def test_one_attempt_consumed_no_retry(self):
  x=self.e["live_execution"]; self.assertEqual(1,x["get_attempts"]); self.assertEqual(1,x["max_get_attempts"]); self.assertFalse(x["retry_performed"])
 def test_no_bytes_no_scan(self):
  x=self.e["live_execution"]; self.assertEqual(0,x["bytes_received"]); self.assertIsNone(x["source_sha256"]); self.assertFalse(x["zip_opened"]); self.assertEqual(0,x["rows_scanned"])
 def test_no_data_conclusion(self):
  i=self.e["interpretation"]; self.assertTrue(i["no_data_conclusion_permitted"]); self.assertFalse(i["no_match_claim"]); self.assertFalse(i["source_unavailable_claim"])
 def test_new_route_required(self):
  n=self.e["next_action"]; self.assertEqual("DESIGN_NEW_SINGLE_USE_TRANSPORT_ROUTE",n["status"]); self.assertFalse(n["same_task_retry_allowed"]); self.assertTrue(n["future_route_must_be_separately_gated"])
if __name__=="__main__": unittest.main()
