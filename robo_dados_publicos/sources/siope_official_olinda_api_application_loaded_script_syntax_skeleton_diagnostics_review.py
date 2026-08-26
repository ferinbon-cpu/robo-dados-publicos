from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SYNTAX_SKELETON_DIAGNOSTICS_REVIEW"


class SiopeOfficialOlindaApiApplicationLoadedScriptSyntaxSkeletonDiagnosticsReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSyntaxSkeletonDiagnosticsReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def git_blob_sha(path: str | Path) -> str:
    data = Path(path).read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSyntaxSkeletonDiagnosticsReviewError(f"{ERROR}_{code}")


def run_review(config: dict, evidence: dict, *, evidence_path: str | Path | None = None) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SYNTAX_SKELETON_DIAGNOSTICS_REVIEW_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_PINNED_LOADED_SCRIPT_SYNTAX_SKELETON_DIAGNOSTICS_REVIEW", "MODE")
    _require(config.get("network_called"), False, "NETWORK")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")
    for key in (
        "script_source_return", "script_source_persistence", "script_url_return", "script_id_return",
        "source_snippet_return", "source_offset_return", "new_script_network_request", "resource_data_request",
        "pilot_limeira_values_send", "dom_interaction", "navigation_execution", "post_request_send",
        "head_request", "route_synthesis_or_guessing", "automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")

    if evidence_path is not None:
        _require(git_blob_sha(evidence_path), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB_SHA")
    _require(evidence.get("run_id"), config["pinned_run_id"], "RUN")
    _require(evidence.get("job_id"), config["pinned_job_id"], "JOB")
    _require(evidence.get("head_sha"), config["pinned_head_sha"], "SHA")
    _require((evidence.get("artifact") or {}).get("id"), config["pinned_artifact_id"], "ARTIFACT")
    _require((evidence.get("artifact") or {}).get("digest"), config["pinned_artifact_digest"], "DIGEST")
    _require(evidence.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SYNTAX_SKELETON_DIAGNOSTICS", "STATUS")
    _require(evidence.get("application_surface_verified"), True, "SURFACE")
    _require(evidence.get("candidate_shape_count"), config["expected_candidate_shape_count"], "CANDIDATES")
    _require(evidence.get("blocked_shape_count"), config["expected_blocked_shape_count"], "BLOCKED")
    qa = evidence.get("qa") or {}
    _require(qa.get("unit_tests"), 738, "QA_UNIT")
    _require(qa.get("unit_failures"), 0, "QA_UNIT_FAILURES")
    _require(qa.get("historical_regressions"), 109, "QA_HISTORICAL")
    _require(qa.get("historical_regression_failures"), 0, "QA_HISTORICAL_FAILURES")

    counts = evidence.get("loaded_script_syntax_skeleton_counts") or {}
    expected_counts = {
        "parsed_script_count": 40,
        "source_read_count": 40,
        "source_read_failure_count": 0,
        "callable_occurrence_count": 4,
        "callable_exact_string_literal_occurrence_count": 4,
        "callable_open_paren_occurrence_count": 0,
        "callable_ordered_parameter_names_512_count": 2,
        "callable_close_paren_after_ordered_parameters_512_count": 0,
        "callable_ano_at_binding_4096_count": 0,
        "callable_num_at_binding_4096_count": 0,
        "callable_sig_at_binding_4096_count": 0,
        "callable_all_three_at_bindings_4096_count": 0,
        "callable_ordered_all_three_at_bindings_4096_count": 0,
        "callable_query_alias_ano_4096_count": 0,
        "callable_query_alias_num_4096_count": 0,
        "callable_query_alias_sig_4096_count": 0,
        "callable_all_three_query_aliases_4096_count": 0,
        "callable_format_assignment_4096_count": 0,
        "callable_full_known_signature_skeleton_4096_count": 0,
    }
    _require(counts, expected_counts, "EXACT_COUNTS")

    safety = evidence.get("safety") or {}
    _require(safety.get("script_source_transient_read_performed"), True, "TRANSIENT_READ")
    _require(safety.get("browser_download_denied"), True, "DOWNLOAD_DENIED")
    for key in (
        "dynamic_candidate_network_sent", "pilot_limeira_values_sent", "resource_data_request_performed",
        "resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized",
        "schedule_enabled", "dom_interaction_performed", "navigation_executed", "form_submission",
        "post_request_performed", "head_request_performed", "authentication_performed", "captcha_bypass",
        "credentials_captured", "cookies_captured", "artifact_downloaded", "script_source_returned",
        "script_source_persisted", "script_url_returned", "script_id_returned", "source_snippet_returned",
        "source_offset_returned", "new_script_network_request_performed", "dom_text_returned",
        "fragment_value_returned", "html_returned", "response_body_persisted", "request_body_persisted",
        "query_values_persisted", "route_synthesized_or_guessed", "automatic_route_promotion",
    ):
        _require(safety.get(key), False, f"SAFETY_{key.upper()}")
    _require(safety.get("remote_writes"), "NONE", "REMOTE_WRITES")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SYNTAX_SKELETON_DIAGNOSTICS_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "evidence_run_id": config["pinned_run_id"],
        "evidence_artifact_id": config["pinned_artifact_id"],
        "loaded_script_coverage_status": "FORTY_PARSED_FORTY_READ_ZERO_FAILURES_ON_PINNED_RUN",
        "technical_callable_presence_status": "FOUR_OCCURRENCES_ALL_EXACT_STRING_LITERALS_ON_PINNED_RUN",
        "ordered_parameter_locality_status": "TWO_OF_FOUR_ORDERED_WITHIN_512_CHARS_ON_PINNED_RUN",
        "callable_open_parenthesis_status": "NOT_OBSERVED_ON_PINNED_LOADED_SCRIPTS",
        "known_at_binding_status": "NOT_OBSERVED_ON_PINNED_LOADED_SCRIPTS",
        "known_query_alias_status": "NOT_OBSERVED_ON_PINNED_LOADED_SCRIPTS",
        "known_format_assignment_status": "NOT_OBSERVED_ON_PINNED_LOADED_SCRIPTS",
        "full_known_signature_skeleton_status": "NOT_OBSERVED_ON_PINNED_LOADED_SCRIPTS",
        "loaded_script_known_syntax_strategy_status": "EXHAUSTED_FOR_THIS_KNOWN_TEXTUAL_SKELETON_ON_PINNED_RUN",
        "callable_semantics_status": "UNPROVEN",
        "resource_route_contract_status": "UNPROVEN",
        "network_called": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
