import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "scripts/github_task_244_acquisition_ready_state_gate.py"
SPEC = importlib.util.spec_from_file_location("task244_gate", GATE_PATH)
GATE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GATE)


class Task244AcquisitionReadyStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = GATE.load(GATE.EVIDENCE)
        cls.readiness = GATE.load(GATE.READINESS)
        cls.gold = GATE.load(GATE.GOLD)
        cls.task242 = GATE.load(GATE.TASK242)
        cls.task243 = GATE.load(GATE.TASK243)

    def run_gate(self, **changes):
        values = {
            "evidence": copy.deepcopy(self.evidence),
            "readiness": copy.deepcopy(self.readiness),
            "gold": copy.deepcopy(self.gold),
            "task242": copy.deepcopy(self.task242),
            "task243": copy.deepcopy(self.task243),
        }
        values.update(changes)
        return GATE.validate_objects(**values)

    def test_current_snapshot_passes(self):
        self.assertEqual(self.run_gate(), GATE.PASS)

    def test_rejects_financial_promotion_by_task_completion(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["entry_state"]["financial_metrics_1_to_6"] = "6_OF_6_PROVEN_COMPARABLE"
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_per_capita_promotion_by_task_completion(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["entry_state"]["per_capita_metrics_7_to_8"] = "2_OF_2_PROVEN_COMPARABLE"
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_gold_authorization(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["authorization_state"]["gold_calculation_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(readiness=readiness)

    def test_rejects_series_inclusion_authorization(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["authorization_state"]["series_inclusion_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(readiness=readiness)

    def test_rejects_release_promotion(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["release_0_8_0"] = "ACTIVE"
        with self.assertRaises(ValueError):
            self.run_gate(readiness=readiness)

    def test_rejects_financial_route_drift(self):
        gold = copy.deepcopy(self.gold)
        gold["next_evidence_gates"][0] = "GOLD_NOW"
        with self.assertRaises(ValueError):
            self.run_gate(gold=gold)

    def test_rejects_ibge_route_drift(self):
        gold = copy.deepcopy(self.gold)
        gold["next_evidence_gates"][1] = "USE_NUM_POPU"
        with self.assertRaises(ValueError):
            self.run_gate(gold=gold)

    def test_rejects_historical_task242_rewrite(self):
        task242 = copy.deepcopy(self.task242)
        task242["offline_decision"]["status"] = "PROVEN"
        with self.assertRaises(ValueError):
            self.run_gate(task242=task242)

    def test_rejects_historical_task243_rewrite(self):
        task243 = copy.deepcopy(self.task243)
        task243["decision"]["status"] = "PROVEN"
        with self.assertRaises(ValueError):
            self.run_gate(task243=task243)


if __name__ == "__main__":
    unittest.main()
