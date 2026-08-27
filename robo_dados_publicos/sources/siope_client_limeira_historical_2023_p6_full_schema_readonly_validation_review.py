from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW"


class Historical2023P6ValidationReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Historical2023P6ValidationReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise Historical2023P6ValidationReviewError(f"{ERROR}_{code}")


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324 - Git object identity, not security.


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "bronze_single_record_capture_design_authorized": True,
        "collection_authorized": False,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW_0_8_0",
        "historical_collection_authorized": False,
        "mode": "OFFLINE_PINNED_HISTORICAL_2023_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_BRONZE_SINGLE_RECORD_CAPTURE_0_8_0",
        "pinned_artifact_digest": "sha256:ecc6aaf9e4444d51f7dc7489776da5cee8ac1084e105bb6772692b3008281be0",
        "pinned_artifact_id": 9629258315,
        "pinned_artifact_result_sha256": "aca0515f81b747050816b89026d506e37129b966d7c302be052c1ad3a161a3f0",
        "pinned_evidence_blob_sha": "2def272a4b365c4276172db9396836e257c98b2c",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_FULL_SCHEMA_READONLY_VALIDATION_RUN_1_0.8.0.json",
        "pinned_head_sha": "257b63b8fc7db246853e328e78fe61a6864ed56c",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98374745065,
        "pinned_response_byte_count": 2080,
        "pinned_response_sha256": "a986596ea31bcfc8f39807736eb8d30d2c9ef62fd3e9cdeca59983e4df27f37e",
        "pinned_run_id": 33028313110,
        "pinned_schema_key_count": 52,
        "pinned_unit_tests": 951,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
    }
    _require(config, expected_config, "CONFIG_DRIFT")

    evidence_path = Path(root) / config["pinned_evidence_path"]
    raw = evidence_path.read_bytes()
    _require(_git_blob_sha(raw), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB_DRIFT")
    evidence = json.loads(raw.decode("utf-8"))
    expected_evidence = {
        "artifact_digest": config["pinned_artifact_digest"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-client-limeira-historical-2023-p6-full-schema-readonly-validation-33028313110",
        "artifact_size_bytes": 813,
        "artifact_result_sha256": config["pinned_artifact_result_sha256"],
        "content_type": "application/json",
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_FULL_SCHEMA_READONLY_VALIDATION_0_8_0",
        "generic_client_used": True,
        "head_sha": config["pinned_head_sha"],
        "historical_collection_authorized": False,
        "historical_failures": 0,
        "historical_passes": config["pinned_historical_regressions"],
        "historical_tests": config["pinned_historical_regressions"],
        "job_id": config["pinned_job_id"],
        "network_called": True,
        "network_method": "GET_ONLY",
        "odata_context_present": True,
        "odata_nextlink_followed": False,
        "odata_nextlink_present": False,
        "persistence_authorized": False,
        "processing_authorized": False,
        "query_values_persisted_in_result": False,
        "record_values_persisted": False,
        "recurrence_authorized": False,
        "redirect_followed": False,
        "request_count": 1,
        "resource": "Dados_Gerais_Siope",
        "response_body_persisted": False,
        "response_byte_count": config["pinned_response_byte_count"],
        "response_sha256": config["pinned_response_sha256"],
        "response_status": 200,
        "retry_performed": False,
        "run_id": config["pinned_run_id"],
        "run_number": 1,
        "schedule_enabled": False,
        "selected_schema_exact": True,
        "selected_schema_key_count": config["pinned_schema_key_count"],
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2023_P6_FULL_SCHEMA_READONLY_VALIDATION",
        "unit_failures": 0,
        "unit_passes": config["pinned_unit_tests"],
        "unit_tests": config["pinned_unit_tests"],
        "value_count": 1,
        "workflow_event": "workflow_dispatch",
        "workflow_head_branch": "main",
    }
    _require(evidence, expected_evidence, "EVIDENCE_DRIFT")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "pinned_year": 2023,
        "pinned_period": 6,
        "selected_schema_key_count": 52,
        "bronze_single_record_capture_design_authorized": True,
        "historical_collection_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
