from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

from robo_dados_publicos.analytics.current_observatory_bundle import (
    build_current_products,
)
from robo_dados_publicos.productization.human_answer_renderer import (
    build_answer_card,
    render_answer_card_markdown,
)
from robo_dados_publicos.productization.task206_answer_cli_qa import (
    build_current_representative_qa,
    load_contract,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/render_observatory_answer_offline.py"
_SPEC = importlib.util.spec_from_file_location("task206_cli", SCRIPT)
assert _SPEC and _SPEC.loader
_CLI = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CLI)


class TestTask206OfflineAnswerCliQa(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_contract()
        cls.products = build_current_products(
            generated_at=cls.contract["default_generated_at"],
            software_version=cls.contract["default_software_version"],
        )

    def test_contract_is_offline_and_pins_three_cli_modes(self):
        self.assertEqual(self.contract["issue"], 656)
        self.assertEqual(
            self.contract["cli"]["modes"],
            ["ONE_QUESTION", "ALL_38", "LIST_QUESTIONS"],
        )
        self.assertFalse(self.contract["cli"]["arbitrary_prompt_allowed"])
        self.assertFalse(self.contract["cli"]["arbitrary_path_allowed"])
        self.assertFalse(self.contract["cli"]["arbitrary_url_allowed"])
        self.assertTrue(all(v is False for v in self.contract["remote_effects"].values()))

    def test_list_questions_is_exactly_38_and_contains_representative_ids(self):
        rows = _CLI.canonical_questions()
        self.assertEqual(len(rows), 38)
        ids = {row["question_id"] for row in rows}
        for qid in ("ACC_Q1", "FIN_Q3", "PLAN_Q1", "NORMS_Q1", "TEACH_Q2", "EQUITY_Q1"):
            self.assertIn(qid, ids)
        rendered = _CLI.render_question_list()
        self.assertEqual(len(rendered.strip().splitlines()), 39)

    def test_single_question_cli_path_renders_real_accounting_values(self):
        rendered = _CLI.build_single_answer("ACC_Q1")
        self.assertEqual(rendered["question_id"], "ACC_Q1")
        self.assertIn("368762412.07", rendered["markdown"])
        self.assertIn("262452288.06", rendered["markdown"])
        self.assertIn("227797802.44", rendered["markdown"])
        self.assertEqual(len(rendered["markdown_sha256"]), 64)
        self.assertFalse(rendered["llm_used"])
        self.assertFalse(rendered["remote_effects_performed"])

    def test_unknown_question_fails_closed(self):
        with self.assertRaisesRegex(_CLI.Task206CliStop, "TASK206_UNKNOWN_QUESTION"):
            _CLI.build_single_answer("NOT_A_QUESTION")

    def test_all_mode_contains_exactly_38_answer_sections(self):
        got = _CLI.build_all_answers()
        self.assertEqual(got["question_count"], 38)
        self.assertEqual(got["markdown"].count("- **Question ID:**"), 38)
        self.assertEqual(got["markdown"].count("\n\n---\n\n"), 37)
        self.assertEqual(len(got["markdown_sha256"]), 64)
        self.assertFalse(got["llm_used"])
        self.assertFalse(got["remote_effects_performed"])

    def test_representative_qa_passes_six_real_rendered_cases(self):
        got = build_current_representative_qa()
        self.assertEqual(got["status"], "PASS")
        self.assertEqual(got["case_count"], 6)
        self.assertEqual(
            {row["question_id"] for row in got["cases"]},
            {"ACC_Q1", "FIN_Q3", "PLAN_Q1", "NORMS_Q1", "TEACH_Q2", "EQUITY_Q1"},
        )
        self.assertTrue(got["presentation_repairs_verified"]["teacher_bond_context_visible"])
        self.assertTrue(got["presentation_repairs_verified"]["equity_territory_missingness_visible"])
        self.assertFalse(got["llm_used"])

    def test_teacher_answer_now_exposes_actual_bond_counts(self):
        card = build_answer_card("TEACH_Q2", self.products)
        facts = "\n".join(row["text"] for row in card["NUMBER_OR_FACT"])
        self.assertIn("1280", facts)
        self.assertIn("681", facts)
        self.assertIn("291", facts)
        self.assertIn("400", facts)
        self.assertIn("PERSONNEL_EVENT_FLOW_NE_WORKFORCE_STOCK", card["CAUTION_OR_LIMIT"])

    def test_equity_answer_now_exposes_partial_territory_coverage(self):
        card = build_answer_card("EQUITY_Q1", self.products)
        facts = "\n".join(row["text"] for row in card["NUMBER_OR_FACT"])
        self.assertIn("64/69", facts)
        self.assertIn("5 escolas permanecem HELD", facts)
        self.assertIn(
            "TERRITORY_COVERAGE_64_OF_69_5_HELD_NE_FULL_NETWORK",
            card["CAUTION_OR_LIMIT"],
        )

    def test_planning_and_norm_answers_keep_implementation_boundary_visible(self):
        plan = build_answer_card("PLAN_Q1", self.products)
        norms = build_answer_card("NORMS_Q1", self.products)
        self.assertIn("PLANNING_NE_EXECUTION", plan["CAUTION_OR_LIMIT"])
        self.assertIn("NORM_NE_IMPLEMENTATION", norms["CAUTION_OR_LIMIT"])
        plan_md = render_answer_card_markdown(plan)["markdown"]
        norms_md = render_answer_card_markdown(norms)["markdown"]
        self.assertIn("Planejamento e autorização não provam, por si só, execução.", plan_md)
        self.assertIn("A existência de uma norma não prova implementação ou resultado.", norms_md)


if __name__ == "__main__":
    unittest.main()
