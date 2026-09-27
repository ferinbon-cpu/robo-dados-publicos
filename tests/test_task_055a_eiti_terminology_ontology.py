from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.task055a_eiti_terminology_ontology import (
    RESULT,
    Task055AError,
    validate_task055a_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
E55A = ROOT / "docs/evidence/TASK_055A_F01_EITI_TERMINOLOGY_ONTOLOGY_0.8.0.json"
E55 = ROOT / "docs/evidence/TASK_055_F01_SELECTED_GRANULAR_SOURCE_BOUNDED_CONTENT_READ_0.8.0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class Task055AOntologyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.e55a = load(E55A)
        self.e55 = load(E55)

    def test_canonical_ontology_passes(self) -> None:
        result = validate_task055a_evidence(self.e55a, self.e55)
        self.assertEqual(result["status"], RESULT)
        self.assertEqual(result["family_count"], 5)
        self.assertTrue(result["ontology_required_for_task056"])

    def test_eiti_only_is_not_enough_ontology(self) -> None:
        e = copy.deepcopy(self.e55a)
        e["ontology"]["A_CANONICAL_POLICY_IDENTIFIERS"] = ["EITI"]
        with self.assertRaises(Task055AError):
            validate_task055a_evidence(e, self.e55)

    def test_local_planning_aliases_are_required(self) -> None:
        e = copy.deepcopy(self.e55a)
        e["ontology"]["B_LOCAL_PLANNING_AND_NORMATIVE_ALIASES"].remove("indice de alunos em Educacao Integral")
        with self.assertRaises(Task055AError):
            validate_task055a_evidence(e, self.e55)

    def test_finance_terms_cannot_be_promoted_alone(self) -> None:
        e = copy.deepcopy(self.e55a)
        e["matching_rules"]["finance_signal_rule"] = "FUNDEB_ALONE_PROVES_EITI"
        with self.assertRaises(Task055AError):
            validate_task055a_evidence(e, self.e55)

    def test_task055_lexical_absence_must_remain_non_exhaustive(self) -> None:
        e = copy.deepcopy(self.e55a)
        e["task055_reinterpretation"]["pre_055a_lexical_negative_search_is_exhaustive"] = True
        with self.assertRaises(Task055AError):
            validate_task055a_evidence(e, self.e55)

    def test_task056_must_use_all_families(self) -> None:
        e = copy.deepcopy(self.e55a)
        e["future_task056_contract"]["search_all_five_term_families"] = False
        with self.assertRaises(Task055AError):
            validate_task055a_evidence(e, self.e55)


if __name__ == "__main__":
    unittest.main()
