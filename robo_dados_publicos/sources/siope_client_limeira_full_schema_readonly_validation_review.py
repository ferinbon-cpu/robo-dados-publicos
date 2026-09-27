from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_FULL_SCHEMA_READONLY_VALIDATION_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_FULL_SCHEMA_READONLY_VALIDATION_REVIEW"


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


def run_review(config: dict, evidence: dict, *, evidence_path: str | Path) -> dict:
    expected_config = {
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_FULL_SCHEMA_READONLY_VALIDATION_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "mode": "OFFLINE_PINNED_SIOPE_CLIENT_LIMEIRA_FULL_SCHEMA_READONLY_VALIDATION_REVIEW",
        "network_called": False,
        "pinned_run_id": 33014442460,
        "pinned_run_number": 1,
        "pinned_job_id": 98328886063,
        "pinned_head_sha": "09786f806cd3d62bef5268a94b8db60cbdd431c5",
        "pinned_artifact_id": 9623887505,
        "pinned_artifact_digest": "sha256:e3303ac2e53de7d0a7a6418f28f035fc344b9fb8de32bff6a326da1a05d74100",
        "pinned_unit_tests": 864,
        "pinned_historical_regressions": 109,
        "pinned_response_sha256": "0228721c96bbb72b695c1eb39d4e74b5ce180873b800ea3c5495da73f14a2253",
        "pinned_response_byte_count": 2600,
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_FULL_SCHEMA_READONLY_VALIDATION_RUN_1_0.8.0.json",
        "pinned_evidence_blob_sha": "b97c482dc3d2671663396bfe89b02378ce57005f",
        "full_schema_status": "PROVEN_EXACT_52_FIELDS_ON_PINNED_LIMEIRA_RUN",
        "single_bronze_capture_design_authorized": True,
        "recurring_collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_BRONZE_SINGLE_RECORD_CAPTURE_0_8_0",
    }
    _require(config, expected_config, "CONFIG")
    _require(_git_blob_sha(evidence_path), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB")
    _require(evidence.get("run_id"), config["pinned_run_id"], "RUN_ID")
    _require(evidence.get("job_id"), config["pinned_job_id"], "JOB_ID")
    _require(evidence.get("head_sha"), config["pinned_head_sha"], "HEAD_SHA")
    _require(evidence.get("artifact_id"), config["pinned_artifact_id"], "ARTIFACT_ID")
    _require(evidence.get("artifact_digest"), config["pinned_artifact_digest"], "ARTIFACT_DIGEST")
    _require(evidence.get("qa"), {"historical_regressions": 109, "unit_tests": 864}, "QA")
    result = evidence.get("result")
    if not isinstance(result, dict):
        raise ReviewError(f"{ERROR}_RESULT")
    checks = {
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_FULL_SCHEMA_READONLY_VALIDATION",
        "request_count": 1,
        "resource": "Dados_Gerais_Siope",
        "response_status": 200,
        "content_type": "application/json",
        "response_byte_count": 2600,
        "response_sha256": config["pinned_response_sha256"],
        "value_count": 1,
        "selected_schema_exact": True,
        "selected_schema_key_count": 52,
        "proven_schema_allowlist_count": 52,
        "all_records_match_municipality_code": True,
        "all_records_match_municipality_name": True,
        "all_records_match_year": True,
        "all_records_match_period": True,
        "all_records_match_state": True,
        "odata_nextlink_present": False,
        "redirect_followed": False,
        "retry_performed": False,
        "record_values_persisted": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }
    for key, expected in checks.items():
        _require(result.get(key), expected, f"RESULT_{key.upper()}")
    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "full_schema_status": config["full_schema_status"],
        "single_bronze_capture_design_authorized": True,
        "recurring_collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
