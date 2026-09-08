from __future__ import annotations

import copy
import unittest

from robo_dados_publicos.analytics.current_observatory_bundle import (
    build_current_products,
)
from robo_dados_publicos.productization.human_answer_renderer import (
    Task205AnswerStop,
    build_answer_card,
    build_human_answer_bundle,
    load_contract,
    render_answer_card_markdown,
    validate_answer_card,
)


GENERATED_AT = "2026-09-08T02:05:00+00:00"
SOFTWARE_VERSION = "0.8.0"


class TestTask205HumanAnswerRenderer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.products = build_current_products(
            generated_at=GENERATED_AT,
            software_version=SOFTWARE_VERSION,
        )
        cls.bundle = build_human_answer_bundle(cls.products)

    def test_contract_is_offline_deterministic_and_complete(self):
        contract = load_contract()
        self.assertEqual(contract["expected_question_count"], 38)
        self.assertEqual(len(contract["domain_explanations"]), 15)
        self.assertEqual(
            contract["required_answer_parts"],
            [
                "NUMBER_OR_FACT",
                "TIME_REFERENCE",
                "COMPARISON_OR_TREND",
                "PLAIN_LANGUAGE_EXPLANATION",
                "SOURCE_AND_PROVENANCE",
                "CAUTION_OR_LIMIT",
            ],
        )
        self.assertTrue(all(v is False for v in contract["remote_effects"].values()))

    def test_all_38_questions_have_cards_and_markdown(self):
        self.assertEqual(self.bundle["question_count"], 38)
        self.assertEqual(self.bundle["answer_card_count"], 38)
        self.assertEqual(self.bundle["markdown_render_count"], 38)
        self.assertEqual(
            self.bundle["backing_counts"],
            {
                "BOUNDED_SOURCE_PINNED_PROJECTION_BACKED": 11,
                "LOCAL_RECORD_BACKED": 27,
            },
        )
        self.assertEqual(
            self.bundle["comparison_available_count"]
            + self.bundle["comparison_unavailable_count"],
            38,
        )

    def test_every_card_has_required_answer_contract_and_provenance(self):
        for card in self.bundle["cards"]:
            validate_answer_card(card)
            self.assertTrue(card["NUMBER_OR_FACT"])
            self.assertTrue(card["TIME_REFERENCE"])
            self.assertTrue(card["COMPARISON_OR_TREND"])
            self.assertTrue(card["PLAIN_LANGUAGE_EXPLANATION"])
            self.assertTrue(card["SOURCE_AND_PROVENANCE"])
            self.assertTrue(card["CAUTION_OR_LIMIT"])
            self.assertEqual(len(card["answer_card_sha256"]), 64)
            self.assertFalse(card["llm_used"])
            self.assertFalse(card["numeric_invention_performed"])
            self.assertFalse(card["causal_effect_created"])

    def test_acc_q1_copies_exact_task204_values_and_stage_guard(self):
        card = build_answer_card("ACC_Q1", self.products)
        facts = "\n".join(row["text"] for row in card["NUMBER_OR_FACT"])
        self.assertIn("368762412.07", facts)
        self.assertIn("262452288.06", facts)
        self.assertIn("227797802.44", facts)
        self.assertIn(
            "COMMITMENT_NE_LIQUIDATION_NE_PAYMENT",
            card["CAUTION_OR_LIMIT"],
        )
        self.assertEqual(card["backing"], "BOUNDED_SOURCE_PINNED_PROJECTION_BACKED")

    def test_acc_q3_keeps_rests_separate(self):
        card = build_answer_card("ACC_Q3", self.products)
        facts = "\n".join(row["text"] for row in card["NUMBER_OR_FACT"])
        self.assertIn("3010505.55", facts)
        self.assertIn(
            "RESTS_PAYABLE_NE_CURRENT_YEAR_EXPENDITURE",
            card["CAUTION_OR_LIMIT"],
        )

    def test_fin_q3_keeps_revenue_separate_from_expenditure(self):
        card = build_answer_card("FIN_Q3", self.products)
        facts = "\n".join(row["text"] for row in card["NUMBER_OR_FACT"])
        self.assertIn("118066203.65", facts)
        self.assertIn("3692142.87", facts)
        self.assertIn("REVENUE_NE_EXPENDITURE", card["CAUTION_OR_LIMIT"])

    def test_projection_provenance_names_only_actual_source_ledger(self):
        acc = build_answer_card("ACC_Q1", self.products)
        acc_products = {ref.get("product") for ref in acc["SOURCE_AND_PROVENANCE"]}
        self.assertIn("ACCOUNTING_LEDGER", acc_products)
        self.assertNotIn("REVENUE_LEDGER", acc_products)

        fin = build_answer_card("FIN_Q3", self.products)
        fin_products = {ref.get("product") for ref in fin["SOURCE_AND_PROVENANCE"]}
        self.assertIn("REVENUE_LEDGER", fin_products)

    def test_markdown_is_deterministic_and_contains_fixed_sections(self):
        card = build_answer_card("ACC_Q1", self.products)
        a = render_answer_card_markdown(card)
        b = render_answer_card_markdown(copy.deepcopy(card))
        self.assertEqual(a, b)
        self.assertEqual(len(a["markdown_sha256"]), 64)
        self.assertIn("## Número ou fato", a["markdown"])
        self.assertIn("## Referência temporal", a["markdown"])
        self.assertIn("## Comparação ou tendência", a["markdown"])
        self.assertIn("## Fonte e proveniência", a["markdown"])
        self.assertIn("## Cautelas e limites", a["markdown"])

    def test_tampered_card_hash_fails_closed(self):
        card = build_answer_card("ACC_Q1", self.products)
        bad = copy.deepcopy(card)
        bad["NUMBER_OR_FACT"][0]["text"] += " adulterado"
        with self.assertRaisesRegex(Task205AnswerStop, "CARD_SHA_MISMATCH"):
            validate_answer_card(bad)

    def test_missing_comparison_is_explicit_not_invented(self):
        marker = load_contract()["unavailable_marker"]
        self.assertTrue(
            any(
                card["COMPARISON_OR_TREND"] == [marker]
                for card in self.bundle["cards"]
            )
        )

    def test_local_record_cards_remain_source_backed(self):
        local_cards = [
            card
            for card in self.bundle["cards"]
            if card["backing"] == "LOCAL_RECORD_BACKED"
        ]
        self.assertEqual(len(local_cards), 27)
        self.assertTrue(
            all(
                any(
                    ref.get("source_sha256")
                    or ref.get("provenance_ref")
                    or ref.get("document_id")
                    or ref.get("event_id")
                    for ref in card["SOURCE_AND_PROVENANCE"]
                )
                for card in local_cards
            )
        )

    def test_bundle_is_deterministic_for_identical_products(self):
        second = build_human_answer_bundle(self.products)
        self.assertEqual(self.bundle["bundle_sha256"], second["bundle_sha256"])
        self.assertEqual(
            [x["answer_card_sha256"] for x in self.bundle["cards"]],
            [x["answer_card_sha256"] for x in second["cards"]],
        )

    def test_no_serving_publication_or_llm_is_enabled(self):
        self.assertFalse(self.bundle["llm_used"])
        self.assertTrue(all(v is False for v in self.bundle["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
