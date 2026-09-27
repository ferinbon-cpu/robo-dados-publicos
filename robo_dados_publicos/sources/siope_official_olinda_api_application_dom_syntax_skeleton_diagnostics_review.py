from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS_REVIEW"


class SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def git_blob_sha(path: str | Path) -> str:
    data = Path(path).read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsReviewError(f"{ERROR}_{code}")


def run_review(config: dict, evidence: dict, *, evidence_path: str | Path | None = None) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS_REVIEW_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_PINNED_RENDERED_DOM_SYNTAX_SKELETON_DIAGNOSTICS_REVIEW", "MODE")
    _require(config.get("network_called"), False, "NETWORK")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")
    for key in (
        "raw_navigation_value_return", "navigation_fragment_return", "dom_text_return", "dom_attribute_value_return",
        "element_text_return", "element_attribute_return", "tag_name_return", "html_capture", "script_source_capture",
        "response_body_capture", "request_body_capture", "query_value_persistence", "dom_interaction",
        "navigation_execution", "form_submission", "dynamic_candidate_network_send", "resource_data_request",
        "pilot_limeira_values_send", "post_request_send", "head_request", "authentication", "captcha_bypass",
        "credential_capture", "cookie_capture", "artifact_download", "remote_writes", "route_synthesis_or_guessing",
        "automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")

    if evidence_path is not None:
        _require(git_blob_sha(evidence_path), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB_SHA")
    _require(evidence.get("run_id"), config["pinned_run_id"], "RUN")
    _require(evidence.get("job_id"), config["pinned_job_id"], "JOB")
    _require(evidence.get("head_sha"), config["pinned_head_sha"], "SHA")
    _require(evidence.get("event"), "workflow_dispatch", "EVENT")
    _require(evidence.get("head_branch"), "main", "BRANCH")
    _require(evidence.get("workflow_conclusion"), "success", "CONCLUSION")
    _require((evidence.get("artifact") or {}).get("id"), config["pinned_artifact_id"], "ARTIFACT")
    _require((evidence.get("artifact") or {}).get("digest"), config["pinned_artifact_digest"], "DIGEST")
    _require(evidence.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS", "STATUS")
    _require(evidence.get("application_surface_verified"), True, "SURFACE")
    _require(evidence.get("candidate_shape_count"), 0, "CANDIDATES")
    _require(evidence.get("blocked_shape_count"), 1, "BLOCKED")
    _require(evidence.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT")
    qa = evidence.get("qa") or {}
    _require(qa.get("unit_tests"), config["expected_unit_tests"], "QA_UNIT")
    _require(qa.get("unit_test_failures"), 0, "QA_UNIT_FAILURES")
    _require(qa.get("historical_regressions"), config["expected_historical_regressions"], "QA_HISTORICAL")
    _require(qa.get("historical_regression_failures"), 0, "QA_HISTORICAL_FAILURES")

    expected_counts = {
        "minimal_contract_container_count": 1,
        "callable_occurrence_in_minimal_container_count": 2,
        "callable_open_paren_in_minimal_container_count": 0,
        "callable_ordered_parameter_names_512_in_minimal_container_count": 1,
        "callable_close_paren_after_ordered_parameters_512_in_minimal_container_count": 0,
        "callable_ano_at_binding_4096_in_minimal_container_count": 0,
        "callable_num_at_binding_4096_in_minimal_container_count": 0,
        "callable_sig_at_binding_4096_in_minimal_container_count": 0,
        "callable_all_three_at_bindings_4096_in_minimal_container_count": 0,
        "callable_ordered_all_three_at_bindings_4096_in_minimal_container_count": 0,
        "callable_query_alias_ano_4096_in_minimal_container_count": 0,
        "callable_query_alias_num_4096_in_minimal_container_count": 0,
        "callable_query_alias_sig_4096_in_minimal_container_count": 0,
        "callable_all_three_query_aliases_4096_in_minimal_container_count": 0,
        "callable_format_assignment_4096_in_minimal_container_count": 0,
        "callable_full_known_signature_skeleton_4096_in_minimal_container_count": 0,
    }
    _require(evidence.get("dom_syntax_skeleton_counts"), expected_counts, "EXACT_COUNTS")

    safety = evidence.get("safety") or {}
    _require(safety.get("initial_document_network_sent"), True, "INITIAL_DOCUMENT_SENT")
    _require(safety.get("browser_download_denied"), True, "DOWNLOAD_DENIED")
    _require(safety.get("dom_text_transient_analysis_performed"), True, "TRANSIENT_DOM")
    for key in (
        "dynamic_candidate_network_sent", "pilot_limeira_values_sent", "resource_data_request_performed",
        "resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized",
        "schedule_enabled", "dom_interaction_performed", "navigation_executed", "form_submission",
        "post_request_performed", "head_request_performed", "authentication_performed", "captcha_bypass",
        "credentials_captured", "cookies_captured", "artifact_downloaded", "dom_text_returned",
        "dom_attribute_values_returned", "element_text_returned", "element_attribute_returned", "tag_name_returned",
        "fragment_value_returned", "html_returned", "script_source_returned", "response_body_persisted",
        "request_body_persisted", "query_values_persisted", "route_synthesized_or_guessed", "automatic_route_promotion",
    ):
        _require(safety.get(key), False, f"SAFETY_{key.upper()}")
    _require(safety.get("remote_writes"), "NONE", "REMOTE_WRITES")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "evidence_run_id": config["pinned_run_id"],
        "evidence_artifact_id": config["pinned_artifact_id"],
        "minimal_contract_container_status": "ONE_RENDERED_DOM_MINIMAL_CONTAINER_ON_PINNED_RUN",
        "technical_callable_presence_status": "TWO_EXACT_CALLABLE_OCCURRENCES_IN_MINIMAL_CONTAINER_ON_PINNED_RUN",
        "ordered_parameter_locality_status": "ONE_OF_TWO_ORDERED_WITHIN_512_CHARS_ON_PINNED_RUN",
        "callable_open_parenthesis_status": "NOT_OBSERVED_ON_PINNED_RENDERED_DOM",
        "known_at_binding_status": "NOT_OBSERVED_ON_PINNED_RENDERED_DOM",
        "known_query_alias_status": "NOT_OBSERVED_ON_PINNED_RENDERED_DOM",
        "known_format_assignment_status": "NOT_OBSERVED_ON_PINNED_RENDERED_DOM",
        "full_known_signature_skeleton_status": "NOT_OBSERVED_ON_PINNED_RENDERED_DOM",
        "rendered_dom_known_syntax_strategy_status": "EXHAUSTED_FOR_THIS_KNOWN_TEXTUAL_SKELETON_ON_PINNED_RUN",
        "callable_semantics_status": "UNPROVEN",
        "resource_route_contract_status": "UNPROVEN",
        "cross_surface_name_identity_status": "UNPROVEN",
        "network_called": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
