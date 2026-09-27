from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_REVIEW"
PASS = "PASS_M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_REVIEW"


class SiopeOfficialOlindaLimeiraPilotReadonlyGetReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetReviewError(f"{ERROR}_{code}")


def _git_blob_sha(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324 - Git object identity requires SHA-1


def run_review(config: dict, evidence: dict, *, evidence_path: str | Path) -> dict:
    exact_config = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "mode": "OFFLINE_PINNED_LIMEIRA_PILOT_READONLY_GET_REVIEW",
        "network_called": False,
        "pinned_run_id": 33011469147,
        "pinned_run_number": 2,
        "pinned_job_id": 98318551596,
        "pinned_head_sha": "99a2fba53529da31c19a54e35fc74910cc614c1a",
        "pinned_artifact_id": 9622695666,
        "pinned_artifact_digest": "sha256:056dfebf034205579241e01dbd88c35cb8ecdb694fa04c28e0be324495874449",
        "pinned_unit_tests": 843,
        "pinned_historical_regressions": 109,
        "pinned_response_sha256": "9c71bcb25ac1439fa5d505f10df3d0e9b6e1dc1ff965dc7202f0c2e9527c9ed4",
        "pinned_response_byte_count": 264,
        "pinned_value_count": 1,
        "pinned_schema_key_count": 5,
        "pilot_contract_status": "PROVEN_ON_PINNED_MANUAL_LIMEIRA_RUN",
        "ongoing_resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_CLIENT_FOUNDATION_DESIGN_0_8_0",
    }
    for key, expected in exact_config.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(
        config.get("pinned_evidence_path"),
        "docs/evidence/M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_RUN_2_0.8.0.json",
        "CONFIG_EVIDENCE_PATH",
    )
    _require(
        config.get("pinned_evidence_blob_sha"),
        "2fca23a8c2e6e69dddeb755b304dd25d9d451e26",
        "CONFIG_EVIDENCE_BLOB_SHA",
    )
    _require(
        config.get("proven_query_features"),
        ["parameter_aliases", "server_side_filter", "server_side_select", "format_json", "percent20_filter_encoding"],
        "CONFIG_PROVEN_QUERY_FEATURES",
    )
    _require(
        config.get("proven_identity_fields"),
        ["COD_MUNI", "NOM_MUNI", "NUM_ANO", "NUM_PERI", "SIG_UF"],
        "CONFIG_PROVEN_IDENTITY_FIELDS",
    )
    _require(_git_blob_sha(evidence_path), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB_SHA")

    exact_evidence = {
        "evidence_type": "M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_RUN_2_0_8_0",
        "run_id": config["pinned_run_id"],
        "run_number": config["pinned_run_number"],
        "job_id": config["pinned_job_id"],
        "head_sha": config["pinned_head_sha"],
        "artifact_id": config["pinned_artifact_id"],
        "artifact_name": "siope-official-olinda-limeira-pilot-readonly-get-33011469147",
        "artifact_digest": config["pinned_artifact_digest"],
    }
    for key, expected in exact_evidence.items():
        _require(evidence.get(key), expected, f"EVIDENCE_{key.upper()}")
    _require(evidence.get("qa"), {"historical_regressions": 109, "unit_tests": 843}, "EVIDENCE_QA")

    result = evidence.get("result")
    if not isinstance(result, dict):
        raise SiopeOfficialOlindaLimeiraPilotReadonlyGetReviewError(f"{ERROR}_RESULT_OBJECT_REQUIRED")

    required_result = {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET",
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_0_8_0",
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "mode": "EXACT_ONE_REQUEST_LIMEIRA_READONLY_ODATA_FILTERED_SELECTED_GET",
        "network_called": True,
        "network_method": "GET_ONLY",
        "request_count": 1,
        "pilot_limeira_values_sent": True,
        "response_status": 200,
        "content_type": "application/json",
        "response_byte_count": config["pinned_response_byte_count"],
        "response_sha256": config["pinned_response_sha256"],
        "top_level_json_object": True,
        "value_list_present": True,
        "value_count": config["pinned_value_count"],
        "selected_schema_exact": True,
        "selected_schema_key_count": config["pinned_schema_key_count"],
        "all_records_match_municipality_code": True,
        "all_records_match_municipality_name": True,
        "all_records_match_year": True,
        "all_records_match_period": True,
        "all_records_match_state": True,
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
        "manual_single_limeira_pilot_authorization_consumed": True,
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_LIMEIRA_PILOT_READONLY_GET_REVIEW_0_8_0",
    }
    for key, expected in required_result.items():
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
        "resource_contract_status": "PROVEN_DADOS_GERAIS_SIOPE",
        "parameter_alias_contract_status": "PROVEN_ANO_PERIODO_UF",
        "server_side_filter_status": "PROVEN_COD_MUNI",
        "server_side_select_status": "PROVEN_FIVE_IDENTITY_FIELDS",
        "filter_encoding_status": "PROVEN_PERCENT20",
        "municipal_identity_status": "PROVEN_LIMEIRA_352690_SP_2024_6",
        "response_contract_status": "HTTP_200_JSON_ODATA_VALUE_ONE_RECORD",
        "ongoing_resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
