from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_PERSISTENCE_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_PERSISTENCE_REVIEW"


class SilverDrivePersistenceReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SilverDrivePersistenceReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SilverDrivePersistenceReviewError(f"{ERROR}_{code}")


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "drive_readback_design_authorized": True,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_PERSISTENCE_REVIEW_0_8_0",
        "gold_authorized": False,
        "mode": "OFFLINE_PINNED_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_PERSISTENCE_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_VERIFICATION_0_8_0",
        "pinned_artifact_digest": "sha256:d60d51938bb7b4a2488c36f46614c9eccc5601e9a30485405998243493dc68e0",
        "pinned_artifact_id": 9626815277,
        "pinned_evidence_blob_sha": "b12aebd71f5e470631b3dbde20ca5c16c31c004e",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_PERSISTENCE_RUN_1_0.8.0.json",
        "pinned_head_sha": "b9bdc4793c8e965d96792459ac7adc42550600d5",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98353751269,
        "pinned_record_sha256": "20dd61298f9d4603fc7d5e20a373f331137d5bc37f59be687370bd0f289b97c6",
        "pinned_remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2024_P6__352690__072283e3d9e5__silver_v1.json",
        "pinned_run_id": 33021813756,
        "pinned_run_number": 1,
        "pinned_silver_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_VALIDATED_RECORD_SILVER_V1",
        "pinned_silver_payload_bytes": 2328,
        "pinned_silver_payload_sha256": "072283e3d9e5f12e6a3a697d32e653b64e618f4665e28f53e553b35506ce68da",
        "pinned_unit_tests": 903,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
    }
    _require(config, expected_config, "CONFIG")

    evidence = load_json(Path(root) / config["pinned_evidence_path"])
    expected_evidence = {
        "artifact_digest": config["pinned_artifact_digest"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-client-limeira-silver-drive-persistence-33021813756",
        "drive_create_only": True,
        "drive_network_called": True,
        "drive_write_count": 1,
        "event": "workflow_dispatch",
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_PERSISTENCE_0_8_0",
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
        "silver_contract": config["pinned_silver_contract"],
        "silver_payload_bytes": config["pinned_silver_payload_bytes"],
        "silver_payload_md5_verified": True,
        "silver_payload_persisted": True,
        "silver_payload_sha256": config["pinned_silver_payload_sha256"],
        "source_network_called": False,
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_PERSISTENCE",
        "unit_tests": config["pinned_unit_tests"],
        "unit_tests_passed": config["pinned_unit_tests"],
    }
    _require(evidence, expected_evidence, "EVIDENCE")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "pinned_run_id": config["pinned_run_id"],
        "silver_payload_sha256": config["pinned_silver_payload_sha256"],
        "silver_payload_bytes": config["pinned_silver_payload_bytes"],
        "record_sha256": config["pinned_record_sha256"],
        "drive_readback_design_authorized": True,
        "gold_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
