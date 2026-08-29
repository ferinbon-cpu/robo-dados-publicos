import copy
import json
import unittest

from scripts.github_task_010n_r_e_m3_siope_2025_operational_financial_alias_bridge_gate import EVIDENCE, FIXTURE, validate


class Task010NREM3OperationalFinancialAliasBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def assert_rejected(self, mutate, message):
        fixture, evidence = copy.deepcopy(self.fixture), copy.deepcopy(self.evidence)
        mutate(fixture, evidence)
        with self.assertRaisesRegex(ValueError, message):
            validate(fixture, evidence)

    def test_pinned_evidence_passes_and_has_ten_rows(self):
        matrix = validate(copy.deepcopy(self.fixture), copy.deepcopy(self.evidence))
        self.assertEqual(10, len(matrix))

    def test_rejects_identity_missing_duplicate_or_unexpected_stage(self):
        self.assert_rejected(lambda f, e: f["identity"].update(NUM_PERI=5), "identity")
        self.assert_rejected(lambda f, e: f["aliases"].append(copy.deepcopy(f["aliases"][0])), "duplicate")
        self.assert_rejected(lambda f, e: f["receita_siope"][0].update(stage="XX"), "missing or unexpected")
        self.assert_rejected(lambda f, e: f["rreo_anexo_1"].pop(), "missing or unexpected")

    def test_rejects_any_altered_alias_or_component_cent(self):
        self.assert_rejected(lambda f, e: f["aliases"][0].update(value="2241993843.28"), "alias value was altered")
        self.assert_rejected(lambda f, e: f["receita_siope"][0].update(value="2198860107.13"), "reconciliation failed")
        self.assert_rejected(lambda f, e: f["rreo_anexo_1"][2].update(value="1988819180.57"), "reconciliation failed")

    def test_rejects_float_or_non_cent_money(self):
        self.assert_rejected(lambda f, e: f["aliases"][0].update(value=2241993843.27), "decimal string")
        self.assert_rejected(lambda f, e: f["aliases"][0].update(value="2241993843.270"), "decimal string")

    def test_rejects_education_subtotal_double_count_contract_drift(self):
        self.assert_rejected(lambda f, e: f["despesas_funcao_educacao_siope"][1].update(row_role="INCLUDE"), "DES_SUBF=365")
        self.assert_rejected(lambda f, e: f["despesas_funcao_educacao_siope"][1].update(DE="463766660.31"), "DES_SUBF=365")

    def test_rejects_hierarchical_child_addition_or_variance_drift(self):
        self.assert_rejected(lambda f, e: f["dados_informados_consolidado_despesa"][1].update(hierarchy_role="PARENT_INCLUDE_ONCE"), "parent/child")
        self.assert_rejected(lambda f, e: f["dados_informados_consolidado_despesa"][0].update(DA="1000.01"), "hierarchical child")
        self.assert_rejected(lambda f, e: f["rreo_anexo_8_line_33"].update(DA="520398255.48"), "variance")

    def test_rejects_matrix_status_summary_or_state_promotion(self):
        self.assert_rejected(lambda f, e: e["matrix"][6].update(status="PROVEN_EXACT_RREO_EQUALITY"), "matrix evidence")
        self.assert_rejected(lambda f, e: e["summary"].update(PARTIAL=1), "summary")
        self.assert_rejected(lambda f, e: e["canonical_state"].update(semantic_comparability_status="PROVEN"), "bounded B2")
        self.assert_rejected(lambda f, e: e["canonical_state"].update(S1_NUM_POPU="PROVEN"), "bounded B2")

    def test_rejects_network_drive_publication_or_gold(self):
        for field, value in (("validator_network_requests", 1), ("drive_reads", 1), ("publication", True), ("gold_computation", True)):
            with self.subTest(field=field):
                self.assert_rejected(lambda f, e, field=field, value=value: f["provenance"].update({field: value}), "provenance")


if __name__ == "__main__":
    unittest.main()
