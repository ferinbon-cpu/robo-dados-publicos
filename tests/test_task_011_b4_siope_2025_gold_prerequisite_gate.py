import copy
import json
import unittest
from scripts.github_task_011_b4_siope_2025_gold_prerequisite_gate import CONFIG, DECISION, KEYS, READY, validate


class B4GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data = json.loads(CONFIG.read_text(encoding="utf-8"))
    def test_current_result_lists_all_blockers(self):
        result = validate(copy.deepcopy(self.data)); self.assertEqual(result["decision"], DECISION); self.assertEqual(result["unmet"], KEYS); self.assertFalse(result["gold_2025_calculated"])
    def test_every_partial_combination_remains_stopped(self):
        for mask in range(1, 8):
            data = copy.deepcopy(self.data)
            for index, key in enumerate(KEYS[:3]):
                if mask & (1 << index): data["prerequisites"][key] = "PROVEN"
            self.assertEqual(validate(data)["decision"], DECISION)
        data = copy.deepcopy(self.data)
        for key in KEYS[:3]: data["prerequisites"][key] = "PROVEN"
        self.assertEqual(validate(data)["unmet"], ["SEMANTIC_COMPARABILITY"])
    def test_all_proven_is_evaluation_only_ready(self):
        data = copy.deepcopy(self.data)
        for key in KEYS: data["prerequisites"][key] = "PROVEN"
        result = validate(data)
        self.assertEqual(result["decision"], READY); self.assertEqual(result["unmet"], [])
        self.assertFalse(result["gold_2025_calculated"]); self.assertEqual(result["authorization_effect"], "NONE_EVALUATION_ONLY")
    def test_rejects_structural_submission_and_nine_of_ten_shortcuts(self):
        for key, value in (("year_2025", "PROVEN"), ("VALID_ANNUAL_SUBMISSION", "CURRENTLY_EFFECTIVE_DECLARATION"), ("financial_aliases_proven_exact_operational", "10/10")):
            data = copy.deepcopy(self.data); data["context_only"][key] = value
            with self.assertRaises(ValueError): validate(data)
    def test_rejects_effect_or_scope_drift(self):
        for mutation in (lambda d: d["effects"].update(gold_arithmetic=1), lambda d: d.update(gold_2025_calculated=True), lambda d: d["scope"].update(year=2026)):
            data = copy.deepcopy(self.data); mutation(data)
            with self.assertRaises(ValueError): validate(data)


if __name__ == "__main__": unittest.main()
