import unittest
from pathlib import Path
from robo_dados_publicos.research.task264_jom_pncp_8of8_canonization import *
ROOT=Path(__file__).resolve().parents[1]
class T(unittest.TestCase):
    def test_canonical(self):
        self.assertEqual(validate()["status"],"PASS_TASK264_8OF8_JOM_PNCP_EXACT_IDENTITY_CANONIZATION")
    def test_process_domains_stay_distinct(self):
        for r in load_rows(ROOT/"docs/evidence/fixtures/task264/TASK_264_JOM_PNCP_8OF8_IDENTITY.jsonl"):
            self.assertFalse(r["jom_admin_process_equals_pncp_processo"])
            self.assertNotEqual(r["jom_process"],r["pncp_processo"])
    def test_648_transient_history_not_absence(self):
        r=next(x for x in load_rows(ROOT/"docs/evidence/fixtures/task264/TASK_264_JOM_PNCP_8OF8_IDENTITY.jsonl") if x["seq"]==648)
        self.assertEqual([x["http"] for x in r["prior_transient_observations"]],[500,500,503])
        self.assertTrue(r["exact_identity_proven"])
if __name__=="__main__": unittest.main()
