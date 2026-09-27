from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION_REVIEW"


class SiopeClientLimeiraLiveValidationReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeClientLimeiraLiveValidationReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeClientLimeiraLiveValidationReviewError(f"{ERROR}_{code}")


def _git_blob_sha(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324 - Git object identity requires SHA-1


def run_review(config: dict, evidence: dict, *, evidence_path: str | Path) -> dict:
    exact_config = {
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "mode": "OFFLINE_PINNED_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION_REVIEW",
        "network_called": False,
        "pinned_run_id": 33013439285,
        "pinned_run_number": 1,
        "pinned_job_id": 98325382892,
        "pinned_head_sha": "94b5d450b652f11d0d7a00b3cf4beae39651e542",
        "pinned_artifact_id": 9623487310,
        "pinned_artifact_digest": "sha256:278cac26737784c86d2694a0fc68a5d9639661271eb8452a2683ea98c9f3e484",
        "pinned_unit_tests": 856,
        "pinned_historical_regressions": 109,
        "pinned_response_sha256": "9c71bcb25ac1439fa5d505f10df3d0e9b6e1dc1ff965dc7202f0c2e9527c9ed4",
        "pinned_response_byte_count": 264,
        "pinned_evidence_path": "docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION_RUN_1_0.8.0.json",
        "pinned_evidence_blob_sha": "8e8521739de65be5ca0f73449cac1a754c8f1981",
        "generic_client_contract_status": "PROVEN_ON_PINNED_MANUAL_LIMEIRA_RUN",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_FULL_SCHEMA_READONLY_VALIDATION_0_8_0",
    }
    _require(set(config), set(exact_config), "CONFIG_KEYS")
    for key, expected in exact_config.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(_git_blob_sha(evidence_path), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB_SHA")
    exact_top = {
        "evidence_type": "M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION_RUN_1_0_8_0",
        "run_id": config["pinned_run_id"],
        "run_number": config["pinned_run_number"],
        "job_id": config["pinned_job_id"],
        "head_sha": config["pinned_head_sha"],
        "workflow_path": ".github/workflows/siope-client-limeira-live-validation-gate.yml",
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-client-limeira-live-validation-33013439285",
        "artifact_digest": config["pinned_artifact_digest"],
    }
    _require(set(evidence), set(exact_top) | {"qa", "result"}, "EVIDENCE_KEYS")
    for key, expected in exact_top.items():
        _require(evidence.get(key), expected, f"EVIDENCE_{key.upper()}")
    _require(
        evidence.get("qa"),
        {"historical_regressions": config["pinned_historical_regressions"], "unit_tests": config["pinned_unit_tests"]},
        "EVIDENCE_QA",
    )

    result = evidence.get("result")
    if not isinstance(result, dict):
        raise SiopeClientLimeiraLiveValidationReviewError(f"{ERROR}_RESULT_OBJECT_REQUIRED")
    expected_result = {
        "status": "PASS_M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION",
        "gate_id": "M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION_0_8_0",
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "mode": "ONE_REQUEST_GENERIC_SIOPE_CLIENT_LIMEIRA_IDENTITY_VALIDATION",
        "network_called": True,
        "network_method": "GET_ONLY",
        "request_count": 1,
        "generic_client_used": True,
        "resource": "Dados_Gerais_Siope",
        "response_status": 200,
        "content_type": "application/json",
        "response_byte_count": config["pinned_response_byte_count"],
        "response_sha256": config["pinned_response_sha256"],
        "odata_context_present": True,
        "odata_nextlink_present": False,
        "odata_nextlink_followed": False,
        "redirect_followed": False,
        "retry_performed": False,
        "value_count": 1,
        "selected_schema_exact": True,
        "selected_schema_key_count": 5,
        "all_records_match_municipality_code": True,
        "all_records_match_municipality_name": True,
        "all_records_match_year": True,
        "all_records_match_period": True,
        "all_records_match_state": True,
        "response_body_persisted": False,
        "record_values_persisted": False,
        "query_values_persisted_in_result": False,
        "nextlink_url_persisted": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "manual_single_validation_authorization_consumed": True,
        "next_gate": "M7_SIOPE_CLIENT_LIMEIRA_LIVE_VALIDATION_REVIEW_0_8_0",
    }
    _require(set(result), set(expected_result), "RESULT_KEYS")
    for key, expected in expected_result.items():
        _require(result.get(key), expected, f"RESULT_{key.upper()}")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "network_called": False,
        "pinned_run_id": config["pinned_run_id"],
        "pinned_artifact_id": config["pinned_artifact_id"],
        "qa_unit_tests": config["pinned_unit_tests"],
        "qa_historical_regressions": config["pinned_historical_regressions"],
        "generic_client_live_status": "PROVEN_LIMEIRA_352690_SP_2024_6",
        "resource_contract_status": "PROVEN_DADOS_GERAIS_SIOPE_THROUGH_GENERIC_CLIENT",
        "response_contract_status": "HTTP_200_JSON_ODATA_VALUE_ONE_RECORD",
        "five_field_identity_schema_status": "PROVEN_EXACT",
        "full_schema_validation_runtime_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
