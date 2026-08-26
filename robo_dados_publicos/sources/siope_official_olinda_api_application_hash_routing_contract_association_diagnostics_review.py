from __future__ import annotations

import hashlib
import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_CONTRACT_ASSOCIATION_DIAGNOSTICS_REVIEW"
EXPECTED_COUNTS = {
    "parsed_script_count": 43,
    "source_read_count": 43,
    "source_read_failure_count": 0,
    "callable_occurrence_count": 4,
    "location_hash_family_count": 2,
    "ngroute_family_count": 2,
    "ambiguous_family_count": 0,
    "location_hash_family_all_parameter_names_1024_count": 2,
    "ngroute_family_all_parameter_names_1024_count": 2,
    "location_hash_family_format_window_16384_count": 2,
    "location_hash_family_odata_window_16384_count": 0,
    "location_hash_family_odata_format_window_16384_count": 0,
    "location_hash_family_format_window_65536_count": 2,
    "location_hash_family_odata_window_65536_count": 2,
    "location_hash_family_odata_format_window_65536_count": 2,
    "ngroute_family_format_window_16384_count": 0,
    "ngroute_family_odata_window_16384_count": 0,
    "ngroute_family_odata_format_window_16384_count": 0,
    "ngroute_family_format_window_65536_count": 0,
    "ngroute_family_odata_window_65536_count": 0,
    "ngroute_family_odata_format_window_65536_count": 0,
}
EXPECTED_INTERPRETATION = {
    "loaded_script_coverage_status": "FORTY_THREE_PARSED_FORTY_THREE_READ_ZERO_FAILURES_ON_PINNED_RUN",
    "family_partition_status": "EXACT_TWO_LOCATION_HASH_AND_TWO_NGROUTE_WITH_ZERO_AMBIGUOUS_OCCURRENCES",
    "parameter_locality_status": "ALL_FOUR_OCCURRENCES_HAVE_ALL_THREE_PARAMETER_NAMES_WITHIN_1024_CHARS",
    "location_hash_format_status": "BOTH_LOCATION_HASH_FAMILY_OCCURRENCES_HAVE_FORMAT_WITHIN_16384_CHARS",
    "location_hash_odata_status": "ODATA_ABSENT_WITHIN_16384_BUT_PRESENT_WITH_FORMAT_WITHIN_65536_FOR_BOTH_LOCATION_HASH_OCCURRENCES",
    "ngroute_contract_status": "ZERO_FORMAT_AND_ZERO_ODATA_THROUGH_65536_FOR_BOTH_NGROUTE_OCCURRENCES",
    "contract_family_status": "KNOWN_ODATA_CONTRACT_TOKENS_ARE_EXCLUSIVELY_ASSOCIATED_WITH_LOCATION_HASH_FAMILY_ON_PINNED_RUN",
    "locality_semantics_status": "PROVEN_FAMILY_SPECIFIC_DISTANCE_BUCKET_COLOCATION_ONLY_NOT_SAME_STATEMENT_EXPRESSION_OR_DATAFLOW",
    "fragment_route_semantics_status": "UNPROVEN",
    "resource_route_contract_status": "UNPROVEN",
    "callable_semantics_status": "UNPROVEN",
    "next_safe_surface": "PASSIVE_LOCATION_HASH_FAMILY_RELATIVE_SIDE_AND_ORDER_COUNTS_WITHOUT_OFFSETS_OR_RAW_SOURCE",
}

class SiopeOfficialOlindaApiApplicationHashRoutingContractAssociationDiagnosticsReviewError(RuntimeError):
    pass

def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationHashRoutingContractAssociationDiagnosticsReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload

def git_blob_sha(path: str | Path) -> str:
    data = Path(path).read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()

def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationHashRoutingContractAssociationDiagnosticsReviewError(f"{ERROR}_{code}")

def run_review(config: dict, evidence: dict, *, evidence_path: str | Path | None = None) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_CONTRACT_ASSOCIATION_DIAGNOSTICS_REVIEW_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_PINNED_HASH_ROUTING_CONTRACT_ASSOCIATION_DIAGNOSTICS_REVIEW", "MODE")
    _require(config.get("network_called"), False, "NETWORK")
    if evidence_path is not None:
        _require(git_blob_sha(evidence_path), config["pinned_evidence_blob_sha"], "EVIDENCE_BLOB_SHA")
    _require(evidence.get("run_id"), config["pinned_run_id"], "RUN")
    _require(evidence.get("run_number"), 1, "RUN_NUMBER")
    _require(evidence.get("job_id"), config["pinned_job_id"], "JOB")
    _require(evidence.get("event"), "workflow_dispatch", "EVENT")
    _require(evidence.get("branch"), "main", "BRANCH")
    _require(evidence.get("head_sha"), config["pinned_head_sha"], "HEAD")
    artifact = evidence.get("artifact") or {}
    _require(artifact.get("id"), config["pinned_artifact_id"], "ARTIFACT_ID")
    _require(artifact.get("digest"), config["pinned_artifact_digest"], "ARTIFACT_DIGEST")
    _require(evidence.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_CONTRACT_ASSOCIATION_DIAGNOSTICS", "STATUS")
    _require(evidence.get("application_surface_verified"), True, "SURFACE")
    _require(evidence.get("candidate_shape_count"), 0, "CANDIDATES")
    _require(evidence.get("blocked_shape_count"), 1, "BLOCKED")
    _require(evidence.get("hash_routing_contract_association_counts"), EXPECTED_COUNTS, "COUNTS")
    _require(evidence.get("interpretation"), EXPECTED_INTERPRETATION, "INTERPRETATION")
    qa = evidence.get("qa") or {}
    _require(qa.get("unit_tests"), config["pinned_unit_tests"], "QA_UNIT")
    _require(qa.get("unit_tests_passed"), config["pinned_unit_tests"], "QA_UNIT_PASS")
    _require(qa.get("historical_regressions"), config["pinned_historical_regressions"], "QA_HIST")
    _require(qa.get("historical_regressions_passed"), config["pinned_historical_regressions"], "QA_HIST_PASS")
    for key in (
        "script_source_return", "script_source_persistence", "script_url_return", "script_id_return",
        "source_snippet_return", "source_offset_return", "fragment_value_capture", "new_script_network_request",
        "resource_data_request", "pilot_limeira_values_send", "dom_interaction", "navigation_execution",
        "history_state_mutation", "post_request_send", "head_request", "route_synthesis_or_guessing", "automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")
    safety = evidence.get("safety") or {}
    _require(safety.get("script_source_transient_read_performed"), True, "TRANSIENT_READ")
    _require(safety.get("browser_download_denied"), True, "DOWNLOAD_DENIED")
    for key in (
        "dynamic_candidate_network_sent", "script_source_returned", "script_source_persisted", "script_url_returned",
        "script_id_returned", "source_snippet_returned", "source_offset_returned", "new_script_network_request_performed",
        "fragment_value_read_performed", "fragment_value_returned", "dom_interaction_performed", "navigation_executed",
        "history_state_mutated", "pilot_limeira_values_sent", "resource_data_request_performed", "resource_get_authorized",
        "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled", "post_request_performed",
        "head_request_performed", "route_synthesized_or_guessed", "automatic_route_promotion",
    ):
        _require(safety.get(key), False, f"SAFETY_{key.upper()}")
    _require(safety.get("remote_writes"), "NONE", "REMOTE_WRITES")
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_CONTRACT_ASSOCIATION_DIAGNOSTICS_REVIEW",
        "gate_id": config["gate_id"], "source_id": config["source_id"], "software_version": config["software_version"],
        "review_mode": config["mode"], "evidence_run_id": config["pinned_run_id"], "evidence_artifact_id": config["pinned_artifact_id"],
        **EXPECTED_INTERPRETATION,
        "network_called": False, "resource_get_authorized": False, "collection_authorized": False,
        "processing_authorized": False, "recurrence_authorized": False, "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
