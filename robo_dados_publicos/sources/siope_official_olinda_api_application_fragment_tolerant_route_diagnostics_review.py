from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TOLERANT_ROUTE_DIAGNOSTICS_REVIEW"


class SiopeOfficialOlindaApiApplicationFragmentTolerantRouteDiagnosticsReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationFragmentTolerantRouteDiagnosticsReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationFragmentTolerantRouteDiagnosticsReviewError(f"{ERROR}_{code}")


def run_review(config: dict, evidence: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TOLERANT_ROUTE_DIAGNOSTICS_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_PINNED_FRAGMENT_TOLERANT_ROUTE_DIAGNOSTICS_REVIEW",
        "network_called": False,
        "dom_interaction_authorized": False,
        "body_text_capture": "PROHIBITED",
        "html_capture": "PROHIBITED",
        "script_source_capture": "PROHIBITED",
        "response_body_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "query_value_persistence": "PROHIBITED",
        "dynamic_candidate_network_send": "PROHIBITED",
        "resource_data_request": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "post_request_send": "PROHIBITED",
        "head_request": "PROHIBITED",
        "authentication": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "credential_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "remote_writes": "PROHIBITED",
        "route_synthesis_or_guessing": "PROHIBITED",
        "automatic_route_promotion": "PROHIBITED",
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS_DESIGN_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(evidence.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TOLERANT_ROUTE_DIAGNOSTICS_0_8_0", "EVIDENCE_GATE")
    _require(evidence.get("run_id"), config["pinned_run_id"], "RUN_ID")
    _require(evidence.get("job_id"), config["pinned_job_id"], "JOB_ID")
    _require((evidence.get("artifact") or {}).get("id"), config["pinned_artifact_id"], "ARTIFACT_ID")
    _require((evidence.get("artifact") or {}).get("digest"), config["pinned_artifact_digest"], "ARTIFACT_DIGEST")
    _require(evidence.get("workflow_conclusion"), "success", "WORKFLOW_CONCLUSION")
    _require(evidence.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TOLERANT_ROUTE_DIAGNOSTICS", "STATUS")
    _require(evidence.get("application_surface_verified"), True, "SURFACE")
    _require(evidence.get("surface_identity_uses_fragment"), False, "FRAGMENT_IDENTITY")
    _require(evidence.get("fragment_value_returned"), False, "FRAGMENT_VALUE")
    _require(evidence.get("candidate_shape_count"), config["expected_candidate_shape_count"], "CANDIDATE_COUNT")
    _require(evidence.get("candidate_shapes"), [], "CANDIDATE_SHAPES")
    _require(evidence.get("blocked_shape_count"), config["expected_blocked_shape_count"], "BLOCKED_COUNT")
    blocked = evidence.get("blocked_shapes") or []
    _require(len(blocked), 1, "BLOCKED_LIST")
    _require(blocked[0].get("route_without_query"), config["expected_blocked_route_without_query"], "BLOCKED_ROUTE")
    _require(blocked[0].get("network_sent"), False, "BLOCKED_SENT")
    _require(blocked[0].get("intercepted_before_network"), True, "BLOCKED_INTERCEPT")

    safety = evidence.get("safety") or {}
    false_keys = [
        "dynamic_candidate_network_sent", "pilot_limeira_values_sent", "resource_data_request_performed",
        "resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized",
        "schedule_enabled", "dom_interaction_performed", "form_submission", "post_request_performed",
        "head_request_performed", "authentication_performed", "captcha_bypass", "credentials_captured",
        "cookies_captured", "artifact_downloaded", "body_text_returned", "html_returned",
        "script_source_returned", "response_body_persisted", "request_body_persisted",
        "query_values_persisted", "route_synthesized_or_guessed", "automatic_route_promotion",
    ]
    for key in false_keys:
        _require(safety.get(key), False, f"SAFETY_{key.upper()}")
    _require(safety.get("remote_writes"), "NONE", "REMOTE_WRITES")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TOLERANT_ROUTE_DIAGNOSTICS_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "evidence_run_id": config["pinned_run_id"],
        "evidence_artifact_id": config["pinned_artifact_id"],
        "application_surface_status": "PROVEN_FRAGMENT_TOLERANT_ON_PINNED_RUN",
        "passive_network_route_status": "EXHAUSTED_ZERO_DYNAMIC_CANDIDATES_ON_PINNED_RUN",
        "fragment_semantics_status": "UNPROVEN_VALUE_NOT_CAPTURED",
        "dynamic_route_contract_status": "UNPROVEN_ZERO_CANDIDATES",
        "network_called": False,
        "pilot_limeira_values_sent": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
