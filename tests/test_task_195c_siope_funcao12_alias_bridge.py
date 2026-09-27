from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.github_task_195c_siope_funcao12_alias_bridge_gate import validate

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/task195c_siope_funcao12_alias_bridge.v1.json"
EVIDENCE = ROOT / "docs/evidence/TASK_195C_SIOPE_FUNCAO12_ALIAS_BRIDGE_0.8.0.json"


class Task195CFuncao12AliasBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_canonical_contract_passes(self) -> None:
        validate(copy.deepcopy(self.config), copy.deepcopy(self.evidence))

    def test_target_is_proven_at_concept_level_only(self) -> None:
        semantic = self.config["semantic_decision"]
        self.assertEqual(
            semantic["VL_DESP_DOTA_ATUA_EDU"],
            "PROVEN_ALIAS_TO_EDUCATION_EXPENSE_UPDATED_BUDGET_CONCEPT",
        )
        self.assertEqual(
            semantic["backend_account_inclusion_formula"],
            "NOT_PROVEN_NOT_REQUIRED_FOR_ALIAS_TO_CONCEPT_IDENTITY",
        )
        self.assertEqual(semantic["source_defined_1000_inclusion_rule"], "NOT_CLAIMED")

    def test_official_ui_keeps_three_semantic_surfaces_distinct(self) -> None:
        tutorial = self.config["official_documentary_chain"]["tutorial_2024"]
        self.assertEqual(
            tutorial["dados_gerais_tabs_observed"],
            [
                "Receita total do Município",
                "Despesa total do Município",
                "Despesa com Educação (Função 12)",
            ],
        )
        self.assertTrue(tutorial["mde_is_separate_guide"])
        self.assertTrue(tutorial["demonstrativo_is_separate_screen"])
        self.assertFalse(self.config["semantic_decision"]["EDU_equals_MDE"])
        self.assertFalse(self.config["semantic_decision"]["rreo_line_33_identity_required"])

    def test_historical_dictionary_has_exact_education_dotacao_concept(self) -> None:
        fields = self.config["official_documentary_chain"]["dictionary_2019"]["fields"]
        row = next(x for x in fields if x["current_alias"] == "VL_DESP_DOTA_ATUA_EDU")
        self.assertEqual(row["historical_field"], "VL_DOTACAO_ATUALIZADA_EDUCACAO")
        self.assertEqual(row["meaning"], "Valor de despesa dotada atualizada com educação")

    def test_current_metadata_keeps_education_and_mde_separate(self) -> None:
        metadata = self.config["official_documentary_chain"]["metadata_2025"]
        self.assertEqual(metadata["education_root"], {"name": "Despesas com Educação", "COD_PAST": 27})
        self.assertEqual(metadata["standard_stages"]["DA"], "Dotação Atualizada")
        self.assertTrue(metadata["mde_separate_structure"])

    def test_r1000_variance_is_not_promoted_to_formula(self) -> None:
        op = self.config["operational_evidence"]
        self.assertEqual(op["rreo_variance"], "1000.00")
        self.assertEqual(
            op["budget_only_candidate_account"]["role"],
            "CANDIDATE_EXPLANATION_ONLY_NOT_REQUIRED_FOR_ALIAS_SEMANTICS",
        )
        self.assertEqual(self.evidence["result"]["1000_account_inclusion_rule"], "NOT_PROVEN_AND_NOT_ASSERTED")

    def test_transport_failures_do_not_become_negative_data_evidence(self) -> None:
        probe = self.config["bounded_remote_probe"]
        self.assertTrue(probe["timeout_is_not_zero_rows"])
        self.assertFalse(probe["form_submission_performed"])
        self.assertFalse(probe["captcha_bypass_attempted"])
        self.assertFalse(probe["tinyfish_used"])
        self.assertEqual(len(probe["odata_da_runs"]), 3)
        self.assertTrue(all(x["semantic_result"] is False for x in probe["odata_da_runs"]))

    def test_b2_promoted_b3_and_gold_remain_blocked(self) -> None:
        release = self.config["release_effect"]
        self.assertEqual(release["B2_FINANCIAL_ALIAS_BRIDGE"], "PROVEN_10_OF_10_ALIAS_TO_CONCEPT")
        self.assertEqual(release["B3_EFFECTIVE_ANNUAL_DECLARATION"], "NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING")
        self.assertFalse(release["gold_2025_calculated"])
        self.assertEqual(release["release_0_8_0"], "CANDIDATE")
        self.assertEqual(release["closed_annual_series"], "2016-2024")

    def test_mutation_rreo_identity_requirement_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.config)
        mutated["semantic_decision"]["rreo_line_33_identity_required"] = True
        with self.assertRaises(ValueError):
            validate(mutated, copy.deepcopy(self.evidence))

    def test_mutation_formula_promotion_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.config)
        mutated["semantic_decision"]["backend_account_inclusion_formula"] = "PROVEN"
        with self.assertRaises(ValueError):
            validate(mutated, copy.deepcopy(self.evidence))

    def test_mutation_b3_promotion_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.config)
        mutated["release_effect"]["B3_EFFECTIVE_ANNUAL_DECLARATION"] = "PROVEN"
        with self.assertRaises(ValueError):
            validate(mutated, copy.deepcopy(self.evidence))

    def test_mutation_timeout_as_zero_rows_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.config)
        mutated["bounded_remote_probe"]["timeout_is_not_zero_rows"] = False
        with self.assertRaises(ValueError):
            validate(mutated, copy.deepcopy(self.evidence))


if __name__ == "__main__":
    unittest.main()
