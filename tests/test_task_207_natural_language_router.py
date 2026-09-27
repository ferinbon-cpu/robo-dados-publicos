from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest

from robo_dados_publicos.analytics.current_observatory_answerability import (
    current_answerability_config,
)
from robo_dados_publicos.productization.natural_language_router import (
    Task207RouteStop,
    load_contract,
    normalize_text,
    route_and_render,
    route_natural_language,
    validate_contract,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/ask_observatory_offline.py"
_SPEC = importlib.util.spec_from_file_location("task207_cli", SCRIPT)
assert _SPEC and _SPEC.loader
_CLI = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CLI)


class TestTask207NaturalLanguageRouter(unittest.TestCase):
    def test_contract_is_offline_and_covers_exact_current_38(self):
        contract = load_contract()
        got = validate_contract()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["question_count"], 38)
        self.assertEqual(len(contract["question_routes"]), 38)
        self.assertTrue(all(v is False for v in contract["remote_effects"].values()))
        self.assertFalse(got["llm"])

    def test_normalization_handles_accents_case_and_punctuation(self):
        self.assertEqual(
            normalize_text("  Educação: FUNDEB, Matrículas?! "),
            "educacao fundeb matriculas",
        )

    def test_all_38_exact_canonical_question_texts_self_route(self):
        config = current_answerability_config()
        self.assertEqual(len(config["questions"]), 38)
        for row in config["questions"]:
            got = route_natural_language(row["text"])
            self.assertEqual(got["state"], "ROUTED", row["id"])
            self.assertEqual(got["route_mode"], "EXACT_CANONICAL_TEXT", row["id"])
            self.assertEqual(got["selected_question_ids"], [row["id"]], row["id"])
            self.assertEqual(got["confidence"], 1.0)
            self.assertFalse(got["text_is_truth_source"])
            self.assertFalse(got["numeric_truth_created"])
            self.assertFalse(got["llm_used"])

    def test_representative_natural_phrasings_route_correctly(self):
        cases = {
            "quanto Limeira gastou com educação": ["FIN_Q1"],
            "quanto foi empenhado liquidado e pago": ["ACC_Q1"],
            "quanto se gasta por aluno": ["FIN_Q2"],
            "quanto veio do Fundeb e de transferências": ["FIN_Q3"],
            "tem restos a pagar": ["ACC_Q3"],
            "quantos professores efetivos temporários e CLT": ["TEACH_Q2"],
            "como está a formação e o esforço dos professores": ["TEACH_Q1"],
            "como está o AEE": ["EQUITY_Q2"],
            "desigualdade por raça renda e território": ["EQUITY_Q1"],
            "quais normas mudaram calendário e matrícula": ["NORMS_Q2"],
            "o que saiu no Jornal Oficial": ["JOM_Q1"],
            "quais fontes estão desatualizadas ou bloqueadas": ["CTRL_Q1"],
        }
        for text, expected in cases.items():
            got = route_natural_language(text)
            self.assertEqual(got["state"], "ROUTED", text)
            self.assertEqual(got["selected_question_ids"], expected, text)
            self.assertGreaterEqual(got["confidence"], 0.5, text)
            self.assertTrue(got["candidates"][0]["score"] >= 8, text)

    def test_compound_question_routes_two_clear_canonical_questions(self):
        got = route_natural_language(
            "quanto gastou com educação e quanto veio do Fundeb"
        )
        self.assertEqual(got["state"], "ROUTED")
        self.assertEqual(got["route_mode"], "COMPOUND")
        self.assertEqual(set(got["selected_question_ids"]), {"FIN_Q1", "FIN_Q3"})
        self.assertEqual(len(got["selected_question_ids"]), 2)

    def test_ambiguous_teacher_wording_does_not_silently_choose(self):
        got = route_natural_language("como estão os professores")
        self.assertEqual(got["state"], "AMBIGUOUS")
        self.assertEqual(got["selected_question_ids"], [])
        top_ids = {row["question_id"] for row in got["candidates"][:2]}
        self.assertEqual(top_ids, {"TEACH_Q1", "TEACH_Q2"})
        self.assertEqual(got["confidence"], 0.0)

    def test_low_confidence_text_stops(self):
        got = route_natural_language("me conta alguma coisa")
        self.assertEqual(got["state"], "LOW_CONFIDENCE_STOP")
        self.assertEqual(got["selected_question_ids"], [])
        self.assertEqual(got["confidence"], 0.0)

    def test_route_is_deterministic(self):
        text = "quanto Limeira gastou com educação"
        a = route_natural_language(text)
        b = route_natural_language(copy.deepcopy(text))
        self.assertEqual(a, b)
        self.assertEqual(len(a["route_result_sha256"]), 64)

    def test_route_and_render_reuses_canonical_answer_not_text_truth(self):
        got = route_and_render("quanto foi empenhado liquidado e pago")
        self.assertEqual(got["answer_count"], 1)
        self.assertEqual(got["answers"][0]["question_id"], "ACC_Q1")
        markdown = got["answers"][0]["markdown"]
        self.assertIn("368762412.07", markdown)
        self.assertIn("262452288.06", markdown)
        self.assertIn("227797802.44", markdown)
        self.assertFalse(got["text_is_truth_source"])
        self.assertFalse(got["llm_used"])
        self.assertFalse(got["numeric_truth_created_by_router"])

    def test_route_and_render_refuses_ambiguous_or_low_confidence(self):
        with self.assertRaisesRegex(Task207RouteStop, "TASK207_ROUTE_NOT_RENDERABLE:AMBIGUOUS"):
            route_and_render("como estão os professores")
        with self.assertRaisesRegex(Task207RouteStop, "TASK207_ROUTE_NOT_RENDERABLE:LOW_CONFIDENCE_STOP"):
            route_and_render("me conta alguma coisa")

    def test_cli_parser_requires_ask_and_has_route_only_mode(self):
        parser = _CLI.build_parser()
        args = parser.parse_args(["--ask", "como está o AEE", "--route-only"])
        self.assertEqual(args.ask, "como está o AEE")
        self.assertTrue(args.route_only)


if __name__ == "__main__":
    unittest.main()
