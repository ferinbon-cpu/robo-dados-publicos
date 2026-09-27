from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_READBACK_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_READBACK_REVIEW"


class HistoricalSilverDriveReadbackReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HistoricalSilverDriveReadbackReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise HistoricalSilverDriveReadbackReviewError(f"{ERROR}_{code}")


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_READBACK_REVIEW_0_8_0",
        "gold_authorized": False,
        "gold_transform_preview_design_authorized": True,
        "mode": "OFFLINE_PINNED_HISTORICAL_SILVER_DRIVE_READBACK_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_GOLD_TRANSFORM_PREVIEW_0_8_0",
        "pinned_artifact_digest": "sha256:51e3167b8adf1f9974d82675ce9ce7d1425523653316cb1508cdc41d0cfeeffe",
        "pinned_artifact_id": 9631234755,
        "pinned_evidence_blob_sha": "139d8356610ed39c56934b5d498e980ff1077624",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_READBACK_VERIFICATION_RUN_1_0.8.0.json",
        "pinned_head_sha": "63bfe6e34c13af3ec6c4a07d80ecf288be57c024",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98392018636,
        "pinned_record_sha256": "8b63fd15413c3ab9ca5f82749ea5d89e5a1c92b06e7b80cb6def7af60b769919",
        "pinned_run_id": 33033807842,
        "pinned_schema_key_count": 52,
        "pinned_silver_payload_bytes": 1830,
        "pinned_silver_payload_sha256": "6d5c6a96f7a0b57b06ad6a6b7078a46ba58ef5fd1242f08c3de8c7aa5f2c87fb",
        "pinned_unit_tests": 1006,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
    }
    _require(config, expected_config, "CONFIG_DRIFT")

    evidence_path = Path(root) / config["pinned_evidence_path"]
    raw = evidence_path.read_bytes()
    _require(_git_blob_sha(raw), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB_SHA")
    evidence = json.loads(raw.decode("utf-8"))
    expected_evidence = {
        "artifact_digest": config["pinned_artifact_digest"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-client-limeira-historical-2023-p6-silver-drive-readback-verification-33033807842",
        "artifact_size_bytes": 691,
        "byte_identity_verified": True,
        "drive_file_download_count": 1,
        "drive_network_called": True,
        "drive_write_count": 0,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_READBACK_VERIFICATION_0_8_0",
        "gold_authorized": False,
        "head_sha": config["pinned_head_sha"],
        "historical_collection_authorized": False,
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
        "remote_name": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA__Dados_Gerais_Siope__Limeira_SP__2023_P6__352690__6d5c6a96f7a0__silver_v1.json",
        "run_id": config["pinned_run_id"],
        "schedule_enabled": False,
        "schema_key_count": config["pinned_schema_key_count"],
        "silver_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_VALIDATED_RECORD_SILVER_V1",
        "silver_payload_bytes": config["pinned_silver_payload_bytes"],
        "silver_payload_md5_verified": True,
        "silver_payload_sha256": config["pinned_silver_payload_sha256"],
        "source_network_called": False,
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_SILVER_DRIVE_READBACK_VERIFICATION",
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
        "historical_collection_authorized": False,
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
