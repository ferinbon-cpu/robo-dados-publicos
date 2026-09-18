import unittest
from pathlib import Path
from robo_dados_publicos.research.task267_pncp_items_8of8_canonization import *
ROOT=Path(__file__).resolve().parents[1]
class T(unittest.TestCase):
    def test_canonical(self):
        self.assertEqual(validate()["status"],"PASS_TASK267_PNCP_ITEMS_8OF8_CANONIZATION")
    def test_counts(self):
        rows=load_rows(ROOT/"docs/evidence/fixtures/task267/TASK_267_PNCP_ITEMS_8OF8_SUMMARY.jsonl")
        self.assertEqual(sum(x["item_count"] for x in rows),40)
        self.assertEqual(sum(x["material_count"] for x in rows),28)
        self.assertEqual(sum(x["service_count"] for x in rows),12)
    def test_financial_boundary(self):
        e=load_evidence(ROOT/"docs/evidence/TASK_267_PNCP_ITEMS_8OF8_CANONICAL_0.8.0.json")
        self.assertFalse(e["financial_adjudication"]["selected_valor_total_sum_is_payment"])
        self.assertFalse(e["financial_adjudication"]["selected_valor_total_sum_is_budget_execution"])
        self.assertFalse(e["financial_adjudication"]["pncp_to_tce_chain_proven"])
if __name__=="__main__":unittest.main()
