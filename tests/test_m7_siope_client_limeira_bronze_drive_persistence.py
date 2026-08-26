from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_bronze_drive_persistence import (
    DrivePersistenceError,
    load_json as load_drive_json,
    persist_bundle,
    validate_config,
)
from robo_dados_publicos.sources.siope_client_limeira_bronze_single_record_capture_review import (
    ReviewError,
    load_json as load_review_json,
    run_review,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_bronze_single_record_capture_review.json"
DRIVE_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_bronze_drive_persistence.json"
EVIDENCE = ROOT / "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_CAPTURE_RUN_1_0.8.0.json"
RECORD = ROOT / "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_RUN_1_RECORD_0.8.0.json"
MANIFEST = ROOT / "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_RUN_1_MANIFEST_0.8.0.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-bronze-drive-persistence-gate.yml"


class FakeDrive:
    def __init__(self, *, collision: bool = False):
        self.collision = collision
        self.find_calls = []
        self.put_calls = []

    def find_by_name(self, parent_id, name):
        self.find_calls.append((parent_id, name))
        return [{"id": "existing"}] if self.collision else []

    def put(self, local_path, remote_name, parent_id=None, mime_type="application/octet-stream"):
        raw = Path(local_path).read_bytes()
        self.put_calls.append((raw, remote_name, parent_id, mime_type))
        return {
            "id": "not-exposed-by-result",
            "name": remote_name,
            "mimeType": mime_type,
            "size": str(len(raw)),
            "parents": [parent_id],
            "md5Checksum": hashlib.md5(raw).hexdigest(),  # noqa: S324
        }


class BronzeDrivePersistenceTests(unittest.TestCase):
    def test_pinned_capture_review_passes_offline(self):
        result = run_review(
            load_review_json(REVIEW_CONFIG),
            load_review_json(EVIDENCE),
            evidence_path=EVIDENCE,
            record_path=RECORD,
            manifest_path=MANIFEST,
        )
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW")
        self.assertFalse(result["network_called"])
        self.assertTrue(result["durable_bronze_drive_persistence_design_authorized"])
        self.assertFalse(result["processing_authorized"])

    def test_tampered_capture_evidence_fails_closed(self):
        evidence = load_review_json(EVIDENCE)
        evidence["artifact_digest"] = "sha256:" + "0" * 64
        with self.assertRaises(ReviewError):
            run_review(
                load_review_json(REVIEW_CONFIG),
                evidence,
                evidence_path=EVIDENCE,
                record_path=RECORD,
                manifest_path=MANIFEST,
            )

    def test_drive_design_is_exact_and_network_free(self):
        result = validate_config(load_drive_json(DRIVE_CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_PERSISTENCE_DESIGN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["source_network_called"])
        self.assertEqual(result["drive_write_count"], 0)
        self.assertEqual(result["bundle_bytes"], 2461)
        self.assertEqual(
            result["bundle_sha256"],
            "eb30b820c34a702a5850b1e246d7d29a8d86c0e84064b79b14c0308060950dbf",
        )

    def test_mocked_live_persists_exactly_one_create_only_bundle(self):
        drive = FakeDrive()
        result = persist_bundle(load_drive_json(DRIVE_CONFIG), root=ROOT, drive=drive)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_PERSISTENCE")
        self.assertEqual(result["drive_write_count"], 1)
        self.assertTrue(result["drive_create_only"])
        self.assertFalse(result["source_network_called"])
        self.assertFalse(result["remote_file_id_persisted"])
        self.assertEqual(len(drive.find_calls), 1)
        self.assertEqual(len(drive.put_calls), 1)
        raw, remote_name, parent_id, mime_type = drive.put_calls[0]
        self.assertEqual(parent_id, "18yR-e6I1VCiy7XqG7Zhr0vUIJF0qA_MG")
        self.assertEqual(mime_type, "application/json")
        self.assertTrue(remote_name.endswith("__20dd61298f9d__bundle.json"))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), result["bundle_sha256"])
        bundle = json.loads(raw.decode("utf-8"))
        self.assertEqual(bundle["manifest"]["record_sha256"], result["record_sha256"])
        self.assertEqual(bundle["record"]["COD_MUNI"], 352690)
        self.assertEqual(len(bundle["record"]), 52)
        self.assertFalse(result["silver_authorized"])
        self.assertFalse(result["gold_authorized"])
        self.assertFalse(result["processing_authorized"])

    def test_remote_name_collision_stops_before_write(self):
        drive = FakeDrive(collision=True)
        with self.assertRaises(DrivePersistenceError):
            persist_bundle(load_drive_json(DRIVE_CONFIG), root=ROOT, drive=drive)
        self.assertEqual(len(drive.find_calls), 1)
        self.assertEqual(drive.put_calls, [])

    def test_config_drift_cannot_enable_processing_or_overwrite(self):
        for key in ("overwrite_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
            with self.subTest(key=key):
                config = copy.deepcopy(load_drive_json(DRIVE_CONFIG))
                config[key] = True
                with self.assertRaises(DrivePersistenceError):
                    validate_config(config, root=ROOT)

    def test_workflow_is_manual_single_drive_write_and_full_qa_precedes_live(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_bronze_drive_persistence", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("GOOGLE_DRIVE_CLIENT_ID: ${{ secrets.GOOGLE_DRIVE_CLIENT_ID }}", text)
        self.assertIn("github_siope_client_limeira_bronze_single_record_capture_review_gate.py", text)
        self.assertIn("github_siope_client_limeira_bronze_drive_persistence_gate.py --dry-run", text)
        unit_pos = text.index("python -m unittest discover -s tests -v")
        regression_pos = text.index("python main.py selftest")
        live_pos = text.index("Persistir exatamente um bundle imutável no 01_BRONZE")
        self.assertLess(unit_pos, live_pos)
        self.assertLess(regression_pos, live_pos)
        self.assertNotIn("SiopeClient(", text)
        self.assertNotIn("Dados_Gerais_Siope(", text)
        self.assertNotIn("replace_content", text)
        self.assertNotIn(".delete(", text)
        self.assertNotIn("02_SILVER", text)
        self.assertNotIn("03_GOLD", text)


if __name__ == "__main__":
    unittest.main()
