import unittest

from robo_dados_publicos.analytics.observatory_knowledge_pack import (
    Task183Stop,
    _dedupe_or_stop,
    _school_key,
    build_fused_products,
    build_knowledge_pack,
    fused_source_rows,
    metric_inventory,
    question_answerability,
    sample_packet_summaries,
    validate_contract,
)


GENERATED_AT = "2026-09-06T08:15:00-03:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask183ObservatoryKnowledgePack(unittest.TestCase):
    def products(self):
        return build_fused_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )

    def test_contract_covers_all_38_questions_and_15_domains(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["question_count"], 38)
        self.assertEqual(got["domain_count"], 15)
        self.assertGreaterEqual(got["recipe_count"], 20)
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["serving"])

    def test_fused_source_rows_are_exactly_current_materialized_blocks(self):
        got = fused_source_rows()
        self.assertEqual(got["source_block_counts"], {
            "TASK_180_SCHOOL": 798,
            "TASK_181_SCHOOL": 171,
            "TASK_181_FISCAL": 38,
            "TASK_182_SCHOOL": 48,
        })
        self.assertEqual(len(got["school_rows"]), 1017)
        self.assertEqual(len(got["fiscal_rows"]), 38)

    def test_fused_products_are_deterministic(self):
        a = self.products()
        b = self.products()
        self.assertEqual(a["SCHOOL_INDICATOR_SERIES"]["row_count"], 1017)
        self.assertEqual(a["FISCAL_SERIES"]["row_count"], 38)
        self.assertEqual(a["QUERY_PRODUCT_CATALOG"]["row_count"], 2)
        self.assertEqual(
            a["SCHOOL_INDICATOR_SERIES"]["snapshot_id"],
            b["SCHOOL_INDICATOR_SERIES"]["snapshot_id"],
        )
        self.assertEqual(
            a["FISCAL_SERIES"]["snapshot_id"],
            b["FISCAL_SERIES"]["snapshot_id"],
        )
        self.assertEqual(
            a["QUERY_PRODUCT_CATALOG"]["snapshot_id"],
            b["QUERY_PRODUCT_CATALOG"]["snapshot_id"],
        )

    def test_metric_inventory_has_36_school_metrics_plus_2_fiscal_metrics(self):
        got = metric_inventory(self.products())
        self.assertEqual(got["metric_count"], 38)
        school = {
            row["metric_id"]
            for row in got["metrics"]
            if row["product_name"] == "SCHOOL_INDICATOR_SERIES"
        }
        fiscal = {
            row["metric_id"]
            for row in got["metrics"]
            if row["product_name"] == "FISCAL_SERIES"
        }
        self.assertEqual(len(school), 36)
        self.assertEqual(fiscal, {
            "SIOPE_MDE_SHARE",
            "SIOPE_FUNDEB_REMUNERATION_SHARE",
        })
        self.assertIn("IDEB", school)
        self.assertIn("PPI_SHARE", school)
        self.assertIn("AEE_ROOM_AVAILABILITY_RATE", school)

    def test_conflicting_logical_school_key_fails_closed(self):
        row = {
            "scope_level": "SCHOOL",
            "scope_id": "35000001",
            "period": "2025",
            "indicator_id": "IDEB",
            "source_family": "IDEB",
            "value": 7.0,
            "provenance_ref": "A",
        }
        conflict = dict(row)
        conflict["value"] = 7.1
        with self.assertRaisesRegex(Task183Stop, "TASK183_TEST_CONFLICT"):
            _dedupe_or_stop(
                [row, conflict],
                key_fn=_school_key,
                code="TASK183_TEST",
            )

    def test_exact_duplicate_can_dedupe(self):
        row = {
            "scope_level": "SCHOOL",
            "scope_id": "35000001",
            "period": "2025",
            "indicator_id": "IDEB",
            "source_family": "IDEB",
            "value": 7.0,
            "provenance_ref": "A",
        }
        got = _dedupe_or_stop(
            [row, dict(row)],
            key_fn=_school_key,
            code="TASK183_TEST",
        )
        self.assertEqual(len(got), 1)

    def test_semantic_answerability_distinguishes_answerable_partial_route_source_and_gap(self):
        report = question_answerability(self.products())
        by_id = {row["question_id"]: row for row in report["questions"]}

        self.assertEqual(by_id["LEARN_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["LEARN_Q2"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["LEARN_Q3"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(by_id["TEACH_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["NETWORK_Q3"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["NETWORK_Q2"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(by_id["NETWORK_Q1"]["status"], "EXPLICIT_GAP")
        self.assertEqual(by_id["INFRA_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["INFRA_Q2"]["status"], "ROUTE_READY_PRODUCT_NOT_BUNDLED")
        self.assertEqual(by_id["EQUITY_Q1"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(by_id["EQUITY_Q2"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertEqual(by_id["FIN_Q1"]["status"], "ROUTE_READY_PRODUCT_NOT_BUNDLED")
        self.assertEqual(by_id["FIN_Q2"]["status"], "EXPLICIT_GAP")
        self.assertEqual(by_id["FIN_Q3"]["status"], "MATERIALIZED_PARTIAL")
        self.assertEqual(by_id["FIN_Q4"]["status"], "EXPLICIT_GAP")
        self.assertEqual(by_id["PLAN_Q1"]["status"], "SOURCE_READY_NOT_MATERIALIZED")
        self.assertEqual(by_id["PLAN_Q3"]["status"], "ROUTE_READY_PRODUCT_NOT_BUNDLED")
        self.assertEqual(by_id["ACC_Q1"]["status"], "ROUTE_READY_PRODUCT_NOT_BUNDLED")
        self.assertEqual(by_id["JOM_Q1"]["status"], "ROUTE_READY_PRODUCT_NOT_BUNDLED")
        self.assertEqual(by_id["TERR_Q1"]["status"], "EXPLICIT_GAP")
        self.assertEqual(by_id["CTRL_Q1"]["status"], "MATERIALIZED_ANSWERABLE")
        self.assertFalse(report["llm_may_fill_missing_numeric_evidence"])

    def test_product_presence_does_not_make_total_enrollment_answerable(self):
        report = question_answerability(self.products())
        q = next(row for row in report["questions"] if row["question_id"] == "NETWORK_Q1")
        self.assertEqual(q["status"], "EXPLICIT_GAP")
        self.assertIn("BASIC_EDUCATION_ENROLLMENT", q["missing_or_insufficient_metrics"])
        self.assertIn("CLASS_COUNT", q["missing_or_insufficient_metrics"])
        self.assertIn("SCHOOL_COUNT", q["missing_or_insufficient_metrics"])

    def test_short_full_time_series_is_partial_not_trend_answerable(self):
        report = question_answerability(self.products())
        q = next(row for row in report["questions"] if row["question_id"] == "NETWORK_Q2")
        self.assertEqual(q["status"], "MATERIALIZED_PARTIAL")
        signal = q["signal_results"][0]
        metric = signal["metrics"][0]
        self.assertEqual(metric["metric_id"], "FULL_TIME_SHARE")
        self.assertEqual(metric["period_count"], 1)
        self.assertEqual(metric["min_periods_required"], 2)

    def test_spending_per_student_remains_explicit_gap(self):
        report = question_answerability(self.products())
        q = next(row for row in report["questions"] if row["question_id"] == "FIN_Q2")
        self.assertEqual(q["status"], "EXPLICIT_GAP")
        self.assertIn("EDUCATION_EXPENDITURE", q["missing_or_insufficient_metrics"])
        self.assertIn("BASIC_EDUCATION_ENROLLMENT", q["missing_or_insufficient_metrics"])

    def test_planning_is_source_ready_but_not_falsely_bundled(self):
        report = question_answerability(self.products())
        q = next(row for row in report["questions"] if row["question_id"] == "PLAN_Q1")
        self.assertEqual(q["status"], "SOURCE_READY_NOT_MATERIALIZED")
        self.assertEqual(q["required_nonbundled_products"], ["PLANNING_DOCUMENT_INDEX"])

    def test_samples_produce_real_evidence_packets_from_fused_snapshots(self):
        products = self.products()
        samples = {row["sample_id"]: row for row in sample_packet_summaries(products)}
        self.assertEqual(set(samples), {
            "LEARNING_2025",
            "RAFAEL_EQUITY_2025",
            "FINANCING_2025",
        })
        self.assertGreater(samples["LEARNING_2025"]["numeric_record_count"], 0)
        self.assertGreater(samples["RAFAEL_EQUITY_2025"]["numeric_record_count"], 0)
        self.assertGreater(samples["FINANCING_2025"]["numeric_record_count"], 0)
        self.assertTrue(samples["LEARNING_2025"]["packet_id"].startswith("EVPK_"))

    def test_knowledge_pack_binds_products_inventory_answerability_and_missing_ledgers(self):
        pack = build_knowledge_pack(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        self.assertEqual(pack["schema"], "OBSERVATORY_EXISTING_CUSTODY_KNOWLEDGE_PACK_V1")
        self.assertEqual(pack["products"]["SCHOOL_INDICATOR_SERIES"]["row_count"], 1017)
        self.assertEqual(pack["products"]["FISCAL_SERIES"]["row_count"], 38)
        self.assertEqual(pack["metric_inventory"]["metric_count"], 38)
        self.assertEqual(pack["answerability"]["question_count"], 38)
        self.assertEqual(pack["answerability"]["domain_count"], 15)
        self.assertEqual(len(pack["sample_packet_summaries"]), 3)
        self.assertIn("TASK_180", pack["missing_ledgers"])
        self.assertIn("TASK_181", pack["missing_ledgers"])
        self.assertFalse(pack["remote_effects"]["network"])
        self.assertFalse(pack["remote_effects"]["drive_write"])
        self.assertFalse(pack["remote_effects"]["serving"])


if __name__ == "__main__":
    unittest.main()
