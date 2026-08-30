import copy
import json
import unittest
from scripts.github_task_011_b5_siope_2016_2025_series_inclusion_gate import CANDIDATE_CONTRACT, CONFIG, DECISION, HISTORICAL, READY, validate


class B5GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CONFIG.read_text(encoding="utf-8")); cls.historical = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    def reject(self, fn):
        data = copy.deepcopy(self.data); fn(data)
        with self.assertRaises(ValueError): validate(data, self.historical)
    def test_current_series_passes_to_stop(self):
        result = validate(copy.deepcopy(self.data), self.historical); self.assertEqual(result["decision"], DECISION); self.assertFalse(result["candidate_present"])
    def test_rejects_missing_duplicate_reorder_and_future_year(self):
        self.reject(lambda d: d["historical_contract"]["years"].pop(2))
        self.reject(lambda d: d["historical_contract"]["years"].__setitem__(2, 2017))
        self.reject(lambda d: d["historical_contract"]["years"].reverse())
        self.reject(lambda d: d["historical_contract"]["years"].append(2026))
    def test_rejects_append_and_promotions(self):
        self.reject(lambda d: d.update(candidate_2025={"year": 2025})); self.reject(lambda d: d.update(automatic_append=True))
        self.reject(lambda d: d.update(closed_annual_series="2016-2025")); self.reject(lambda d: d.update(release_0_8_0="ACTIVE"))
    def test_rejects_b4_shortcut_and_unvalidated_gold(self):
        self.reject(lambda d: d["required_state"].update(GOLD_2025_DETERMINISTIC_EVIDENCE="ARTIFACT_PRESENT"))
        self.reject(lambda d: d["required_state"].update(SEMANTIC_COMPARABILITY="UNKNOWN"))
        self.reject(lambda d: d["effects"].update(series_rows_appended=1))
    def candidate(self, data):
        data["candidate_2025"] = {"identity": copy.deepcopy(CANDIDATE_CONTRACT["identity"]), "gold_evidence": copy.deepcopy(CANDIDATE_CONTRACT["gold_evidence"])}
    def test_partial_progress_stops_with_exact_unmet(self):
        data = copy.deepcopy(self.data); data["prerequisites"]["B4_GOLD_2025"] = data["required_state"]["B4_GOLD_2025"]
        result = validate(data, self.historical); self.assertEqual(result["decision"], DECISION); self.assertNotIn("B4_GOLD_2025", result["unmet"])
    def test_rejects_invalid_candidate_identity_and_gold_evidence(self):
        for field, value in (("year", 2026), ("period", 5), ("uf", "RJ"), ("municipality", "Campinas"), ("municipality_code", 350950)):
            data = copy.deepcopy(self.data); self.candidate(data); data["candidate_2025"]["identity"][field] = value
            with self.assertRaises(ValueError): validate(data, self.historical)
        for field, value in (("provenance_status", "ABSENT"), ("arithmetic_contract_schema", "PARALLEL_SCHEMA"), ("arithmetic_validation_status", "UNKNOWN")):
            data = copy.deepcopy(self.data); self.candidate(data); data["candidate_2025"]["gold_evidence"][field] = value
            with self.assertRaises(ValueError): validate(data, self.historical)
    def test_valid_candidate_all_proven_is_non_mutating_ready(self):
        data = copy.deepcopy(self.data); self.candidate(data); data["prerequisites"] = copy.deepcopy(data["required_state"])
        result = validate(data, self.historical)
        self.assertEqual(result["decision"], READY); self.assertEqual(result["unmet"], [])
        self.assertEqual((result["writes"], result["series_rows_appended"], result["release_promotion"]), (0, 0, False))


if __name__ == "__main__": unittest.main()
