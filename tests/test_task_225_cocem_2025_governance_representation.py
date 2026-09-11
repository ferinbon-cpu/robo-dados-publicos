from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/cocem_2025_governance_representation.v1.json"


class TestTask225Cocem2025GovernanceRepresentation(unittest.TestCase):
    def setUp(self) -> None:
        self.obj = json.loads(CONFIG.read_text(encoding="utf-8"))
        self.rows = self.obj["annex_ii"]["rows"]

    def test_source_and_event_scope(self) -> None:
        src = self.obj["source"]
        self.assertEqual(src["md_01_3_id"], "DOC-105")
        self.assertEqual(src["pages"], 11)
        self.assertEqual(src["key_pages"]["annex_ii"], [9, 10])
        self.assertIn("BYTE_HASH_NOT_PROVEN", src["source_identity"])
        self.assertEqual(self.obj["event"]["conference_dates"], ["2025-10-24", "2025-10-25"])
        self.assertEqual(self.obj["event"]["preconference_period"], {"start": "2025-09-11", "end": "2025-10-03"})

    def test_annex_ii_is_complete_and_totals_reconstruct(self) -> None:
        annex = self.obj["annex_ii"]
        self.assertEqual(len(self.rows), 69)
        self.assertEqual(annex["unit_count"], 69)
        self.assertEqual(sum(r["teacher_delegate_slots"] for r in self.rows), 111)
        self.assertEqual(annex["teacher_delegate_slots_total"], 111)
        self.assertEqual(len({r["school_name_source"] for r in self.rows}), 69)
        self.assertTrue(all(r["source_page"] in {9, 10} for r in self.rows))

    def test_school_type_distribution_and_known_rows(self) -> None:
        counts = Counter()
        for row in self.rows:
            name = row["school_name_source"]
            if name.startswith("CEIEF "):
                counts["CEIEF"] += 1
            elif name.startswith("CI "):
                counts["CI"] += 1
            elif name.startswith("EMEI "):
                counts["EMEI"] += 1
            elif name.startswith("EMEIEF "):
                counts["EMEIEF"] += 1
        self.assertEqual(counts, Counter({"EMEIEF": 33, "CI": 25, "CEIEF": 7, "EMEI": 4}))
        by_name = {r["school_name_source"]: r["teacher_delegate_slots"] for r in self.rows}
        self.assertEqual(by_name["CEIEF RAFAEL AFFONSO LEITE"], 3)
        self.assertEqual(by_name["EMEIEF MARIA APPª DE LUCA MOORE, PROFª"], 5)

    def test_governance_rules_preserve_source_semantics(self) -> None:
        gov = self.obj["governance"]
        self.assertEqual(gov["teacher_delegate_rule"]["source_article"], "Art. 5º, II")
        self.assertTrue(gov["teacher_delegate_rule"]["election_by_peers"])
        self.assertEqual(gov["decision_rule"]["source_article"], "Art. 11, III")
        self.assertIn("maioria simples", gov["decision_rule"]["rule"])
        self.assertEqual(gov["financial_rule"]["source_article"], "Art. 14")
        self.assertFalse(gov["financial_rule"]["amount_proven"])

    def test_privacy_and_overclaim_guards(self) -> None:
        self.assertFalse(self.obj["privacy"]["personal_data_materialized"])
        dumped = json.dumps(self.obj, ensure_ascii=False).lower()
        self.assertNotIn('"cpf":', dumped)
        guards = set(self.obj["guards"])
        self.assertIn("PLANNED_DELEGATE_SLOTS_NE_ACTUAL_ATTENDANCE", guards)
        self.assertIn("REGIMENTO_NE_FINAL_MINUTES", guards)
        self.assertIn("PROPOSAL_PRESENTED_NE_PROPOSAL_APPROVED", guards)
        self.assertIn("ARTICLE_14_BUDGET_SOURCE_NE_EXPENDITURE_AMOUNT", guards)
        self.assertIn("COCEM_2025_RULES_NE_OTHER_COCEM_EDITIONS", guards)

    def test_no_contextual_coverage_or_remote_effect_inflation(self) -> None:
        cov = self.obj["canonical_contextual_coverage"]
        self.assertEqual((cov["answerable"], cov["total"]), (38, 38))
        self.assertFalse(cov["changed_by_this_task"])
        self.assertTrue(all(value is False for value in self.obj["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
