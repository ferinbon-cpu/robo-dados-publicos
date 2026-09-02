from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.task056_f01_secondary_education_source_bounded_content_read import (
    Task056Error,
    validate_task056_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "docs/evidence/TASK_056_F01_SECONDARY_EDUCATION_SOURCE_BOUNDED_CONTENT_READ_0.8.0.json"
UPSTREAM_PATH = ROOT / "docs/evidence/TASK_055A_F01_EITI_TERMINOLOGY_ONTOLOGY_0.8.0.json"


class Task056Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
        cls.upstream = json.loads(UPSTREAM_PATH.read_text(encoding="utf-8"))

    def test_canonical_evidence_passes(self) -> None:
        result = validate_task056_evidence(copy.deepcopy(self.evidence), copy.deepcopy(self.upstream))
        self.assertEqual(
            result["status"],
            "PASS_TASK056_MAVS_FOMENTO_ETI_REPORTING_IDENTITY_PARTIAL_NO_TRANSACTION_LINKAGE_NO_PROMOTION",
        )

    def test_other_source_read_fails_closed(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["effects"]["other_source_content_reads"] = 1
        with self.assertRaises(Task056Error):
            validate_task056_evidence(evidence, copy.deepcopy(self.upstream))

    def test_zero_cannot_be_generalized(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["interpretation"]["zero_value_must_not_be_generalized_beyond_fundeb_fomento_eti_bucket_and_period"] = False
        with self.assertRaises(Task056Error):
            validate_task056_evidence(evidence, copy.deepcopy(self.upstream))

    def test_reporting_identity_cannot_be_promoted_to_transaction_identity(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["fomento_eti_reporting_findings"]["transaction_level_eiti_financial_identity_proven"] = True
        with self.assertRaises(Task056Error):
            validate_task056_evidence(evidence, copy.deepcopy(self.upstream))

    def test_fomento_eti_alias_must_be_preserved(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["ontology_scan"]["new_alias_discovered"]["must_be_added_to_future_matching"] = False
        with self.assertRaises(Task056Error):
            validate_task056_evidence(evidence, copy.deepcopy(self.upstream))

    def test_gold_must_remain_blocked(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["promotion"]["gold"] = True
        with self.assertRaises(Task056Error):
            validate_task056_evidence(evidence, copy.deepcopy(self.upstream))

    def test_next_gate_must_be_metadata_only(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["next_bounded_gate"]["no_source_content_read"] = False
        with self.assertRaises(Task056Error):
            validate_task056_evidence(evidence, copy.deepcopy(self.upstream))


if __name__ == "__main__":
    unittest.main()
