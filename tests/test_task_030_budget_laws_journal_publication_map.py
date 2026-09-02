from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.budget_publication_map import (
    BudgetPublicationMapStop,
    validate_budget_publication_map,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "budget_laws_journal_publication_map.v1.json"


class Task030BudgetPublicationMapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_valid_map_passes(self) -> None:
        result = validate_budget_publication_map(copy.deepcopy(self.data))
        self.assertEqual(result["status"], "PASS_TASK_030_BUDGET_LAWS_JOURNAL_PUBLICATION_MAP")
        self.assertFalse(result["promotion_authorized"])

    def test_exact_three_document_families_required(self) -> None:
        drift = copy.deepcopy(self.data)
        drift["records"].pop()
        with self.assertRaises(BudgetPublicationMapStop):
            validate_budget_publication_map(drift)

    def test_wrong_law_number_fails(self) -> None:
        drift = copy.deepcopy(self.data)
        drift["records"][0]["law_number"] = "7.999/2025"
        with self.assertRaises(BudgetPublicationMapStop):
            validate_budget_publication_map(drift)

    def test_wrong_edition_fails(self) -> None:
        drift = copy.deepcopy(self.data)
        drift["records"][1]["journal_edition"] = 7025
        with self.assertRaises(BudgetPublicationMapStop):
            validate_budget_publication_map(drift)

    def test_ldo_end_page_drift_fails(self) -> None:
        drift = copy.deepcopy(self.data)
        drift["records"][1]["journal_verified_end_page"] = 40
        with self.assertRaises(BudgetPublicationMapStop):
            validate_budget_publication_map(drift)

    def test_loa_candidate_end_must_not_be_verified(self) -> None:
        drift = copy.deepcopy(self.data)
        drift["records"][2]["journal_verified_end_page"] = 480
        with self.assertRaises(BudgetPublicationMapStop):
            validate_budget_publication_map(drift)

    def test_ppa_section_boundary_does_not_prove_end(self) -> None:
        drift = copy.deepcopy(self.data)
        drift["records"][0]["journal_verified_end_page"] = 76
        with self.assertRaises(BudgetPublicationMapStop):
            validate_budget_publication_map(drift)

    def test_full_equivalence_cannot_be_inferred_from_same_law(self) -> None:
        drift = copy.deepcopy(self.data)
        drift["guardrails"]["infer_full_equivalence_from_same_law_number"] = True
        with self.assertRaises(BudgetPublicationMapStop):
            validate_budget_publication_map(drift)

    def test_page_count_alignment_does_not_authorize_equivalence(self) -> None:
        drift = copy.deepcopy(self.data)
        drift["guardrails"]["infer_full_equivalence_from_page_count_alignment"] = True
        with self.assertRaises(BudgetPublicationMapStop):
            validate_budget_publication_map(drift)

    def test_journal_cannot_replace_canonical_without_proof(self) -> None:
        drift = copy.deepcopy(self.data)
        drift["guardrails"]["journal_replaces_canonical_pdf_without_equivalence_proof"] = True
        with self.assertRaises(BudgetPublicationMapStop):
            validate_budget_publication_map(drift)

    def test_promotion_remains_forbidden(self) -> None:
        for key in ("silver", "gold", "serving", "publication"):
            with self.subTest(key=key):
                drift = copy.deepcopy(self.data)
                drift["promotion"][key] = True
                with self.assertRaises(BudgetPublicationMapStop):
                    validate_budget_publication_map(drift)


if __name__ == "__main__":
    unittest.main()
