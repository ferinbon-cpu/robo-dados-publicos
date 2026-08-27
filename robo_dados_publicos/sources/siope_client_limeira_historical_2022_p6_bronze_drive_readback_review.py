from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_REVIEW"


class Historical2022P6BronzeDriveReadbackReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Historical2022P6BronzeDriveReadbackReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise Historical2022P6BronzeDriveReadbackReviewError(f"{ERROR}_{code}")


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_REVIEW_0_8_0",
        "historical_collection_authorized": False,
        "mode": "OFFLINE_PINNED_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW_0_8_0",
        "pinned_artifact_digest": "sha256:0cbb5ce90961e9768773dfe37b26136ccf532bec79ec0967b0139e760f4eea9f",
        "pinned_artifact_id": 9647032885,
        "pinned_bundle_bytes": 2081,
        "pinned_bundle_sha256": "68b659026fe5af968864d24fba10a6883058db4a9aa700d7f65a5a09c47ab54f",
        "pinned_evidence_blob_sha": "8fd1cce2d5cfcb7741b5b7701e3d04cb67878511",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_VERIFICATION_RUN_1_0.8.0.json",
        "pinned_head_sha": "cf0119cfae8b0c53667d0705cca96b5fd827529e",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98523282125,
        "pinned_record_sha256": "79b786f438d29803fe15d513f4ff17d4ab55fde1dd631f503b6752370e21b68a",
        "pinned_run_id": 33073981604,
        "pinned_run_number": 1,
        "pinned_schema_key_count": 52,
        "pinned_unit_tests": 1074,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "silver_authorized": False,
        "silver_transform_preview_design_authorized": True,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
    }
    _require(config, expected_config, "CONFIG_DRIFT")

    evidence_path = Path(root) / config["pinned_evidence_path"]
    _require(_git_blob_sha(evidence_path), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB_DRIFT")
    evidence = load_json(evidence_path)
    expected_evidence = {
        "artifact_digest": config["pinned_artifact_digest"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-client-limeira-historical-2022-p6-bronze-drive-readback-verification-33073981604",
        "artifact_size_bytes": 659,
        "bundle_bytes": config["pinned_bundle_bytes"],
        "bundle_md5_verified": True,
        "bundle_sha256": config["pinned_bundle_sha256"],
        "byte_identity_verified": True,
        "drive_file_download_count": 1,
        "drive_network_called": True,
        "drive_write_count": 0,
        "event": "workflow_dispatch",
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_VERIFICATION_0_8_0",
        "gold_authorized": False,
        "head_branch": "main",
        "head_sha": config["pinned_head_sha"],
        "historical_collection_authorized": False,
        "historical_regressions": config["pinned_historical_regressions"],
        "historical_regressions_passed": config["pinned_historical_regressions"],
        "job_id": config["pinned_job_id"],
        "network_called": True,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_REVIEW_0_8_0",
        "processing_authorized": False,
        "record_count": 1,
        "record_sha256": config["pinned_record_sha256"],
        "recurrence_authorized": False,
        "remote_file_id_persisted": False,
        "remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2022_P6__352690__79b786f438d2__bundle.json",
        "run_id": config["pinned_run_id"],
        "run_number": config["pinned_run_number"],
        "schedule_enabled": False,
        "schema_key_count": config["pinned_schema_key_count"],
        "silver_authorized": False,
        "source_network_called": False,
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_READBACK_VERIFICATION",
        "unit_tests": config["pinned_unit_tests"],
        "unit_tests_passed": config["pinned_unit_tests"],
    }
    _require(evidence, expected_evidence, "EVIDENCE_DRIFT")

    return {
        "bundle_sha256": config["pinned_bundle_sha256"],
        "gate_id": config["gate_id"],
        "historical_collection_authorized": False,
        "network_called": False,
        "next_gate": config["next_gate"],
        "pinned_run_id": config["pinned_run_id"],
        "processing_authorized": False,
        "record_sha256": config["pinned_record_sha256"],
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "schema_key_count": config["pinned_schema_key_count"],
        "silver_authorized": False,
        "silver_transform_preview_design_authorized": True,
        "status": PASS,
    }
