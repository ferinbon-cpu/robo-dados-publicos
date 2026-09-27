from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_READBACK_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_READBACK_REVIEW"


class BronzeDriveReadbackReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BronzeDriveReadbackReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise BronzeDriveReadbackReviewError(f"{ERROR}_{code}")


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_READBACK_REVIEW_0_8_0",
        "mode": "OFFLINE_PINNED_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_READBACK_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW_0_8_0",
        "pinned_artifact_digest": "sha256:9f120b40c20ab033f0df92b5f81aba0d2b9230be54679fc70654fe1a49b419b7",
        "pinned_artifact_id": 9625604687,
        "pinned_bundle_bytes": 2461,
        "pinned_bundle_sha256": "eb30b820c34a702a5850b1e246d7d29a8d86c0e84064b79b14c0308060950dbf",
        "pinned_evidence_blob_sha": "7d8966df9100ba77c28ceb9ce7d9e99c46bf1eb0",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_READBACK_VERIFICATION_RUN_1_0.8.0.json",
        "pinned_head_sha": "9f0a50cabd206256219037923c91656f688f3496",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98343070069,
        "pinned_record_sha256": "20dd61298f9d4603fc7d5e20a373f331137d5bc37f59be687370bd0f289b97c6",
        "pinned_run_id": 33018602293,
        "pinned_run_number": 1,
        "pinned_schema_key_count": 52,
        "pinned_unit_tests": 885,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "silver_authorized": False,
        "silver_transform_preview_design_authorized": True,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
    }
    _require(config, expected_config, "CONFIG_DRIFT")

    evidence = load_json(Path(root) / config["pinned_evidence_path"])
    expected_evidence = {
        "artifact_digest": config["pinned_artifact_digest"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-client-limeira-bronze-drive-readback-verification-33018602293",
        "artifact_size_bytes": 632,
        "bundle_bytes": config["pinned_bundle_bytes"],
        "bundle_md5_verified": True,
        "bundle_sha256": config["pinned_bundle_sha256"],
        "byte_identity_verified": True,
        "drive_file_download_count": 1,
        "drive_network_called": True,
        "drive_write_count": 0,
        "event": "workflow_dispatch",
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_READBACK_VERIFICATION_0_8_0",
        "gold_authorized": False,
        "head_branch": "main",
        "head_sha": config["pinned_head_sha"],
        "historical_regressions": 109,
        "historical_regressions_passed": 109,
        "job_id": config["pinned_job_id"],
        "network_called": True,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_READBACK_REVIEW_0_8_0",
        "processing_authorized": False,
        "record_count": 1,
        "record_sha256": config["pinned_record_sha256"],
        "recurrence_authorized": False,
        "remote_file_id_persisted": False,
        "remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2024_P6__352690__20dd61298f9d__bundle.json",
        "run_id": config["pinned_run_id"],
        "run_number": config["pinned_run_number"],
        "schedule_enabled": False,
        "schema_key_count": config["pinned_schema_key_count"],
        "silver_authorized": False,
        "source_network_called": False,
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_READBACK_VERIFICATION",
        "unit_tests": config["pinned_unit_tests"],
        "unit_tests_passed": config["pinned_unit_tests"],
    }
    _require(evidence, expected_evidence, "EVIDENCE_DRIFT")

    return {
        "bundle_sha256": config["pinned_bundle_sha256"],
        "gate_id": config["gate_id"],
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
