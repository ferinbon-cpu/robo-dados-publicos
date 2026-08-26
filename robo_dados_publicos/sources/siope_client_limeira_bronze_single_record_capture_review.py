from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW"


class ReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise ReviewError(f"{ERROR}_{code}")


def _git_blob_sha(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()  # noqa: S324


def _canonical_sha256(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def run_review(
    config: dict,
    evidence: dict,
    *,
    evidence_path: str | Path,
    record_path: str | Path,
    manifest_path: str | Path,
) -> dict:
    expected_config = {
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "mode": "OFFLINE_PINNED_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW",
        "network_called": False,
        "pinned_run_id": 33015912285,
        "pinned_run_number": 1,
        "pinned_job_id": 98333960231,
        "pinned_head_sha": "cb83f82a36eaba6db7dbf58f6ebd03e6faacbc5f",
        "pinned_artifact_id": 9624488389,
        "pinned_artifact_digest": "sha256:1a7d66db75042e672ca2c63cca64d5668efdc0a1f58b28f4c796b82cf8104c0a",
        "pinned_unit_tests": 869,
        "pinned_historical_regressions": 109,
        "pinned_record_sha256": "20dd61298f9d4603fc7d5e20a373f331137d5bc37f59be687370bd0f289b97c6",
        "pinned_response_sha256": "0228721c96bbb72b695c1eb39d4e74b5ce180873b800ea3c5495da73f14a2253",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_CAPTURE_RUN_1_0.8.0.json",
        "pinned_evidence_blob_sha": "47af51041f98bab94c2e714e435c0b5666428536",
        "pinned_record_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_RUN_1_RECORD_0.8.0.json",
        "pinned_record_payload_blob_sha": "2d6198b4eb370e13ca9143ad0474d8f99f148a2b",
        "pinned_manifest_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_RUN_1_MANIFEST_0.8.0.json",
        "pinned_manifest_payload_blob_sha": "80f47c36e2354fca58b1846d090336cfa459943c",
        "durable_bronze_drive_persistence_design_authorized": True,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_BRONZE_DRIVE_PERSISTENCE_0_8_0",
    }
    _require(config, expected_config, "CONFIG")
    _require(_git_blob_sha(evidence_path), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB")
    _require(_git_blob_sha(record_path), config["pinned_record_payload_blob_sha"], "RECORD_BLOB")
    _require(_git_blob_sha(manifest_path), config["pinned_manifest_payload_blob_sha"], "MANIFEST_BLOB")

    _require(evidence.get("run_id"), config["pinned_run_id"], "RUN_ID")
    _require(evidence.get("run_number"), config["pinned_run_number"], "RUN_NUMBER")
    _require(evidence.get("job_id"), config["pinned_job_id"], "JOB_ID")
    _require(evidence.get("head_sha"), config["pinned_head_sha"], "HEAD_SHA")
    _require(evidence.get("artifact_id"), config["pinned_artifact_id"], "ARTIFACT_ID")
    _require(evidence.get("artifact_digest"), config["pinned_artifact_digest"], "ARTIFACT_DIGEST")
    _require(evidence.get("qa"), {"historical_regressions": 109, "unit_tests": 869}, "QA")

    result = evidence.get("result")
    if not isinstance(result, dict):
        raise ReviewError(f"{ERROR}_RESULT")
    checks = {
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_CAPTURE",
        "request_count": 1,
        "resource": "Dados_Gerais_Siope",
        "response_status": 200,
        "content_type": "application/json",
        "response_byte_count": 2600,
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
        "single_collection_authorized": True,
        "recurring_collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }
    for key, expected in checks.items():
        _require(result.get(key), expected, f"RESULT_{key.upper()}")

    manifest = load_json(manifest_path)
    expected_manifest = {
        "bronze_contract": "SIOPE_DADOS_GERAIS_LIMEIRA_SINGLE_RECORD_V1",
        "municipality_code": 352690,
        "nextlink_url_persisted": False,
        "period": 6,
        "processing_authorized": False,
        "record_count": 1,
        "record_sha256": config["pinned_record_sha256"],
        "recurrence_authorized": False,
        "resource": "Dados_Gerais_Siope",
        "response_byte_count": 2600,
        "response_envelope_persisted": False,
        "response_sha256": config["pinned_response_sha256"],
        "schema_key_count": 52,
        "software_version": "0.8.0",
        "source_id": config["source_id"],
        "state": "SP",
        "year": 2024,
    }
    _require(manifest, expected_manifest, "MANIFEST")
    _require(evidence.get("manifest"), expected_manifest, "EVIDENCE_MANIFEST")

    record = load_json(record_path)
    _require(len(record), 52, "RECORD_SCHEMA_COUNT")
    _require(record.get("COD_MUNI"), 352690, "RECORD_MUNICIPALITY")
    _require(record.get("NOM_MUNI"), "Limeira", "RECORD_MUNICIPALITY_NAME")
    _require(record.get("SIG_UF"), "SP", "RECORD_STATE")
    _require(record.get("NUM_ANO"), 2024, "RECORD_YEAR")
    _require(record.get("NUM_PERI"), 6, "RECORD_PERIOD")
    _require(_canonical_sha256(record), config["pinned_record_sha256"], "RECORD_CANONICAL_SHA256")

    verification = evidence.get("verification")
    if not isinstance(verification, dict):
        raise ReviewError(f"{ERROR}_VERIFICATION")
    _require(verification.get("artifact_file_count"), 3, "ARTIFACT_FILE_COUNT")
    _require(verification.get("artifact_files"), ["manifest.json", "record.json", "result.json"], "ARTIFACT_FILES")
    _require(verification.get("record_canonical_json_sha256_verified"), True, "CANONICAL_VERIFIED")
    _require(verification.get("record_canonical_json_sha256"), config["pinned_record_sha256"], "CANONICAL_SHA")
    _require(verification.get("record_schema_key_count"), 52, "VERIFIED_SCHEMA_COUNT")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "record_sha256": config["pinned_record_sha256"],
        "record_schema_key_count": 52,
        "durable_bronze_drive_persistence_design_authorized": True,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
