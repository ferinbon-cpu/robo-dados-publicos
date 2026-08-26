from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_REVIEW"


class SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def git_blob_sha(path: str | Path) -> str:
    data = Path(path).read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsReviewError(f"{ERROR}_{code}")


def run_review(config: dict, evidence: dict, *, evidence_path: str | Path | None = None) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_REVIEW_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_PINNED_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_REVIEW", "MODE")
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
    _require(evidence.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS", "STATUS")
    _require(evidence.get("loaded_script_signature_counts"), config["expected_loaded_script_signature_counts"], "COUNTS")
    _require(evidence.get("candidate_shape_count"), config["expected_candidate_shape_count"], "CANDIDATES")
    _require(evidence.get("blocked_shape_count"), config["expected_blocked_shape_count"], "BLOCKED")
    _require(evidence.get("application_surface_verified"), True, "SURFACE")

    counts = evidence["loaded_script_signature_counts"]
    _require(counts.get("parsed_script_count"), 40, "PARSED_40")
    _require(counts.get("source_read_count"), 40, "READ_40")
    _require(counts.get("source_read_failure_count"), 0, "READ_FAILURE_ZERO")
    _require(counts.get("callable_occurrence_count"), 4, "CALLABLE_OCCURRENCES_4")
    _require(counts.get("callable_name_script_count"), 2, "CALLABLE_SCRIPTS_2")
    _require(counts.get("service_document_name_script_count"), 0, "SERVICE_NAME_ZERO")
    _require(counts.get("both_names_same_script_count"), 0, "BOTH_NAMES_ZERO")
    _require(counts.get("all_parameter_names_window_count"), 4, "PARAM_WINDOWS_4")
    _require(counts.get("ordered_callable_parameter_sequence_window_count"), 2, "ORDERED_WINDOWS_2")
    for key in (
        "callable_open_parenthesis_window_count",
        "all_at_parameter_names_window_count",
        "odata_literal_window_count",
        "format_token_window_count",
        "query_marker_window_count",
        "contract_like_window_count",
    ):
        _require(counts.get(key), 0, f"ZERO_{key.upper()}")

    safety = evidence.get("safety") or {}
    _require(safety.get("script_source_transient_read_performed"), True, "TRANSIENT_READ")
    _require(safety.get("browser_download_denied"), True, "DOWNLOAD_DENIED")
    for key in (
        "dynamic_candidate_network_sent", "pilot_limeira_values_sent", "resource_data_request_performed",
        "resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized",
        "schedule_enabled", "dom_interaction_performed", "navigation_executed", "post_request_performed",
        "head_request_performed", "script_source_returned", "script_source_persisted", "script_url_returned",
        "script_id_returned", "source_snippet_returned", "source_offset_returned", "new_script_network_request_performed",
        "route_synthesized_or_guessed", "automatic_route_promotion",
    ):
        _require(safety.get(key), False, f"SAFETY_{key.upper()}")
    _require(safety.get("remote_writes"), "NONE", "REMOTE_WRITES")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "evidence_run_id": config["pinned_run_id"],
        "evidence_artifact_id": config["pinned_artifact_id"],
        "loaded_script_coverage_status": "FORTY_PARSED_FORTY_READ_ZERO_FAILURES_ON_PINNED_RUN",
        "technical_callable_presence_status": "PROVEN_TWO_SCRIPTS_FOUR_OCCURRENCES_ON_PINNED_RUN",
        "parameter_binding_status": "PROVEN_ALL_THREE_PARAMETERS_LOCAL_ON_FOUR_OCCURRENCES_ORDERED_ON_TWO",
        "service_document_name_script_status": "NOT_OBSERVED_ON_PINNED_RUN",
        "local_executable_contract_status": "NOT_OBSERVED_NO_PAREN_QUERY_AT_PARAMS_ODATA_OR_FORMAT_TOKEN",
        "callable_semantics_status": "STRUCTURAL_NAME_PARAMETER_BINDING_CORROBORATED_EXECUTABLE_CALL_SYNTAX_UNPROVEN",
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
