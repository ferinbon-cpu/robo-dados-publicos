from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/"docs/evidence/TASK_127_JOM_EITI_ACCOUNTING_FIELD_SCAN_0.8.0.json"
A=ROOT/"docs/evidence/TASK_127_OWNER_AUTHORIZATION_PRE_RUN_0.8.0.json"
class TestTask127Closure(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.e=json.loads(E.read_text(encoding="utf-8")); cls.a=json.loads(A.read_text(encoding="utf-8"))
 def test_one_get_zero_bytes_no_retry(self):
  x=self.e["live_execution"]; self.assertEqual(1,x["get_attempts"]); self.assertEqual(0,x["bytes_received"]); self.assertFalse(x["retry_performed"])
 def test_no_scan_was_fabricated(self):
  x=self.e["live_execution"]; self.assertFalse(x["pdf_opened"]); self.assertEqual(0,x["pages_scanned"]); self.assertFalse(x["accounting_term_scan_performed"])
 def test_transport_stop_has_no_data_conclusion(self):
  i=self.e["interpretation"]; self.assertTrue(i["transport_failure_only"]); self.assertTrue(i["no_data_conclusion"]); self.assertFalse(i["no_accounting_field_absence_claim"]); self.assertFalse(i["source_unavailable_claim"])
 def test_no_identity_promotion(self):
  self.assertTrue(all(v is False for v in self.e["promotion"].values()))
 def test_authorization_consumed(self):
  self.assertEqual("CONSUMED_SINGLE_USE_TRANSPORT_STOP",self.a["status"]); self.assertEqual(1,self.a["consumed_by"]["get_attempts"]); self.assertFalse(self.a["future_retry_authorized"])
if __name__=="__main__": unittest.main()
