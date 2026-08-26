from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_silver_drive_persistence import (
    SilverDrivePersistenceError,
    load_json as load_persistence_json,
    persist,
    validate_config,
)
from robo_dados_publicos.sources.siope_client_limeira_silver_single_record_transform_review import (
    SilverTransformReviewError,
    load_json as load_review_json,
    review,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_silver_single_record_transform_review.json"
PERSISTENCE_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_silver_drive_persistence.json"
CLOUD_CONFIG = ROOT / "config/cloud.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-silver-drive-persistence-gate.yml"


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


class SilverDrivePersistenceTests(unittest.TestCase):
    def test_pinned_preview_review_passes_offline(self):
        result = review(load_review_json(REVIEW_CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_SILVER_SINGLE_RECORD_TRANSFORM_REVIEW")
        self.assertFalse(result["network_called"])
        self.assertTrue(result["silver_drive_persistence_design_authorized"])
        self.assertFalse(result["silver_remote_write_authorized"])
        self.assertEqual(result["silver_payload_bytes"], 2328)
        self.assertEqual(
            result["silver_payload_sha256"],
            "072283e3d9e5f12e6a3a697d32e653b64e618f4665e28f53e553b35506ce68da",
        )

    def test_tampered_preview_evidence_fails_closed(self):
        config = copy.deepcopy(load_review_json(REVIEW_CONFIG))
        config["pinned_artifact_digest"] = "sha256:" + "0" * 64
        with self.assertRaises(SilverTransformReviewError):
            review(config, root=ROOT)

    def test_silver_folder_matches_cloud_config(self):
        persistence = load_persistence_json(PERSISTENCE_CONFIG)
        cloud = json.loads(CLOUD_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(persistence["silver_folder_id"], cloud["silver_id"])
        self.assertEqual(persistence["silver_folder_id"], "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo")

    def test_persistence_design_rebuilds_exact_preview_payload_without_network(self):
        result = validate_config(load_persistence_json(PERSISTENCE_CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_PERSISTENCE_DESIGN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["source_network_called"])
        self.assertEqual(result["drive_write_count"], 0)
        self.assertFalse(result["silver_payload_persisted"])
        self.assertEqual(result["silver_payload_bytes"], 2328)
        self.assertEqual(
            result["silver_payload_sha256"],
            "072283e3d9e5f12e6a3a697d32e653b64e618f4665e28f53e553b35506ce68da",
        )

    def test_mocked_live_creates_exactly_one_validated_silver(self):
        drive = FakeDrive()
        result = persist(load_persistence_json(PERSISTENCE_CONFIG), root=ROOT, drive=drive)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_PERSISTENCE")
        self.assertEqual(result["drive_write_count"], 1)
        self.assertTrue(result["drive_create_only"])
        self.assertTrue(result["silver_payload_persisted"])
        self.assertFalse(result["source_network_called"])
        self.assertFalse(result["remote_file_id_persisted"])
        self.assertEqual(len(drive.find_calls), 1)
        self.assertEqual(len(drive.put_calls), 1)
        raw, remote_name, parent_id, mime_type = drive.put_calls[0]
        self.assertEqual(parent_id, "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo")
        self.assertEqual(mime_type, "application/json")
        self.assertTrue(remote_name.endswith("__072283e3d9e5__silver_v1.json"))
        self.assertEqual(len(raw), 2328)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), result["silver_payload_sha256"])
        payload = json.loads(raw.decode("utf-8"))
        self.assertEqual(payload["silver_contract"], "SIOPE_DADOS_GERAIS_LIMEIRA_VALIDATED_RECORD_SILVER_V1")
        self.assertEqual(payload["identity"]["municipality_code"], 352690)
        self.assertEqual(payload["identity"]["year"], 2024)
        self.assertEqual(payload["identity"]["period"], 6)
        self.assertEqual(len(payload["data"]), 52)
        self.assertEqual(payload["provenance"]["record_sha256"], result["record_sha256"])
        self.assertFalse(result["gold_authorized"])
        self.assertFalse(result["processing_authorized"])
        self.assertFalse(result["recurrence_authorized"])

    def test_remote_name_collision_stops_before_write(self):
        drive = FakeDrive(collision=True)
        with self.assertRaises(SilverDrivePersistenceError):
            persist(load_persistence_json(PERSISTENCE_CONFIG), root=ROOT, drive=drive)
        self.assertEqual(len(drive.find_calls), 1)
        self.assertEqual(drive.put_calls, [])

    def test_config_drift_cannot_enable_overwrite_gold_processing_or_recurrence(self):
        for key in (
            "overwrite_authorized",
            "delete_authorized",
            "replace_authorized",
            "gold_authorized",
            "processing_authorized",
            "recurrence_authorized",
            "schedule_enabled",
        ):
            with self.subTest(key=key):
                config = copy.deepcopy(load_persistence_json(PERSISTENCE_CONFIG))
                config[key] = True
                with self.assertRaises(SilverDrivePersistenceError):
                    validate_config(config, root=ROOT)

    def test_workflow_is_manual_one_silver_write_and_full_qa_precedes_live(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_silver_drive_persistence", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("GOOGLE_DRIVE_CLIENT_ID: ${{ secrets.GOOGLE_DRIVE_CLIENT_ID }}", text)
        self.assertIn("github_siope_client_limeira_silver_single_record_transform_review_gate.py", text)
        self.assertIn("github_siope_client_limeira_silver_drive_persistence_gate.py --dry-run", text)
        unit_pos = text.index("python -m unittest discover -s tests -v")
        regression_pos = text.index("python main.py selftest")
        live_pos = text.index("Persistir exatamente um payload validado no 02_SILVER")
        self.assertLess(unit_pos, live_pos)
        self.assertLess(regression_pos, live_pos)
        self.assertNotIn("SiopeClient(", text)
        self.assertNotIn("Dados_Gerais_Siope(", text)
        self.assertNotIn("replace_content", text)
        self.assertNotIn(".delete(", text)
        self.assertNotIn("03_GOLD", text)


if __name__ == "__main__":
    unittest.main()
