from __future__ import annotations

import json
import unittest
from pathlib import Path

from robo_dados_publicos.manual_ingest.drive_ingestion_controller import (
    DriveIngestionStop,
    classify_metadata,
    load_controller_contract,
    route_inventory,
    summarize_routes,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "config/drive_ingestion_controller.v1.json"
FIXTURE_PATH = ROOT / "tests/fixtures/task_059_drive_ingestion_controller.json"
EVIDENCE_PATH = ROOT / "docs/evidence/TASK_059_DRIVE_INGESTION_CONTROLLER_0.8.0.json"


class Task059DriveIngestionControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_controller_contract(CONTRACT_PATH)
        cls.fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    def test_fixture_routes(self) -> None:
        for item in self.fixtures:
            decision = classify_metadata(item, self.contract)
            self.assertEqual(decision.route, item["expected"], item["title"])

    def test_known_fundeb_is_auto_ingest_routing_only(self) -> None:
        decision = classify_metadata({"id":"x","title":"FUNDEB_LIMEIRA_2026_01.pdf","mime_type":"application/pdf","in_authorized_scope":True,"content_hydrated":False}, self.contract)
        self.assertEqual(decision.route, "AUTO_INGEST")
        self.assertIn("EXECUTION_AUTH_REQUIRED", decision.reasons)
        self.assertFalse(self.contract["content_read_authorized"])
        self.assertFalse(self.contract["bronze_write_authorized"])

    def test_content_hydration_quarantines(self) -> None:
        decision = classify_metadata({"id":"x","title":"LOA_2026.pdf","mime_type":"application/pdf","content_hydrated":True}, self.contract)
        self.assertEqual(decision.route, "QUARANTINE")

    def test_unknown_family_quarantines(self) -> None:
        decision = classify_metadata({"id":"x","title":"foto_festa.pdf","mime_type":"application/pdf"}, self.contract)
        self.assertEqual(decision.route, "QUARANTINE")

    def test_duplicate_file_id_goes_to_review(self) -> None:
        records = [
            {"id":"same","title":"FUNDEB_1.pdf","mime_type":"application/pdf"},
            {"id":"same","title":"FUNDEB_2.pdf","mime_type":"application/pdf"},
        ]
        decisions = route_inventory(records, self.contract)
        self.assertEqual(decisions[0].route, "AUTO_INGEST")
        self.assertEqual(decisions[1].route, "REVIEW")
        self.assertIn("DUPLICATE_METADATA_FILE_ID", decisions[1].reasons)

    def test_route_summary(self) -> None:
        decisions = route_inventory(self.fixtures, self.contract)
        summary = summarize_routes(decisions)
        self.assertEqual(sum(summary.values()), len(self.fixtures))
        self.assertGreater(summary["AUTO_INGEST"], 0)
        self.assertGreater(summary["REVIEW"], 0)
        self.assertGreater(summary["QUARANTINE"], 0)

    def test_contract_rejects_remote_effects(self) -> None:
        raw = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        raw["content_read_authorized"] = True
        temp = ROOT / "tests/fixtures/_tmp_task059_bad_contract.json"
        try:
            temp.write_text(json.dumps(raw), encoding="utf-8")
            with self.assertRaises(DriveIngestionStop):
                load_controller_contract(temp)
        finally:
            if temp.exists():
                temp.unlink()

    def test_evidence_keeps_all_remote_effects_zero(self) -> None:
        self.assertEqual(self.evidence["base_sha"], "e5c6658b1e05fc2d824e5d9cbcc116b0e9f40a5c")
        self.assertTrue(all(value == 0 for value in self.evidence["hard_boundaries"].values()))
        self.assertEqual(self.evidence["task058_status"], "DEFERRED_NOT_EXECUTED")
        self.assertEqual(self.evidence["eiti_transaction_level_financial_identity"], "EVIDENCIA_INSUFICIENTE")
        self.assertEqual(self.evidence["result"], "PASS_TASK059_DRIVE_INGESTION_CONTROLLER_OFFLINE_READY_FOR_METADATA_PILOT")


if __name__ == "__main__":
    unittest.main()
