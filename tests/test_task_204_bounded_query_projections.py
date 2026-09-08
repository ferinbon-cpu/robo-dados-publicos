import json
import unittest

from robo_dados_publicos.analytics.current_observatory_bundle import (
    build_current_products,
)
from robo_dados_publicos.productization.bounded_query_projections import (
    build_renderable_packet,
    build_task204_renderability_audit,
    load_contract,
    projection_views_for_question,
    validate_projection_values,
)


GENERATED_AT = "2026-09-08T01:40:00+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask204BoundedQueryProjections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.products = build_current_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        cls.audit = build_task204_renderability_audit(cls.products)

    def test_source_snapshots_are_byte_hash_pinned(self):
        contract = load_contract()
        acct = contract["source_snapshots"]["ACCOUNTING_LEDGER"]
        revenue = contract["source_snapshots"]["REVENUE_LEDGER"]
        self.assertEqual(acct["row_count"], 39783)
        self.assertEqual(acct["gzip_bytes"], 7845217)
        self.assertEqual(
            acct["gzip_sha256"],
            "5447581813677855ac8edcc70e6a90164ef1caa7799df544cc0a08d62ada25b0",
        )
        self.assertEqual(
            acct["content_sha256"],
            "64503339d8352a2f61e1ee8596e9a7ab4dcd6237d1d84010682b4203992b4cb8",
        )
        self.assertEqual(revenue["row_count"], 2286)
        self.assertEqual(revenue["gzip_bytes"], 246707)
        self.assertEqual(
            revenue["gzip_sha256"],
            "02c644bfaf35a70a981967afdc15e0d0e548ed7df30a6da54e21435b17564847",
        )
        self.assertEqual(
            revenue["content_sha256"],
            "fd110fa5c0c2a2583c475a191fef23669c9453a2dbf015a92036247c03d3b8e6",
        )

    def test_projection_values_match_verified_source_anchors(self):
        got = validate_projection_values()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["projection_question_count"], 11)
        self.assertEqual(got["accounting_source_rows"], 39783)
        self.assertEqual(got["revenue_source_rows"], 2286)

        contract = load_contract()
        views = contract["projection_views"]
        stage = views["ACCOUNTING_EDUCATION_STAGE_TOTALS"]
        self.assertEqual(stage["through_april"]["empenhado_liquido_brl"], "319000956.31")
        self.assertEqual(stage["through_april"]["liquidado_brl"], "138279835.79")
        self.assertEqual(stage["through_april"]["pago_brl"], "104176664.15")
        self.assertEqual(stage["through_july"]["empenhado_liquido_brl"], "368762412.07")
        self.assertEqual(stage["through_july"]["liquidado_brl"], "262452288.06")
        self.assertEqual(stage["through_july"]["pago_brl"], "227797802.44")

        revenue = views["REVENUE_EDUCATION_FUNDING_APPLICATION_SUMMARY"]["net_totals"]
        self.assertEqual(revenue["education_application_brl"], "241960964.18")
        self.assertEqual(revenue["education_tesouro_brl"], "109552581.52")
        self.assertEqual(revenue["education_state_transfers_brl"], "119045512.07")
        self.assertEqual(revenue["education_federal_transfers_brl"], "13362870.59")
        self.assertEqual(revenue["fundeb_linked_brl"], "118066203.65")

    def test_task203_baseline_is_preserved_and_task204_covers_exactly_backlog(self):
        self.assertEqual(
            self.audit["task203_productization_counts"],
            {
                "CAPABILITY_ONLY": 3,
                "MIXED_RECORD_AND_CAPABILITY": 8,
                "RECORD_BACKED": 27,
            },
        )
        self.assertEqual(
            self.audit["task204_renderability_counts"],
            {
                "BOUNDED_SOURCE_PINNED_PROJECTION_BACKED": 11,
                "LOCAL_RECORD_BACKED": 27,
            },
        )
        self.assertEqual(self.audit["ontology_summary_renderable_count"], 38)
        self.assertEqual(
            set(self.audit["bounded_projection_questions"]),
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

    def test_all_38_have_deterministic_renderable_packets(self):
        self.assertEqual(len(self.audit["questions"]), 38)
        ids = set()
        for row in self.audit["questions"]:
            self.assertTrue(row["ontology_summary_renderable"])
            self.assertTrue(row["renderable_packet_id"].startswith("RPK_"))
            self.assertEqual(len(row["renderable_packet_sha256"]), 64)
            ids.add(row["renderable_packet_id"])
        self.assertEqual(len(ids), 38)

    def test_acc_q1_is_projection_backed_with_exact_stage_totals(self):
        packet = build_renderable_packet("ACC_Q1", self.products)
        self.assertEqual(packet["projection_count"], 1)
        projection = packet["bounded_projection_views"][0]
        self.assertEqual(projection["projection_view"], "ACCOUNTING_EDUCATION_STAGE_TOTALS")
        self.assertEqual(
            projection["value"]["through_july"]["empenhado_liquido_brl"],
            "368762412.07",
        )
        self.assertFalse(packet["projection_replaces_source_snapshot"])
        self.assertTrue(packet["source_snapshot_remains_canonical"])
        self.assertFalse(packet["llm_numeric_truth_allowed"])

    def test_acc_q2_has_program_funding_and_expense_projection(self):
        names = {
            row["projection_view"]
            for row in projection_views_for_question("ACC_Q2")
        }
        self.assertEqual(
            names,
            {
                "ACCOUNTING_PROGRAM_ACTION_SUMMARY",
                "ACCOUNTING_FUNDING_APPLICATION_SUMMARY",
                "ACCOUNTING_EXPENSE_ELEMENT_SUMMARY",
            },
        )

    def test_acc_q3_rests_are_not_relabelled_as_current_year_spending(self):
        packet = build_renderable_packet("ACC_Q3", self.products)
        rests = packet["bounded_projection_views"][0]["value"]
        april = next(row for row in rests["education"] if row["period"] == "2026-04")
        self.assertEqual(april["total_balance_brl"], "3010505.55")
        self.assertTrue(self.audit["semantics"]["ontology_summary_renderable_ne_arbitrary_drilldown_complete"])

    def test_fin_q3_revenue_projection_preserves_revenue_expenditure_boundary(self):
        contract = load_contract()
        self.assertTrue(contract["semantics"]["revenue_ne_expenditure"])
        packet = build_renderable_packet("FIN_Q3", self.products)
        revenue = packet["bounded_projection_views"][0]["value"]["net_totals"]
        self.assertEqual(revenue["fundeb_linked_brl"], "118066203.65")
        self.assertEqual(revenue["eti_all_linked_brl"], "3692142.87")

    def test_person_supplier_rows_are_redacted_aggregate_only(self):
        contract = load_contract()
        procurement = contract["projection_views"]["ACCOUNTING_PROCUREMENT_SUPPLIER_MODALITY_SUMMARY"]
        self.assertEqual(procurement["person_rows_redacted"], 28)
        self.assertFalse(procurement["person_supplier_names_or_identifiers_persisted"])
        encoded = json.dumps(procurement, ensure_ascii=False).casefold()
        self.assertNotIn("cpf", encoded)
        self.assertNotIn("pessoa física -", encoded)
        self.assertEqual(procurement["redacted_person_aggregate"]["pago_brl"], "8000.00")

    def test_selected_rankings_are_explicitly_non_exhaustive(self):
        contract = load_contract()
        self.assertFalse(contract["semantics"]["selected_rankings_are_exhaustive"])
        self.assertFalse(
            contract["projection_views"]["ACCOUNTING_PROGRAM_ACTION_SUMMARY"][
                "selected_actions_are_complete_list"
            ]
        )
        self.assertFalse(
            contract["projection_views"]["ACCOUNTING_FUNDING_APPLICATION_SUMMARY"][
                "selected_pairs_are_complete_list"
            ]
        )
        self.assertFalse(
            contract["projection_views"]["ACCOUNTING_EXPENSE_ELEMENT_SUMMARY"][
                "selected_elements_are_complete_list"
            ]
        )

    def test_no_serving_or_other_remote_effect_is_enabled(self):
        self.assertTrue(all(v is False for v in self.audit["remote_effects"].values()))
        contract = load_contract()
        self.assertTrue(all(v is False for v in contract["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
