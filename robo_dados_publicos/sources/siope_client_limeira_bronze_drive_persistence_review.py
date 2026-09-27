from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_PERSISTENCE_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_PERSISTENCE_REVIEW"


class DrivePersistenceReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DrivePersistenceReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise DrivePersistenceReviewError(f"{ERROR}_{code}")


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "drive_readback_design_authorized": True,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_PERSISTENCE_REVIEW_0_8_0",
        "gold_authorized": False,
        "mode": "OFFLINE_PINNED_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_PERSISTENCE_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_READBACK_VERIFICATION_0_8_0",
        "pinned_artifact_digest": "sha256:8860f0b74ab2c041a8c1cd09905aed22e453148326095d4caba4a4852ee6745a",
        "pinned_artifact_id": 9624998290,
        "pinned_bundle_bytes": 2461,
        "pinned_bundle_sha256": "eb30b820c34a702a5850b1e246d7d29a8d86c0e84064b79b14c0308060950dbf",
        "pinned_evidence_blob_sha": "db91e6e43abe60bcc69d623db9dcdcd00f9a208a",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_PERSISTENCE_RUN_1_0.8.0.json",
        "pinned_head_sha": "a4456980522cca09690446dca2c2796b8fd3e9a8",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98338265306,
        "pinned_record_sha256": "20dd61298f9d4603fc7d5e20a373f331137d5bc37f59be687370bd0f289b97c6",
        "pinned_remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2024_P6__352690__20dd61298f9d__bundle.json",
        "pinned_run_id": 33017170345,
        "pinned_run_number": 1,
        "pinned_unit_tests": 876,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "silver_authorized": False,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
    }
    _require(config, expected_config, "CONFIG")

    evidence = load_json(Path(root) / config["pinned_evidence_path"])
    expected_evidence = {
        "artifact_digest": config["pinned_artifact_digest"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-client-limeira-bronze-drive-persistence-33017170345",
        "bundle_bytes": config["pinned_bundle_bytes"],
        "bundle_md5_verified": True,
        "bundle_sha256": config["pinned_bundle_sha256"],
        "drive_create_only": True,
        "drive_network_called": True,
        "drive_write_count": 1,
        "event": "workflow_dispatch",
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_PERSISTENCE_0_8_0",
        "gold_authorized": False,
        "head_branch": "main",
        "head_sha": config["pinned_head_sha"],
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
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_PERSISTENCE",
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
        "silver_authorized": False,
        "gold_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
