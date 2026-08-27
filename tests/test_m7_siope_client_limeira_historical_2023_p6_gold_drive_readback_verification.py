from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_historical_2023_p6_gold_drive_persistence_review import (
    HistoricalGoldDrivePersistenceReviewError,
    load_json as load_review_json,
    review,
)
from robo_dados_publicos.sources.siope_client_limeira_historical_2023_p6_gold_drive_readback_verification import (
    HistoricalGoldDriveReadbackVerificationError,
    _expected_payload,
    load_json,
    validate_config,
    verify_readback,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2023_p6_gold_drive_persistence_review.json"
READBACK_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2023_p6_gold_drive_readback_verification.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-historical-2023-p6-gold-drive-readback-verification-gate.yml"


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


class HistoricalGoldDriveReadbackVerificationTests(unittest.TestCase):
    def test_persistence_review_passes_exact_pinned_evidence(self):
        result = review(load_review_json(REVIEW_CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_DRIVE_PERSISTENCE_REVIEW")
        self.assertTrue(result["drive_readback_design_authorized"])
        self.assertEqual(result["pinned_run_id"], 33036318345)
        self.assertFalse(result["network_called"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["compliance_claims_authorized"])

    def test_tampered_persistence_evidence_fails_closed(self):
        config = load_review_json(REVIEW_CONFIG)
        source = ROOT / config["evidence_path"]
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            target = tmp / config["evidence_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            evidence = json.loads(source.read_text(encoding="utf-8"))
            evidence["drive_write_count"] = 2
            target.write_text(json.dumps(evidence), encoding="utf-8")
            with self.assertRaises(HistoricalGoldDrivePersistenceReviewError):
                review(config, root=tmp)

    def test_readback_design_is_network_free_write_closed_and_historical_collection_closed(self):
        config = load_json(READBACK_CONFIG)
        result = validate_config(config, root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_DRIVE_READBACK_VERIFICATION_DESIGN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["drive_network_called"])
        self.assertEqual(result["drive_write_count"], 0)
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["compliance_claims_authorized"])
        self.assertFalse(result["imputation_performed"])
        self.assertFalse(result["processing_authorized"])
        self.assertFalse(result["recurrence_authorized"])
        self.assertFalse(result["schedule_enabled"])

    def test_expected_payload_is_exact_historical_gold(self):
        config = load_json(READBACK_CONFIG)
        payload, expected_bytes = _expected_payload(config, root=ROOT)
        self.assertEqual(len(expected_bytes), 1623)
        self.assertEqual(hashlib.sha256(expected_bytes).hexdigest(), "a4da994fd2a04ef0b3133d9a20855e6809922f19366075d48aab3296ca488272")
        self.assertEqual(payload["identity"]["year"], 2023)
        self.assertEqual(payload["identity"]["period"], 6)
        self.assertEqual(len(payload["metrics"]), 8)

    def test_mocked_live_readback_verifies_exact_bytes_without_writes(self):
        config = load_json(READBACK_CONFIG)
        _, expected_bytes = _expected_payload(config, root=ROOT)
        drive = FakeDrive(parent_id=config["gold_folder_id"], name=config["remote_name"], mime_type=config["mime_type"], payload=expected_bytes)
        result = verify_readback(config, root=ROOT, drive=drive)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_DRIVE_READBACK_VERIFICATION")
        self.assertEqual(result["drive_file_download_count"], 1)
        self.assertEqual(result["drive_write_count"], 0)
        self.assertTrue(result["byte_identity_verified"])
        self.assertTrue(result["gold_payload_md5_verified"])
        self.assertFalse(result["remote_file_id_persisted"])
        self.assertFalse(result["source_network_called"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["compliance_claims_authorized"])
        self.assertEqual(result["metric_count"], 8)
        self.assertEqual(drive.get_calls, 1)
        self.assertEqual(drive.write_calls, 0)

    def test_tampered_remote_payload_fails_closed(self):
        config = load_json(READBACK_CONFIG)
        _, expected_bytes = _expected_payload(config, root=ROOT)
        tampered = bytearray(expected_bytes)
        tampered[-2] = (tampered[-2] + 1) % 255
        drive = FakeDrive(parent_id=config["gold_folder_id"], name=config["remote_name"], mime_type=config["mime_type"], payload=bytes(tampered))
        with self.assertRaises(HistoricalGoldDriveReadbackVerificationError):
            verify_readback(config, root=ROOT, drive=drive)

    def test_duplicate_remote_name_fails_before_download(self):
        config = load_json(READBACK_CONFIG)
        _, expected_bytes = _expected_payload(config, root=ROOT)
        drive = FakeDrive(parent_id=config["gold_folder_id"], name=config["remote_name"], mime_type=config["mime_type"], payload=expected_bytes, duplicate=True)
        with self.assertRaises(HistoricalGoldDriveReadbackVerificationError):
            verify_readback(config, root=ROOT, drive=drive)
        self.assertEqual(drive.get_calls, 0)

    def test_config_drift_cannot_enable_unsafe_operations(self):
        for field, value in (
            ("drive_write_count", 1),
            ("overwrite_authorized", True),
            ("delete_authorized", True),
            ("replace_authorized", True),
            ("source_network_authorized", True),
            ("historical_collection_authorized", True),
            ("compliance_claims_authorized", True),
            ("imputation_authorized", True),
            ("processing_authorized", True),
            ("recurrence_authorized", True),
            ("schedule_enabled", True),
        ):
            config = load_json(READBACK_CONFIG)
            config[field] = value
            with self.assertRaises(HistoricalGoldDriveReadbackVerificationError, msg=field):
                validate_config(config, root=ROOT)

    def test_gate_scripts_run_directly_in_offline_mode(self):
        review_cp = subprocess.run([sys.executable, "scripts/github_siope_client_limeira_historical_2023_p6_gold_drive_persistence_review_gate.py"], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(review_cp.returncode, 0, review_cp.stderr or review_cp.stdout)
        readback_cp = subprocess.run([sys.executable, "scripts/github_siope_client_limeira_historical_2023_p6_gold_drive_readback_verification_gate.py", "--dry-run"], cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(readback_cp.returncode, 0, readback_cp.stderr or readback_cp.stdout)

    def test_workflow_is_manual_readonly_full_qa_and_no_drive_write(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_historical_2023_p6_gold_drive_readback_verification", text)
        self.assertIn("contents: read", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("python main.py selftest", text)
        self.assertIn("github_siope_client_limeira_historical_2023_p6_gold_drive_persistence_review_gate.py", text)
        self.assertIn("github_siope_client_limeira_historical_2023_p6_gold_drive_readback_verification_gate.py --dry-run", text)
        self.assertNotIn("github_siope_client_limeira_historical_2023_p6_gold_drive_persistence_gate.py >", text)
        self.assertNotIn("https://www.fnde.gov.br", text)
        self.assertNotIn("Dados_Gerais_Siope(", text)
        self.assertNotIn("replace_content", text)
        self.assertNotIn("drive.delete", text)
        self.assertNotIn("drive.put", text)


if __name__ == "__main__":
    unittest.main()
