from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW"
PASS = "PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW"


class Historical2022P6ValidationReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Historical2022P6ValidationReviewError(f"{ERROR}_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise Historical2022P6ValidationReviewError(f"{ERROR}_{code}")


def _git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()  # noqa: S324 - Git object identity, not security.


def review(config: dict, *, root: str | Path) -> dict:
    expected_config = {'bronze_single_record_capture_design_authorized': True,
 'collection_authorized': False,
 'gate_id': 'M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW_0_8_0',
 'historical_collection_authorized': False,
 'mode': 'OFFLINE_PINNED_HISTORICAL_2022_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW',
 'network_called': False,
 'next_gate': 'M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_BRONZE_SINGLE_RECORD_CAPTURE_0_8_0',
 'pinned_artifact_digest': 'sha256:757aa3c949b9446bb82aee9b3aba18316b1bc0a68d54dd85fecf2662f27f98a4',
 'pinned_artifact_id': 9644450135,
 'pinned_artifact_result_sha256': '928a9b1069b03cec9cd22139a5aaecba54eab8053dad195514342b0a54793e94',
 'pinned_evidence_blob_sha': 'd41429ef185bda469b665b060ce4af3f77b93cd8',
 'pinned_evidence_path': 'docs/evidence/M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_FULL_SCHEMA_READONLY_VALIDATION_RUN_1_0.8.0.json',
 'pinned_head_sha': 'fa12e781df35e521a544ea66a4d1b2a792e0a2a0',
 'pinned_historical_regressions': 109,
 'pinned_job_id': 98502060174,
 'pinned_response_byte_count': 2075,
 'pinned_response_sha256': '66a716a4097730d5a77795a49aaf6b7fec86ec3324cf97fdd0bb9593b5f4b9d2',
 'pinned_run_id': 33067774766,
 'pinned_schema_key_count': 52,
 'pinned_unit_tests': 1045,
 'processing_authorized': False,
 'recurrence_authorized': False,
 'schedule_enabled': False,
 'software_version': '0.8.0',
 'source_id': 'FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA'}
    _require(config, expected_config, "CONFIG_DRIFT")

    evidence_path = Path(root) / config["pinned_evidence_path"]
    raw = evidence_path.read_bytes()
    _require(_git_blob_sha(raw), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB_DRIFT")
    evidence = json.loads(raw.decode("utf-8"))
    expected_evidence = {'all_records_match_municipality_code': True,
 'all_records_match_municipality_name': True,
 'all_records_match_period': True,
 'all_records_match_state': True,
 'all_records_match_year': True,
 'artifact_digest': 'sha256:757aa3c949b9446bb82aee9b3aba18316b1bc0a68d54dd85fecf2662f27f98a4',
 'artifact_id': 9644450135,
 'artifact_name': 'siope-client-limeira-historical-2022-p6-full-schema-readonly-validation-33067774766',
 'artifact_result_sha256': '928a9b1069b03cec9cd22139a5aaecba54eab8053dad195514342b0a54793e94',
 'artifact_size_bytes': 817,
 'collection_authorized': False,
 'content_type': 'application/json',
 'gate_id': 'M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_FULL_SCHEMA_READONLY_VALIDATION_0_8_0',
 'generic_client_used': True,
 'head_sha': 'fa12e781df35e521a544ea66a4d1b2a792e0a2a0',
 'historical_collection_authorized': False,
 'historical_failures': 0,
 'historical_passes': 109,
 'historical_tests': 109,
 'job_id': 98502060174,
 'manual_single_historical_period_validation_authorization_consumed': True,
 'mode': 'ONE_REQUEST_GENERIC_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_FULL_52_FIELD_SCHEMA_VALIDATION',
 'network_called': True,
 'network_method': 'GET_ONLY',
 'next_gate': 'M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_FULL_SCHEMA_READONLY_VALIDATION_REVIEW_0_8_0',
 'nextlink_url_persisted': False,
 'odata_context_present': True,
 'odata_nextlink_followed': False,
 'odata_nextlink_present': False,
 'persistence_authorized': False,
 'processing_authorized': False,
 'proven_schema_allowlist_count': 52,
 'query_values_persisted_in_result': False,
 'record_values_persisted': False,
 'recurrence_authorized': False,
 'redirect_followed': False,
 'request_count': 1,
 'resource': 'Dados_Gerais_Siope',
 'response_body_persisted': False,
 'response_byte_count': 2075,
 'response_sha256': '66a716a4097730d5a77795a49aaf6b7fec86ec3324cf97fdd0bb9593b5f4b9d2',
 'response_status': 200,
 'retry_performed': False,
 'run_id': 33067774766,
 'run_number': 1,
 'schedule_enabled': False,
 'selected_schema_exact': True,
 'selected_schema_key_count': 52,
 'software_version': '0.8.0',
 'source_id': 'FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA',
 'status': 'PASS_M7_SIOPE_CLIENT_LIMEIRA_HISTORICAL_2022_P6_FULL_SCHEMA_READONLY_VALIDATION',
 'unit_failures': 0,
 'unit_passes': 1045,
 'unit_tests': 1045,
 'value_count': 1,
 'workflow_event': 'workflow_dispatch',
 'workflow_head_branch': 'main'}
    _require(evidence, expected_evidence, "EVIDENCE_DRIFT")

    return {
        "status": PASS,
        "gate_id": config["gate_id"],
        "network_called": False,
        "pinned_year": 2022,
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
