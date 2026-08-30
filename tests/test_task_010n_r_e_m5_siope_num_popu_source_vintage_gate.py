import copy
import json
import unittest

from scripts.github_task_010n_r_e_m5_siope_num_popu_source_vintage_gate import DECISION, EVIDENCE, validate


class Task010NREM5NumPopuSourceVintageGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def reject(self, mutation, pattern):
        data = copy.deepcopy(self.data)
        mutation(data)
        with self.assertRaisesRegex(ValueError, pattern):
            validate(data, verify_files=False)

    def test_pinned_fail_closed_decision_passes(self):
        self.assertEqual(DECISION, validate(copy.deepcopy(self.data)))

    def test_rejects_authority_url_artifact_hash_or_proposition_drift(self):
        self.reject(lambda d: d["official_documentary_sources"][0].update(authority="IBGE"), "authority")
        self.reject(lambda d: d["official_documentary_sources"][0].update(url="https://example.test"), "URL")
        self.reject(lambda d: d["official_documentary_sources"][3].update(artifact_sha256="0" * 64), "hash")
        self.reject(lambda d: d["official_documentary_sources"][0].update(supports=""), "proposition")

    def test_rejects_definition_source_or_vintage_promotion_and_disappearance(self):
        for key in ("NUM_POPU_2025_SEMANTICS", "NUM_POPU_2025_SOURCE", "NUM_POPU_2025_VINTAGE"):
            with self.subTest(key=key):
                self.reject(lambda d, key=key: d["proof_results"].update({key: "PROVEN"}), "result")
                self.reject(lambda d, key=key: d["proof_results"].pop(key), "result")

    def test_rejects_target_change_or_nonexact_reconciliation(self):
        self.reject(lambda d: d["observed_target"].update(year=2024), "observed target")
        self.reject(lambda d: d["observed_target"].update(municipality="Campinas"), "observed target")
        self.reject(lambda d: d["observed_target"].update(approximate_equality_accepted=True), "approximate")
        self.reject(lambda d: d["observed_target"].update(value_used_for_reconciliation=291748), "reconciliation")

    def test_rejects_historical_rule_substitution(self):
        self.reject(lambda d: d["guards"].update(historical_rule_substituted_for_current=True), "guard")
        self.reject(lambda d: d["proof_results"].update(NUM_POPU_2016_2024_CONTINUITY="PROVEN"), "continuity")

    def test_rejects_every_forbidden_global_promotion(self):
        changes = {"release_0_8_0": "ACTIVE", "S1_NUM_POPU": "PROVEN", "S2_FINANCIAL_ALIAS_BRIDGE": "PROVEN", "annual_closure_status": "PROVEN", "semantic_comparability_status": "PROVEN", "closed_annual_series": "2016-2025", "gold_2025": "PROVEN", "year_2026": "PROVEN_CURRENT_YEAR"}
        for key, value in changes.items():
            with self.subTest(key=key):
                self.reject(lambda d, key=key, value=value: d["canonical_state"].update({key: value}), "global state")

    def test_rejects_network_effect_or_decision_changes(self):
        self.reject(lambda d: d["bounded_discovery"].update(siope_data_endpoint_call_count=1), "discovery")
        self.reject(lambda d: d["guards"].update(remote_writes=1), "guard")
        self.reject(lambda d: d.update(decision="PROVE_S1_NUM_POPU_CURRENT_2025"), "decision")


if __name__ == "__main__":
    unittest.main()
