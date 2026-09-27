import unittest

from robo_dados_publicos.analytics.current_observatory_bundle import (
    CANONICAL_PRODUCT_SET,
    build_current_bundle,
)
from robo_dados_publicos.productization.question_readiness import (
    build_current_productization_audit,
    load_contract,
)


GENERATED_AT = "2026-09-08T01:24:18+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask203CurrentBundleProductization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = build_current_bundle(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        cls.audit = build_current_productization_audit(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        cls.by_question = {
            row["question_id"]: row
            for row in cls.audit["questions"]
        }

    def test_contract_is_offline_and_separates_answerability_from_renderability(self):
        contract = load_contract()
        self.assertTrue(all(v is False for v in contract["remote_effects"].values()))
        self.assertFalse(contract["payload_boundaries"]["capability_metadata_may_supply_numeric_value"])
        self.assertFalse(contract["payload_boundaries"]["semantic_answerability_equals_human_ready_answer"])

    def test_production_bundle_is_canonical_eight_products_and_38_of_38(self):
        self.assertEqual(set(self.bundle["products"]), CANONICAL_PRODUCT_SET)
        self.assertEqual(self.bundle["product_count"], 8)
        self.assertEqual(
            self.bundle["answerability"]["status_counts"],
            {"MATERIALIZED_ANSWERABLE": 38},
        )
        self.assertEqual(self.bundle["answerability"]["question_count"], 38)
        self.assertFalse(self.bundle["semantics"]["capability_metadata_may_supply_numeric_value"])

    def test_remote_ledger_payload_boundaries_are_explicit(self):
        inventory = {
            row["product_name"]: row
            for row in self.bundle["payload_inventory"]
        }
        accounting = inventory["ACCOUNTING_LEDGER"]
        revenue = inventory["REVENUE_LEDGER"]
        self.assertEqual(accounting["declared_row_count"], 39783)
        self.assertEqual(accounting["local_row_count"], 0)
        self.assertEqual(accounting["payload_state"], "REMOTE_SNAPSHOT_METADATA_ONLY")
        self.assertTrue(accounting["remote_snapshot_drive_id"])
        self.assertEqual(revenue["declared_row_count"], 2286)
        self.assertEqual(revenue["local_row_count"], 0)
        self.assertEqual(revenue["payload_state"], "REMOTE_SNAPSHOT_METADATA_ONLY")
        self.assertTrue(revenue["remote_snapshot_drive_id"])

    def test_productization_readiness_is_27_record_8_mixed_3_capability_only(self):
        self.assertEqual(
            self.audit["productization_counts"],
            {
                "CAPABILITY_ONLY": 3,
                "MIXED_RECORD_AND_CAPABILITY": 8,
                "RECORD_BACKED": 27,
            },
        )
        self.assertEqual(self.audit["human_ready_count"], 27)
        self.assertEqual(self.audit["query_projection_backlog_count"], 11)
        self.assertEqual(
            set(self.audit["query_projection_backlog_questions"]),
            {
                "INFRA_Q2",
                "FIN_Q1",
                "FIN_Q3",
                "PLAN_Q3",
                "PROC_Q1",
                "PROC_Q2",
                "PROC_Q3",
                "CTRL_Q2",
                "ACC_Q1",
                "ACC_Q2",
                "ACC_Q3",
            },
        )

    def test_accounting_questions_are_not_falsely_human_ready(self):
        for qid in ("ACC_Q1", "ACC_Q2", "ACC_Q3"):
            row = self.by_question[qid]
            self.assertEqual(row["semantic_status"], "MATERIALIZED_ANSWERABLE")
            self.assertEqual(row["productization_status"], "CAPABILITY_ONLY")
            self.assertFalse(row["human_answer_ready"])
            self.assertTrue(row["signal_traces"])
            self.assertTrue(
                all(trace["backing"] == "CAPABILITY_METADATA_ONLY" for trace in row["signal_traces"])
            )
            self.assertTrue(
                all(trace["local_record_count"] == 0 for trace in row["signal_traces"])
            )
            self.assertTrue(
                all(trace["remote_snapshot_drive_id"] for trace in row["signal_traces"])
            )

    def test_mixed_questions_require_both_local_records_and_remote_projection(self):
        for qid in ("INFRA_Q2", "FIN_Q1", "FIN_Q3", "PLAN_Q3", "PROC_Q1", "PROC_Q2", "PROC_Q3", "CTRL_Q2"):
            row = self.by_question[qid]
            self.assertEqual(row["productization_status"], "MIXED_RECORD_AND_CAPABILITY")
            self.assertFalse(row["human_answer_ready"])
            backings = {trace["backing"] for trace in row["signal_traces"]}
            self.assertEqual(backings, {"LOCAL_RECORDS", "CAPABILITY_METADATA_ONLY"})

    def test_record_backed_questions_have_no_capability_only_signal(self):
        ready = [
            row for row in self.audit["questions"]
            if row["productization_status"] == "RECORD_BACKED"
        ]
        self.assertEqual(len(ready), 27)
        self.assertTrue(all(row["human_answer_ready"] for row in ready))
        for row in ready:
            self.assertTrue(
                all(trace["backing"] == "LOCAL_RECORDS" for trace in row["signal_traces"])
            )

    def test_all_38_questions_have_deterministic_query_envelopes_without_product_gaps(self):
        self.assertEqual(len(self.audit["questions"]), 38)
        for row in self.audit["questions"]:
            self.assertTrue(row["query_packet_id"].startswith("EVPK_"))
            self.assertEqual(len(row["query_packet_sha256"]), 64)
            self.assertEqual(row["query_product_gap_count"], 0)
            self.assertEqual(row["semantic_status"], "MATERIALIZED_ANSWERABLE")

    def test_no_remote_effect_is_enabled(self):
        self.assertTrue(all(v is False for v in self.bundle["remote_effects"].values()))
        self.assertTrue(all(v is False for v in self.audit["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
