from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_SILVER_SINGLE_RECORD_TRANSFORM_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_SILVER_SINGLE_RECORD_TRANSFORM_REVIEW"


class SilverTransformReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SilverTransformReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SilverTransformReviewError(f"{ERROR}_{code}")


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_SILVER_SINGLE_RECORD_TRANSFORM_REVIEW_0_8_0",
        "mode": "OFFLINE_PINNED_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_SILVER_DRIVE_PERSISTENCE_0_8_0",
        "pinned_artifact_digest": "sha256:d25aadaa164fc2c762afb7e04d6891e033e08552b3ecb09f7a828df045a03bec",
        "pinned_artifact_id": 9626019769,
        "pinned_evidence_blob_sha": "b412534125048247a4e1d8f3a3ff7dd22f167c21",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW_RUN_1_0.8.0.json",
        "pinned_head_sha": "9ab97bdeb648da7fb008726ee42bfb867be8a530",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98346914957,
        "pinned_record_sha256": "20dd61298f9d4603fc7d5e20a373f331137d5bc37f59be687370bd0f289b97c6",
        "pinned_run_id": 33019750859,
        "pinned_schema_key_count": 52,
        "pinned_silver_payload_bytes": 2328,
        "pinned_silver_payload_sha256": "072283e3d9e5f12e6a3a697d32e653b64e618f4665e28f53e553b35506ce68da",
        "pinned_unit_tests": 895,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "silver_drive_persistence_design_authorized": True,
        "silver_remote_write_authorized": False,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
    }
    _require(config, expected_config, "CONFIG_DRIFT")

    evidence = load_json(Path(root) / config["pinned_evidence_path"])
    expected_evidence = {
        "artifact_digest": config["pinned_artifact_digest"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-client-limeira-silver-single-record-transform-preview-33019750859",
        "artifact_size_bytes": 581,
        "drive_network_called": False,
        "drive_write_count": 0,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW_0_8_0",
        "gold_authorized": False,
        "head_sha": config["pinned_head_sha"],
        "historical_failures": 0,
        "historical_passes": config["pinned_historical_regressions"],
        "historical_tests": config["pinned_historical_regressions"],
        "identity_verified": True,
        "job_id": config["pinned_job_id"],
        "lossless_record_embedding_verified": True,
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_SILVER_SINGLE_RECORD_TRANSFORM_REVIEW_0_8_0",
        "processing_authorized": False,
        "record_count": 1,
        "record_sha256": config["pinned_record_sha256"],
        "recurrence_authorized": False,
        "run_id": config["pinned_run_id"],
        "schedule_enabled": False,
        "schema_key_count": config["pinned_schema_key_count"],
        "silver_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_VALIDATED_RECORD_SILVER_V1",
        "silver_payload_bytes": config["pinned_silver_payload_bytes"],
        "silver_payload_persisted": False,
        "silver_payload_sha256": config["pinned_silver_payload_sha256"],
        "silver_remote_write_authorized": False,
        "source_network_called": False,
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW",
        "unit_failures": 0,
        "unit_passes": config["pinned_unit_tests"],
        "unit_tests": config["pinned_unit_tests"],
        "workflow_event": "workflow_dispatch",
        "workflow_head_branch": "main",
    }
    _require(evidence, expected_evidence, "EVIDENCE_DRIFT")

    return {
        "gate_id": config["gate_id"],
        "network_called": False,
        "next_gate": config["next_gate"],
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "silver_drive_persistence_design_authorized": True,
        "silver_payload_bytes": config["pinned_silver_payload_bytes"],
        "silver_payload_sha256": config["pinned_silver_payload_sha256"],
        "silver_remote_write_authorized": False,
        "status": PASS,
    }
