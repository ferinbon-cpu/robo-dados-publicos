from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from robo_dados_publicos.sources.siope_client_limeira_historical_2022_p6_gold_drive_persistence import (
    HistoricalGoldDrivePersistenceError,
    load_json as load_persistence_json,
    persist,
    validate_config as validate_persistence,
)
from robo_dados_publicos.sources.siope_client_limeira_historical_2022_p6_gold_transform_review import (
    HistoricalGoldTransformReviewError,
    load_json as load_review_json,
    review,
)

ROOT = Path(__file__).resolve().parents[1]
REVIEW_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2022_p6_gold_transform_review.json"
PERSISTENCE_CONFIG = ROOT / "config/source_expansion.siope_client_limeira_historical_2022_p6_gold_drive_persistence.json"
CLOUD_CONFIG = ROOT / "config/cloud.json"
WORKFLOW = ROOT / ".github/workflows/siope-client-limeira-historical-2022-p6-gold-drive-persistence-gate.yml"


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


class HistoricalGoldDrivePersistenceTests(unittest.TestCase):
    def test_pinned_historical_gold_preview_review_passes_offline_and_blob(self):
        result = review(load_review_json(REVIEW_CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_TRANSFORM_REVIEW")
        self.assertFalse(result["network_called"])
        self.assertTrue(result["gold_drive_persistence_design_authorized"])
        self.assertFalse(result["gold_remote_write_authorized"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["compliance_claims_authorized"])
        self.assertEqual(result["metric_count"], 8)
        self.assertEqual(result["gold_payload_bytes"], 1623)
        self.assertEqual(result["gold_payload_sha256"], "4057aac2b18dc7184db992ee989d64c8732c4ad858cc6e8b7520cd50c4d37f68")

    def test_review_rejects_tampered_pinned_identity(self):
        for key, value in (
            ("evidence_blob_sha", "0" * 40),
            ("expected_artifact_id", 1),
            ("expected_run_id", 1),
            ("gold_payload_sha256", "0" * 64),
            ("gold_remote_write_authorized", True),
            ("compliance_claims_authorized", True),
            ("historical_collection_authorized", True),
        ):
            with self.subTest(key=key):
                config = copy.deepcopy(load_review_json(REVIEW_CONFIG))
                config[key] = value
                with self.assertRaises(HistoricalGoldTransformReviewError):
                    review(config, root=ROOT)

    def test_gold_folder_matches_cloud_config(self):
        persistence = load_persistence_json(PERSISTENCE_CONFIG)
        cloud = json.loads(CLOUD_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(persistence["gold_folder_id"], cloud["gold_id"])
        self.assertEqual(persistence["gold_folder_id"], "1hAmQNBnY6MNBtyr14ACfVfRkmWhsoRq4")

    def test_persistence_design_rebuilds_exact_historical_gold_without_network(self):
        result = validate_persistence(load_persistence_json(PERSISTENCE_CONFIG), root=ROOT)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_DRIVE_PERSISTENCE_DESIGN")
        self.assertFalse(result["network_called"])
        self.assertFalse(result["source_network_called"])
        self.assertFalse(result["drive_network_called"])
        self.assertEqual(result["drive_write_count"], 0)
        self.assertFalse(result["gold_payload_persisted"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["compliance_claims_authorized"])
        self.assertFalse(result["imputation_performed"])
        self.assertEqual(result["metric_count"], 8)
        self.assertEqual(result["gold_payload_bytes"], 1623)
        self.assertEqual(result["gold_payload_sha256"], "4057aac2b18dc7184db992ee989d64c8732c4ad858cc6e8b7520cd50c4d37f68")

    def test_mocked_live_creates_exactly_one_validated_historical_gold(self):
        drive = FakeDrive()
        result = persist(load_persistence_json(PERSISTENCE_CONFIG), root=ROOT, drive=drive)
        self.assertEqual(result["status"], "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_DRIVE_PERSISTENCE")
        self.assertEqual(result["drive_write_count"], 1)
        self.assertTrue(result["drive_create_only"])
        self.assertTrue(result["gold_payload_persisted"])
        self.assertTrue(result["gold_payload_md5_verified"])
        self.assertFalse(result["source_network_called"])
        self.assertFalse(result["remote_file_id_persisted"])
        self.assertFalse(result["historical_collection_authorized"])
        self.assertFalse(result["compliance_claims_authorized"])
        self.assertFalse(result["processing_authorized"])
        self.assertFalse(result["recurrence_authorized"])
        self.assertEqual(len(drive.find_calls), 1)
        self.assertEqual(len(drive.put_calls), 1)
        raw, remote_name, parent_id, mime_type = drive.put_calls[0]
        self.assertEqual(parent_id, "1hAmQNBnY6MNBtyr14ACfVfRkmWhsoRq4")
        self.assertEqual(mime_type, "application/json")
        self.assertEqual(remote_name, "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2022_P6__352690__4057aac2b18d__gold_v1.json")
        self.assertEqual(len(raw), 1623)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), result["gold_payload_sha256"])
        payload = json.loads(raw.decode("utf-8"))
        self.assertEqual(payload["identity"]["municipality_code"], 352690)
        self.assertEqual(payload["identity"]["year"], 2022)
        self.assertEqual(payload["identity"]["period"], 6)
        self.assertEqual(len(payload["metrics"]), 8)
        self.assertFalse(payload["semantic_scope"]["mde_compliance_conclusion"])
        self.assertFalse(payload["semantic_scope"]["fundeb_compliance_conclusion"])
        self.assertFalse(payload["semantic_scope"]["fiscal_audit_conclusion"])

    def test_remote_name_collision_stops_before_write(self):
        drive = FakeDrive(collision=True)
        with self.assertRaises(HistoricalGoldDrivePersistenceError):
            persist(load_persistence_json(PERSISTENCE_CONFIG), root=ROOT, drive=drive)
        self.assertEqual(len(drive.find_calls), 1)
        self.assertEqual(drive.put_calls, [])

    def test_config_drift_cannot_enable_unsafe_operations_or_history(self):
        unsafe_changes = (
            ("create_only", False),
            ("drive_write_count", 2),
            ("overwrite_authorized", True),
            ("delete_authorized", True),
            ("replace_authorized", True),
            ("compliance_claims_authorized", True),
            ("historical_collection_authorized", True),
            ("imputation_authorized", True),
            ("processing_authorized", True),
            ("recurrence_authorized", True),
            ("schedule_enabled", True),
            ("source_network_authorized", True),
        )
        for key, value in unsafe_changes:
            with self.subTest(key=key):
                config = copy.deepcopy(load_persistence_json(PERSISTENCE_CONFIG))
                config[key] = value
                with self.assertRaises(HistoricalGoldDrivePersistenceError):
                    validate_persistence(config, root=ROOT)

    def test_gate_scripts_run_directly_without_live_network(self):
        review_run = subprocess.run(
            [sys.executable, "scripts/github_siope_client_limeira_historical_2022_p6_gold_transform_review_gate.py"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(review_run.returncode, 0, review_run.stderr + review_run.stdout)
        self.assertIn("PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_TRANSFORM_REVIEW", review_run.stdout)
        design_run = subprocess.run(
            [sys.executable, "scripts/github_siope_client_limeira_historical_2022_p6_gold_drive_persistence_gate.py", "--dry-run"],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(design_run.returncode, 0, design_run.stderr + design_run.stdout)
        self.assertIn("PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_GOLD_DRIVE_PERSISTENCE_DESIGN", design_run.stdout)

    def test_workflow_is_manual_create_only_and_full_qa_precedes_live(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("confirm_siope_client_limeira_historical_2022_p6_gold_drive_persistence", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertNotIn("schedule:", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("GOOGLE_DRIVE_CLIENT_ID: ${{ secrets.GOOGLE_DRIVE_CLIENT_ID }}", text)
        self.assertIn("github_siope_client_limeira_historical_2022_p6_gold_transform_review_gate.py", text)
        self.assertIn("github_siope_client_limeira_historical_2022_p6_gold_drive_persistence_gate.py --dry-run", text)
        unit_pos = text.index("python -m unittest discover -s tests -v")
        regression_pos = text.index("python main.py selftest")
        live_pos = text.index("Persistir exatamente um payload Gold histórico 2022 P6 validado no 03_GOLD")
        self.assertLess(unit_pos, live_pos)
        self.assertLess(regression_pos, live_pos)
        self.assertNotIn("SiopeClient(", text)
        self.assertNotIn("Dados_Gerais_Siope(", text)
        self.assertNotIn("replace_content", text)
        self.assertNotIn(".delete(", text)
        self.assertIn("sem novo GET SIOPE", text)


if __name__ == "__main__":
    unittest.main()
