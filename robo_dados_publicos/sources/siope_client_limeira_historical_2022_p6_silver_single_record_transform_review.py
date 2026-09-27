from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_REVIEW"


class HistoricalSilverTransformReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HistoricalSilverTransformReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise HistoricalSilverTransformReviewError(f"{ERROR}_{code}")


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_REVIEW_0_8_0",
        "gold_authorized": False,
        "historical_collection_authorized": False,
        "mode": "OFFLINE_PINNED_HISTORICAL_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_DRIVE_PERSISTENCE_0_8_0",
        "pinned_artifact_digest": "sha256:8f1e846b12ed0b499accd41ee0e8e783fe95702b814aafedaf0ddcebac219ff1",
        "pinned_artifact_id": 9648287214,
        "pinned_evidence_blob_sha": "174f525e7924ae7a4a4020d14b9af4cf6489f65b",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW_RUN_1_0.8.0.json",
        "pinned_head_sha": "c2ed70e5d5b63d5ac34c9891938abe048a1a115b",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98533581168,
        "pinned_record_sha256": "79b786f438d29803fe15d513f4ff17d4ab55fde1dd631f503b6752370e21b68a",
        "pinned_run_id": 33076965815,
        "pinned_schema_key_count": 52,
        "pinned_silver_payload_bytes": 1825,
        "pinned_silver_payload_sha256": "d8f14e5fa52cf214c837cb6a3d702f8b5a12310252045695547b289f88a03632",
        "pinned_unit_tests": 1084,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "silver_drive_persistence_design_authorized": True,
        "silver_remote_write_authorized": False,
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
        "artifact_name": "siope-client-limeira-historical-2022-p6-silver-single-record-transform-preview-33076965815",
        "artifact_size_bytes": 613,
        "drive_network_called": False,
        "drive_write_count": 0,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW_0_8_0",
        "gold_authorized": False,
        "head_sha": config["pinned_head_sha"],
        "historical_collection_authorized": False,
        "historical_failures": 0,
        "historical_passes": config["pinned_historical_regressions"],
        "historical_tests": config["pinned_historical_regressions"],
        "identity_verified": True,
        "job_id": config["pinned_job_id"],
        "lossless_record_embedding_verified": True,
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_REVIEW_0_8_0",
        "processing_authorized": False,
        "record_count": 1,
        "record_sha256": config["pinned_record_sha256"],
        "recurrence_authorized": False,
        "run_id": config["pinned_run_id"],
        "schedule_enabled": False,
        "schema_key_count": config["pinned_schema_key_count"],
        "silver_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_VALIDATED_RECORD_SILVER_V1",
        "silver_payload_bytes": config["pinned_silver_payload_bytes"],
        "silver_payload_persisted": False,
        "silver_payload_sha256": config["pinned_silver_payload_sha256"],
        "silver_remote_write_authorized": False,
        "source_network_called": False,
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_SILVER_SINGLE_RECORD_TRANSFORM_PREVIEW",
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
        "historical_collection_authorized": False,
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
