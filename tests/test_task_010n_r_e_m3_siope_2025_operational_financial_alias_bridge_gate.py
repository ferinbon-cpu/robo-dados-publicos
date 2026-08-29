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
        self.assert_rejected(lambda f, e: f["aliases"][0].update(canonical_money="2241993843.28"), "raw observed alias")
        self.assert_rejected(lambda f, e: f["receita_siope"][0].update(value="2198860107.13"), "reconciliation failed")
        self.assert_rejected(lambda f, e: f["rreo_anexo_1"][2].update(value="1988819180.57"), "reconciliation failed")

    def test_rejects_float_or_non_cent_money(self):
        self.assert_rejected(lambda f, e: f["aliases"][0].update(canonical_money=2241993843.27), "decimal string")
        self.assert_rejected(lambda f, e: f["aliases"][0].update(canonical_money="2241993843.270"), "decimal string")

    def test_rejects_change_to_each_of_the_ten_real_education_rows(self):
        for index in range(10):
            with self.subTest(index=index):
                self.assert_rejected(lambda f, e, index=index: f["despesas_funcao_educacao_siope"][index].update(DE="0.00"), "official education row altered")

    def test_rejects_missing_duplicate_365_or_broken_component_subtotal_identity(self):
        self.assert_rejected(lambda f, e: f["despesas_funcao_educacao_siope"].pop(4), "ten exact education rows")
        self.assert_rejected(lambda f, e: f["despesas_funcao_educacao_siope"].append(copy.deepcopy(f["despesas_funcao_educacao_siope"][4])), "duplicate")
        self.assert_rejected(lambda f, e: f["despesas_funcao_educacao_siope"][6].update(DE="154882159.30"), "official education row altered")

    def test_rejects_double_counted_education_total(self):
        self.assert_rejected(lambda f, e: e["matrix"][7].update(reconciled_value="618648819.63"), "matrix evidence")

    def test_rejects_hierarchical_child_addition_or_variance_drift(self):
        self.assert_rejected(lambda f, e: f["dados_informados_consolidado_despesa"][1].update(hierarchy_role="PARENT_INCLUDE_ONCE"), "parent/child")
        self.assert_rejected(lambda f, e: f["dados_informados_consolidado_despesa"][0].update(DA="1000.01"), "hierarchical child")
        self.assert_rejected(lambda f, e: f["rreo_anexo_8_line_33"].update(DA="520398255.48"), "variance")
        self.assert_rejected(lambda f, e: f["dados_informados_consolidado_despesa_total"].update(canonical_money="526804985.20"), "consolidated DA total")
        self.assert_rejected(lambda f, e: f["dados_informados_consolidado_despesa_total"].update(raw_observed_value="526804985.20"), "consolidated DA total")

    def test_rejects_matrix_status_summary_or_state_promotion(self):
        self.assert_rejected(lambda f, e: e["matrix"][6].update(status="PROVEN_EXACT_RREO_EQUALITY"), "matrix evidence")
        self.assert_rejected(lambda f, e: e["summary"].update(PARTIAL=0), "summary")
        self.assert_rejected(lambda f, e: e["canonical_state"].update(semantic_comparability_status="PROVEN"), "bounded B2")
        self.assert_rejected(lambda f, e: e["canonical_state"].update(S1_NUM_POPU="PROVEN"), "bounded B2")
        self.assert_rejected(lambda f, e: e["canonical_state"].update(S2_FINANCIAL_ALIAS_BRIDGE="PROVEN"), "bounded B2")

    def test_rejects_cod_muni_type_and_every_other_forbidden_promotion(self):
        self.assert_rejected(lambda f, e: f["identity"].update(COD_MUNI="352690"), "identity")
        for field, value in (("annual_closure_status", "PROVEN"), ("gold_2025", "PROVEN"), ("release_0_8_0", "ACTIVE"), ("year_2026", "PROVEN")):
            with self.subTest(field=field):
                self.assert_rejected(lambda f, e, field=field, value=value: e["canonical_state"].update({field: value}), "bounded B2")

    def test_rejects_network_drive_publication_or_gold(self):
        for field, value in (("validator_network_requests", 1), ("drive_reads", 1), ("publication", True), ("gold_computation", True)):
            with self.subTest(field=field):
                self.assert_rejected(lambda f, e, field=field, value=value: f["provenance"].update({field: value}), "provenance")


if __name__ == "__main__":
    unittest.main()
