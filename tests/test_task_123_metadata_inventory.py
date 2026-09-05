from copy import deepcopy
from pathlib import Path
import unittest
from robo_dados_publicos.research.task123_metadata_inventory import Task123Stop,load_task123_contract,validate_task123_contract
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"config/task123_granular_execution_metadata_inventory.v1.json"

class TestTask123(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.c=load_task123_contract(P)
    def test_exact_budget(self):
        self.assertEqual(8,self.c["search_contract"]["max_probes"])
        self.assertEqual(20,self.c["search_contract"]["topn_per_probe"])
        self.assertFalse(self.c["search_contract"]["content_hydration_allowed"])
    def test_hydration_fails_closed(self):
        x=deepcopy(self.c); x["search_contract"]["content_hydration_allowed"]=True
        with self.assertRaises(Task123Stop): validate_task123_contract(x)
    def test_content_read_fails_closed(self):
        x=deepcopy(self.c); x["remote_effects"]["drive_content_read"]=True
        with self.assertRaises(Task123Stop): validate_task123_contract(x)
    def test_future_read_not_authorized(self):
        x=deepcopy(self.c); x["future_content_read_authorized"]=True
        with self.assertRaises(Task123Stop): validate_task123_contract(x)
if __name__=="__main__": unittest.main()
