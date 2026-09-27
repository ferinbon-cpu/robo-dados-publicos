from pathlib import Path
import json,unittest
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"docs/evidence/TASK_123_GRANULAR_EXECUTION_METADATA_INVENTORY_0.8.0.json"
class TestTask123Closure(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.e=json.loads(P.read_text(encoding="utf-8"))
 def test_exact_probe_budget_consumed(self):
  self.assertEqual(8,self.e["probe_count"]); self.assertEqual(8,self.e["request_counts"]["drive_metadata_searches"])
  self.assertEqual(0,self.e["request_counts"]["drive_content_reads"]); self.assertEqual(0,self.e["request_counts"]["drive_writes"])
 def test_no_candidate_or_forced_ranking(self):
  self.assertEqual([],self.e["candidate_inventory"]); self.assertIsNone(self.e["recommended_next_content_read"])
  self.assertTrue(self.e["interpretation"]["no_probative_candidate_found"])
 def test_known_aggregate_preserved_as_insufficient(self):
  x=[r for r in self.e["observed_metadata"] if r["title"]=="05 - Maio_despesa.pdf"]
  self.assertEqual(1,len(x)); self.assertEqual("KNOWN_INSUFFICIENT_TASK055_AGGREGATE_ECONOMIC_ELEMENT_REPORT",x[0]["classification"])
 def test_no_global_absence_claim(self):
  self.assertFalse(self.e["interpretation"]["proves_no_granular_source_exists_in_drive"])
  self.assertFalse(self.e["interpretation"]["proves_no_eiti_execution_exists"])
 def test_next_action_is_public_source_discovery_not_content_read(self):
  self.assertEqual("ESCALATE_TO_PUBLIC_SOURCE_DISCOVERY",self.e["next_action"]["status"])
  self.assertFalse(self.e["next_action"]["content_read_authorized"])
if __name__=="__main__": unittest.main()
