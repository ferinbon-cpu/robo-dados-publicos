from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = ROOT / "config/normative_sme_legal_coverage.v1.json"


class TestTask222SMELegalV3Coverage(unittest.TestCase):
    def setUp(self) -> None:
        self.obj = json.loads(COVERAGE.read_text(encoding="utf-8"))
        self.items = self.obj["items"]

    def test_schema_source_and_total(self) -> None:
        self.assertEqual(self.obj["schema"], "NORMATIVE_SME_LEGAL_COVERAGE_V1")
        self.assertEqual(self.obj["task"], "TASK_222")
        self.assertEqual(self.obj["issue"], 755)
        self.assertEqual(self.obj["source"]["version"], "v3.0")
        self.assertEqual(self.obj["counts"]["total_items"], 74)
        self.assertEqual(len(self.items), 74)
        self.assertEqual([x["id"] for x in self.items], [f"SMELEGAL-{i:03d}" for i in range(1, 75)])

    def test_declared_counts_match_rows(self) -> None:
        by_status = Counter(row["status"] for row in self.items)
        by_group = Counter(row["group"] for row in self.items)
        self.assertEqual(dict(by_status), self.obj["counts"]["by_status"])
        self.assertEqual(dict(by_group), self.obj["counts"]["by_group"])
        self.assertEqual(by_status["INTEGRADO_CORPUS"], 11)
        self.assertEqual(by_status["PARCIAL"], 28)
        self.assertEqual(by_status["PENDENTE_CORPUS_INTEGRAL"], 34)
        self.assertEqual(by_status["LACUNA_CONFIRMADA"], 1)

    def test_vale_alimentacao_remains_confirmed_gap(self) -> None:
        gaps = [x for x in self.items if x["status"] == "LACUNA_CONFIRMADA"]
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["id"], "SMELEGAL-068")
        self.assertEqual(gaps[0]["item"], "Instrução de Serviço nº 4: Vale Alimentação")

    def test_integrated_corpus_does_not_claim_current_vigency(self) -> None:
        self.assertIn("INTEGRADO_CORPUS_NE_CURRENT_VIGENCY_PROOF", self.obj["guards"])
        self.assertIn("SYNTHESIS_NE_LEGAL_PROOF", self.obj["guards"])
        self.assertEqual(
            self.obj["precedence"][0],
            "EXACT_OFFICIAL_NORMATIVE_DOCUMENT_WITH_CURRENT_VIGENCY_CHECK",
        )
        self.assertIn("does not by itself prove current vigency", self.obj["semantics"]["INTEGRADO_CORPUS"])

    def test_partial_pending_and_gap_are_fail_closed_states(self) -> None:
        self.assertIn("PARTIAL_PENDING_GAP_MUST_BE_DECLARED", self.obj["guards"])
        self.assertEqual(
            {x["status"] for x in self.items},
            {"INTEGRADO_CORPUS", "PARCIAL", "PENDENTE_CORPUS_INTEGRAL", "LACUNA_CONFIRMADA"},
        )

    def test_contextual_coverage_and_remote_effects_unchanged(self) -> None:
        cov = self.obj["canonical_contextual_coverage"]
        self.assertEqual((cov["answerable"], cov["total"]), (38, 38))
        self.assertFalse(cov["changed_by_this_task"])
        self.assertTrue(all(value is False for value in self.obj["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
