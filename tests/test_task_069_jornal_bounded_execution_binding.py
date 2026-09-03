from __future__ import annotations

import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.jornal_execution_binding import (
    downstream_auto_promotion_allowed,
    evaluate_new_edition_candidate,
    load_jornal_profile,
)

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "config" / "jornal_bounded_execution_profile.v1.json"


class Task069Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profile = load_jornal_profile(PROFILE)

    def candidate(self, **overrides):
        base = {
            "edition": 7316,
            "publication_date": "2026-09-01",
            "family": "JORNAL_OFICIAL",
            "duplicate_edition": False,
            "discovery_requests": 1,
            "discovery_pages": 1,
            "authorization_enabled": True,
        }
        base.update(overrides)
        return base

    def test_valid_new_candidate_is_only_live_gate_eligible(self):
        state, reasons = evaluate_new_edition_candidate(self.candidate(), self.profile)
        self.assertEqual(state, "ELIGIBLE_FOR_BOUNDED_LIVE_JORNAL_GATE")
        self.assertIn("ALL_BOUNDED_REQUIREMENTS_SATISFIED", reasons)

    def test_old_edition_stops(self):
        state, reasons = evaluate_new_edition_candidate(self.candidate(edition=7315), self.profile)
        self.assertEqual(state, "STOP_TO_REVIEW")
        self.assertIn("EDITION_NOT_GREATER_THAN_CHECKPOINT", reasons)

    def test_old_date_stops(self):
        state, reasons = evaluate_new_edition_candidate(self.candidate(publication_date="2026-08-28"), self.profile)
        self.assertEqual(state, "STOP_TO_REVIEW")
        self.assertIn("PUBLICATION_DATE_OLDER_THAN_CHECKPOINT_FRONTIER", reasons)

    def test_missing_separate_authorization_stops(self):
        state, reasons = evaluate_new_edition_candidate(self.candidate(authorization_enabled=False), self.profile)
        self.assertEqual(state, "STOP_TO_REVIEW")
        self.assertIn("SEPARATE_EXECUTION_AUTHORIZATION_MISSING", reasons)

    def test_discovery_bound_is_enforced(self):
        state, reasons = evaluate_new_edition_candidate(self.candidate(discovery_requests=9), self.profile)
        self.assertEqual(state, "STOP_TO_REVIEW")
        self.assertIn("DISCOVERY_REQUEST_LIMIT_EXCEEDED", reasons)

    def test_recurrence_and_downstream_promotion_remain_disabled(self):
        self.assertEqual(self.profile["recurrence_status"], "NOT_GLOBALLY_PROMOTED")
        self.assertFalse(self.profile["schedule_authorized"])
        self.assertFalse(self.profile["live_execution_authorized_by_task_069"])
        self.assertFalse(downstream_auto_promotion_allowed(self.profile))


if __name__ == "__main__":
    unittest.main()
