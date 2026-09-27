from __future__ import annotations

from decimal import Decimal
import unittest

from robo_dados_publicos.productization.custody_ledger_projection_execution import (
    execute_contextual_query_v5,
    load_contract,
    load_projection,
    render_contextual_answer_v5,
    validate_contract,
)
from robo_dados_publicos.productization.safe_local_mixed_execution import (
    execute_contextual_query_v4,
)


GENERATED_AT = "2026-09-08T17:55:00+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask214CustodyLedgerProjectionExecution(unittest.TestCase):
    def execute(self, text: str, **kwargs):
        return execute_contextual_query_v5(
            text,
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
            **kwargs,
        )

    def test_contract_and_projection_validate_exact_custody(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["accounting_source_rows"], 39783)
        self.assertEqual(got["tce_source_rows"], 39779)
        self.assertEqual(got["revenue_source_rows"], 2286)
        self.assertEqual(got["classification_groups"], 422)
        self.assertEqual(got["classification_display_rows"], 30)
        self.assertEqual(got["promoted_question_count"], 4)
        self.assertEqual(got["semantic_blocker_count"], 6)
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_read"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["llm"])

        contract = load_contract()
        self.assertEqual(
            contract["source_snapshots"]["ACCOUNTING_LEDGER"]["gzip_sha256"],
            "5447581813677855ac8edcc70e6a90164ef1caa7799df544cc0a08d62ada25b0",
        )
        self.assertEqual(
            contract["source_snapshots"]["REVENUE_LEDGER"]["gzip_sha256"],
            "02c644bfaf35a70a981967afdc15e0d0e548ed7df30a6da54e21435b17564847",
        )
        self.assertEqual(
            set(contract["promoted_questions"]),
            {"ACC_Q1", "ACC_Q2", "ACC_Q3", "FIN_Q3"},
        )

    def test_projection_recomputes_canonical_education_and_eti_signals(self):
        p = load_projection()
        acc1 = p["views"]["ACC_Q1_STAGE_TOTALS"]
        by_stage = {}
        for month, stage, count, amount in acc1["education_function_by_month_source_stage"]:
            slot = by_stage.setdefault(stage, [0, Decimal("0")])
            slot[0] += count
            slot[1] += Decimal(amount)
        self.assertEqual(by_stage["Empenhado"][1], Decimal("337824523.73"))
        self.assertEqual(by_stage["Reforço"][1], Decimal("34418997.78"))
        self.assertEqual(by_stage["Anulação"][1], Decimal("3481109.44"))
        self.assertEqual(by_stage["Valor Liquidado"][1], Decimal("262452288.06"))
        self.assertEqual(by_stage["Valor Pago"][1], Decimal("227797802.44"))
        self.assertEqual(
            by_stage["Empenhado"][1] + by_stage["Reforço"][1] - by_stage["Anulação"][1],
            Decimal("368762412.07"),
        )

        fin = p["views"]["FIN_Q3_REVENUE_SOURCES"]
        eti = fin["eti_rows"]
        self.assertEqual(eti["covered_source_rows"], 7)
        self.assertEqual(
            sum(Decimal(row["amount_brl"]) for row in eti["rows"]),
            Decimal("3692142.87"),
        )
        self.assertEqual(
            sum(
                Decimal(row["amount_brl"])
                for row in eti["rows"]
                if row["eti_direct_transfer"]
            ),
            Decimal("3606418.18"),
        )
        self.assertEqual(
            sum(
                Decimal(row["amount_brl"])
                for row in eti["rows"]
                if row["eti_financial_remuneration"]
            ),
            Decimal("85724.69"),
        )

    def test_acc_q1_year_2026_is_observed_jan_jul_not_full_year(self):
        got = self.execute("quanto foi empenhado liquidado e pago em 2026?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "ACC_Q1")
        fact = next(
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "ACCOUNTING_SOURCE_STAGE_TOTALS"
        )
        self.assertEqual(fact["period"], "2026-01..2026-07")
        self.assertTrue(fact["observed_ytd_not_full_year"])
        stages = fact["source_stages"]
        self.assertEqual(stages["Empenhado"]["amount_brl"], "1759388496.22")
        self.assertEqual(stages["Reforço"]["amount_brl"], "46507977.05")
        self.assertEqual(stages["Anulação"]["amount_brl"], "65259446.13")
        self.assertEqual(stages["Valor Liquidado"]["amount_brl"], "1024476679.69")
        self.assertEqual(stages["Valor Pago"]["amount_brl"], "921567699.04")
        self.assertEqual(
            fact["commitment_plus_reinforcement_minus_reversal_arithmetic_brl"],
            "1740637027.14",
        )
        self.assertFalse(fact["legal_net_expenditure_claim"])
        self.assertIn("OBSERVED_JAN_JUL_2026_NE_FULL_YEAR_2026", got["CAUTION_OR_LIMIT"])

    def test_acc_q1_exact_ytd_april_does_not_use_july(self):
        got = self.execute("quanto foi empenhado liquidado e pago até abril de 2026?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        fact = next(
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "ACCOUNTING_SOURCE_STAGE_TOTALS"
        )
        self.assertEqual(fact["period"], "2026-01..2026-04")
        stages = fact["source_stages"]
        self.assertEqual(stages["Empenhado"]["amount_brl"], "1595872804.32")
        self.assertEqual(stages["Valor Liquidado"]["amount_brl"], "529415596.88")
        self.assertEqual(stages["Valor Pago"]["amount_brl"], "453786007.06")
        self.assertNotIn("921567699.04", str(got))

    def test_acc_q2_exposes_universe_and_top30_without_calling_it_full_list(self):
        got = self.execute("qual ficha dotacao fonte e aplicacao sustentam o gasto em 2026?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "ACC_Q2")
        universe = next(
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "CLASSIFICATION_UNIVERSE"
        )
        self.assertEqual(universe["source_rows"], 39779)
        self.assertEqual(universe["group_count"], 422)
        self.assertEqual(universe["displayed_group_count"], 30)
        self.assertFalse(universe["top30_equals_full_list"])
        groups = [
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "CLASSIFICATION_TOP_GROUP"
        ]
        self.assertEqual(len(groups), 30)
        self.assertEqual(groups[0]["rank"], 1)
        self.assertEqual(groups[0]["program_code"], "9001")
        self.assertIn("TOP30_CLASSIFICATION_NE_FULL_CLASSIFICATION_LIST", got["CAUTION_OR_LIMIT"])

    def test_acc_q2_month_specific_is_not_inferred_from_jan_jul_ranking(self):
        got = self.execute("qual ficha dotacao fonte e aplicacao sustentam o gasto em abril de 2026?")
        self.assertEqual(got["question_id"], "ACC_Q2")
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertNotIn("CLASSIFICATION_TOP_GROUP", str(got))

    def test_acc_q3_april_preserves_processed_nonprocessed_and_scopes(self):
        got = self.execute("ha restos a pagar em abril de 2026?")
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "ACC_Q3")
        rows = [
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "RESTS_PAYABLE_SNAPSHOT"
        ]
        self.assertEqual(len(rows), 2)
        by_scope = {row["scope_type"]: row for row in rows}
        municipal = by_scope["MUNICIPAL_TOTAL_EXCEPT_INTRABUDGET"]
        education = by_scope["ORGAN"]
        self.assertEqual(municipal["total_balance_brl"], "51053179.39")
        self.assertEqual(municipal["processed_balance_brl"], "16476433.49")
        self.assertEqual(municipal["nonprocessed_balance_brl"], "34576745.90")
        self.assertEqual(education["total_balance_brl"], "3010505.55")
        self.assertEqual(education["processed_balance_brl"], "308667.86")
        self.assertEqual(education["nonprocessed_balance_brl"], "2701837.69")

    def test_acc_q3_june_is_explicit_gap_no_nearest_april_snap(self):
        got = self.execute("ha restos a pagar em junho de 2026?")
        self.assertEqual(got["question_id"], "ACC_Q3")
        self.assertEqual(got["state"], "EXPLICIT_CONTEXT_GAP")
        gap = next(row for row in got["NUMBER_OR_FACT"] if row["kind"] == "EXACT_RESTS_PERIOD_GAP")
        self.assertEqual(gap["requested_month"], 6)
        self.assertEqual(gap["available_exact_months"], [2, 4])
        self.assertFalse(gap["nearest_month_substitution"])
        self.assertNotIn("51053179.39", str(got))

    def test_fin_q3_july_reconciles_revenue_fundeb_and_exact_eti(self):
        got = self.execute(
            "quanto vem de FUNDEB recursos proprios e transferencias até julho de 2026?"
        )
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        self.assertEqual(got["question_id"], "FIN_Q3")
        self.assertEqual(
            got["filter_accounting"]["POLICY_SERVICE_FACETS"]["status"],
            "APPLIED_BY_RECIPE_SCOPE",
        )
        signals = next(
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "EDUCATION_REVENUE_APPLICATION_SIGNALS"
        )
        self.assertEqual(signals["fundeb_linked_brl"], "118066203.65")
        self.assertEqual(signals["eti_linked_brl"], "3692142.87")
        self.assertEqual(signals["eti_direct_transfer_brl"], "3606418.18")
        self.assertEqual(signals["eti_financial_remuneration_brl"], "85724.69")
        self.assertEqual(signals["broad_education_application_brl"], "241960964.18")
        funding = next(
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "REVENUE_FUNDING_SOURCE_TOTALS"
        )
        self.assertEqual(funding["period"], "2026-01..2026-07")
        self.assertTrue(funding["observed_ytd_not_full_year"])
        by_source = {row["funding_source"]: row for row in funding["funding_sources"]}
        self.assertEqual(by_source["01 - TESOURO"]["value_brl"], "828918301.92")
        self.assertIn("REVENUE_NE_EXPENDITURE", got["CAUTION_OR_LIMIT"])
        self.assertIn("ETI_DIRECT_TRANSFER_NE_ETI_FINANCIAL_REMUNERATION", got["CAUTION_OR_LIMIT"])

    def test_fin_q3_month_may_uses_only_exact_month_rows(self):
        got = self.execute(
            "quanto vem de FUNDEB recursos proprios e transferencias em maio de 2026?"
        )
        self.assertEqual(got["state"], "ANSWERED_CONTEXTUALLY")
        signals = next(
            row for row in got["NUMBER_OR_FACT"]
            if row["kind"] == "EDUCATION_REVENUE_APPLICATION_SIGNALS"
        )
        self.assertEqual(signals["eti_linked_brl"], "3468164.78")
        self.assertEqual(signals["eti_direct_transfer_brl"], "3423955.92")
        self.assertEqual(signals["eti_financial_remuneration_brl"], "44208.86")

    def test_school_filter_is_not_invented_for_accounting_projection(self):
        got = self.execute(
            "quanto foi empenhado liquidado e pago no Rafael Affonso Leite em 2026?"
        )
        self.assertEqual(got["question_id"], "ACC_Q1")
        self.assertEqual(got["state"], "UNSUPPORTED_CONTEXT_COMBINATION")
        self.assertEqual(got["filter_accounting"]["SCHOOL"]["status"], "UNSUPPORTED")

    def test_six_questions_are_semantic_gaps_not_payload_gaps(self):
        cases = {
            "CTRL_Q2": "o que TCE e demais controles corroboram em 2026?",
            "INFRA_Q2": "quais escolas receberam obras reformas ou equipamentos em 2026?",
            "PLAN_Q3": "planejamento e execucao estao coerentes em 2026?",
            "PROC_Q1": "o que a prefeitura esta comprando em 2026?",
            "PROC_Q2": "quem fornece por quanto e por quanto tempo em 2026?",
            "PROC_Q3": "houve aditivo apostilamento ou nova licitacao em 2026?",
        }
        for qid, text in cases.items():
            with self.subTest(qid=qid):
                got = self.execute(text)
                self.assertEqual(got["question_id"], qid)
                self.assertEqual(got["state"], "EXPLICIT_CONTEXT_GAP")
                blocker = next(
                    row for row in got["NUMBER_OR_FACT"]
                    if row["kind"] == "TASK214_SEMANTIC_BLOCKER"
                )
                self.assertFalse(blocker["weak_join_used"])
                self.assertIn(
                    "PAYLOAD_PRESENT_BUT_CROSS_PRODUCT_IDENTITY_NOT_PROVEN",
                    got["CAUTION_OR_LIMIT"],
                )
                self.assertEqual(
                    got["gap_scope"],
                    "TASK214_CROSS_PRODUCT_IDENTITY_OR_COHERENCE",
                )

    def test_representative_task209_task210_task211_task213_delegate_exactly(self):
        cases = [
            ("Quanto a Educação gastou até julho deste ano?", {"reference_date": "2026-09-08"}),
            ("infraestrutura da escola Rafael Affonso Leite em 2025", {}),
            ("nomeações e exonerações em 2026", {}),
            ("quanto por aluno em 2025?", {}),
        ]
        for text, kwargs in cases:
            with self.subTest(text=text):
                a = self.execute(text, **kwargs)
                b = execute_contextual_query_v4(
                    text,
                    generated_at=GENERATED_AT,
                    software_version=SOFTWARE_VERSION,
                    **kwargs,
                )
                self.assertEqual(a, b)

    def test_renderer_reuses_contextual_answer_schema(self):
        answer = self.execute("ha restos a pagar em abril de 2026?")
        rendered = render_contextual_answer_v5(answer)
        self.assertEqual(rendered["question_id"], "ACC_Q3")
        self.assertIn("51053179.39", rendered["markdown"])
        self.assertIn("3010505.55", rendered["markdown"])

    def test_outputs_are_deterministic_and_offline(self):
        for text in (
            "quanto foi empenhado liquidado e pago em 2026?",
            "ha restos a pagar em abril de 2026?",
            "quanto vem de FUNDEB recursos proprios e transferencias até julho de 2026?",
        ):
            with self.subTest(text=text):
                a = self.execute(text)
                b = self.execute(text)
                self.assertEqual(a, b)
                self.assertEqual(len(a["answer_sha256"]), 64)
                self.assertFalse(a["llm_used"])
                self.assertTrue(all(v is False for v in a["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
