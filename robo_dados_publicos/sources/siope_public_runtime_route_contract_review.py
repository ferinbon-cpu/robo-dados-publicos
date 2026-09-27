from __future__ import annotations

import json
from pathlib import Path


ERROR = "STOP_M7_SIOPE_PUBLIC_RUNTIME_ROUTE_CONTRACT_REVIEW"


class SiopePublicRuntimeRouteContractReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopePublicRuntimeRouteContractReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopePublicRuntimeRouteContractReviewError(f"{ERROR}_{code}")


def validate_review_config(config: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_RUNTIME_ROUTE_CONTRACT_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_PINNED_RUNTIME_EVIDENCE_REVIEW",
        "evidence_path": "docs/evidence/M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_ATTEMPT_5_0.8.0.json",
        "evidence_git_blob_sha": "2124abf679e3b8bb38f7b7543de7632beb6ba9f0",
        "expected_prior_gate_id": "M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0",
        "expected_prior_status": "PASS_M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS",
        "expected_run_id": 32874848478,
        "expected_run_number": 5,
        "expected_head_sha": "1fbddb4dacad6f66c831c20b72e54b0388ef803c",
        "expected_artifact_id": 9573491988,
        "expected_artifact_digest": "sha256:dde2847d12aeb3a2def4869f70c681792a4f86bfab81e846d67d043d1990bebe",
        "required_candidate_shape_count": 0,
        "public_get_contract_disposition": "PROVEN_FOR_PINNED_PUBLIC_INDEXED_EXAMPLE",
        "dynamic_route_contract_disposition": "UNPROVEN_ZERO_CANDIDATES",
        "automatic_route_promotion": "PROHIBITED",
        "route_synthesis_or_guessing": "PROHIBITED",
        "network_access": "PROHIBITED",
        "candidate_route_call": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "authentication": "PROHIBITED",
        "credential_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "response_body_capture": "PROHIBITED",
        "query_value_persistence": "PROHIBITED",
        "head_request": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "remote_writes": "PROHIBITED",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INTERACTION_DIAGNOSTICS_DESIGN_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")


def review_public_runtime_route_contract(config: dict, evidence: dict) -> dict:
    validate_review_config(config)

    _require(evidence.get("gate_id"), config["expected_prior_gate_id"], "EVIDENCE_GATE_ID")
    _require(evidence.get("software_version"), config["software_version"], "EVIDENCE_VERSION")
    _require(evidence.get("release_status"), config["release_status"], "EVIDENCE_RELEASE_STATUS")

    run = evidence.get("run") or {}
    _require(run.get("id"), config["expected_run_id"], "RUN_ID")
    _require(run.get("number"), config["expected_run_number"], "RUN_NUMBER")
    _require(run.get("event"), "workflow_dispatch", "RUN_EVENT")
    _require(run.get("status"), "completed", "RUN_STATUS")
    _require(run.get("conclusion"), "success", "RUN_CONCLUSION")
    _require(run.get("head_branch"), "main", "RUN_HEAD_BRANCH")
    _require(run.get("head_sha"), config["expected_head_sha"], "RUN_HEAD_SHA")

    artifact = evidence.get("artifact") or {}
    _require(artifact.get("id"), config["expected_artifact_id"], "ARTIFACT_ID")
    _require(artifact.get("digest"), config["expected_artifact_digest"], "ARTIFACT_DIGEST")

    result = evidence.get("result") or {}
    _require(result.get("status"), config["expected_prior_status"], "PRIOR_STATUS")
    _require(result.get("page_surface_verified"), True, "PUBLIC_SURFACE")
    _require(result.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(result.get("initial_document_network_sent"), True, "INITIAL_DOCUMENT_SENT")
    _require(result.get("candidate_shape_count"), config["required_candidate_shape_count"], "CANDIDATE_COUNT")
    _require(result.get("candidate_shapes"), [], "CANDIDATE_SHAPES")
    _require(result.get("dynamic_candidate_network_sent"), False, "DYNAMIC_NETWORK_SENT")
    _require(result.get("pilot_limeira_values_sent"), False, "PILOT_VALUES_SENT")
    _require(result.get("form_submission"), False, "FORM_SUBMISSION")
    _require(result.get("captcha_bypass"), False, "CAPTCHA_BYPASS")
    _require(result.get("authentication_performed"), False, "AUTHENTICATION")
    _require(result.get("credentials_captured"), False, "CREDENTIAL_CAPTURE")
    _require(result.get("cookies_captured"), False, "COOKIE_CAPTURE")
    _require(result.get("request_body_persisted"), False, "REQUEST_BODY")
    _require(result.get("response_body_persisted"), False, "RESPONSE_BODY")
    _require(result.get("query_values_persisted"), False, "QUERY_VALUES")
    _require(result.get("head_request_performed"), False, "HEAD_REQUEST")
    _require(result.get("browser_download_denied"), True, "DOWNLOAD_DENIAL")
    _require(result.get("artifact_downloaded"), False, "ARTIFACT_DOWNLOAD")
    _require(result.get("remote_writes"), "NONE", "REMOTE_WRITES")
    _require(result.get("collection_authorized"), False, "COLLECTION_AUTH")
    _require(result.get("processing_authorized"), False, "PROCESSING_AUTH")
    _require(result.get("recurrence_authorized"), False, "RECURRENCE_AUTH")
    _require(result.get("schedule_enabled"), False, "SCHEDULE")
    _require(result.get("next_gate"), config["gate_id"], "PRIOR_NEXT_GATE")

    blocked_shapes = list(result.get("blocked_shapes") or [])
    if any(shape.get("network_sent") is not False for shape in blocked_shapes):
        raise SiopePublicRuntimeRouteContractReviewError(f"{ERROR}_BLOCKED_SHAPE_NETWORK_SENT")
    if any(shape.get("candidate_dynamic_data_request") is True for shape in blocked_shapes):
        raise SiopePublicRuntimeRouteContractReviewError(f"{ERROR}_BLOCKED_CANDIDATE_INCONSISTENCY")

    interpretation = evidence.get("interpretation") or {}
    _require(interpretation.get("public_indexed_get_contract_verified_at_runtime"), True, "INTERPRETATION_PUBLIC_GET")
    _require(interpretation.get("dynamic_data_route_proven"), False, "INTERPRETATION_DYNAMIC_ROUTE")
    _require(
        interpretation.get("reason_dynamic_route_unproven"),
        "ZERO_SAME_HOST_XHR_OR_FETCH_CANDIDATE_SHAPES_OBSERVED",
        "INTERPRETATION_ZERO_CANDIDATES",
    )
    _require(interpretation.get("automatic_route_promotion"), "PROHIBITED", "INTERPRETATION_PROMOTION")
    _require(interpretation.get("route_synthesis_or_guessing"), "PROHIBITED", "INTERPRETATION_GUESSING")

    return {
        "status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_ROUTE_CONTRACT_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "network_called": False,
        "evidence_run_id": config["expected_run_id"],
        "evidence_artifact_id": config["expected_artifact_id"],
        "public_get_contract_status": config["public_get_contract_disposition"],
        "dynamic_route_contract_status": config["dynamic_route_contract_disposition"],
        "candidate_shape_count": 0,
        "contract_promoted": False,
        "route_synthesized_or_guessed": False,
        "candidate_route_called": False,
        "pilot_limeira_values_sent": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
