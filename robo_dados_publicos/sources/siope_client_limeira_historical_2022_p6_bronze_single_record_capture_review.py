from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW"


class Historical2022P6BronzeCaptureReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Historical2022P6BronzeCaptureReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise Historical2022P6BronzeCaptureReviewError(f"{ERROR}_{code}")


def _git_blob_sha(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()  # noqa: S324


def _canonical_sha256(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def run_review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "durable_historical_bronze_drive_persistence_design_authorized": True,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW_0_8_0",
        "historical_collection_authorized": False,
        "mode": "OFFLINE_PINNED_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_CAPTURE_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_DRIVE_PERSISTENCE_0_8_0",
        "pinned_artifact_digest": "sha256:8d2f55039eb11911e857f12ab91abc2b59d0c3c3b30fa8ce723e2f3162dd4cd0",
        "pinned_artifact_id": 9645355893,
        "pinned_evidence_blob_sha": "475a84a239c1f67cbe6da271ab4690174615a664",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_CAPTURE_RUN_1_0.8.0.json",
        "pinned_head_sha": "6a3a43ff9591f0d786aa13dedcb7bdb94c27fa1a",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98509478135,
        "pinned_manifest_payload_blob_sha": "148d06f671f83689d3753b8c7090661adf134cff",
        "pinned_manifest_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_RUN_1_MANIFEST_0.8.0.json",
        "pinned_record_payload_blob_sha": "124a95bf6bad0c54ada9fdb03f9a9735bc71c81e",
        "pinned_record_payload_path": "docs/evidence/payloads/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_RUN_1_RECORD_0.8.0.json",
        "pinned_record_sha256": "79b786f438d29803fe15d513f4ff17d4ab55fde1dd631f503b6752370e21b68a",
        "pinned_response_sha256": "66a716a4097730d5a77795a49aaf6b7fec86ec3324cf97fdd0bb9593b5f4b9d2",
        "pinned_run_id": 33069995137,
        "pinned_run_number": 1,
        "pinned_unit_tests": 1056,
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
    for key, expected in {
        "run_id": config["pinned_run_id"],
        "run_number": config["pinned_run_number"],
        "job_id": config["pinned_job_id"],
        "head_sha": config["pinned_head_sha"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_digest": config["pinned_artifact_digest"],
    }.items():
        _require(evidence.get(key), expected, key.upper())
    _require(evidence.get("qa"), {"historical_regressions": 109, "unit_tests": 1056}, "QA")

    result = evidence.get("result")
    if not isinstance(result, dict):
        raise Historical2022P6BronzeCaptureReviewError(f"{ERROR}_RESULT")
    checks = {
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_CAPTURE",
        "request_count": 1,
        "resource": "Dados_Gerais_Siope",
        "response_status": 200,
        "content_type": "application/json",
        "response_byte_count": 2075,
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
        "response_byte_count": 2075,
        "response_envelope_persisted": False,
        "response_sha256": config["pinned_response_sha256"],
        "schema_key_count": 52,
        "software_version": "0.8.0",
        "source_id": config["source_id"],
        "state": "SP",
        "validation_prerequisite_run_id": 33067774766,
        "year": 2022,
    }
    manifest = load_json(manifest_path)
    _require(manifest, expected_manifest, "MANIFEST")
    _require(evidence.get("manifest"), expected_manifest, "EVIDENCE_MANIFEST")

    record = load_json(record_path)
    _require(len(record), 52, "RECORD_SCHEMA_COUNT")
    _require(record.get("COD_MUNI"), 352690, "RECORD_MUNICIPALITY")
    _require(record.get("NOM_MUNI"), "Limeira", "RECORD_MUNICIPALITY_NAME")
    _require(record.get("SIG_UF"), "SP", "RECORD_STATE")
    _require(record.get("NUM_ANO"), 2022, "RECORD_YEAR")
    _require(record.get("NUM_PERI"), 6, "RECORD_PERIOD")
    _require(_canonical_sha256(record), config["pinned_record_sha256"], "RECORD_CANONICAL_SHA256")

    verification = evidence.get("verification")
    if not isinstance(verification, dict):
        raise Historical2022P6BronzeCaptureReviewError(f"{ERROR}_VERIFICATION")
    _require(verification.get("artifact_file_count"), 3, "ARTIFACT_FILE_COUNT")
    _require(verification.get("artifact_files"), ["manifest.json", "record.json", "result.json"], "ARTIFACT_FILES")
    _require(verification.get("record_canonical_json_sha256_verified"), True, "CANONICAL_VERIFIED")
    _require(verification.get("record_canonical_json_sha256"), config["pinned_record_sha256"], "CANONICAL_SHA")
    _require(verification.get("record_identity"), {"municipality_code": 352690, "municipality_name": "Limeira", "period": 6, "state": "SP", "year": 2022}, "RECORD_IDENTITY")
    _require(verification.get("record_schema_key_count"), 52, "VERIFIED_SCHEMA_COUNT")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "pinned_year": 2022,
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
