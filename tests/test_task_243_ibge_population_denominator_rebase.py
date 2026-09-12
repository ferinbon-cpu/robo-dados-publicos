import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "scripts/github_task_243_ibge_population_denominator_rebase_gate.py"
SPEC = importlib.util.spec_from_file_location("task243_gate", GATE_PATH)
GATE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GATE)


def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


class Task243IbgePopulationDenominatorRebaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = load(GATE.EVIDENCE)
        cls.contract = load(GATE.CONTRACT)
        cls.discovery = load(GATE.DISCOVERY)
        cls.task241 = load(GATE.TASK241)
        cls.b1 = load(GATE.B1)
        cls.territory = load(GATE.TERRITORY)
        cls.gold_scope_text = GATE.GOLD_SCOPE.read_text(encoding="utf-8")

    def run_gate(self, **changes):
        values = {
            "evidence": copy.deepcopy(self.evidence),
            "contract": copy.deepcopy(self.contract),
            "discovery": copy.deepcopy(self.discovery),
            "task241": copy.deepcopy(self.task241),
            "b1": copy.deepcopy(self.b1),
            "territory": copy.deepcopy(self.territory),
            "gold_scope_text": self.gold_scope_text,
        }
        values.update(changes)
        return GATE.validate_objects(**values)

    def test_current_snapshot_passes(self):
        self.assertEqual(self.run_gate(), GATE.PASS)

    def test_rejects_num_popu_reuse(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["guards"]["num_popu_used_as_2025_denominator"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_historical_num_popu_inference(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["guards"]["historical_num_popu_compatibility_inferred"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_single_2025_estimate_as_full_series(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["offline_discovery_result"]["single_year_observations_sufficient_for_rebase"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_sidra_assumption(self):
        discovery = copy.deepcopy(self.discovery)
        discovery["candidate_product_policy"]["sidra_assumed"] = True
        with self.assertRaises(ValueError):
            self.run_gate(discovery=discovery)

    def test_rejects_ibge_cidades_assumption(self):
        discovery = copy.deepcopy(self.discovery)
        discovery["candidate_product_policy"]["ibge_cidades_assumed"] = True
        with self.assertRaises(ValueError):
            self.run_gate(discovery=discovery)

    def test_rejects_annual_estimate_assumption(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["offline_discovery_result"]["annual_estimates_assumed"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_census_copy_to_all_years(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["guards"]["census_2022_count_reused_for_other_years"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_reference_year_publication_year_collapse(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["guards"]["reference_year_equated_to_publication_year"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_census_estimate_mix_without_contract(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["guards"]["census_and_estimate_mixed_without_contract"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_imputation(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["guards"]["imputation_performed"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_historical_gold_rewrite(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["rebased_series_contract"]["historical_gold_mutation_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_rebased_series_calculation(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["rebased_series_contract"]["calculation_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_remote_acquisition_authorization(self):
        contract = copy.deepcopy(self.contract)
        contract["remote_acquisition_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(contract=contract)

    def test_rejects_discovery_execution_authorization(self):
        discovery = copy.deepcopy(self.discovery)
        discovery["execution_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(discovery=discovery)

    def test_rejects_product_preselection(self):
        discovery = copy.deepcopy(self.discovery)
        discovery["candidate_product_policy"]["preselected_product"] = "SIDRA"
        with self.assertRaises(ValueError):
            self.run_gate(discovery=discovery)

    def test_rejects_year_scope_shrink(self):
        discovery = copy.deepcopy(self.discovery)
        discovery["target_years"] = list(range(2020, 2026))
        with self.assertRaises(ValueError):
            self.run_gate(discovery=discovery)

    def test_rejects_gold_authorization(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["decision"]["gold_2025_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)

    def test_rejects_release_promotion(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["decision"]["release_promotion_authorized"] = True
        with self.assertRaises(ValueError):
            self.run_gate(evidence=evidence)


if __name__ == "__main__":
    unittest.main()
