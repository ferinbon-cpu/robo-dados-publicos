from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS_REVIEW"


class SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationDomSignatureDiagnosticsReviewError(f"{ERROR}_{code}")


def run_review(config: dict, evidence: dict) -> dict:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS_REVIEW_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "OFFLINE_PINNED_BOOLEAN_DOM_SIGNATURE_DIAGNOSTICS_REVIEW",
        "network_called": False,
        "dom_interaction_authorized": False,
        "dom_text_return": "PROHIBITED",
        "dom_attribute_value_return": "PROHIBITED",
        "fragment_value_capture": "PROHIBITED",
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
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_STRUCTURAL_BINDING_DIAGNOSTICS_DESIGN_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(evidence.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS_0_8_0", "EVIDENCE_GATE")
    _require(evidence.get("run_id"), config["pinned_run_id"], "RUN_ID")
    _require(evidence.get("job_id"), config["pinned_job_id"], "JOB_ID")
    _require(evidence.get("event"), "workflow_dispatch", "EVENT")
    _require(evidence.get("branch"), "main", "BRANCH")
    _require(evidence.get("workflow_conclusion"), "success", "WORKFLOW_CONCLUSION")
    _require((evidence.get("artifact") or {}).get("id"), config["pinned_artifact_id"], "ARTIFACT_ID")
    _require((evidence.get("artifact") or {}).get("digest"), config["pinned_artifact_digest"], "ARTIFACT_DIGEST")
    _require(evidence.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS", "STATUS")
    _require(evidence.get("application_surface_verified"), True, "SURFACE")
    _require(evidence.get("boolean_signature"), config["expected_boolean_signature"], "BOOLEAN_SIGNATURE")
    _require(evidence.get("matched_signature_count"), config["expected_matched_signature_count"], "MATCHED_COUNT")
    _require(evidence.get("candidate_shape_count"), config["expected_candidate_shape_count"], "CANDIDATE_COUNT")
    _require(evidence.get("candidate_shapes"), [], "CANDIDATE_SHAPES")
    _require(evidence.get("blocked_shape_count"), config["expected_blocked_shape_count"], "BLOCKED_COUNT")

    blocked = evidence.get("blocked_shapes") or []
    _require(len(blocked), 1, "BLOCKED_LIST")
    _require(blocked[0].get("route_without_query"), config["expected_blocked_route_without_query"], "BLOCKED_ROUTE")
    _require(blocked[0].get("network_sent"), False, "BLOCKED_SENT")
    _require(blocked[0].get("intercepted_before_network"), True, "BLOCKED_INTERCEPT")
    _require(blocked[0].get("candidate_dynamic_request"), False, "BLOCKED_CANDIDATE")

    qa = evidence.get("qa") or {}
    _require(qa.get("unit_tests"), 645, "UNIT_TESTS")
    _require(qa.get("unit_failures"), 0, "UNIT_FAILURES")
    _require(qa.get("historical_regressions"), 109, "REGRESSIONS")
    _require(qa.get("historical_regression_failures"), 0, "REGRESSION_FAILURES")

    safety = evidence.get("safety") or {}
    _require(safety.get("initial_document_network_sent"), True, "INITIAL_DOCUMENT_SENT")
    _require(safety.get("browser_download_denied"), True, "DOWNLOAD_DENIED")
    false_keys = [
        "dynamic_candidate_network_sent", "pilot_limeira_values_sent", "resource_data_request_performed",
        "resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized",
        "schedule_enabled", "dom_interaction_performed", "form_submission", "post_request_performed",
        "head_request_performed", "authentication_performed", "captcha_bypass", "credentials_captured",
        "cookies_captured", "artifact_downloaded", "dom_text_returned", "dom_attribute_values_returned",
        "fragment_value_returned", "html_returned", "script_source_returned", "response_body_persisted",
        "request_body_persisted", "query_values_persisted", "route_synthesized_or_guessed",
        "automatic_route_promotion",
    ]
    for key in false_keys:
        _require(safety.get(key), False, f"SAFETY_{key.upper()}")
    _require(safety.get("remote_writes"), "NONE", "REMOTE_WRITES")

    interpretation = evidence.get("interpretation") or {}
    _require(interpretation.get("name_identity_relation"), "UNPROVEN_DIFFERENT_OFFICIAL_SURFACES_OBSERVE_DIFFERENT_NAMES", "NAME_RELATION")
    _require(interpretation.get("dynamic_route_contract"), "UNPROVEN_ZERO_CANDIDATES", "DYNAMIC_ROUTE")
    _require(interpretation.get("resource_request_authorized"), False, "INTERPRETATION_RESOURCE_AUTH")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SIGNATURE_DIAGNOSTICS_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "evidence_run_id": config["pinned_run_id"],
        "evidence_artifact_id": config["pinned_artifact_id"],
        "technical_callable_pattern_status": "PROVEN_PRESENT_ON_OFFICIAL_APPLICATION_PINNED_RUN",
        "technical_parameter_presence_status": "PROVEN_ALL_THREE_PRESENT_ON_OFFICIAL_APPLICATION_PINNED_RUN",
        "service_document_name_application_status": "NOT_OBSERVED_ON_PINNED_APPLICATION_RUN",
        "cross_surface_name_relation_status": "UNPROVEN_DIFFERENT_OFFICIAL_SURFACES",
        "official_application_corroboration_status": "CALLABLE_NAME_AND_PARAMETER_NAMES_CORROBORATED_AT_BOOLEAN_PRESENCE_LEVEL",
        "structural_binding_status": "UNPROVEN",
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
