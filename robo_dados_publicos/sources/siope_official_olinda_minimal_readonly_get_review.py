from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_REVIEW"
PASS = "PASS_M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_REVIEW"


class SiopeOfficialOlindaMinimalReadonlyGetReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaMinimalReadonlyGetReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaMinimalReadonlyGetReviewError(f"{ERROR}_{code}")


def _git_blob_sha(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324 - Git object identity requires SHA-1


def run_review(config: dict, evidence: dict, *, evidence_path: str | Path) -> dict:
    exact_config = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "mode": "OFFLINE_PINNED_MINIMAL_READONLY_GET_REVIEW",
        "network_called": False,
        "pinned_run_id": 33007890616,
        "pinned_run_number": 2,
        "pinned_job_id": 98306304632,
        "pinned_head_sha": "b1c519edaa012f7cdc4af296b03a786b2ad9a479",
        "pinned_artifact_id": 9621300733,
        "pinned_artifact_digest": "sha256:8f0d6062fdb79152b3e2f77ec6b7493e99ac007a468f84676fd5a1534a67266b",
        "pinned_unit_tests": 833,
        "pinned_historical_regressions": 109,
        "pinned_response_sha256": "e5d798232bb246234bd68319047b6c01485bbcbc7789bf08dd3e0f1cf8390416",
        "pinned_response_byte_count": 226681,
        "pinned_value_count": 184,
        "pinned_schema_key_count": 52,
        "minimal_get_contract_status": "PROVEN_ON_PINNED_MANUAL_NON_LIMEIRA_RUN",
        "ongoing_resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_DESIGN_0_8_0",
    }
    for key, expected in exact_config.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(
        config.get("pinned_evidence_path"),
        "docs/evidence/M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_RUN_2_0.8.0.json",
        "CONFIG_EVIDENCE_PATH",
    )
    _require(config.get("pinned_evidence_blob_sha"), "8ac8e090256922b6b8f546f233c861f5df84eef9", "CONFIG_EVIDENCE_BLOB_SHA")
    _require(
        config.get("required_schema_keys_for_limeira_pilot"),
        ["COD_MUNI", "NOM_MUNI", "NUM_ANO", "NUM_PERI", "SIG_UF"],
        "CONFIG_REQUIRED_SCHEMA_KEYS",
    )
    _require(_git_blob_sha(evidence_path), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB_SHA")

    exact_evidence = {
        "evidence_type": "M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_RUN_2_0_8_0",
        "run_id": config["pinned_run_id"],
        "run_number": config["pinned_run_number"],
        "job_id": config["pinned_job_id"],
        "head_sha": config["pinned_head_sha"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-official-olinda-minimal-readonly-get-33007890616",
        "artifact_digest": config["pinned_artifact_digest"],
    }
    for key, expected in exact_evidence.items():
        _require(evidence.get(key), expected, f"EVIDENCE_{key.upper()}")
    _require(evidence.get("qa"), {"historical_regressions": 109, "unit_tests": 833}, "EVIDENCE_QA")

    result = evidence.get("result")
    if not isinstance(result, dict):
        raise SiopeOfficialOlindaMinimalReadonlyGetReviewError(f"{ERROR}_RESULT_OBJECT_REQUIRED")

    required_result = {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET",
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_0_8_0",
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "mode": "EXACT_ONE_REQUEST_NON_LIMEIRA_READONLY_ODATA_GET",
        "network_called": True,
        "network_method": "GET_ONLY",
        "request_count": 1,
        "fixed_non_limeira_example": True,
        "pilot_limeira_values_sent": False,
        "response_status": 200,
        "content_type": "application/json",
        "response_byte_count": config["pinned_response_byte_count"],
        "response_sha256": config["pinned_response_sha256"],
        "top_level_json_object": True,
        "value_list_present": True,
        "value_count": config["pinned_value_count"],
        "first_record_object": True,
        "first_record_schema_key_count": config["pinned_schema_key_count"],
        "odata_context_present": True,
        "odata_nextlink_present": False,
        "redirect_followed": False,
        "odata_nextlink_followed": False,
        "response_body_persisted": False,
        "record_values_persisted": False,
        "nextlink_url_persisted": False,
        "query_values_persisted_in_result": False,
        "artifact_downloaded": False,
        "form_submission": False,
        "post_request_performed": False,
        "head_request_performed": False,
        "authentication_performed": False,
        "credentials_captured": False,
        "cookies_captured": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "automatic_route_promotion": False,
        "ongoing_resource_get_authorized": False,
        "manual_single_get_authorization_consumed": True,
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_MINIMAL_READONLY_GET_REVIEW_0_8_0",
    }
    for key, expected in required_result.items():
        _require(result.get(key), expected, f"RESULT_{key.upper()}")

    schema_keys = result.get("first_record_schema_keys")
    if not isinstance(schema_keys, list) or len(schema_keys) != config["pinned_schema_key_count"]:
        raise SiopeOfficialOlindaMinimalReadonlyGetReviewError(f"{ERROR}_SCHEMA_KEYS_COUNT")
    if len(set(schema_keys)) != len(schema_keys) or any(not isinstance(key, str) or not key for key in schema_keys):
        raise SiopeOfficialOlindaMinimalReadonlyGetReviewError(f"{ERROR}_SCHEMA_KEYS_INVALID")
    missing = sorted(set(config["required_schema_keys_for_limeira_pilot"]) - set(schema_keys))
    if missing:
        raise SiopeOfficialOlindaMinimalReadonlyGetReviewError(f"{ERROR}_PILOT_SCHEMA_KEYS_MISSING")

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
        "executable_contract_status": "PROVEN_FOR_EXACT_RESOURCE_AND_PARAMETER_SHAPE_ON_PINNED_MANUAL_RUN",
        "response_contract_status": "HTTP_200_JSON_ODATA_VALUE_PROVEN_ON_PINNED_RUN",
        "schema_status": "PROVEN_52_FIELDS_ON_PINNED_NON_LIMEIRA_RUN",
        "required_limeira_pilot_schema_keys_observed": True,
        "query_narrowing_status": "UNPROVEN_PENDING_LIMEIRA_PILOT",
        "ongoing_resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
