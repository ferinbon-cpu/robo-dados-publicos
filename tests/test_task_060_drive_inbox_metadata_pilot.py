from __future__ import annotations

import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.drive_ingestion_controller import (
    classify_metadata,
    load_controller_contract,
    route_inventory,
    summarize_routes,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config" / "drive_ingestion_controller.v2.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "task_060_drive_inbox_metadata_pilot.json"
EVIDENCE_PATH = ROOT / "docs" / "evidence" / "TASK_060_DRIVE_INBOX_METADATA_PILOT_0.8.0.json"


class Task060DriveInboxMetadataPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_controller_contract(CONTRACT_PATH)
        cls.fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    def test_all_real_metadata_records_match_expected_route(self) -> None:
        for item in self.fixtures:
            decision = classify_metadata(item, self.contract)
            self.assertEqual(decision.route, item["expected_route"], item["title"])
            self.assertEqual(decision.family, item["expected_family"], item["title"])
            self.assertIn(item["expected_reason"], decision.reasons, item["title"])

    def test_real_pilot_summary_is_nine_review_only(self) -> None:
        summary = summarize_routes(route_inventory(self.fixtures, self.contract))
        self.assertEqual(summary, {"AUTO_INGEST": 0, "REVIEW": 9, "QUARANTINE": 0})
        self.assertEqual(self.evidence["routing_summary"]["total"], 9)
        self.assertEqual(self.evidence["routing_summary"]["REVIEW"], 9)

    def test_jom_planning_sources_fail_closed_as_multiple_family(self) -> None:
        for item in self.fixtures[:3]:
            decision = classify_metadata(item, self.contract)
            self.assertEqual(decision.route, "REVIEW")
            self.assertIsNone(decision.family)
            self.assertIn("MULTIPLE_FAMILY_MATCHES", decision.reasons)

    def test_manifests_are_not_auto_ingested(self) -> None:
        manifests = [item for item in self.fixtures if item["title"].startswith("MANIFEST_")]
        self.assertEqual(len(manifests), 3)
        for item in manifests:
            decision = classify_metadata(item, self.contract)
            self.assertEqual(decision.route, "REVIEW")
            self.assertIn("MULTIPLE_FAMILY_MATCHES", decision.reasons)

    def test_standalone_planning_sources_remain_review_first(self) -> None:
        expected = {"LOA", "LDO", "PPA"}
        observed = set()
        for item in self.fixtures:
            decision = classify_metadata(item, self.contract)
            if decision.family in expected:
                observed.add(decision.family)
                self.assertEqual(decision.route, "REVIEW")
                self.assertIn("KNOWN_FAMILY_REQUIRES_SUPERVISED_REVIEW", decision.reasons)
        self.assertEqual(observed, expected)

    def test_eiti_is_not_ingestion_filter(self) -> None:
        self.assertEqual(self.contract["eiti_role"], "ANALYTIC_USE_CASE_NOT_GLOBAL_INGESTION_FILTER")
        self.assertTrue(self.evidence["interpretation"]["eiti_is_not_global_filter"])

    def test_metadata_boundary_is_zero_content_and_zero_drive_write(self) -> None:
        self.assertFalse(self.contract["content_read_authorized"])
        self.assertFalse(self.contract["drive_write_authorized"])
        self.assertEqual(self.evidence["metadata_contract"]["source_content_reads"], 0)
        self.assertFalse(self.evidence["metadata_contract"]["content_hydration_observed"])
        self.assertTrue(all(value == 0 for value in self.evidence["hard_boundaries"].values()))

    def test_task_result_and_next_gate(self) -> None:
        self.assertEqual(
            self.evidence["result"],
            "PASS_TASK060_10_INBOX_METADATA_ONLY_PILOT_9_REVIEW_0_AUTO_0_QUARANTINE_NO_CONTENT_READ",
        )
        self.assertTrue(self.evidence["next_gate"]["requires_new_authorization"])
        self.assertFalse(self.evidence["next_gate"]["content_read_allowed_by_task060"])


if __name__ == "__main__":
    unittest.main()
