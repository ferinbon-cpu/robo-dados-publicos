from __future__ import annotations

import unittest

from robo_dados_publicos.productization.mixed_context_planner import (
    build_remaining_question_planning_matrix,
    plan_contextual_query,
    plan_question,
    product_payload_inventory,
    validate_contract,
)


GENERATED_AT = "2026-09-08T16:20:00+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask212MixedContextPlanner(unittest.TestCase):
    def plan(self, text: str, **kwargs):
        return plan_contextual_query(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )

    def test_contract_and_baseline_partition(self):
        got = validate_contract(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["remaining_question_count"], 18)
        self.assertEqual(got["baseline_ready_count"], 8)
        self.assertEqual(got["baseline_metadata_blocked_count"], 10)
        self.assertEqual(got["accounting_payload_state"], "METADATA_ONLY")
        self.assertEqual(got["revenue_payload_state"], "METADATA_ONLY")
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_read"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["llm"])

    def test_current_payload_truth_distinguishes_local_rows_from_metadata_shells(self):
        rows = {
            row["product"]: row
            for row in product_payload_inventory(
                generated_at=GENERATED_AT,
                software_version=SOFTWARE_VERSION,
            )
        }
        self.assertEqual(rows["ACCOUNTING_LEDGER"]["payload_state"], "METADATA_ONLY")
        self.assertEqual(rows["ACCOUNTING_LEDGER"]["local_row_count"], 0)
        self.assertEqual(rows["ACCOUNTING_LEDGER"]["declared_row_count"], 39783)
        self.assertEqual(rows["REVENUE_LEDGER"]["payload_state"], "METADATA_ONLY")
        self.assertEqual(rows["REVENUE_LEDGER"]["local_row_count"], 0)
        self.assertEqual(rows["REVENUE_LEDGER"]["declared_row_count"], 2286)
        for name in (
            "SCHOOL_INDICATOR_SERIES",
            "FISCAL_SERIES",
            "JOM_EVENT_INDEX",
            "PLANNING_DOCUMENT_INDEX",
            "TERRITORY_PROFILE",
            "QUERY_PRODUCT_CATALOG",
        ):
            self.assertEqual(rows[name]["payload_state"], "LOCAL_ROWS_PRESENT")
            self.assertGreater(rows[name]["local_row_count"], 0)

    def test_remaining_18_partition_is_exact(self):
        matrix = build_remaining_question_planning_matrix(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(matrix["question_count"], 18)
        self.assertEqual(
            matrix["planning_state_counts"],
            {
                "BLOCKED_METADATA_ONLY": 10,
                "READY_FOR_SAFE_EXECUTOR_DESIGN": 8,
            },
        )
        by_state = {}
        for row in matrix["questions"]:
            by_state.setdefault(row["planning_state"], set()).add(row["question_id"])
            self.assertFalse(row["numeric_answer_created"])
            self.assertFalse(row["execution_class_promoted"])

        self.assertEqual(
            by_state["READY_FOR_SAFE_EXECUTOR_DESIGN"],
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
        self.assertEqual(
            by_state["BLOCKED_METADATA_ONLY"],
            {
                "ACC_Q1",
                "ACC_Q2",
                "ACC_Q3",
                "CTRL_Q2",
                "FIN_Q3",
                "INFRA_Q2",
                "PLAN_Q3",
                "PROC_Q1",
                "PROC_Q2",
                "PROC_Q3",
            },
        )

    def test_fin_q2_2025_is_safe_ratio_alignment_plan_only(self):
        got = self.plan("quanto por aluno em 2025?")
        self.assertEqual(got["question_id"], "FIN_Q2")
        self.assertEqual(got["planning_state"], "READY_FOR_SAFE_EXECUTOR_DESIGN")
        self.assertEqual(
            [row["signal_state"] for row in got["signals"]],
            ["LOCAL_EXECUTABLE", "LOCAL_EXECUTABLE"],
        )
        join = got["join_plan"]
        self.assertEqual(join["mode"], "SAFE_RATIO_ALIGNMENT")
        self.assertEqual(join["status"], "SAFE_FOR_EXECUTOR_DESIGN")
        self.assertIn("2025", join["common_exact_annual_periods"])
        self.assertEqual(join["numerator_scope"], "MUNICIPAL_ENTITY")
        self.assertEqual(join["denominator_scope"], "NETWORK")
        self.assertFalse(join["period_prefix_match_is_sufficient"])
        self.assertFalse(join["partial_period_may_equal_annual_period"])
        self.assertFalse(join["numeric_ratio_computed"])
        self.assertFalse(got["numeric_answer_created"])

    def test_fin_q2_school_specific_cross_grain_ratio_is_blocked(self):
        got = self.plan("quanto por aluno no Rafael Affonso Leite em 2025?")
        self.assertEqual(got["question_id"], "FIN_Q2")
        self.assertEqual(got["planning_state"], "CONTEXT_INCOMPATIBLE")
        fiscal = next(row for row in got["signals"] if row["product"] == "FISCAL_SERIES")
        self.assertEqual(fiscal["signal_state"], "CONTEXT_INCOMPATIBLE")
        self.assertEqual(fiscal["reason"], "FISCAL_SERIES_HAS_NO_STRUCTURED_SCHOOL_GRAIN")
        self.assertEqual(got["join_plan"]["mode"], "SAFE_RATIO_ALIGNMENT")
        self.assertEqual(got["join_plan"]["status"], "BLOCKED_CROSS_GRAIN")
        self.assertFalse(got["join_plan"]["identity_created"])
        self.assertFalse(got["join_plan"]["weak_join_used"])
        self.assertFalse(got["numeric_answer_created"])

    def test_fin_q3_is_blocked_by_revenue_metadata_shell(self):
        got = self.plan("quanto veio do Fundeb e de transferências em 2025?")
        self.assertEqual(got["question_id"], "FIN_Q3")
        self.assertEqual(got["planning_state"], "BLOCKED_METADATA_ONLY")
        fiscal = next(row for row in got["signals"] if row["product"] == "FISCAL_SERIES")
        revenue = next(row for row in got["signals"] if row["product"] == "REVENUE_LEDGER")
        self.assertEqual(fiscal["signal_state"], "LOCAL_EXECUTABLE")
        self.assertEqual(revenue["signal_state"], "METADATA_ONLY")
        self.assertFalse(revenue["context_inventory"]["row_filtering_authorized"])
        self.assertGreater(len(revenue["context_inventory"]["metadata_capabilities"]), 0)
        self.assertFalse(got["numeric_answer_created"])

    def test_accounting_question_is_metadata_only_not_locally_filterable(self):
        got = self.plan("quanto foi empenhado, liquidado e pago em 2026?")
        self.assertEqual(got["question_id"], "ACC_Q1")
        self.assertEqual(got["planning_state"], "BLOCKED_METADATA_ONLY")
        self.assertEqual(len(got["signals"]), 1)
        signal = got["signals"][0]
        self.assertEqual(signal["product"], "ACCOUNTING_LEDGER")
        self.assertEqual(signal["signal_state"], "METADATA_ONLY")
        self.assertEqual(signal["local_row_count"], 0)
        self.assertFalse(signal["context_inventory"]["row_filtering_authorized"])
        self.assertFalse(got["numeric_answer_created"])

    def test_fin_q4_2025_same_product_nominal_real_alignment_is_safe(self):
        got = self.plan("valor nominal e real em 2025")
        self.assertEqual(got["question_id"], "FIN_Q4")
        self.assertEqual(got["planning_state"], "READY_FOR_SAFE_EXECUTOR_DESIGN")
        self.assertTrue(all(row["signal_state"] == "LOCAL_EXECUTABLE" for row in got["signals"]))
        join = got["join_plan"]
        self.assertEqual(join["mode"], "SAME_PRODUCT_SERIES_ALIGNMENT")
        self.assertEqual(join["status"], "SAFE_FOR_EXECUTOR_DESIGN")
        self.assertIn("2025", join["common_exact_annual_periods"])
        self.assertTrue(join["exact_entity_and_period_required"])
        self.assertFalse(join["nominal_equals_real"])
        self.assertFalse(got["numeric_answer_created"])

    def test_fin_q4_month_context_is_fail_closed(self):
        got = self.plan("valor nominal e real em abril de 2025")
        self.assertEqual(got["question_id"], "FIN_Q4")
        self.assertEqual(got["planning_state"], "CONTEXT_INCOMPATIBLE")
        self.assertTrue(
            any(
                row["signal_state"] == "CONTEXT_INCOMPATIBLE"
                and row["reason"] == "TASK212_PLANNER_SUPPORTS_EXACT_YEAR_ONLY"
                for row in got["signals"]
            )
        )
        self.assertFalse(got["numeric_answer_created"])

    def test_fin_q2_2026_does_not_treat_partial_fiscal_period_as_annual(self):
        got = self.plan("quanto por aluno em 2026?")
        self.assertEqual(got["question_id"], "FIN_Q2")
        self.assertNotEqual(got["planning_state"], "READY_FOR_SAFE_EXECUTOR_DESIGN")
        self.assertEqual(got["join_plan"]["mode"], "SAFE_RATIO_ALIGNMENT")
        self.assertNotIn("2026", got["join_plan"]["common_exact_annual_periods"])
        self.assertFalse(got["join_plan"]["partial_period_may_equal_annual_period"])
        self.assertFalse(got["numeric_answer_created"])

    def test_teach_q2_join_is_parallel_evidence_only(self):
        got = plan_question(
            "TEACH_Q2",
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(got["planning_state"], "READY_FOR_SAFE_EXECUTOR_DESIGN")
        self.assertEqual(got["join_plan"]["mode"], "PARALLEL_EVIDENCE_ONLY")
        self.assertFalse(got["join_plan"]["row_level_join_allowed"])
        self.assertFalse(got["join_plan"]["jom_personnel_event_equals_workforce_stock"])
        self.assertFalse(got["join_plan"]["identity_created"])

    def test_equity_join_never_turns_sector_income_into_student_income(self):
        got = plan_question(
            "EQUITY_Q1",
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(got["planning_state"], "READY_FOR_SAFE_EXECUTOR_DESIGN")
        self.assertEqual(
            got["join_plan"]["mode"],
            "EXACT_SCHOOL_CODE_OR_PARALLEL_CONTEXT",
        )
        self.assertFalse(got["join_plan"]["sector_income_equals_student_household_income"])
        self.assertFalse(got["join_plan"]["weak_join_used"])

    def test_territory_and_catalog_questions_are_locally_plannable_but_not_promoted(self):
        for qid in ("TERR_Q1", "TERR_Q2", "CTRL_Q1", "CTRL_Q3"):
            got = plan_question(
                qid,
                generated_at=GENERATED_AT,
                software_version=SOFTWARE_VERSION,
            )
            self.assertEqual(got["planning_state"], "READY_FOR_SAFE_EXECUTOR_DESIGN")
            self.assertEqual(got["join_plan"]["mode"], "NO_JOIN_REQUIRED")
            self.assertFalse(got["numeric_answer_created"])
            self.assertFalse(got["execution_class_promoted"])

    def test_existing_task211_executor_is_preserved_and_not_replanned(self):
        got = self.plan("decreto sobre escola em 2024")
        self.assertEqual(got["question_id"], "NORMS_Q1")
        self.assertEqual(got["planning_state"], "UPSTREAM_CONTEXT_EXECUTOR_AVAILABLE")
        self.assertEqual(got["upstream_execution_class"], "GENERIC_LOCAL_DOCUMENT_EVENT")
        self.assertEqual(got["signals"], [])
        self.assertEqual(got["join_plan"]["mode"], "UPSTREAM_OWNS_EXECUTION")

    def test_existing_task210_metric_executor_is_preserved(self):
        got = self.plan("infraestrutura da escola Rafael Affonso Leite em 2025")
        self.assertEqual(got["question_id"], "INFRA_Q1")
        self.assertEqual(got["planning_state"], "UPSTREAM_CONTEXT_EXECUTOR_AVAILABLE")
        self.assertEqual(got["upstream_execution_class"], "GENERIC_LOCAL_SCHOOL_METRIC")

    def test_existing_task209_special_executor_is_preserved(self):
        got = self.plan("Quanto a Educação gastou até abril de 2026?")
        self.assertEqual(got["question_id"], "FIN_Q1")
        self.assertEqual(got["planning_state"], "UPSTREAM_CONTEXT_EXECUTOR_AVAILABLE")
        self.assertEqual(got["upstream_execution_class"], "TASK209_SPECIAL")

    def test_plan_hash_is_deterministic(self):
        a = self.plan("quanto por aluno em 2025?")
        b = self.plan("quanto por aluno em 2025?")
        self.assertEqual(a, b)
        self.assertEqual(len(a["plan_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
