from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE_REVIEW"


class Historical2023P6DrivePersistenceReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Historical2023P6DrivePersistenceReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise Historical2023P6DrivePersistenceReviewError(f"{ERROR}_{code}")


def _git_blob_sha(path: str | Path) -> str:
    data = Path(path).read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()  # noqa: S324


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "drive_readback_design_authorized": True,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE_REVIEW_0_8_0",
        "gold_authorized": False,
        "historical_collection_authorized": False,
        "mode": "OFFLINE_PINNED_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_READBACK_VERIFICATION_0_8_0",
        "pinned_artifact_digest": "sha256:2f94382930a376d04185be364eb7fe7c31f6ca9365e7fd84d11450ee30eaf029",
        "pinned_artifact_id": 9629859801,
        "pinned_bundle_bytes": 2086,
        "pinned_bundle_sha256": "929a999672343b0e423283dcbd8f1ba797f9f924cecaee00b70b37b312ec2dfc",
        "pinned_evidence_blob_sha": "c3911e2a9246e14a0a39e1c3bc7054b011eb72c6",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE_RUN_1_0.8.0.json",
        "pinned_head_sha": "42f5db1e5b8354737414911a2c3a0d6f7ea69b7e",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98380105925,
        "pinned_record_sha256": "8b63fd15413c3ab9ca5f82749ea5d89e5a1c92b06e7b80cb6def7af60b769919",
        "pinned_remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2023_P6__352690__8b63fd15413c__bundle.json",
        "pinned_run_id": 33030007528,
        "pinned_run_number": 1,
        "pinned_unit_tests": 971,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "silver_authorized": False,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
    }
    _require(config, expected_config, "CONFIG")

    evidence_path = Path(root) / config["pinned_evidence_path"]
    _require(_git_blob_sha(evidence_path), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB_SHA")
    evidence = load_json(evidence_path)
    expected_evidence = {
        "artifact_digest": config["pinned_artifact_digest"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-client-limeira-historical-2023-p6-bronze-drive-persistence-33030007528",
        "bundle_bytes": config["pinned_bundle_bytes"],
        "bundle_md5_verified": True,
        "bundle_sha256": config["pinned_bundle_sha256"],
        "drive_create_only": True,
        "drive_network_called": True,
        "drive_write_count": 1,
        "event": "workflow_dispatch",
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE_0_8_0",
        "gold_authorized": False,
        "head_branch": "main",
        "head_sha": config["pinned_head_sha"],
        "historical_collection_authorized": False,
        "historical_regressions": config["pinned_historical_regressions"],
        "historical_regressions_passed": config["pinned_historical_regressions"],
        "job_id": config["pinned_job_id"],
        "network_called": True,
        "next_gate": config["gate_id"],
        "processing_authorized": False,
        "record_count": 1,
        "record_sha256": config["pinned_record_sha256"],
        "recurrence_authorized": False,
        "remote_file_id_persisted": False,
        "remote_name": config["pinned_remote_name"],
        "run_id": config["pinned_run_id"],
        "run_number": config["pinned_run_number"],
        "schedule_enabled": False,
        "schema_key_count": 52,
        "silver_authorized": False,
        "source_network_called": False,
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE",
        "unit_tests": config["pinned_unit_tests"],
        "unit_tests_passed": config["pinned_unit_tests"],
    }
    _require(evidence, expected_evidence, "EVIDENCE")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "pinned_run_id": config["pinned_run_id"],
        "bundle_sha256": config["pinned_bundle_sha256"],
        "record_sha256": config["pinned_record_sha256"],
        "drive_readback_design_authorized": True,
        "historical_collection_authorized": False,
        "silver_authorized": False,
        "gold_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
