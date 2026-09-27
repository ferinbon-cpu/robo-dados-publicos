from __future__ import annotations

import hashlib
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_historical_2022_p6_silver_drive_persistence_review import (
    load_json as load_persistence_review_json,
    review as persistence_review,
)
from robo_dados_publicos.sources.siope_client_limeira_historical_2022_p6_silver_drive_readback_verification import (
    HistoricalSilverDriveReadbackVerificationError,
    _expected_payload,
    load_json,
    validate_config,
    verify_readback,
)

ROOT = Path(__file__).resolve().parents[1]
PERSISTENCE_REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2022_p6_silver_drive_persistence_review.json"
READBACK_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2022_p6_silver_drive_readback_verification.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-historical-2022-p6-silver-drive-readback-verification-gate.yml"


class FakeDrive:
    def __init__(self, *, parent_id: str, name: str, mime_type: str, payload: bytes, duplicate: bool = False):
        self.parent_id = parent_id
        self.name = name
        self.mime_type = mime_type
        self.payload = payload
        self.duplicate = duplicate
        self.get_calls = 0
        self.write_calls = 0

    def find_by_name(self, parent_id, name):
        if parent_id != self.parent_id or name != self.name:
            return []
        item = {
            "id": "opaque-test-id",
            "name": self.name,
            "mimeType": self.mime_type,
            "size": str(len(self.payload)),
            "md5Checksum": hashlib.md5(self.payload).hexdigest(),  # noqa: S324
            "parents": [self.parent_id],
        }
        return [item, dict(item)] if self.duplicate else [item]

    def get(self, file_id, destination):
        self.get_calls += 1
        Path(destination).write_bytes(self.payload)
        return {
            "file_id": file_id,
            "path": str(destination),
            "bytes": len(self.payload),
            "sha256": hashlib.sha256(self.payload).hexdigest(),
        }


class Historical2022P6SilverDriveReadbackVerificationTests(unittest.TestCase):
    def test_persistence_review_passes_exact_live_pin(self):
        result = persistence_review(load_persistence_review_json(PERSISTENCE_REVIEW_CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_DRIVE_PERSISTENCE_REVIEW")
        self.assertEqual(result["pinned_run_id"], 33078760226)
        self.assertEqual(result["silver_payload_bytes"], 1825)
        self.assertFalse(result["network_called"])

    def test_readback_design_is_offline_and_write_closed(self):
        result = validate_config(load_json(READBACK_CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_DRIVE_READBACK_VERIFICATION_DESIGN")
        self.assertFalse(result["network_called"])
        self.assertEqual(result["drive_write_count"], 0)
        self.assertFalse(result["gold_authorized"])

    def test_mocked_readback_verifies_exact_bytes_once(self):
        config = load_json(READBACK_CONFIG)
        _, expected = _expected_payload(config, root=ROOT)
        drive = FakeDrive(parent_id=config["silver_folder_id"], name=config["remote_name"], mime_type=config["mime_type"], payload=expected)
        result = verify_readback(config, root=ROOT, drive=drive)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_DRIVE_READBACK_VERIFICATION")
        self.assertEqual(result["drive_file_download_count"], 1)
        self.assertEqual(result["drive_write_count"], 0)
        self.assertTrue(result["byte_identity_verified"])
        self.assertTrue(result["silver_payload_md5_verified"])
        self.assertFalse(result["remote_file_id_persisted"])
        self.assertEqual(result["record_sha256"], "79b786f438d29803fe15d513f4ff17d4ab55fde1dd631f503b6752370e21b68a")
        self.assertEqual(drive.get_calls, 1)
        self.assertEqual(drive.write_calls, 0)

    def test_tamper_and_duplicate_fail_closed(self):
        config = load_json(READBACK_CONFIG)
        _, expected = _expected_payload(config, root=ROOT)
        tampered = bytearray(expected)
        tampered[-2] = (tampered[-2] + 1) % 255
        with self.assertRaises(HistoricalSilverDriveReadbackVerificationError):
            verify_readback(config, root=ROOT, drive=FakeDrive(parent_id=config["silver_folder_id"], name=config["remote_name"], mime_type=config["mime_type"], payload=bytes(tampered)))
        dup = FakeDrive(parent_id=config["silver_folder_id"], name=config["remote_name"], mime_type=config["mime_type"], payload=expected, duplicate=True)
        with self.assertRaises(HistoricalSilverDriveReadbackVerificationError):
            verify_readback(config, root=ROOT, drive=dup)
        self.assertEqual(dup.get_calls, 0)

    def test_config_drift_cannot_open_mutations_or_gold(self):
        for field, value in (
            ("drive_write_count", 1),
            ("overwrite_authorized", True),
            ("delete_authorized", True),
            ("replace_authorized", True),
            ("source_network_authorized", True),
            ("historical_collection_authorized", True),
            ("gold_authorized", True),
            ("processing_authorized", True),
            ("recurrence_authorized", True),
            ("schedule_enabled", True),
        ):
            config = load_json(READBACK_CONFIG)
            config[field] = value
            with self.assertRaises(HistoricalSilverDriveReadbackVerificationError, msg=field):
                validate_config(config, root=ROOT)

    def test_gate_script_dry_run_and_workflow_contract(self):
        cp = subprocess.run(
            [sys.executable, "scripts/github_siope_client_limeira_historical_2022_p6_silver_drive_readback_verification_gate.py", "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(cp.returncode, 0, cp.stderr or cp.stdout)
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_historical_2022_p6_silver_drive_readback_verification", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("github_siope_client_limeira_historical_2022_p6_silver_drive_persistence_review_gate.py", text)
        self.assertNotIn("https://www.fnde.gov.br", text)
        self.assertNotIn("drive.put", text)
        self.assertNotIn("drive.delete", text)


if __name__ == "__main__":
    unittest.main()
