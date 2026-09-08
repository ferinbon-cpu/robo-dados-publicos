import unittest

from robo_dados_publicos.analytics.current_observatory_answerability import (
    current_answerability_config,
    current_question_answerability,
    load_pointer,
)
from tests.test_task_202_equity_missingness_aware_gate import latest_products


class TestTask202CCurrentAnswerabilityPointer(unittest.TestCase):
    def test_pointer_is_v4_and_remote_effects_off(self):
        pointer = load_pointer()
        self.assertEqual(pointer["canonical_version"], 4)
        self.assertEqual(pointer["expected_status_counts"], {"MATERIALIZED_ANSWERABLE": 38})
        self.assertTrue(all(v is False for v in pointer["remote_effects"].values()))

    def test_canonical_config_is_v4_overlay(self):
        cfg = current_answerability_config()
        self.assertEqual(cfg["version"], 4)
        self.assertEqual(cfg["task"], "TASK_202_EQUITY_MISSINGNESS_AWARE_GATE")
        self.assertEqual(cfg["current_overlay"], "config/observatory_semantic_answerability.v4.overlay.json")

    def test_canonical_current_evaluator_is_38_of_38(self):
        report = current_question_answerability(latest_products(task202=True))
        self.assertEqual(report["question_count"], 38)
        self.assertEqual(report["status_counts"], {"MATERIALIZED_ANSWERABLE": 38})
        self.assertTrue(all(row["status"] == "MATERIALIZED_ANSWERABLE" for row in report["questions"]))


if __name__ == "__main__":
    unittest.main()
