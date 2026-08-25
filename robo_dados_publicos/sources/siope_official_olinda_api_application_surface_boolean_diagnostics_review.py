from __future__ import annotations

import json
from pathlib import Path


ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS_REVIEW"


class SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsReviewError(f"{ERROR}_{code}")


def review_surface_boolean_diagnostics(config: dict, evidence: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS_REVIEW_0_8_0", "GATE")
    _require(config.get("evidence_git_blob_sha"), "58a33d7ba5ae1881863f53ad304ad05b5bf4efad", "EVIDENCE_BLOB")
    _require(evidence.get("gate_id"), config["expected_prior_gate_id"], "EVIDENCE_GATE")
    _require(evidence.get("run_id"), config["expected_run_id"], "RUN_ID")
    _require(evidence.get("run_number"), config["expected_run_number"], "RUN_NUMBER")
    _require(evidence.get("head_sha"), config["expected_head_sha"], "HEAD_SHA")
    _require(evidence.get("job_id"), config["expected_job_id"], "JOB_ID")
    _require(evidence.get("workflow_conclusion"), "success", "WORKFLOW")
    _require(evidence.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS", "STATUS")

    artifact = evidence.get("artifact") or {}
    _require(artifact.get("id"), config["expected_artifact_id"], "ARTIFACT_ID")
    _require(artifact.get("digest"), config["expected_artifact_digest"], "ARTIFACT_DIGEST")
    qa = evidence.get("qa") or {}
    _require(qa.get("unit_tests"), config["expected_unit_tests"], "UNIT_TESTS")
    _require(qa.get("unit_failures"), 0, "UNIT_FAILURES")
    _require(qa.get("historical_regressions"), config["expected_historical_regressions"], "REGRESSIONS")
    _require(qa.get("historical_regression_failures"), 0, "REGRESSION_FAILURES")

    first = evidence.get("first_observation") or {}
    final = evidence.get("final_observation") or {}
    expected_first = {
        "fragment_empty": True, "host_matches": True, "href_exact": True,
        "path_matches": True, "query_empty": True, "ready_complete": False,
        "ready_eligible": False, "ready_interactive": False, "scheme_matches": True,
    }
    expected_final = {
        "fragment_empty": False, "host_matches": True, "href_exact": False,
        "path_matches": True, "query_empty": True, "ready_complete": True,
        "ready_eligible": True, "ready_interactive": False, "scheme_matches": True,
    }
    _require(first, expected_first, "FIRST_OBSERVATION")
    _require(final, expected_final, "FINAL_OBSERVATION")
    _require(evidence.get("boolean_relation_state_changed"), True, "STATE_CHANGED")
    _require(evidence.get("candidate_shape_count"), 0, "CANDIDATE_COUNT")
    _require(evidence.get("candidate_shapes"), [], "CANDIDATES")

    safety = evidence.get("safety") or {}
    for key in (
        "dynamic_candidate_network_sent", "pilot_limeira_values_sent", "resource_data_request_performed",
        "resource_get_authorized", "surface_authorized", "dom_interaction_performed", "form_submission",
        "post_request_performed", "head_request_performed", "authentication_performed", "captcha_bypass",
        "credentials_captured", "cookies_captured", "artifact_downloaded", "actual_location_returned",
        "ready_state_string_returned", "body_text_returned", "html_returned", "script_source_returned",
        "request_body_persisted", "response_body_persisted", "query_values_persisted",
        "route_synthesized_or_guessed", "automatic_route_promotion", "collection_authorized",
        "processing_authorized", "recurrence_authorized", "schedule_enabled",
    ):
        _require(safety.get(key), False, f"SAFETY_{key.upper()}")
    _require(safety.get("remote_writes"), "NONE", "REMOTE_WRITES")

    interpretation = evidence.get("interpretation") or {}
    for key in (
        "first_observation_exact_location_before_ready",
        "final_observation_same_scheme_host_path_and_empty_query",
        "final_observation_ready_complete",
        "fragment_transition_empty_to_nonempty_observed",
        "prior_exact_href_and_ready_predicate_explained_by_observed_transition",
    ):
        _require(interpretation.get(key), True, f"INTERPRETATION_{key.upper()}")
    _require(interpretation.get("fragment_value_observed_or_persisted"), False, "FRAGMENT_VALUE")
    _require(interpretation.get("fragment_semantics_proven"), False, "FRAGMENT_SEMANTICS")
    _require(interpretation.get("dynamic_route_contract_proven"), False, "DYNAMIC_PROVEN")
    _require(interpretation.get("resource_request_authorized"), False, "RESOURCE_AUTH")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "network_called": False,
        "evidence_run_id": config["expected_run_id"],
        "evidence_artifact_id": config["expected_artifact_id"],
        "origin_path_query_status": config["origin_path_query_disposition"],
        "readiness_status": config["readiness_disposition"],
        "fragment_status": config["fragment_disposition"],
        "fragment_semantics_status": config["fragment_semantics_disposition"],
        "prior_failure_status": config["prior_failure_disposition"],
        "revised_surface_predicate": config["revised_surface_predicate"],
        "dynamic_route_status": config["dynamic_route_status"],
        "network_safety_status": config["network_safety_status"],
        "fragment_value_captured": False,
        "fragment_used_for_route_identity": False,
        "resource_get_authorized": False,
        "surface_authorized": False,
        "pilot_limeira_values_sent": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
