from __future__ import annotations

import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.ingestion_execution_policy import (
    decide_execution,
    load_execution_policy,
    promotion_after_ingest,
)

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config" / "ingestion_execution_policy.v1.json"


class Task061Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_execution_policy(POLICY)

    def test_all_prerequisites_allow_only_content_hash_bronze_eligibility(self):
        record = {"id":"x","folder_scope_authorized":True,"content_hydrated":False,"unresolved_duplicate_signal":False}
        decision = decide_execution(record, "AUTO_INGEST", "JORNAL_OFICIAL", self.policy)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.state, "ELIGIBLE_FOR_AUTHORIZED_CONTENT_HASH_BRONZE")

    def test_review_never_auto_executes(self):
        record = {"id":"x","folder_scope_authorized":True,"content_hydrated":False,"unresolved_duplicate_signal":False}
        decision = decide_execution(record, "REVIEW", "PPA", self.policy)
        self.assertFalse(decision.allowed)
        self.assertIn("ROUTE_NOT_AUTO_INGEST", decision.reasons)

    def test_folder_scope_required(self):
        record = {"id":"x","folder_scope_authorized":False,"content_hydrated":False,"unresolved_duplicate_signal":False}
        self.assertFalse(decide_execution(record, "AUTO_INGEST", "SIOPE", self.policy).allowed)

    def test_duplicate_signal_blocks(self):
        record = {"id":"x","folder_scope_authorized":True,"content_hydrated":False,"unresolved_duplicate_signal":True}
        self.assertFalse(decide_execution(record, "AUTO_INGEST", "SIOPE", self.policy).allowed)

    def test_schema_drift_stops_before_silver(self):
        self.assertEqual(promotion_after_ingest(schema_valid=False, qa_valid=True, reconciliation_valid=True), "STOP_BEFORE_SILVER_SCHEMA_DRIFT")

    def test_gold_remains_separate_gate(self):
        self.assertEqual(promotion_after_ingest(schema_valid=True, qa_valid=True, reconciliation_valid=True), "ELIGIBLE_FOR_SEPARATE_GOLD_GATE")


if __name__ == "__main__":
    unittest.main()
