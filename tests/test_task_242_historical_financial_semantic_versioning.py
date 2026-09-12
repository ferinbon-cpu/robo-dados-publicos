import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "scripts/github_task_242_historical_financial_semantic_versioning_gate.py"
SPEC = importlib.util.spec_from_file_location("task242_gate", GATE_PATH)
GATE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GATE)


def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


class Task242HistoricalFinancialSemanticVersioningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = load(GATE.EVIDENCE)
        cls.contract = load(GATE.CONTRACT)
        cls.acquisition = load(GATE.ACQUISITION)
        cls.task241 = load(GATE.TASK241)
        cls.continuity = load(GATE.CONTINUITY)
        cls.proof_standard_text = GATE.PROOF_STANDARD_DOC.read_text(encoding="utf-8")
        cls.b2 = load(GATE.B2)

    def run_gate(self, **changes):
        values = {
            "evidence": copy.deepcopy(self.evidence),
            "contract": copy.deepcopy(self.contract),
            "acquisition": copy.deepcopy(self.acquisition),
            "task241": copy.deepcopy(self.task241),
            "continuity": copy.deepcopy(self.continuity),
            "proof_standard_text": self.proof_standard_text,
            "b2": copy.deepcopy(self.b2),
        }
        values.update(changes)
        return GATE.validate_objects(**values)

    def test_current_snapshot_passes(self):
        self.assertEqual(self.run_gate(), GATE.PASS)

    def test_rejects_historical_year_promotion(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["year_regime_matrix"][0]["status"] = "PROVEN_COMPARABLE"
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_financial_input_promotion(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["financial_inputs"][0]["status"] = "PROVEN_COMPARABLE"
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_financial_metric_promotion(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["financial_metrics_1_to_6"][0]["status"] = "PROVEN_COMPARABLE"
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_internal_identity_becoming_mandatory(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["proof_standard"]["source_internal_identity_required_by_default"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_remote_acquisition_authorization_in_evidence(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["offline_decision"]["remote_acquisition_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_remote_acquisition_authorization_in_contract(self):
        contract = copy.deepcopy(self.contract)
        contract["remote_acquisition_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(contract=contract)

    def test_rejects_acquisition_execution_authorization(self):
        acquisition = copy.deepcopy(self.acquisition)
        acquisition["execution_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(acquisition=acquisition)

    def test_rejects_remote_collection_authorization(self):
        acquisition = copy.deepcopy(self.acquisition)
        acquisition["remote_collection_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(acquisition=acquisition)

    def test_rejects_gold_authorization(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["offline_decision"]["gold_2025_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_rewriting_task241_partial_state(self):
        task241 = copy.deepcopy(self.task241)
        task241["financial_inputs_summary"]["PARTIAL"] = 9
        task241["financial_inputs_summary"]["PROVEN_COMPARABLE"] = 1
        with self.assertRaises(ValueError):
            self.run_gate(task241=task241)

    def test_rejects_rewriting_historical_proof_gap(self):
        continuity = copy.deepcopy(self.continuity)
        continuity["result"]["code"] = "PROVEN_CONTINUITY"
        with self.assertRaises(ValueError):
            self.run_gate(continuity=continuity)

    def test_rejects_2016_period_boundary_drift(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["year_regime_matrix"][0]["period"] = 6
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_missing_year(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["year_regime_matrix"] = evidence["year_regime_matrix"][:-1]
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_collapsing_required_temporal_years_in_acquisition(self):
        acquisition = copy.deepcopy(self.acquisition)
        acquisition["years"] = list(range(2019, 2025))
        with self.assertRaises(ValueError):
            self.run_gate(acquisition=acquisition)

    def test_rejects_alias_scope_shrink(self):
        acquisition = copy.deepcopy(self.acquisition)
        acquisition["aliases"] = acquisition["aliases"][:-1]
        with self.assertRaises(ValueError):
            self.run_gate(acquisition=acquisition)

    def test_rejects_proof_route_shrink(self):
        acquisition = copy.deepcopy(self.acquisition)
        acquisition["acceptable_proof_routes"] = acquisition["acceptable_proof_routes"][:2]
        with self.assertRaises(ValueError):
            self.run_gate(acquisition=acquisition)

    def test_rejects_guard_violation(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["guards"]["absence_of_positive_break_used_as_proof"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)


if __name__ == "__main__":
    unittest.main()
