from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_historical_2023_p6_silver_drive_persistence import (
    HistoricalSilverDrivePersistenceError,
    load_json as load_persistence_json,
    persist,
    validate_config,
)
from robo_dados_publicos.sources.siope_client_limeira_historical_2023_p6_silver_single_record_transform_review import (
    HistoricalSilverTransformReviewError,
    load_json as load_review_json,
    review,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2023_p6_silver_single_record_transform_review.json"
PERSISTENCE_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2023_p6_silver_drive_persistence.json"
CLOUD_CONFIG = ROOT / "config/cloud.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-historical-2023-p6-silver-drive-persistence-gate.yml"
EVIDENCE = ROOT / "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW_RUN_1_0.8.0.json"


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


class HistoricalSilverDrivePersistenceTests(unittest.TestCase):
    def test_pinned_historical_preview_review_passes_offline_and_blob_is_exact(self):
        result = review(load_review_json(REVIEW_CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_SINGLE_RECORD_TRANSFORM_REVIEW")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["gold_authorized"])
        self.assertTrue(result["silver_drive_persistence_design_authorized"])
        self.assertFalse(result["silver_remote_write_authorized"])
        self.assertEqual(result["silver_payload_bytes"], 1830)
        raw = EVIDENCE.read_bytes()
        blob_sha = hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()  # noqa: S324
        self.assertEqual(blob_sha, "98e23ab9bb1038b3baa7f2dc82bd520eda15c5f1")

    def test_tampered_preview_review_fails_closed(self):
        config = copy.deepcopy(load_review_json(REVIEW_CONFIG))
        config["pinned_artifact_digest"] = "sha256:" + "0" * 64
        with self.assertRaises(HistoricalSilverTransformReviewError):
            review(config, root=ROOT)

    def test_silver_folder_matches_cloud_config(self):
        persistence = load_persistence_json(PERSISTENCE_CONFIG)
        cloud = json.loads(CLOUD_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(persistence["silver_folder_id"], cloud["silver_id"])
        self.assertEqual(persistence["silver_folder_id"], "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo")

    def test_persistence_design_rebuilds_exact_historical_preview_without_network(self):
        result = validate_config(load_persistence_json(PERSISTENCE_CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_PERSISTENCE_DESIGN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["source_network_called"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertEqual(result["drive_write_count"], 0)
        self.assertFalse(result["silver_payload_persisted"])
        self.assertEqual(result["silver_payload_bytes"], 1830)
        self.assertEqual(result["silver_payload_sha256"], "6d5c6a96f7a0b57b06ad6a6b7078a46ba58ef5fd1242f08c3de8c7aa5f2c87fb")

    def test_mocked_live_creates_exactly_one_historical_silver(self):
        drive = FakeDrive()
        result = persist(load_persistence_json(PERSISTENCE_CONFIG), root=ROOT, drive=drive)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_PERSISTENCE")
        self.assertEqual(result["drive_write_count"], 1)
        self.assertTrue(result["drive_create_only"])
        self.assertTrue(result["silver_payload_persisted"])
        self.assertFalse(result["source_network_called"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["remote_file_id_persisted"])
        self.assertEqual(len(drive.find_calls), 1)
        self.assertEqual(len(drive.put_calls), 1)
        raw, remote_name, parent_id, mime_type = drive.put_calls[0]
        self.assertEqual(parent_id, "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo")
        self.assertEqual(mime_type, "application/json")
        self.assertTrue(remote_name.endswith("__6d5c6a96f7a0__silver_v1.json"))
        self.assertEqual(len(raw), 1830)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), result["silver_payload_sha256"])
        payload = json.loads(raw.decode("utf-8"))
        self.assertEqual(payload["silver_contract"], "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_VALIDATED_RECORD_SILVER_V1")
        self.assertEqual(payload["identity"]["municipality_code"], 352690)
        self.assertEqual(payload["identity"]["year"], 2023)
        self.assertEqual(payload["identity"]["period"], 6)
        self.assertEqual(len(payload["data"]), 52)
        self.assertEqual(payload["provenance"]["record_sha256"], result["record_sha256"])
        self.assertFalse(result["gold_authorized"])
        self.assertFalse(result["processing_authorized"])
        self.assertFalse(result["recurrence_authorized"])

    def test_remote_name_collision_stops_before_write(self):
        drive = FakeDrive(collision=True)
        with self.assertRaises(HistoricalSilverDrivePersistenceError):
            persist(load_persistence_json(PERSISTENCE_CONFIG), root=ROOT, drive=drive)
        self.assertEqual(len(drive.find_calls), 1)
        self.assertEqual(drive.put_calls, [])

    def test_config_drift_cannot_enable_unsafe_operations_or_history(self):
        for key in (
            "overwrite_authorized",
            "delete_authorized",
            "replace_authorized",
            "gold_authorized",
            "historical_collection_authorized",
            "processing_authorized",
            "recurrence_authorized",
            "schedule_enabled",
        ):
            with self.subTest(key=key):
                config = copy.deepcopy(load_persistence_json(PERSISTENCE_CONFIG))
                config[key] = True
                with self.assertRaises(HistoricalSilverDrivePersistenceError):
                    validate_config(config, root=ROOT)

    def test_workflow_is_manual_one_silver_write_and_full_qa_precedes_live(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_historical_2023_p6_silver_drive_persistence", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("GOOGLE_DRIVE_CLIENT_ID: ${{ secrets.GOOGLE_DRIVE_CLIENT_ID }}", text)
        self.assertIn("github_siope_client_limeira_historical_2023_p6_silver_single_record_transform_review_gate.py", text)
        self.assertIn("github_siope_client_limeira_historical_2023_p6_silver_drive_persistence_gate.py --dry-run", text)
        unit_pos = text.index("python -m unittest discover -s tests -v")
        regression_pos = text.index("python main.py selftest")
        live_pos = text.index("Persistir exatamente um payload histórico validado no 02_SILVER")
        self.assertLess(unit_pos, live_pos)
        self.assertLess(regression_pos, live_pos)
        self.assertNotIn("SiopeClient(", text)
        self.assertNotIn("Dados_Gerais_Siope(", text)
        self.assertNotIn("replace_content", text)
        self.assertNotIn(".delete(", text)
        self.assertNotIn("03_GOLD", text)


if __name__ == "__main__":
    unittest.main()
