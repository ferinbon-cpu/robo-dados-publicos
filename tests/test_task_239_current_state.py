import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "scripts/github_task_239_current_state_gate.py"
SPEC = importlib.util.spec_from_file_location("task239_gate", GATE_PATH)
GATE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GATE)


def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


class Task239CurrentStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = load(GATE.STATE)
        cls.territory = load(GATE.TERRITORY)
        cls.b1 = load(GATE.B1)
        cls.b2 = load(GATE.B2)
        cls.b3 = load(GATE.B3)
        cls.readiness_v2 = load(GATE.READINESS_V2)
        cls.gold_v2 = load(GATE.GOLD_V2)
        cls.readiness_v1 = load(GATE.READINESS_V1)
        cls.gold_v1 = load(GATE.GOLD_V1)
        cls.task011 = load(GATE.TASK011)
        cls.readme = GATE.README.read_text(encoding="utf-8")
        cls.status = GATE.STATUS.read_text(encoding="utf-8")

    def run_gate(self, **changes):
        values = {
            "state": copy.deepcopy(self.state),
            "territory": copy.deepcopy(self.territory),
            "b1": copy.deepcopy(self.b1),
            "b2": copy.deepcopy(self.b2),
            "b3": copy.deepcopy(self.b3),
            "readiness_v2": copy.deepcopy(self.readiness_v2),
            "gold_v2": copy.deepcopy(self.gold_v2),
            "readiness_v1": copy.deepcopy(self.readiness_v1),
            "gold_v1": copy.deepcopy(self.gold_v1),
            "task011": copy.deepcopy(self.task011),
            "readme": self.readme,
            "status": self.status,
        }
        values.update(changes)
        return GATE.validate_objects(**values)

    def test_current_snapshot_passes(self):
        self.assertEqual(self.run_gate(), GATE.PASS)

    def test_rejects_64_of_69_regression(self):
        state = copy.deepcopy(self.state)
        state["territory"]["strong_school_links"] = 64
        with self.assertRaises(ValueError):
            self.run_gate(state=state)

    def test_rejects_fabricated_69_numeric_income(self):
        state = copy.deepcopy(self.state)
        state["territory"]["schools_with_numeric_income_context"] = 69
        with self.assertRaises(ValueError):
            self.run_gate(state=state)

    def test_rejects_source_x_as_zero(self):
        state = copy.deepcopy(self.state)
        state["territory"]["source_x_is_zero"] = True
        with self.assertRaises(ValueError):
            self.run_gate(state=state)

    def test_rejects_b1_pending_regression(self):
        state = copy.deepcopy(self.state)
        state["siope_2025"]["B1_NUM_POPU"] = "NOT_PROVEN"
        with self.assertRaises(ValueError):
            self.run_gate(state=state)

    def test_rejects_b2_nine_of_ten_regression(self):
        state = copy.deepcopy(self.state)
        state["siope_2025"]["B2_FINANCIAL_ALIAS_BRIDGE"] = "9/10"
        with self.assertRaises(ValueError):
            self.run_gate(state=state)

    def test_rejects_b3_pending_regression(self):
        state = copy.deepcopy(self.state)
        state["siope_2025"]["B3_EFFECTIVE_ANNUAL_DECLARATION"] = "NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING"
        with self.assertRaises(ValueError):
            self.run_gate(state=state)

    def test_rejects_immutable_finality(self):
        state = copy.deepcopy(self.state)
        state["siope_2025"]["immutable_finality_asserted"] = True
        with self.assertRaises(ValueError):
            self.run_gate(state=state)

    def test_rejects_gold_calculation(self):
        gold_v2 = copy.deepcopy(self.gold_v2)
        gold_v2["gold_2025_calculated"] = True
        with self.assertRaises(ValueError):
            self.run_gate(gold_v2=gold_v2)

    def test_rejects_inferred_comparability(self):
        state = copy.deepcopy(self.state)
        state["siope_2025"]["semantic_comparability_2016_2025"] = "PROVEN"
        with self.assertRaises(ValueError):
            self.run_gate(state=state)

    def test_rejects_historical_readiness_rewrite(self):
        readiness_v1 = copy.deepcopy(self.readiness_v1)
        readiness_v1["blockers"]["B1_NUM_POPU"] = GATE.B1_STATE
        with self.assertRaises(ValueError):
            self.run_gate(readiness_v1=readiness_v1)

    def test_rejects_historical_task011_rewrite(self):
        task011 = copy.deepcopy(self.task011)
        task011["requests"][0]["response_status"] = "RESPONDED"
        with self.assertRaises(ValueError):
            self.run_gate(task011=task011)

    def test_rejects_stale_readme(self):
        with self.assertRaises(ValueError):
            self.run_gate(readme=self.readme + "\n**Próximo gate:** respostas oficiais FNDE\n")

    def test_rejects_stale_status(self):
        with self.assertRaises(ValueError):
            self.run_gate(status=self.status + "\nEnquanto pendentes, têm efeito de promoção `NONE`.\n")


if __name__ == "__main__":
    unittest.main()
