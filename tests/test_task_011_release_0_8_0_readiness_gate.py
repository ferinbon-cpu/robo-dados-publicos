import copy
import json
import unittest
from scripts.github_task_011_release_0_8_0_readiness_gate import CONFIG, CURRENT, DECISION, validate


class ReleaseReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data = json.loads(CONFIG.read_text(encoding="utf-8"))
    def test_current_decision_and_all_explicit_blockers(self):
        result = validate(copy.deepcopy(self.data)); self.assertEqual(result["decision"], DECISION); self.assertEqual(result["unmet"], list(CURRENT))
    def test_rejects_active_or_any_transitive_shortcut(self):
        data = copy.deepcopy(self.data); data["RELEASE_0_8_0"] = "ACTIVE"
        with self.assertRaises(ValueError): validate(data)
        for key in CURRENT:
            data = copy.deepcopy(self.data); data["blockers"][key] = "PROVEN"
            with self.assertRaises(ValueError): validate(data)
    def test_rejects_operational_effect(self):
        data = copy.deepcopy(self.data); data["readiness_effect"] = "PUBLISH"
        with self.assertRaises(ValueError): validate(data)


if __name__ == "__main__": unittest.main()
