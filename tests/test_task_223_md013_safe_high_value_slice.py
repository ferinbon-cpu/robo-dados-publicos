from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/md_01_3_safe_high_value_slice.v1.json"


def expand_token(token: str) -> set[str]:
    if ".." not in token:
        return {token}
    left, right = token.split("..", 1)
    a = int(re.search(r"(\d+)$", left).group(1))
    b = int(re.search(r"(\d+)$", right).group(1))
    return {f"DOC-{i:03d}" for i in range(a, b + 1)}


def expand(tokens: list[str]) -> set[str]:
    out: set[str] = set()
    for token in tokens:
        out |= expand_token(token)
    return out


class TestTask223MD013SafeHighValueSlice(unittest.TestCase):
    def setUp(self) -> None:
        self.obj = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_partition_is_exact_and_complete(self) -> None:
        part = self.obj["partition"]
        self.assertEqual(part["eligible_high_value_public_institutional"], 101)
        self.assertEqual(part["excluded_personnel_or_payroll"], 93)
        self.assertEqual(part["total"], 194)
        self.assertTrue(part["partition_complete"])

        eligible = expand(self.obj["eligibility_rule"]["included_id_ranges"])
        excluded = expand(self.obj["eligibility_rule"]["excluded_id_ranges"])
        universe = {f"DOC-{i:03d}" for i in range(1, 195)}
        self.assertEqual(len(eligible), 101)
        self.assertEqual(len(excluded), 93)
        self.assertFalse(eligible & excluded)
        self.assertEqual(eligible | excluded, universe)

    def test_family_counts_reconstruct_eligible_set(self) -> None:
        eligible = expand(self.obj["eligibility_rule"]["included_id_ranges"])
        family_union: set[str] = set()
        count_sum = 0
        for family in self.obj["eligible_families"].values():
            ids = expand(family["ids"])
            self.assertEqual(len(ids), family["count"])
            self.assertFalse(family_union & ids)
            family_union |= ids
            count_sum += family["count"]
        self.assertEqual(count_sum, 101)
        self.assertEqual(family_union, eligible)

    def test_personnel_families_are_fully_excluded(self) -> None:
        excluded = expand(self.obj["eligibility_rule"]["excluded_id_ranges"])
        excluded_union: set[str] = set()
        for family in self.obj["excluded_families"].values():
            ids = expand(family["ids"])
            self.assertEqual(len(ids), family["count"])
            self.assertFalse(excluded_union & ids)
            excluded_union |= ids
        self.assertEqual(excluded_union, excluded)
        self.assertEqual(self.obj["excluded_families"]["FOLHA_HOLERITES"]["count"], 70)
        self.assertEqual(self.obj["excluded_families"]["QUADRO_FUNCIONARIOS"]["count"], 22)
        self.assertEqual(self.obj["excluded_families"]["CARGOS_SALARIOS"]["count"], 1)

    def test_sem_texto_is_preserved_and_not_repaired_silently(self) -> None:
        locators = {x["id"]: x for x in self.obj["exact_high_value_locators"]}
        self.assertEqual(locators["DOC-065"]["status"], "sem_texto")
        self.assertEqual(locators["DOC-100"]["status"], "sem_texto")
        self.assertEqual(
            locators["DOC-100"]["operational_content_status"],
            "SUPERSEDED_FOR_CONTENT_BY_F01_CANONICAL_JOM_CHAIN",
        )
        self.assertIn("SEM_TEXTO_NE_EMPTY_OR_ZERO", self.obj["guards"])

    def test_high_value_first_targets_are_education_balancete_and_cocem(self) -> None:
        targets = self.obj["next_incremental_targets"]
        self.assertEqual(targets[0]["id"], "DOC-066")
        self.assertEqual(targets[1]["id"], "DOC-105")
        self.assertEqual(targets[0]["priority"], 1)
        self.assertEqual(targets[1]["priority"], 2)

    def test_no_numeric_or_coverage_promotion(self) -> None:
        self.assertIn("TRANSCRIPTION_NE_STRUCTURED_NUMERIC_TRUTH", self.obj["guards"])
        self.assertIn("F01_F02_OVERLAP_MUST_NOT_BE_REINGESTED_AS_NEW_FACT", self.obj["guards"])
        cov = self.obj["canonical_contextual_coverage"]
        self.assertEqual((cov["answerable"], cov["total"]), (38, 38))
        self.assertFalse(cov["changed_by_this_task"])
        self.assertTrue(all(v is False for v in self.obj["remote_effects"].values()))


if __name__ == "__main__":
    unittest.main()
