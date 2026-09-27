from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_REVIEW"


class SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsReviewError(f"{ERROR}_{code}")


def validate_config(config: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_PINNED_OLINDA_APPLICATION_ROUTE_STOP_REVIEW",
        "evidence_path": "docs/evidence/M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_RUN_1_0.8.0.json",
        "evidence_git_blob_sha": "2a130bf5ca1539b70c86efbb87cd2131231c4a65",
        "expected_prior_gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0",
        "expected_prior_status": "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS",
        "expected_error_code": "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_APPLICATION_SURFACE_NOT_VERIFIED",
        "expected_run_id": 32900849533,
        "expected_run_number": 1,
        "expected_head_sha": "d7deace8644b23dcb6e7aa31bc67d40c3ca1b172",
        "expected_job_id": 97974113961,
        "expected_artifact_id": 9583003909,
        "expected_artifact_digest": "sha256:5d1ee51f69cc324a5062b790bc79eb845189f4d775ba6befb0071f798641453d",
        "expected_unit_tests": 594,
        "expected_historical_regressions": 109,
        "surface_disposition": "UNVERIFIED_ON_PINNED_RUN",
        "dynamic_route_disposition": "UNPROVEN_ZERO_CANDIDATES",
        "blocked_shape_disposition": "ONE_OFFICIAL_FAVICON_ABORTED_BEFORE_NETWORK",
        "failure_classification": "INSUFFICIENT_BOOLEAN_TELEMETRY_TO_DISTINGUISH_LOCATION_FROM_READY_STATE",
        "network_safety_disposition": "PASS_NO_DYNAMIC_CANDIDATE_SENT",
        "network_access": "PROHIBITED",
        "resource_get": "PROHIBITED",
        "query_parameters": "PROHIBITED",
        "post_request": "PROHIBITED",
        "head_request": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "authentication": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "credential_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "response_body_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "query_value_persistence": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "remote_writes": "PROHIBITED",
        "route_synthesis_or_guessing": "PROHIBITED",
        "automatic_route_promotion": "PROHIBITED",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")


def review(config: dict, evidence: dict) -> dict:
    validate_config(config)
    _require(evidence.get("gate_id"), config["expected_prior_gate_id"], "EVIDENCE_GATE")
    _require(evidence.get("status"), config["expected_prior_status"], "EVIDENCE_STATUS")
    _require(evidence.get("error_code"), config["expected_error_code"], "EVIDENCE_ERROR")
    _require(evidence.get("run_id"), config["expected_run_id"], "RUN_ID")
    _require(evidence.get("run_number"), config["expected_run_number"], "RUN_NUMBER")
    _require(evidence.get("event"), "workflow_dispatch", "RUN_EVENT")
    _require(evidence.get("branch"), "main", "RUN_BRANCH")
    _require(evidence.get("head_sha"), config["expected_head_sha"], "HEAD_SHA")
    _require(evidence.get("job_id"), config["expected_job_id"], "JOB_ID")
    _require(evidence.get("workflow_conclusion"), "failure", "WORKFLOW_CONCLUSION")
    qa = evidence.get("qa") or {}
    _require(qa.get("unit_tests"), config["expected_unit_tests"], "UNIT_TESTS")
    _require(qa.get("unit_failures"), 0, "UNIT_FAILURES")
    _require(qa.get("historical_regressions"), config["expected_historical_regressions"], "REGRESSIONS")
    _require(qa.get("historical_regression_failures"), 0, "REGRESSION_FAILURES")
    artifact = evidence.get("artifact") or {}
    _require(artifact.get("id"), config["expected_artifact_id"], "ARTIFACT_ID")
    _require(artifact.get("digest"), config["expected_artifact_digest"], "ARTIFACT_DIGEST")
    _require(evidence.get("candidate_shapes"), [], "CANDIDATES")
    shapes = evidence.get("blocked_shapes") or []
    _require(len(shapes), 1, "BLOCKED_COUNT")
    favicon = shapes[0]
    _require(favicon.get("route_without_query"), "https://www.fnde.gov.br/favicon.ico", "BLOCKED_ROUTE")
    _require(favicon.get("candidate_dynamic_request"), False, "BLOCKED_CANDIDATE")
    _require(favicon.get("network_sent"), False, "BLOCKED_SENT")
    _require(favicon.get("intercepted_before_network"), True, "BLOCKED_INTERCEPT")
    safety = evidence.get("safety") or {}
    for key in (
        "dynamic_candidate_network_sent", "pilot_limeira_values_sent", "resource_data_request_performed",
        "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled",
        "authentication_performed", "captcha_bypass", "artifact_downloaded", "query_values_persisted",
        "request_body_persisted", "response_body_persisted",
    ):
        _require(safety.get(key), False, f"SAFETY_{key.upper()}")
    _require(safety.get("remote_writes"), "NONE", "REMOTE_WRITES")
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "network_called": False,
        "evidence_run_id": config["expected_run_id"],
        "evidence_artifact_id": config["expected_artifact_id"],
        "application_surface_status": config["surface_disposition"],
        "dynamic_route_status": config["dynamic_route_disposition"],
        "blocked_shape_status": config["blocked_shape_disposition"],
        "failure_classification": config["failure_classification"],
        "network_safety_status": config["network_safety_disposition"],
        "pilot_limeira_values_sent": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
