from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW"


class Historical2021P6ValidationReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Historical2021P6ValidationReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise Historical2021P6ValidationReviewError(f"{ERROR}_{code}")


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324 - Git object identity, not security.


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {
        "bronze_single_record_capture_design_authorized": True,
        "collection_authorized": False,
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW_0_8_0",
        "historical_collection_authorized": False,
        "mode": "OFFLINE_PINNED_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW",
        "network_called": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_BRONZE_SINGLE_RECORD_CAPTURE_0_8_0",
        "pinned_artifact_digest": "sha256:71efbead60f90043af0d1ce82096a978ce63f986bab80c6880e4855ca5828961",
        "pinned_artifact_id": 9660150424,
        "pinned_artifact_result_sha256": "2edd37623393a1969069e71360ecb4a48f73f8edd5365e6dce90e891147248ea",
        "pinned_evidence_blob_sha": "6c13b93f4f95843f5449083527edd8b8faf895b8",
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION_RUN_1_0.8.0.json",
        "pinned_head_sha": "0fe1d98a529427c0507e2afcb80df2bc9896fbe4",
        "pinned_historical_regressions": 109,
        "pinned_job_id": 98633041095,
        "pinned_response_byte_count": 2074,
        "pinned_response_sha256": "469db39caf067ded62a398e522f6fead8a9195b2953310de6ad7169b50d68a44",
        "pinned_run_id": 33105190675,
        "pinned_schema_key_count": 52,
        "pinned_unit_tests": 1137,
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
        "all_records_match_municipality_code": True,
        "all_records_match_municipality_name": True,
        "all_records_match_period": True,
        "all_records_match_state": True,
        "all_records_match_year": True,
        "artifact_digest": "sha256:71efbead60f90043af0d1ce82096a978ce63f986bab80c6880e4855ca5828961",
        "artifact_id": 9660150424,
        "artifact_name": "siope-client-limeira-historical-2021-p6-full-schema-readonly-validation-33105190675",
        "artifact_result_sha256": "2edd37623393a1969069e71360ecb4a48f73f8edd5365e6dce90e891147248ea",
        "artifact_size_bytes": 816,
        "collection_authorized": False,
        "content_type": "application/json",
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION_0_8_0",
        "generic_client_used": True,
        "head_sha": "0fe1d98a529427c0507e2afcb80df2bc9896fbe4",
        "historical_collection_authorized": False,
        "historical_failures": 0,
        "historical_passes": 109,
        "historical_tests": 109,
        "job_id": 98633041095,
        "manual_single_historical_period_validation_authorization_consumed": True,
        "mode": "ONE_REQUEST_GENERIC_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_52_FIELD_SCHEMA_VALIDATION",
        "network_called": True,
        "network_method": "GET_ONLY",
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW_0_8_0",
        "nextlink_url_persisted": False,
        "odata_context_present": True,
        "odata_nextlink_followed": False,
        "odata_nextlink_present": False,
        "persistence_authorized": False,
        "processing_authorized": False,
        "proven_schema_allowlist_count": 52,
        "query_values_persisted_in_result": False,
        "record_values_persisted": False,
        "recurrence_authorized": False,
        "redirect_followed": False,
        "request_count": 1,
        "resource": "Dados_Gerais_Siope",
        "response_body_persisted": False,
        "response_byte_count": 2074,
        "response_sha256": "469db39caf067ded62a398e522f6fead8a9195b2953310de6ad7169b50d68a44",
        "response_status": 200,
        "retry_performed": False,
        "run_id": 33105190675,
        "run_number": 1,
        "schedule_enabled": False,
        "selected_schema_exact": True,
        "selected_schema_key_count": 52,
        "software_version": "0.8.0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2021_P6_FULL_SCHEMA_READONLY_VALIDATION",
        "unit_failures": 0,
        "unit_passes": 1137,
        "unit_tests": 1137,
        "value_count": 1,
        "workflow_event": "workflow_dispatch",
        "workflow_head_branch": "main",
    }
    _require(evidence, expected_evidence, "EVIDENCE_DRIFT")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "pinned_year": 2021,
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
