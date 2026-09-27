import copy
import json
import unittest
from scripts.github_task_011_release_0_8_0_readiness_gate import CONFIG, CURRENT, DECISION, READY, validate


class ReleaseReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data = json.loads(CONFIG.read_text(encoding="utf-8"))
    def test_current_decision_and_all_explicit_blockers(self):
        result = validate(copy.deepcopy(self.data)); self.assertEqual(result["decision"], DECISION); self.assertEqual(result["unmet"], list(CURRENT))
    def test_rejects_active(self):
        data = copy.deepcopy(self.data); data["RELEASE_0_8_0"] = "ACTIVE"
        with self.assertRaises(ValueError): validate(data)
    def test_partial_progress_computes_remaining_blockers(self):
        data = copy.deepcopy(self.data); data["blockers"]["B1_NUM_POPU"] = "PROVEN"
        result = validate(data); self.assertEqual(result["decision"], DECISION); self.assertNotIn("B1_NUM_POPU", result["unmet"])
    def test_all_proven_is_ready_but_candidate_and_non_operational(self):
        data = copy.deepcopy(self.data); data["blockers"] = copy.deepcopy(data["permitted_proven_state"])
        result = validate(data); self.assertEqual(result["decision"], READY); self.assertEqual(result["release"], "0.8.0 CANDIDATE"); self.assertEqual(result["operational_effect"], "NONE_EVALUATION_ONLY")
    def test_rejects_protocol_or_state_vocabulary_drift(self):
        data = copy.deepcopy(self.data); data["blockers"]["B1_NUM_POPU"] = "WAITING_FNDE_LAI_WRONG"
        with self.assertRaises(ValueError): validate(data)
    def test_rejects_operational_effect(self):
        data = copy.deepcopy(self.data); data["readiness_effect"] = "PUBLISH"
        with self.assertRaises(ValueError): validate(data)


if __name__ == "__main__": unittest.main()
