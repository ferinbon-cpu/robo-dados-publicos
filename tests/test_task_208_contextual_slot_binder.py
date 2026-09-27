from __future__ import annotations

import unittest

from robo_dados_publicos.productization.contextual_slot_binder import (
    Task208ContextStop,
    bind_and_render,
    bind_context,
    extract_period,
    resolve_school,
    school_roster,
    validate_contract,
)


class TestTask208ContextualSlotBinder(unittest.TestCase):
    def test_contract_and_roster_are_pinned_offline(self):
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["school_count"], 40)
        self.assertFalse(got["network"])
        self.assertFalse(got["drive_write"])
        self.assertFalse(got["llm"])
        roster = school_roster()
        self.assertEqual(len(roster), 40)
        self.assertEqual(len({x["school_code"] for x in roster}), 40)

    def test_finance_through_july_relative_year_binds_without_implicit_clock(self):
        got = bind_context(
            "Quanto a Educação gastou até julho deste ano?",
            reference_date="2026-09-08",
        )
        self.assertEqual(got["state"], "CONTEXT_BOUND")
        self.assertEqual(got["selected_question_ids"], ["FIN_Q1"])
        self.assertEqual(got["period"]["status"], "RESOLVED")
        self.assertEqual(got["period"]["mode"], "YEAR_TO_MONTH")
        self.assertEqual(got["period"]["year"], 2026)
        self.assertEqual(got["period"]["start_month"], 1)
        self.assertEqual(got["period"]["end_month"], 7)
        self.assertEqual(
            got["route"]["origin"],
            "TASK208_CONTEXTUAL_BRIDGE:FIN_Q1",
        )
        self.assertEqual(got["render_state"], "CONTEXT_UNSUPPORTED_FOR_RENDER")
        self.assertFalse(got["relative_time_uses_implicit_clock"])

    def test_relative_year_requires_caller_reference_date(self):
        got = bind_context("Quanto a Educação gastou até julho deste ano?")
        self.assertEqual(got["state"], "PERIOD_REFERENCE_REQUIRED")
        self.assertEqual(got["selected_question_ids"], [])
        self.assertEqual(got["render_state"], "NOT_RENDERABLE")

    def test_explicit_school_name_resolves_to_pinned_inep_identity(self):
        school = resolve_school("Como está o Rafael Affonso Leite?")
        self.assertEqual(school["status"], "RESOLVED")
        self.assertEqual(school["school_code"], "35470600")
        self.assertEqual(school["school_name"], "CEIEF Rafael Affonso Leite")
        self.assertEqual(school["origin"], "CANONICAL_ALIAS")

        got = bind_context("Como está o Rafael Affonso Leite?")
        self.assertEqual(got["state"], "CONTEXT_BOUND")
        self.assertEqual(got["selected_question_ids"], ["NETWORK_Q3"])
        self.assertEqual(got["school"]["school_code"], "35470600")
        self.assertEqual(got["granularity"]["value"], "SCHOOL_VS_NETWORK")
        self.assertEqual(got["route"]["origin"], "TASK208_SCHOOL_PROFILE_BRIDGE")
        self.assertEqual(got["render_state"], "CONTEXT_UNSUPPORTED_FOR_RENDER")

    def test_norms_registration_2026_binds_topic_and_period(self):
        got = bind_context("Quais normas de matrícula mudaram em 2026?")
        self.assertEqual(got["state"], "CONTEXT_BOUND")
        self.assertEqual(got["selected_question_ids"], ["NORMS_Q2"])
        self.assertEqual(got["period"]["mode"], "YEAR")
        self.assertEqual(got["period"]["year"], 2026)
        self.assertIn("MATRICULA", got["policy_service_facets"])
        self.assertEqual(got["granularity"]["value"], "DOCUMENT_EVENT")
        self.assertEqual(
            got["route"]["origin"],
            "TASK208_CONTEXTUAL_BRIDGE:NORMS_Q2",
        )

    def test_personal_school_reference_needs_explicit_context(self):
        got = bind_context("Compare minha escola com a rede.")
        self.assertEqual(got["state"], "NEEDS_SCHOOL_CONTEXT")
        self.assertEqual(got["selected_question_ids"], [])
        self.assertEqual(got["school"]["status"], "NEEDS_CONTEXT")

    def test_personal_school_reference_with_valid_context_resolves_and_compares(self):
        got = bind_context(
            "Compare minha escola com a rede.",
            context_school_code="35470600",
        )
        self.assertEqual(got["state"], "CONTEXT_BOUND")
        self.assertEqual(got["selected_question_ids"], ["NETWORK_Q3"])
        self.assertEqual(got["school"]["school_code"], "35470600")
        self.assertEqual(got["school"]["origin"], "CALLER_CONTEXT")
        self.assertEqual(got["granularity"]["value"], "SCHOOL_VS_NETWORK")
        self.assertEqual(
            got["route"]["origin"],
            "TASK208_CONTEXTUAL_BRIDGE:NETWORK_Q3",
        )

    def test_invalid_personal_school_context_fails_closed(self):
        got = bind_context(
            "Compare minha escola com a rede.",
            context_school_code="99999999",
        )
        self.assertEqual(got["state"], "SCHOOL_UNRESOLVED")
        self.assertEqual(got["selected_question_ids"], [])

    def test_unknown_school_text_fails_closed(self):
        got = bind_context("Como está a CEIEF Escola Inventada XYZ?")
        self.assertEqual(got["state"], "SCHOOL_UNRESOLVED")
        self.assertEqual(got["selected_question_ids"], [])

    def test_multiple_years_are_ambiguous(self):
        period = extract_period("Compare 2025 com 2026")
        self.assertEqual(period["status"], "AMBIGUOUS")
        got = bind_context("Quanto a Educação gastou em 2025 e 2026?")
        self.assertEqual(got["state"], "PERIOD_AMBIGUOUS")
        self.assertEqual(got["selected_question_ids"], [])

    def test_context_is_never_silently_dropped_into_task207_renderer(self):
        with self.assertRaisesRegex(
            Task208ContextStop,
            "TASK208_CONTEXT_UNSUPPORTED_FOR_RENDER",
        ):
            bind_and_render(
                "Quanto a Educação gastou até julho deste ano?",
                reference_date="2026-09-08",
            )

        with self.assertRaisesRegex(
            Task208ContextStop,
            "TASK208_CONTEXT_UNSUPPORTED_FOR_RENDER",
        ):
            bind_and_render("Como está o Rafael Affonso Leite?")

    def test_uncontextualized_question_can_still_use_task207_renderer(self):
        got = bind_context("quanto foi empenhado liquidado e pago")
        self.assertEqual(got["state"], "CONTEXT_BOUND")
        self.assertEqual(got["selected_question_ids"], ["ACC_Q1"])
        self.assertEqual(got["render_state"], "TASK207_RENDER_SAFE")

        rendered = bind_and_render("quanto foi empenhado liquidado e pago")
        self.assertFalse(rendered["context_dropped"])
        self.assertEqual(
            rendered["task207_render"]["route"]["selected_question_ids"],
            ["ACC_Q1"],
        )

    def test_result_is_deterministic(self):
        a = bind_context(
            "Compare minha escola com a rede.",
            context_school_code="35470600",
        )
        b = bind_context(
            "Compare minha escola com a rede.",
            context_school_code="35470600",
        )
        self.assertEqual(a, b)
        self.assertEqual(len(a["context_result_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
