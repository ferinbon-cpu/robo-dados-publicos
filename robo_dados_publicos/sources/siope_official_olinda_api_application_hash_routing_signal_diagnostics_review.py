from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS_REVIEW"

class SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsReviewError(RuntimeError):
    pass

def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload

def git_blob_sha(path: str | Path) -> str:
    data = Path(path).read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()

def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsReviewError(f"{ERROR}_{code}")

def run_review(config: dict, evidence: dict, *, evidence_path: str | Path | None = None) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS_REVIEW_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_PINNED_HASH_ROUTING_SIGNAL_DIAGNOSTICS_REVIEW", "MODE")
    _require(config.get("network_called"), False, "NETWORK")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")
    for key in (
        "new_script_network_request", "script_source_return", "script_source_persistence", "script_url_return", "script_id_return",
        "source_snippet_return", "source_offset_return", "fragment_value_capture", "dom_text_return", "html_capture",
        "response_body_capture", "request_body_capture", "query_value_persistence", "dynamic_candidate_network_send",
        "resource_data_request", "pilot_limeira_values_send", "dom_interaction", "navigation_execution",
        "history_state_mutation", "form_submission", "post_request_send", "head_request", "authentication",
        "captcha_bypass", "credential_capture", "cookie_capture", "artifact_download", "remote_writes",
        "route_synthesis_or_guessing", "automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")
    if evidence_path is not None:
        _require(git_blob_sha(evidence_path), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB_SHA")
    _require(evidence.get("run_id"), config["pinned_run_id"], "RUN")
    _require(evidence.get("run_number"), 1, "RUN_NUMBER")
    _require(evidence.get("job_id"), config["pinned_job_id"], "JOB")
    _require(evidence.get("event"), "workflow_dispatch", "EVENT")
    _require(evidence.get("branch"), "main", "BRANCH")
    _require(evidence.get("head_sha"), config["pinned_head_sha"], "SHA")
    _require((evidence.get("artifact") or {}).get("id"), config["pinned_artifact_id"], "ARTIFACT")
    _require((evidence.get("artifact") or {}).get("digest"), config["pinned_artifact_digest"], "DIGEST")
    _require(evidence.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS", "STATUS")
    _require(evidence.get("application_surface_verified"), True, "SURFACE")
    _require(evidence.get("candidate_shape_count"), 0, "CANDIDATES")
    _require(evidence.get("blocked_shape_count"), 1, "BLOCKED")
    qa = evidence.get("qa") or {}
    _require(qa.get("unit_tests"), 774, "QA_UNIT")
    _require(qa.get("unit_tests_passed"), 774, "QA_UNIT_PASS")
    _require(qa.get("historical_regressions"), 109, "QA_HIST")
    _require(qa.get("historical_regressions_passed"), 109, "QA_HIST_PASS")
    expected_counts = {
        "parsed_script_count": 40, "source_read_count": 40, "source_read_failure_count": 0,
        "hashchange_token_occurrence_count": 2, "location_hash_token_occurrence_count": 13,
        "onhashchange_token_occurrence_count": 0, "route_provider_token_occurrence_count": 5,
        "ngroute_token_occurrence_count": 3, "hash_prefix_token_occurrence_count": 1,
        "location_provider_token_occurrence_count": 0, "routing_signal_script_count": 13,
        "callable_name_script_count": 2, "callable_and_routing_signal_same_script_count": 2,
        "all_parameter_names_and_routing_signal_same_script_count": 2,
        "service_document_name_and_routing_signal_same_script_count": 0,
        "callable_parameter_and_routing_signal_same_script_count": 2,
    }
    _require(evidence.get("hash_routing_signal_counts") or {}, expected_counts, "COUNTS")
    expected_interpretation = {
        "loaded_script_coverage_status": "FORTY_PARSED_FORTY_READ_ZERO_FAILURES_ON_PINNED_RUN",
        "hash_routing_signal_status": "OBSERVED_IN_13_OF_40_ALREADY_LOADED_SCRIPTS",
        "callable_routing_colocation_status": "ALL_2_CALLABLE_SCRIPTS_ALSO_HAVE_ROUTING_SIGNALS",
        "callable_parameter_routing_colocation_status": "TWO_SCRIPTS_HAVE_CALLABLE_ALL_PARAMETERS_AND_ROUTING_SIGNALS",
        "service_document_routing_colocation_status": "NOT_OBSERVED",
        "hash_routing_locality_status": "UNPROVEN_SAME_SCRIPT_ONLY",
        "fragment_route_semantics_status": "UNPROVEN",
        "resource_route_contract_status": "UNPROVEN",
        "callable_semantics_status": "UNPROVEN",
        "next_safe_surface": "PASSIVE_ALREADY_LOADED_SCRIPT_HASH_ROUTING_LOCALITY_COUNTS_WITHOUT_FRAGMENT_OR_NAVIGATION",
    }
    _require(evidence.get("interpretation") or {}, expected_interpretation, "INTERPRETATION")
    safety = evidence.get("safety") or {}
    _require(safety.get("script_source_transient_read_performed"), True, "TRANSIENT_READ")
    _require(safety.get("browser_download_denied"), True, "DOWNLOAD_DENIED")
    _require(safety.get("remote_writes"), "NONE", "REMOTE_WRITES")
    for key in (
        "dynamic_candidate_network_sent", "pilot_limeira_values_sent", "resource_data_request_performed",
        "resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized",
        "schedule_enabled", "dom_interaction_performed", "navigation_executed", "history_state_mutated",
        "post_request_performed", "head_request_performed", "script_source_returned", "script_source_persisted",
        "script_url_returned", "script_id_returned", "source_snippet_returned", "source_offset_returned",
        "new_script_network_request_performed", "fragment_value_read_performed", "fragment_value_returned",
        "route_synthesized_or_guessed", "automatic_route_promotion",
    ):
        _require(safety.get(key), False, f"SAFETY_{key.upper()}")
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS_REVIEW",
        "gate_id": config["gate_id"], "source_id": config["source_id"], "software_version": config["software_version"],
        "review_mode": config["mode"], "evidence_run_id": config["pinned_run_id"], "evidence_artifact_id": config["pinned_artifact_id"],
        **expected_interpretation,
        "network_called": False, "resource_get_authorized": False, "collection_authorized": False,
        "processing_authorized": False, "recurrence_authorized": False, "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
