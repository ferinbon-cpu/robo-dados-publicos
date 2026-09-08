from __future__ import annotations

from decimal import Decimal
import unittest

from robo_dados_publicos.productization.document_event_context_execution import (
    execute_contextual_query_v3,
)
from robo_dados_publicos.productization.mixed_context_planner import (
    plan_contextual_query,
)
from robo_dados_publicos.productization.safe_local_mixed_execution import (
    execute_contextual_query_v4,
    load_contract,
    render_contextual_answer_v4,
    validate_contract,
)


GENERATED_AT = "2026-09-08T17:05:00+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask213SafeLocalMixedExecution(unittest.TestCase):
    def execute(self, text: str, **kwargs):
        return execute_contextual_query_v4(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )

    def plan(self, text: str, **kwargs):
        return plan_contextual_query(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )

    def test_contract_promotes_exactly_8_and_keeps_10_blocked(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["promoted_question_count"], 8)
        self.assertEqual(got["metadata_blocked_question_count"], 10)
        self.assertEqual(got["planner_gate"], "READY_FOR_SAFE_EXECUTOR_DESIGN")
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_read"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["llm"])
        contract = load_contract()
        self.assertEqual(
            set(contract["promoted_questions"]),
            {
                "CTRL_Q1",
                "CTRL_Q3",
                "EQUITY_Q1",
                "FIN_Q2",
                "FIN_Q4",
                "TEACH_Q2",
                "TERR_Q1",
                "TERR_Q2",
            },
        )
        self.assertTrue(
            set(contract["promoted_questions"]).isdisjoint(
                set(contract["metadata_blocked_questions"])
            )
        )

    def test_fin_q2_2025_answers_exact_ratio_only_after_planner_gate(self):
        got = self.execute("quanto por aluno em 2025?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "FIN_Q2")
        by_kind = {row["kind"]: row for row in got["NUMBER_OR_FACT"]}
        self.assertEqual(
            Decimal(by_kind["SPENDING_PER_STUDENT_NUMERATOR"]["value_brl"]),
            Decimal("463766660.32"),
        )
        self.assertEqual(
            by_kind["SPENDING_PER_STUDENT_DENOMINATOR"]["value"],
            22788,
        )
        ratio = by_kind["SPENDING_PER_ENROLLMENT_DERIVED"]
        self.assertEqual(Decimal(ratio["value_brl_per_enrollment"]), Decimal("20351.35"))
        self.assertEqual(ratio["formula"], "EDUCATION_EXPENDITURE / BASIC_EDUCATION_ENROLLMENT")
        self.assertTrue(ratio["same_annual_period_verified"])
        self.assertFalse(ratio["individual_student_cost_claim"])
        planner = [
            row for row in got["SOURCE_AND_PROVENANCE"]
            if row.get("product") == "TASK212_MIXED_CONTEXT_PLANNER"
        ]
        self.assertEqual(len(planner), 1)
        self.assertEqual(planner[0]["join_mode"], "SAFE_RATIO_ALIGNMENT")
        self.assertFalse(got["numeric_invention_performed"])

    def test_fin_q2_without_period_uses_latest_exact_common_annual_period(self):
        got = self.execute("quanto por aluno?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "FIN_Q2")
        self.assertEqual(got["TIME_REFERENCE"], ["2025"])
        ratio = next(
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "SPENDING_PER_ENROLLMENT_DERIVED"
        )
        self.assertEqual(ratio["period"], "2025")

    def test_fin_q2_school_specific_is_blocked_cross_grain(self):
        got = self.execute("quanto por aluno no Rafael Affonso Leite em 2025?")
        self.assertEqual(got["question_id"], "FIN_Q2")
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertEqual(
            got["filter_accounting"]["SCHOOL"]["status"],
            "BLOCKED_BY_TASK212_PLANNER",
        )
        self.assertIn("TASK212_PLANNER_GATE_ENFORCED", got["CAUTION_OR_LIMIT"])
        encoded = str(got)
        self.assertNotIn("20351.35", encoded)

    def test_fin_q2_2026_does_not_use_partial_2026_04_as_annual(self):
        got = self.execute("quanto por aluno em 2026?")
        self.assertEqual(got["question_id"], "FIN_Q2")
        self.assertEqual(got["state"], "EXPLICIT_CONTEXT_GAP")
        self.assertIn("TASK212_PLANNER_GATE_ENFORCED", got["CAUTION_OR_LIMIT"])
        encoded = str(got)
        self.assertNotIn("20351.35", encoded)
        self.assertNotIn("BRL_PER_ENROLLMENT", encoded)

    def test_fin_q4_2025_returns_exact_nominal_real_pair(self):
        got = self.execute("valor nominal e real em 2025")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "FIN_Q4")
        pairs = [
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "NOMINAL_REAL_ANNUAL_PAIR"
        ]
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["period"], "2025")
        self.assertEqual(Decimal(pairs[0]["nominal_brl"]), Decimal("463766660.32"))
        self.assertEqual(
            Decimal(pairs[0]["real_brl_dec_2025_equivalent"]),
            Decimal("463766660.32"),
        )
        self.assertEqual(got["COMPARISON_OR_TREND"], [])
        self.assertIn("SINGLE_YEAR_SNAPSHOT_NE_MULTIYEAR_TREND", got["CAUTION_OR_LIMIT"])

    def test_fin_q4_without_period_returns_common_annual_series_and_exact_trend(self):
        got = self.execute("valor nominal e real")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "FIN_Q4")
        pairs = [
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "NOMINAL_REAL_ANNUAL_PAIR"
        ]
        self.assertEqual([row["period"] for row in pairs], [str(y) for y in range(2016, 2026)])
        trend = next(
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "NOMINAL_REAL_FIRST_TO_LAST_TREND"
        )
        self.assertEqual(trend["first_period"], "2016")
        self.assertEqual(trend["last_period"], "2025")
        self.assertEqual(Decimal(trend["nominal_change_pct"]), Decimal("115.36"))
        self.assertEqual(Decimal(trend["real_change_pct"]), Decimal("38.91"))
        self.assertNotIn("2026", got["TIME_REFERENCE"])

    def test_teach_q2_2025_returns_stock_bonds_and_parallel_jom_only(self):
        got = self.execute("quantos profissionais e vínculos existem em 2025?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "TEACH_Q2")
        stock = next(row for row in got["NUMBER_OR_FACT"] if row["kind"] == "WORKFORCE_STOCK")
        bonds = next(row for row in got["NUMBER_OR_FACT"] if row["kind"] == "EMPLOYMENT_BOND_COUNTS")
        parallel = next(
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "JOM_PERSONNEL_PARALLEL_EVIDENCE"
        )
        self.assertEqual(stock["value"], 1280)
        self.assertFalse(stock["all_education_workers_claim"])
        self.assertEqual(
            bonds["bond_counts"],
            {
                "CONCURSADO_EFETIVO_ESTAVEL": 681,
                "CONTRATO_TEMPORARIO": 291,
                "CONTRATO_TERCEIRIZADO": 0,
                "CONTRATO_CLT": 400,
            },
        )
        self.assertFalse(bonds["categories_additive"])
        self.assertFalse(parallel["row_level_join_to_workforce_stock"])
        self.assertIn("BOND_COUNTS_NON_ADDITIVE", got["CAUTION_OR_LIMIT"])
        self.assertIn("JOM_PERSONNEL_EVENT_NE_WORKFORCE_STOCK", got["CAUTION_OR_LIMIT"])

    def test_teach_q2_2026_does_not_substitute_2025_or_sme_current_snapshot(self):
        got = self.execute("quantos profissionais e vínculos existem em 2026?")
        self.assertEqual(got["question_id"], "TEACH_Q2")
        self.assertEqual(got["state"], "EXPLICIT_CONTEXT_GAP")
        encoded = str(got)
        self.assertNotIn("'kind': 'WORKFORCE_STOCK'", encoded)
        self.assertNotIn("842 professores", encoded)

    def test_task212_equity_plan_allows_parallel_2022_territory_for_2025_school_metrics(self):
        got = self.plan("desigualdade por contexto social no Rafael Affonso Leite em 2025")
        self.assertEqual(got["question_id"], "EQUITY_Q1")
        self.assertEqual(got["planning_state"], "READY_FOR_SAFE_EXECUTOR_DESIGN")
        territory = next(row for row in got["signals"] if row["product"] == "TERRITORY_PROFILE")
        self.assertEqual(
            territory["context_inventory"]["period_role"],
            "PARALLEL_CONTEXT_PERIOD",
        )
        self.assertEqual(territory["context_inventory"]["observed_periods"], ["2022"])
        self.assertFalse(territory["context_inventory"]["requested_year_relabelled"])

    def test_equity_q1_linked_school_2025_keeps_school_and_territory_periods_separate(self):
        got = self.execute("desigualdade por contexto social no Rafael Affonso Leite em 2025")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "EQUITY_Q1")
        school_metrics = [
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "EQUITY_SCHOOL_OR_NETWORK_METRIC"
        ]
        self.assertEqual(
            {row["metric_id"] for row in school_metrics},
            {"PPI_SHARE", "INSE", "SPECIAL_EDUCATION_ENROLLMENT"},
        )
        self.assertTrue(all(row["period"] == "2025" for row in school_metrics))
        territory = [
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "TERRITORY_METRIC"
        ]
        self.assertEqual(len(territory), 4)
        self.assertTrue(all(row["school_code"] == "35470600" for row in territory))
        self.assertTrue(all(row["period"] == "2022" for row in territory))
        self.assertTrue(
            all(row["period_role"] == "PARALLEL_TERRITORIAL_CONTEXT_PERIOD" for row in territory)
        )
        self.assertEqual(set(got["TIME_REFERENCE"]), {"2025", "2022"})
        self.assertIn("SECTOR_INCOME_NE_STUDENT_HOUSEHOLD_INCOME", got["CAUTION_OR_LIMIT"])

    def test_equity_q1_held_school_preserves_explicit_missingness_without_weak_sector(self):
        plan = self.plan("desigualdade por contexto social no Ismael Pereira Lago em 2025")
        self.assertEqual(plan["question_id"], "EQUITY_Q1")
        self.assertEqual(plan["planning_state"], "READY_FOR_SAFE_EXECUTOR_DESIGN")
        self.assertEqual(
            plan["join_plan"]["status"],
            "SAFE_WITH_EXPLICIT_TERRITORY_MISSINGNESS",
        )
        got = self.execute("desigualdade por contexto social no Ismael Pereira Lago em 2025")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        missing = [
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "EXPLICIT_TERRITORY_MISSINGNESS"
        ]
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]["school_code"], "35208437")
        self.assertFalse(missing[0]["weak_substitution_performed"])
        self.assertFalse(
            any(
                row.get("kind") == "TERRITORY_METRIC"
                and row.get("school_code") == "35208437"
                for row in got["NUMBER_OR_FACT"]
            )
        )

    def test_terr_q1_rafael_returns_exact_2022_school_location_sector_context(self):
        got = self.execute("contexto socioeconomico do territorio do Rafael Affonso Leite")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "TERR_Q1")
        territory = [row for row in got["NUMBER_OR_FACT"] if row["kind"] == "TERRITORY_METRIC"]
        self.assertEqual(len(territory), 4)
        self.assertTrue(all(row["school_code"] == "35470600" for row in territory))
        self.assertTrue(all(row["period"] == "2022" for row in territory))
        self.assertEqual(got["TIME_REFERENCE"], ["2022"])

    def test_terr_q1_held_school_is_explicit_gap_not_weak_geocoding(self):
        got = self.execute("contexto socioeconomico do territorio do Ismael Pereira Lago")
        self.assertEqual(got["question_id"], "TERR_Q1")
        self.assertEqual(got["state"], "EXPLICIT_CONTEXT_GAP")
        self.assertIn("TASK212_PLANNER_GATE_ENFORCED", got["CAUTION_OR_LIMIT"])
        self.assertNotIn("TERRITORY_METRIC", str(got))

    def test_terr_q1_requested_2025_does_not_relabel_2022(self):
        got = self.execute("contexto socioeconomico do territorio do Rafael Affonso Leite em 2025")
        self.assertEqual(got["question_id"], "TERR_Q1")
        self.assertEqual(got["state"], "EXPLICIT_CONTEXT_GAP")
        self.assertNotIn("TERRITORY_METRIC", str(got))

    def test_terr_q2_school_comparison_is_sector_semantic_not_student_income(self):
        got = self.execute("comparacoes territoriais do Rafael Affonso Leite")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "TERR_Q2")
        supported = [
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "SUPPORTED_TERRITORIAL_COMPARISON"
        ]
        self.assertEqual(len(supported), 1)
        self.assertFalse(supported[0]["student_household_claim"])
        self.assertIn("SECTOR_INCOME_NE_STUDENT_HOUSEHOLD_INCOME", got["CAUTION_OR_LIMIT"])

    def test_ctrl_q1_exposes_metadata_only_local_payload_boundary(self):
        got = self.execute("fontes completas bloqueadas ou desatualizadas")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "CTRL_Q1")
        by_product = {
            row["product"]: row
            for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "PRODUCT_PAYLOAD_STATUS"
        }
        self.assertEqual(len(by_product), 8)
        for name, declared in (("ACCOUNTING_LEDGER", 39783), ("REVENUE_LEDGER", 2286)):
            row = by_product[name]
            self.assertEqual(row["declared_row_count"], declared)
            self.assertEqual(row["local_row_count"], 0)
            self.assertEqual(row["payload_state"], "METADATA_ONLY_REMOTE_SNAPSHOT")
            self.assertEqual(row["catalog_readiness"], "READY_WITH_CAUTION")
            self.assertFalse(row["catalog_readiness_overrides_payload_truth"])
        self.assertFalse(by_product["ACCOUNTING_LEDGER"]["generated_at_proves_source_freshness"])

    def test_ctrl_q3_never_promotes_metadata_only_to_numeric_evidence(self):
        got = self.execute("forca da evidencia")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "CTRL_Q3")
        by_product = {
            row["product"]: row
            for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "PRODUCT_EVIDENCE_STRENGTH"
        }
        self.assertEqual(
            by_product["ACCOUNTING_LEDGER"]["strength"],
            "METADATA_ONLY_REMOTE_SNAPSHOT",
        )
        self.assertEqual(
            by_product["REVENUE_LEDGER"]["strength"],
            "METADATA_ONLY_REMOTE_SNAPSHOT",
        )
        self.assertFalse(
            by_product["ACCOUNTING_LEDGER"]["numeric_truth_from_metadata_only_allowed"]
        )
        self.assertEqual(
            by_product["QUERY_PRODUCT_CATALOG"]["strength"],
            "LOCAL_DERIVED_CATALOG",
        )

    def test_control_inventory_rejects_period_filter_instead_of_dropping_it(self):
        got = self.execute("forca da evidencia em 2025")
        self.assertEqual(got["question_id"], "CTRL_Q3")
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertEqual(got["filter_accounting"]["PERIOD"]["status"], "UNSUPPORTED")

    def test_existing_task209_special_is_delegated_exactly(self):
        text = "Quanto a Educação gastou até julho deste ano?"
        kwargs = {"reference_date": "2026-09-08"}
        a = self.execute(text, **kwargs)
        b = execute_contextual_query_v3(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )
        self.assertEqual(a, b)
        self.assertEqual(a["question_id"], "FIN_Q1")

    def test_existing_task210_metric_is_delegated_exactly(self):
        text = "infraestrutura da escola Rafael Affonso Leite em 2025"
        a = self.execute(text)
        b = execute_contextual_query_v3(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(a, b)
        self.assertEqual(a["question_id"], "INFRA_Q1")

    def test_existing_task211_document_event_is_delegated_exactly(self):
        text = "nomeações e exonerações em 2026"
        a = self.execute(text)
        b = execute_contextual_query_v3(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(a, b)
        self.assertEqual(a["question_id"], "PERS_Q1")

    def test_metadata_blocked_accounting_question_remains_prior_behavior(self):
        text = "empenhado liquidado e pago em 2026"
        a = self.execute(text)
        b = execute_contextual_query_v3(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(a, b)
        self.assertEqual(a["question_id"], "ACC_Q1")

    def test_renderer_uses_existing_contextual_answer_contract(self):
        answer = self.execute("quanto por aluno em 2025?")
        rendered = render_contextual_answer_v4(answer)
        self.assertEqual(rendered["question_id"], "FIN_Q2")
        self.assertIn("20351.35", rendered["markdown"])
        self.assertIn("## Filtros contextuais", rendered["markdown"])

    def test_outputs_are_deterministic(self):
        for text in (
            "quanto por aluno em 2025?",
            "valor nominal e real",
            "quantos profissionais e vínculos existem em 2025?",
            "fontes completas bloqueadas ou desatualizadas",
        ):
            a = self.execute(text)
            b = self.execute(text)
            self.assertEqual(a, b)
            self.assertEqual(len(a["answer_sha256"]), 64)
            self.assertFalse(a["llm_used"])
            self.assertTrue(all(v is False for v in a["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
