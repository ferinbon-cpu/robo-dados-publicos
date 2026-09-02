from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.budget_journal_source_first import (
    BudgetJournalSourceFirstStop,
    validate_budget_journal_source_first,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "budget_laws_journal_source_first.v1.json"


class Task031BudgetJournalSourceFirstTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_contract_passes(self) -> None:
        result = validate_budget_journal_source_first(self.data)
        self.assertEqual(result["status"], "PASS_TASK_031_BUDGET_LAWS_JOURNAL_SOURCE_FIRST")
        self.assertEqual(result["editions"], [7024, 7119, 7127])
        self.assertFalse(result["equivalence_required_before_extraction"])
        self.assertTrue(result["custody_required_before_extraction"])
        self.assertFalse(result["live_acquisition_authorized"])

    def test_search_index_cannot_be_extraction_source(self) -> None:
        data = copy.deepcopy(self.data)
        data["decision"]["extract_from_search_engine_index"] = True
        with self.assertRaises(BudgetJournalSourceFirstStop):
            validate_budget_journal_source_first(data)

    def test_equivalence_cannot_be_reintroduced_as_extraction_blocker(self) -> None:
        data = copy.deepcopy(self.data)
        data["decision"]["full_equivalence_required_before_extraction"] = True
        with self.assertRaises(BudgetJournalSourceFirstStop):
            validate_budget_journal_source_first(data)

    def test_custody_cannot_be_claimed_before_download_and_hash(self) -> None:
        data = copy.deepcopy(self.data)
        data["journal_editions"][0]["custody_status"] = "READBACK_VERIFIED"
        data["journal_editions"][0]["sha256"] = "0" * 64
        with self.assertRaises(BudgetJournalSourceFirstStop):
            validate_budget_journal_source_first(data)

    def test_drive_writes_remain_create_only(self) -> None:
        for mutation in ("overwrite", "delete", "replace"):
            data = copy.deepcopy(self.data)
            data["target_drive"][mutation] = True
            with self.assertRaises(BudgetJournalSourceFirstStop):
                validate_budget_journal_source_first(data)

    def test_source_url_is_pinned(self) -> None:
        data = copy.deepcopy(self.data)
        data["journal_editions"][2]["source_url"] = "https://example.org/loa.pdf"
        with self.assertRaises(BudgetJournalSourceFirstStop):
            validate_budget_journal_source_first(data)

    def test_no_layer_promotion_is_authorized(self) -> None:
        for layer in ("source_custody", "bronze", "silver", "gold", "serving", "publication"):
            data = copy.deepcopy(self.data)
            data["promotion"][layer] = True
            with self.assertRaises(BudgetJournalSourceFirstStop):
                validate_budget_journal_source_first(data)


if __name__ == "__main__":
    unittest.main()
