import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "scripts/github_task_241_semantic_comparability_gate.py"
SPEC = importlib.util.spec_from_file_location("task241_gate", GATE_PATH)
GATE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GATE)


def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


class Task241SemanticComparabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = load(GATE.EVIDENCE)
        cls.contract = load(GATE.CONTRACT)
        cls.gold_v3 = load(GATE.GOLD_V3)
        cls.readiness_v3 = load(GATE.READINESS_V3)
        cls.gold_v2 = load(GATE.GOLD_V2)
        cls.readiness_v2 = load(GATE.READINESS_V2)
        cls.continuity = load(GATE.CONTINUITY)
        cls.regimes = load(GATE.REGIMES)
        cls.historical_matrix = load(GATE.HISTORICAL_MATRIX)
        cls.b1 = load(GATE.B1)
        cls.b2 = load(GATE.B2)
        cls.b3 = load(GATE.B3)

    def run_gate(self, **changes):
        values = {
            "evidence": copy.deepcopy(self.evidence),
            "contract": copy.deepcopy(self.contract),
            "gold_v3": copy.deepcopy(self.gold_v3),
            "readiness_v3": copy.deepcopy(self.readiness_v3),
            "gold_v2": copy.deepcopy(self.gold_v2),
            "readiness_v2": copy.deepcopy(self.readiness_v2),
            "continuity": copy.deepcopy(self.continuity),
            "regimes": copy.deepcopy(self.regimes),
            "historical_matrix": copy.deepcopy(self.historical_matrix),
            "b1": copy.deepcopy(self.b1),
            "b2": copy.deepcopy(self.b2),
            "b3": copy.deepcopy(self.b3),
        }
        values.update(changes)
        return GATE.validate_objects(**values)

    def test_current_snapshot_passes(self):
        self.assertEqual(self.run_gate(), GATE.PASS)

    def test_rejects_financial_input_promotion_without_historical_bridge(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["financial_inputs"][0]["status"] = "PROVEN_COMPARABLE"
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_financial_metric_promotion(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["financial_gold_metrics_1_to_6"][0]["status"] = "PROVEN_COMPARABLE"
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_per_capita_promotion(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["per_capita_gold_metrics_7_to_8"][0]["status"] = "PROVEN_COMPARABLE"
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_num_popu_2025_use(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["per_capita_summary"]["num_popu_2025_use_forbidden"] = False
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_historical_denominator_inference(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["per_capita_summary"]["historical_num_popu_compatibility_inferred"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_fabricated_full_8_of_8(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["global_decision"]["full_8_of_8_comparability"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_gold_authorization(self):
        gold_v3 = copy.deepcopy(self.gold_v3)
        gold_v3["gold_2025_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(gold_v3=gold_v3)

    def test_rejects_gold_calculation(self):
        gold_v3 = copy.deepcopy(self.gold_v3)
        gold_v3["gold_2025_calculated"] = True
        with self.assertRaises(ValueError):
            self.run_gate(gold_v3=gold_v3)

    def test_rejects_series_inclusion(self):
        gold_v3 = copy.deepcopy(self.gold_v3)
        gold_v3["closed_annual_series"] = "2016-2025"
        with self.assertRaises(ValueError):
            self.run_gate(gold_v3=gold_v3)

    def test_rejects_release_promotion(self):
        readiness_v3 = copy.deepcopy(self.readiness_v3)
        readiness_v3["release_0_8_0"] = "ACTIVE"
        with self.assertRaises(ValueError):
            self.run_gate(readiness_v3=readiness_v3)

    def test_rejects_rewriting_historical_proof_gap(self):
        continuity = copy.deepcopy(self.continuity)
        continuity["result"]["code"] = "PROVEN_CONTINUITY"
        with self.assertRaises(ValueError):
            self.run_gate(continuity=continuity)

    def test_rejects_rewriting_historical_v2_gold(self):
        gold_v2 = copy.deepcopy(self.gold_v2)
        gold_v2["prerequisites"]["SEMANTIC_COMPARABILITY"] = "PARTIAL"
        with self.assertRaises(ValueError):
            self.run_gate(gold_v2=gold_v2)

    def test_rejects_guard_promotion(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["guards"]["same_field_name_used_as_proof"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)


if __name__ == "__main__":
    unittest.main()
