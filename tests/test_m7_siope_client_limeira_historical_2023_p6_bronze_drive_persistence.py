from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_historical_2023_p6_bronze_drive_persistence import (
    Historical2023P6DrivePersistenceError,
    load_json as load_drive_json,
    persist_bundle,
    validate_config,
)
from robo_dados_publicos.sources.siope_client_limeira_historical_2023_p6_bronze_single_record_capture_review import (
    Historical2023P6BronzeCaptureReviewError,
    load_json as load_review_json,
    run_review,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2023_p6_bronze_single_record_capture_review.json"
DRIVE_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2023_p6_bronze_drive_persistence.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-historical-2023-p6-bronze-drive-persistence-gate.yml"


class FakeDrive:
    def __init__(self, *, collision: bool = False):
        self.collision = collision
        self.put_calls = []

    def find_by_name(self, folder_id: str, name: str):
        if self.collision:
            return [{"id": "existing", "name": name}]
        return []

    def put(self, local: Path, remote_name: str, folder_id: str, mime_type: str):
        raw = Path(local).read_bytes()
        self.put_calls.append((remote_name, folder_id, mime_type, raw))
        return {
            "name": remote_name,
            "mimeType": mime_type,
            "size": str(len(raw)),
            "md5Checksum": hashlib.md5(raw).hexdigest(),  # noqa: S324
        }


class Historical2023P6BronzeDrivePersistenceTests(unittest.TestCase):
    def test_pinned_capture_review_passes_offline(self):
        result = run_review(load_review_json(REVIEW_CONFIG), root=ROOT)
        self.assertEqual(
            result["status"],
            "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW",
        )
        self.assertEqual(result["pinned_year"], 2023)
        self.assertEqual(result["pinned_period"], 6)
        self.assertEqual(result["record_schema_key_count"], 52)
        self.assertTrue(result["durable_historical_bronze_drive_persistence_design_authorized"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["network_called"])

    def test_review_rejects_config_drift(self):
        config = copy.deepcopy(load_review_json(REVIEW_CONFIG))
        config["pinned_run_id"] += 1
        with self.assertRaisesRegex(Historical2023P6BronzeCaptureReviewError, "CONFIG"):
            run_review(config, root=ROOT)

    def test_review_rejects_pinned_evidence_blob_drift(self):
        config = load_review_json(REVIEW_CONFIG)
        with tempfile.TemporaryDirectory() as td:
            temp_root = Path(td)
            for key in ("pinned_evidence_path", "pinned_record_payload_path", "pinned_manifest_payload_path"):
                src = ROOT / config[key]
                dst = temp_root / config[key]
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
            evidence_path = temp_root / config["pinned_evidence_path"]
            evidence_path.write_text(evidence_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
            with self.assertRaisesRegex(Historical2023P6BronzeCaptureReviewError, "EVIDENCE_BLOB"):
                run_review(config, root=temp_root)

    def test_drive_design_is_exact_create_only_and_source_offline(self):
        result = validate_config(load_drive_json(DRIVE_CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE_DESIGN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["source_network_called"])
        self.assertEqual(result["drive_write_count"], 0)
        self.assertEqual(result["bundle_bytes"], 2086)
        self.assertEqual(result["bundle_sha256"], "929a999672343b0e423283dcbd8f1ba797f9f924cecaee00b70b37b312ec2dfc")
        self.assertFalse(result["historical_collection_authorized"])

    def test_drive_config_drift_cannot_enable_bulk_overwrite_processing_or_recurrence(self):
        base = load_drive_json(DRIVE_CONFIG)
        for key in (
            "historical_collection_authorized",
            "overwrite_authorized",
            "delete_authorized",
            "replace_authorized",
            "source_network_authorized",
            "silver_authorized",
            "gold_authorized",
            "processing_authorized",
            "recurrence_authorized",
            "schedule_enabled",
        ):
            config = copy.deepcopy(base)
            config[key] = True
            with self.subTest(key=key), self.assertRaisesRegex(Historical2023P6DrivePersistenceError, "CONFIG"):
                validate_config(config, root=ROOT)

    def test_mocked_drive_persists_exactly_one_historical_bundle(self):
        drive = FakeDrive()
        result = persist_bundle(load_drive_json(DRIVE_CONFIG), root=ROOT, drive=drive)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE")
        self.assertEqual(result["drive_write_count"], 1)
        self.assertTrue(result["drive_create_only"])
        self.assertFalse(result["source_network_called"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertEqual(len(drive.put_calls), 1)
        remote_name, folder_id, mime_type, raw = drive.put_calls[0]
        self.assertIn("__2023_P6__", remote_name)
        self.assertEqual(folder_id, "18yR-e6I1VCiy7XqG7Zhr0vUIJF0qA_MG")
        self.assertEqual(mime_type, "application/json")
        payload = json.loads(raw)
        self.assertEqual(payload["record"]["NUM_ANO"], 2023)
        self.assertEqual(payload["record"]["NUM_PERI"], 6)
        self.assertEqual(payload["manifest"]["record_sha256"], result["record_sha256"])

    def test_remote_name_collision_fails_closed_without_write(self):
        drive = FakeDrive(collision=True)
        with self.assertRaisesRegex(Historical2023P6DrivePersistenceError, "REMOTE_NAME_COLLISION"):
            persist_bundle(load_drive_json(DRIVE_CONFIG), root=ROOT, drive=drive)
        self.assertEqual(drive.put_calls, [])

    def test_gate_scripts_run_offline_without_drive_write(self):
        commands = [
            [sys.executable, "scripts/github_siope_client_limeira_historical_2023_p6_bronze_single_record_capture_review_gate.py"],
            [sys.executable, "scripts/github_siope_client_limeira_historical_2023_p6_bronze_drive_persistence_gate.py", "--dry-run"],
        ]
        for command in commands:
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_workflow_is_manual_one_create_only_no_source_get_and_no_recurrence(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_historical_2023_p6_bronze_drive_persistence", text)
        self.assertIn("contents: read", text)
        self.assertIn("github_siope_client_limeira_historical_2023_p6_bronze_single_record_capture_review_gate.py", text)
        self.assertIn("github_siope_client_limeira_historical_2023_p6_bronze_drive_persistence_gate.py --dry-run", text)
        self.assertIn("GOOGLE_DRIVE_CLIENT_ID", text)
        self.assertIn("GOOGLE_DRIVE_CLIENT_SECRET", text)
        self.assertIn("GOOGLE_DRIVE_REFRESH_TOKEN", text)
        self.assertIn("Persistir exatamente um bundle Bronze histórico imutável no 01_BRONZE", text)
        self.assertNotIn("schedule:", text)
        self.assertNotIn("follow_nextlink", text)
        self.assertNotIn("rerun", text.lower())


if __name__ == "__main__":
    unittest.main()
