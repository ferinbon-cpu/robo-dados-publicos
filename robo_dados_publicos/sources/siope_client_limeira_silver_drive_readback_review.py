from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_REVIEW"


class SilverDriveReadbackReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SilverDriveReadbackReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SilverDriveReadbackReviewError(f"{ERROR}_{code}")


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_REVIEW_0_8_0",
        "gold_authorized": False,
        "gold_transform_preview_design_authorized": True,
        "mode": "OFFLINE_PINNED_SILVER_DRIVE_READBACK_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_GOLD_TRANSFORM_PREVIEW_0_8_0",
        "pinned_artifact_digest": "sha256:db330ac50ce8b29c09bce66425681b246a93f79449a395188c77c47d38d80a3a",
        "pinned_artifact_id": 9627254489,
        "pinned_evidence_blob_sha": "0e086989189e60129b742a4b4835243b853b209c",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_VERIFICATION_RUN_1_0.8.0.json",
        "pinned_head_sha": "d9e30d7321bff02a2d897422d06dbae877b272d5",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98357549012,
        "pinned_record_sha256": "20dd61298f9d4603fc7d5e20a373f331137d5bc37f59be687370bd0f289b97c6",
        "pinned_run_id": 33022961421,
        "pinned_schema_key_count": 52,
        "pinned_silver_payload_bytes": 2328,
        "pinned_silver_payload_sha256": "072283e3d9e5f12e6a3a697d32e653b64e618f4665e28f53e553b35506ce68da",
        "pinned_unit_tests": 912,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
    }
    _require(config, expected_config, "CONFIG_DRIFT")

    evidence = load_json(Path(root) / config["pinned_evidence_path"])
    expected_evidence = {
        "artifact_digest": config["pinned_artifact_digest"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-client-limeira-silver-drive-readback-verification-33022961421",
        "artifact_size_bytes": 664,
        "byte_identity_verified": True,
        "drive_file_download_count": 1,
        "drive_network_called": True,
        "drive_write_count": 0,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_VERIFICATION_0_8_0",
        "gold_authorized": False,
        "head_sha": config["pinned_head_sha"],
        "historical_failures": 0,
        "historical_passes": config["pinned_historical_regressions"],
        "historical_tests": config["pinned_historical_regressions"],
        "job_id": config["pinned_job_id"],
        "network_called": True,
        "next_gate": config["gate_id"],
        "processing_authorized": False,
        "record_count": 1,
        "record_sha256": config["pinned_record_sha256"],
        "recurrence_authorized": False,
        "remote_file_id_persisted": False,
        "remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2024_P6__352690__072283e3d9e5__silver_v1.json",
        "run_id": config["pinned_run_id"],
        "schedule_enabled": False,
        "schema_key_count": config["pinned_schema_key_count"],
        "silver_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_VALIDATED_RECORD_SILVER_V1",
        "silver_payload_bytes": config["pinned_silver_payload_bytes"],
        "silver_payload_md5_verified": True,
        "silver_payload_sha256": config["pinned_silver_payload_sha256"],
        "source_network_called": False,
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_READBACK_VERIFICATION",
        "unit_failures": 0,
        "unit_passes": config["pinned_unit_tests"],
        "unit_tests": config["pinned_unit_tests"],
        "workflow_event": "workflow_dispatch",
        "workflow_head_branch": "main",
    }
    _require(evidence, expected_evidence, "EVIDENCE_DRIFT")

    return {
        "gate_id": config["gate_id"],
        "gold_authorized": False,
        "gold_transform_preview_design_authorized": True,
        "network_called": False,
        "next_gate": config["next_gate"],
        "processing_authorized": False,
        "record_count": 1,
        "record_sha256": config["pinned_record_sha256"],
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "schema_key_count": 52,
        "silver_payload_bytes": config["pinned_silver_payload_bytes"],
        "silver_payload_sha256": config["pinned_silver_payload_sha256"],
        "status": PASS,
    }
