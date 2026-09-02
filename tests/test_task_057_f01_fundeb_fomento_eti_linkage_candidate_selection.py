from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.task057_f01_fundeb_fomento_eti_linkage_candidate_selection import (
    Task057Error,
    validate_task057_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "docs/evidence/TASK_057_F01_FUNDEB_FOMENTO_ETI_LINKAGE_CANDIDATE_SELECTION_0.8.0.json"
UPSTREAM_PATH = ROOT / "docs/evidence/TASK_056_F01_SECONDARY_EDUCATION_SOURCE_BOUNDED_CONTENT_READ_0.8.0.json"


class Task057Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        cls.upstream = json.loads(UPSTREAM_PATH.read_text(encoding="utf-8"))

    def test_canonical_evidence_passes(self) -> None:
        result = validate_task057_evidence(copy.deepcopy(self.evidence), copy.deepcopy(self.upstream))
        self.assertEqual(
            result["status"],
            "PASS_TASK057_METADATA_ONLY_TIE_NO_EVIDENTIARY_BEST_CANDIDATE_NEXT_PROBE_SELECTED_BY_STABLE_ORDER_NO_PROMOTION",
        )

    def test_content_hydration_fails_closed(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["candidate_set"][0]["content_hydrated"] = True
        with self.assertRaises(Task057Error):
            validate_task057_evidence(evidence, copy.deepcopy(self.upstream))

    def test_source_content_read_fails_closed(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["effects"]["source_content_reads"] = 1
        with self.assertRaises(Task057Error):
            validate_task057_evidence(evidence, copy.deepcopy(self.upstream))

    def test_metadata_cannot_invent_best_candidate(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["selection_analysis"]["best_candidate_evidentially_resolved"] = True
        with self.assertRaises(Task057Error):
            validate_task057_evidence(evidence, copy.deepcopy(self.upstream))

    def test_suffix_cannot_be_probative_ranking(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["selection_analysis"]["suffix_01_02_03_must_not_be_treated_as_evidence_of_superior_granularity"] = False
        with self.assertRaises(Task057Error):
            validate_task057_evidence(evidence, copy.deepcopy(self.upstream))

    def test_next_probe_must_not_be_claimed_best(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["deterministic_next_probe"]["selected_is_claimed_best"] = True
        with self.assertRaises(Task057Error):
            validate_task057_evidence(evidence, copy.deepcopy(self.upstream))

    def test_future_content_read_requires_fresh_auth(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["next_bounded_gate"]["fresh_owner_authorization_required"] = False
        with self.assertRaises(Task057Error):
            validate_task057_evidence(evidence, copy.deepcopy(self.upstream))

    def test_gold_stays_blocked(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["promotion"]["gold"] = True
        with self.assertRaises(Task057Error):
            validate_task057_evidence(evidence, copy.deepcopy(self.upstream))


if __name__ == "__main__":
    unittest.main()
