import copy
import json
import unittest
from scripts.github_task_011_b5_siope_2016_2025_series_inclusion_gate import CONFIG, DECISION, HISTORICAL, validate


class B5GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CONFIG.read_text(encoding="utf-8")); cls.historical = json.loads(HISTORICAL.read_text(encoding="utf-8"))
    def reject(self, fn):
        data = copy.deepcopy(self.data); fn(data)
        with self.assertRaises(ValueError): validate(data, self.historical)
    def test_current_series_passes_to_stop(self): self.assertEqual(validate(copy.deepcopy(self.data), self.historical), DECISION)
    def test_rejects_missing_duplicate_reorder_and_future_year(self):
        self.reject(lambda d: d["historical_contract"]["years"].pop(2))
        self.reject(lambda d: d["historical_contract"]["years"].__setitem__(2, 2017))
        self.reject(lambda d: d["historical_contract"]["years"].reverse())
        self.reject(lambda d: d["historical_contract"]["years"].append(2026))
    def test_rejects_append_and_promotions(self):
        self.reject(lambda d: d.update(candidate_2025={"year": 2025})); self.reject(lambda d: d.update(automatic_append=True))
        self.reject(lambda d: d.update(closed_annual_series="2016-2025")); self.reject(lambda d: d.update(release_0_8_0="ACTIVE"))
    def test_rejects_b4_shortcut_and_unvalidated_gold(self):
        self.reject(lambda d: d["prerequisites"].update(B4_GOLD_2025="PROVEN_AUTHORIZED_COMPUTED"))
        self.reject(lambda d: d["required_state"].update(GOLD_2025_DETERMINISTIC_EVIDENCE="ARTIFACT_PRESENT"))
        self.reject(lambda d: d["required_state"].update(SEMANTIC_COMPARABILITY="UNKNOWN"))
        self.reject(lambda d: d["effects"].update(series_rows_appended=1))


if __name__ == "__main__": unittest.main()
