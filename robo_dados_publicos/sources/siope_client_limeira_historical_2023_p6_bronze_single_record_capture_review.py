from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW"


class Historical2023P6BronzeCaptureReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Historical2023P6BronzeCaptureReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise Historical2023P6BronzeCaptureReviewError(f"{ERROR}_{code}")


def _git_blob_sha(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()  # noqa: S324


def _canonical_sha256(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def run_review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "durable_historical_bronze_drive_persistence_design_authorized": True,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW_0_8_0",
        "historical_collection_authorized": False,
        "mode": "OFFLINE_PINNED_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_DRIVE_PERSISTENCE_0_8_0",
        "pinned_artifact_digest": "sha256:4c14ec929ae6e161ea5044aa457657644487e5fa4db51c72f435437776a80b3b",
        "pinned_artifact_id": 9629632056,
        "pinned_evidence_blob_sha": "8bf528eaf8582dabba89b96076171593ca75e903",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE_RUN_1_0.8.0.json",
        "pinned_head_sha": "0ea8597b02aa04af0c1ba9c505dc5ccd74b44531",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98378070280,
        "pinned_manifest_payload_blob_sha": "eec4c613dc669ecb6deaa87817039ae8b9bb952e",
        "pinned_manifest_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_RUN_1_MANIFEST_0.8.0.json",
        "pinned_record_payload_blob_sha": "e0f8f20db506cae0ace828d97e0ebeb7062d9ddd",
        "pinned_record_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_RUN_1_RECORD_0.8.0.json",
        "pinned_record_sha256": "8b63fd15413c3ab9ca5f82749ea5d89e5a1c92b06e7b80cb6def7af60b769919",
        "pinned_response_sha256": "a986596ea31bcfc8f39807736eb8d30d2c9ef62fd3e9cdeca59983e4df27f37e",
        "pinned_run_id": 33029369166,
        "pinned_run_number": 1,
        "pinned_unit_tests": 962,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
    }
    _require(config, expected_config, "CONFIG")

    root_path = Path(root)
    evidence_path = root_path / config["pinned_evidence_path"]
    record_path = root_path / config["pinned_record_payload_path"]
    manifest_path = root_path / config["pinned_manifest_payload_path"]

    _require(_git_blob_sha(evidence_path), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB")
    _require(_git_blob_sha(record_path), config["pinned_record_payload_blob_sha"], "RECORD_BLOB")
    _require(_git_blob_sha(manifest_path), config["pinned_manifest_payload_blob_sha"], "MANIFEST_BLOB")

    evidence = load_json(evidence_path)
    _require(evidence.get("run_id"), config["pinned_run_id"], "RUN_ID")
    _require(evidence.get("run_number"), config["pinned_run_number"], "RUN_NUMBER")
    _require(evidence.get("job_id"), config["pinned_job_id"], "JOB_ID")
    _require(evidence.get("head_sha"), config["pinned_head_sha"], "HEAD_SHA")
    _require(evidence.get("artifact_id"), config["pinned_artifact_id"], "ARTIFACT_ID")
    _require(evidence.get("artifact_digest"), config["pinned_artifact_digest"], "ARTIFACT_DIGEST")
    _require(
        evidence.get("qa"),
        {"historical_regressions": config["pinned_historical_regressions"], "unit_tests": config["pinned_unit_tests"]},
        "QA",
    )

    result = evidence.get("result")
    if not isinstance(result, dict):
        raise Historical2023P6BronzeCaptureReviewError(f"{ERROR}_RESULT")
    checks = {
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE",
        "request_count": 1,
        "resource": "Dados_Gerais_Siope",
        "response_status": 200,
        "content_type": "application/json",
        "response_byte_count": 2080,
        "response_sha256": config["pinned_response_sha256"],
        "value_count": 1,
        "selected_schema_exact": True,
        "selected_schema_key_count": 52,
        "record_sha256": config["pinned_record_sha256"],
        "bronze_record_persisted": True,
        "bronze_manifest_persisted": True,
        "odata_nextlink_present": False,
        "redirect_followed": False,
        "retry_performed": False,
        "response_envelope_persisted": False,
        "single_historical_record_capture_authorized": True,
        "historical_collection_authorized": False,
        "drive_persistence_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }
    for key, expected in checks.items():
        _require(result.get(key), expected, f"RESULT_{key.upper()}")

    expected_manifest = {
        "bronze_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_HISTORICAL_SINGLE_RECORD_V1",
        "drive_persistence_authorized": False,
        "historical_collection_authorized": False,
        "municipality_code": 352690,
        "nextlink_url_persisted": False,
        "period": 6,
        "processing_authorized": False,
        "record_count": 1,
        "record_sha256": config["pinned_record_sha256"],
        "recurrence_authorized": False,
        "resource": "Dados_Gerais_Siope",
        "response_byte_count": 2080,
        "response_envelope_persisted": False,
        "response_sha256": config["pinned_response_sha256"],
        "schema_key_count": 52,
        "software_version": "0.8.0",
        "source_id": config["source_id"],
        "state": "SP",
        "validation_prerequisite_run_id": 33028313110,
        "year": 2023,
    }
    manifest = load_json(manifest_path)
    _require(manifest, expected_manifest, "MANIFEST")
    _require(evidence.get("manifest"), expected_manifest, "EVIDENCE_MANIFEST")

    record = load_json(record_path)
    _require(len(record), 52, "RECORD_SCHEMA_COUNT")
    _require(record.get("COD_MUNI"), 352690, "RECORD_MUNICIPALITY")
    _require(record.get("NOM_MUNI"), "Limeira", "RECORD_MUNICIPALITY_NAME")
    _require(record.get("SIG_UF"), "SP", "RECORD_STATE")
    _require(record.get("NUM_ANO"), 2023, "RECORD_YEAR")
    _require(record.get("NUM_PERI"), 6, "RECORD_PERIOD")
    _require(_canonical_sha256(record), config["pinned_record_sha256"], "RECORD_CANONICAL_SHA256")

    verification = evidence.get("verification")
    if not isinstance(verification, dict):
        raise Historical2023P6BronzeCaptureReviewError(f"{ERROR}_VERIFICATION")
    _require(verification.get("artifact_file_count"), 3, "ARTIFACT_FILE_COUNT")
    _require(verification.get("artifact_files"), ["manifest.json", "record.json", "result.json"], "ARTIFACT_FILES")
    _require(verification.get("record_canonical_json_sha256_verified"), True, "CANONICAL_VERIFIED")
    _require(verification.get("record_canonical_json_sha256"), config["pinned_record_sha256"], "CANONICAL_SHA")
    _require(
        verification.get("record_identity"),
        {"municipality_code": 352690, "municipality_name": "Limeira", "period": 6, "state": "SP", "year": 2023},
        "RECORD_IDENTITY",
    )
    _require(verification.get("record_schema_key_count"), 52, "VERIFIED_SCHEMA_COUNT")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "pinned_year": 2023,
        "pinned_period": 6,
        "record_sha256": config["pinned_record_sha256"],
        "record_schema_key_count": 52,
        "durable_historical_bronze_drive_persistence_design_authorized": True,
        "historical_collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
