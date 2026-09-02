from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from robo_dados_publicos.manual_ingest.live_probe_review import (
    LiveProbeReviewStop,
    review_live_probe,
)


ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class Task029LiveProbeReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load("config/loa_official_equivalence_live_probe_review.v1.json")
        self.evidence = load("docs/evidence/TASK_029_LOA_OFFICIAL_EQUIVALENCE_LIVE_PROBE_0.8.0.json")

    def test_review_passes_fail_closed(self) -> None:
        result = review_live_probe(self.contract, self.evidence)
        self.assertEqual(result["status"], "PASS_TASK_029_LIVE_PROBE_REVIEW_FAIL_CLOSED")
        self.assertEqual(result["request_count"], 3)
        self.assertEqual(result["accessible_initial_surfaces"], 1)
        self.assertEqual(result["blocked_initial_surfaces"], 2)
        self.assertFalse(result["equivalence_proven"])
        self.assertFalse(result["absence_proven"])

    def test_rejects_unpinned_authorization(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["authorization"]["authorized_against_sha"] = "0" * 40
        with self.assertRaises(LiveProbeReviewStop):
            review_live_probe(contract, self.evidence)

    def test_rejects_candidate_followup_authorization(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["authorization"]["candidate_followup"] = True
        with self.assertRaises(LiveProbeReviewStop):
            review_live_probe(contract, self.evidence)

    def test_rejects_extra_request(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["probe"]["request_count"] = 4
        with self.assertRaises(LiveProbeReviewStop):
            review_live_probe(self.contract, evidence)

    def test_rejects_retry(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["probe"]["retry_count"] = 1
        with self.assertRaises(LiveProbeReviewStop):
            review_live_probe(self.contract, evidence)

    def test_rejects_followup_effect(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["probe"]["candidate_followup_count"] = 1
        with self.assertRaises(LiveProbeReviewStop):
            review_live_probe(self.contract, evidence)

    def test_rejects_download(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["probe"]["document_download_count"] = 1
        with self.assertRaises(LiveProbeReviewStop):
            review_live_probe(self.contract, evidence)

    def test_rejects_url_drift(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["probe"]["observations"][0]["url"] = "https://example.com/"
        with self.assertRaises(LiveProbeReviewStop):
            review_live_probe(self.contract, evidence)

    def test_rejects_equivalence_claim(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["claims"]["machine_readable_equivalent_proven"] = True
        with self.assertRaises(LiveProbeReviewStop):
            review_live_probe(self.contract, evidence)

    def test_rejects_absence_claim(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["claims"]["absence_of_equivalent_source_proven"] = True
        with self.assertRaises(LiveProbeReviewStop):
            review_live_probe(self.contract, evidence)

    def test_rejects_silver_write(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["effects"]["silver_writes"] = 1
        with self.assertRaises(LiveProbeReviewStop):
            review_live_probe(self.contract, evidence)

    def test_rejects_non_fail_closed_result(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence["result"] = "PASS_EQUIVALENCE_PROVEN"
        with self.assertRaises(LiveProbeReviewStop):
            review_live_probe(self.contract, evidence)


if __name__ == "__main__":
    unittest.main()
