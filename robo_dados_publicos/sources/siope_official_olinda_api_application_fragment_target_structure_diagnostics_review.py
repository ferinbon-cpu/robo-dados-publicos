from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS_REVIEW"

EXPECTED_COUNTS = {
    "fragment_navigation_match_count": 2,
    "distinct_fragment_value_count": 2,
    "fragment_route_like_count": 2,
    "fragment_anchor_like_count": 0,
    "fragment_target_resolved_count": 0,
    "fragment_target_contains_callable_name_count": 0,
    "fragment_target_contains_all_parameter_names_count": 0,
    "fragment_target_ordered_parameter_sequence_count": 0,
    "fragment_target_open_parenthesis_count": 0,
    "fragment_target_query_marker_count": 0,
    "fragment_target_format_token_count": 0,
    "fragment_target_contract_like_count": 0,
    "fragment_value_contains_all_parameter_names_count": 0,
    "fragment_value_parentheses_present_count": 0,
    "fragment_value_query_marker_present_count": 0,
    "fragment_value_format_token_present_count": 0,
}

EXPECTED_INTERPRETATION = {
    "fragment_navigation_status": "TWO_DISTINCT_FRAGMENT_NAVIGATION_VALUES_ON_PINNED_RUN",
    "fragment_shape_status": "BOTH_OBSERVED_FRAGMENTS_ROUTE_LIKE_NOT_ANCHOR_LIKE_ON_PINNED_RUN",
    "existing_dom_target_status": "NO_EXISTING_DOM_TARGET_RESOLVED_ON_PINNED_RUN",
    "known_contract_syntax_status": "NOT_OBSERVED_IN_FRAGMENT_VALUES_OR_EXISTING_TARGETS_ON_PINNED_RUN",
    "fragment_route_semantics_status": "UNPROVEN_RAW_FRAGMENT_VALUES_NOT_RETURNED_OR_EXECUTED",
    "resource_route_contract_status": "UNPROVEN",
    "callable_semantics_status": "UNPROVEN",
    "next_safe_surface": "PASSIVE_ALREADY_LOADED_SCRIPT_HASH_ROUTING_SIGNAL_COUNTS_WITHOUT_NAVIGATION",
}


class SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsReviewError(RuntimeError):
    pass


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsReviewError(f"{ERROR}_{code}")


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _git_blob_sha(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def run_review(config: dict, evidence: dict, *, evidence_path: str | Path | None = None) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS_REVIEW_0_8_0", "GATE")
    _require(config.get("mode"), "OFFLINE_PINNED_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS_REVIEW", "MODE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("network_called"), False, "NETWORK")
    if evidence_path is not None:
        _require(_git_blob_sha(evidence_path), config.get("pinned_evidence_blob_sha"), "EVIDENCE_BLOB")

    _require(evidence.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS_0_8_0", "EVIDENCE_GATE")
    _require(evidence.get("software_version"), "0.8.0", "EVIDENCE_VERSION")
    _require(evidence.get("run_id"), config.get("pinned_run_id"), "RUN")
    _require(evidence.get("job_id"), config.get("pinned_job_id"), "JOB")
    _require(evidence.get("head_sha"), config.get("pinned_head_sha"), "HEAD_SHA")
    _require(evidence.get("head_branch"), "main", "HEAD_BRANCH")
    _require(evidence.get("event"), "workflow_dispatch", "EVENT")
    _require(evidence.get("workflow_conclusion"), "success", "CONCLUSION")
    artifact = evidence.get("artifact") or {}
    _require(artifact.get("id"), config.get("pinned_artifact_id"), "ARTIFACT_ID")
    _require(artifact.get("digest"), config.get("pinned_artifact_digest"), "ARTIFACT_DIGEST")

    qa = evidence.get("qa") or {}
    _require(qa.get("unit_tests"), config.get("expected_unit_tests"), "UNIT_TESTS")
    _require(qa.get("unit_test_passes"), config.get("expected_unit_tests"), "UNIT_PASSES")
    _require(qa.get("unit_test_failures"), 0, "UNIT_FAILURES")
    _require(qa.get("historical_regressions"), config.get("expected_historical_regressions"), "REGRESSIONS")
    _require(qa.get("historical_regression_passes"), config.get("expected_historical_regressions"), "REGRESSION_PASSES")
    _require(qa.get("historical_regression_failures"), 0, "REGRESSION_FAILURES")

    _require(evidence.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS", "STATUS")
    _require(evidence.get("application_surface_verified"), True, "SURFACE")
    _require(evidence.get("fragment_present"), True, "FRAGMENT_PRESENT")
    _require(evidence.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT")
    _require(evidence.get("candidate_shape_count"), 0, "CANDIDATES")
    _require(evidence.get("candidate_shapes"), [], "CANDIDATE_SHAPES")
    _require(evidence.get("fragment_target_structure_counts"), EXPECTED_COUNTS, "COUNTS")
    _require(evidence.get("interpretation"), EXPECTED_INTERPRETATION, "INTERPRETATION")

    safety = evidence.get("safety") or {}
    required_false = (
        "dynamic_candidate_network_sent", "pilot_limeira_values_sent", "resource_data_request_performed",
        "resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized",
        "schedule_enabled", "dom_interaction_performed", "navigation_executed", "history_state_mutated",
        "form_submission", "post_request_performed", "head_request_performed", "authentication_performed",
        "captcha_bypass", "credentials_captured", "cookies_captured", "artifact_downloaded",
        "raw_navigation_value_returned", "navigation_fragment_returned", "fragment_target_identifier_returned",
        "fragment_target_text_returned", "dom_text_returned", "dom_attribute_values_returned",
        "element_text_returned", "element_attribute_returned", "tag_name_returned", "html_returned",
        "script_source_returned", "response_body_persisted", "request_body_persisted",
        "query_values_persisted", "route_synthesized_or_guessed", "automatic_route_promotion",
    )
    for key in required_false:
        _require(safety.get(key), False, f"SAFETY_{key.upper()}")
    _require(safety.get("initial_document_network_sent"), True, "SAFETY_INITIAL_DOCUMENT")
    _require(safety.get("browser_download_denied"), True, "SAFETY_DOWNLOAD_DENIED")
    _require(safety.get("fragment_value_transient_read_performed"), True, "SAFETY_FRAGMENT_TRANSIENT")
    _require(safety.get("fragment_target_text_transient_read_performed"), True, "SAFETY_TARGET_TRANSIENT")
    _require(safety.get("remote_writes"), "NONE", "SAFETY_WRITES")

    for key in (
        "raw_navigation_value_return", "navigation_fragment_return", "fragment_target_identifier_return",
        "fragment_target_text_return", "dom_text_return", "dom_attribute_value_return", "element_text_return",
        "element_attribute_return", "tag_name_return", "html_capture", "script_source_capture",
        "response_body_capture", "request_body_capture", "query_value_persistence", "dom_interaction",
        "navigation_execution", "history_state_mutation", "form_submission", "dynamic_candidate_network_send",
        "resource_data_request", "pilot_limeira_values_send", "post_request_send", "head_request",
        "authentication", "captcha_bypass", "credential_capture", "cookie_capture", "artifact_download",
        "remote_writes", "route_synthesis_or_guessing", "automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS_REVIEW",
        "gate_id": config["gate_id"],
        "software_version": config["software_version"],
        **EXPECTED_INTERPRETATION,
        "network_called": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
