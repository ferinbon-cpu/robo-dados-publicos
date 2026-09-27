from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_LOCALITY_DIAGNOSTICS_REVIEW"


class SiopeOfficialOlindaApiApplicationLoadedScriptLocalityDiagnosticsReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationLoadedScriptLocalityDiagnosticsReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def git_blob_sha(path: str | Path) -> str:
    data = Path(path).read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptLocalityDiagnosticsReviewError(f"{ERROR}_{code}")


def run_review(config: dict, evidence: dict, *, evidence_path: str | Path | None = None) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_LOCALITY_DIAGNOSTICS_REVIEW_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_PINNED_LOADED_SCRIPT_LOCALITY_DIAGNOSTICS_REVIEW", "MODE")
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
    _require(evidence.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_LOCALITY_DIAGNOSTICS", "STATUS")
    _require(evidence.get("application_surface_verified"), True, "SURFACE")
    _require(evidence.get("candidate_shape_count"), 0, "CANDIDATES")
    _require(evidence.get("blocked_shape_count"), 1, "BLOCKED")
    _require((evidence.get("qa") or {}).get("unit_tests"), 727, "QA_UNIT")
    _require((evidence.get("qa") or {}).get("historical_regressions"), 109, "QA_HISTORICAL")

    counts = evidence.get("loaded_script_locality_counts") or {}
    _require(counts.get("parsed_script_count"), 41, "PARSED_41")
    _require(counts.get("source_read_count"), 41, "READ_41")
    _require(counts.get("source_read_failure_count"), 0, "READ_FAILURE_ZERO")
    _require(counts.get("callable_occurrence_count"), 4, "CALLABLE_4")
    _require(counts.get("callable_exact_string_literal_occurrence_count"), 4, "CALLABLE_LITERAL_4")
    _require(counts.get("all_parameter_names_window_1024_count"), 4, "PARAMS_1024_4")
    _require(counts.get("all_parameter_exact_string_literals_window_1024_count"), 4, "PARAM_LITERALS_1024_4")
    _require(counts.get("odata_literal_window_16384_count"), 0, "ODATA_16384_ZERO")
    _require(counts.get("format_token_window_16384_count"), 2, "FORMAT_16384_2")
    _require(counts.get("odata_literal_window_65536_count"), 2, "ODATA_65536_2")
    _require(counts.get("format_token_window_65536_count"), 2, "FORMAT_65536_2")
    _require(counts.get("all_parameter_names_odata_format_window_65536_count"), 2, "COMBINED_65536_2")
    _require(counts.get("all_parameter_exact_string_literals_odata_format_window_65536_count"), 2, "COMBINED_LITERALS_65536_2")
    _require(counts.get("all_at_parameter_names_odata_format_window_65536_count"), 0, "AT_COMBINED_ZERO")

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
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_LOCALITY_DIAGNOSTICS_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "evidence_run_id": config["pinned_run_id"],
        "evidence_artifact_id": config["pinned_artifact_id"],
        "loaded_script_coverage_status": "FORTY_ONE_PARSED_FORTY_ONE_READ_ZERO_FAILURES_ON_PINNED_RUN",
        "parameter_locality_status": "PROVEN_ALL_FOUR_CALLABLE_OCCURRENCES_HAVE_ALL_THREE_PARAMETER_NAMES_AND_LITERALS_WITHIN_1024_CHARS",
        "format_locality_status": "PROVEN_TWO_OF_FOUR_CALLABLE_OCCURRENCES_HAVE_FORMAT_WITHIN_16384_CHARS",
        "odata_locality_status": "NOT_WITHIN_16384_BUT_PROVEN_WITHIN_65536_FOR_TWO_OF_FOUR_CALLABLE_OCCURRENCES",
        "combined_contract_locality_status": "PROVEN_TWO_OF_FOUR_HAVE_PARAMETERS_ODATA_AND_FORMAT_WITHIN_65536_ONLY",
        "at_prefixed_parameter_status": "NOT_OBSERVED_AS_COMPLETE_THREE_PARAMETER_SET_WITH_ODATA_AND_FORMAT_IN_TESTED_WINDOWS",
        "executable_call_syntax_status": "UNPROVEN",
        "resource_route_contract_status": "UNPROVEN",
        "network_called": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
