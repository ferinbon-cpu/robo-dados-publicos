from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS_REVIEW"


class SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsReviewError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsReviewError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsReviewError(f"{ERROR}_{code}")


def run_review(config: dict, evidence: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS_REVIEW_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("network_called"), False, "NETWORK")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")
    for key in ("raw_navigation_value_return", "navigation_execution", "resource_data_request", "pilot_limeira_values_send", "dom_interaction", "post_request_send", "head_request", "route_synthesis_or_guessing", "automatic_route_promotion"):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")

    _require(evidence.get("run_id"), config["pinned_run_id"], "RUN")
    _require(evidence.get("job_id"), config["pinned_job_id"], "JOB")
    _require(evidence.get("head_sha"), config["pinned_head_sha"], "SHA")
    _require((evidence.get("artifact") or {}).get("id"), config["pinned_artifact_id"], "ARTIFACT")
    _require((evidence.get("artifact") or {}).get("digest"), config["pinned_artifact_digest"], "DIGEST")
    _require(evidence.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS", "STATUS")
    _require(evidence.get("navigation_match_distribution_counts"), config["expected_navigation_match_distribution_counts"], "COUNTS")
    _require(evidence.get("candidate_shape_count"), config["expected_candidate_shape_count"], "CANDIDATES")
    _require(evidence.get("blocked_shape_count"), config["expected_blocked_shape_count"], "BLOCKED")
    _require(evidence.get("application_surface_verified"), True, "SURFACE")

    counts = evidence["navigation_match_distribution_counts"]
    _require(counts.get("navigation_match_count"), 2, "TOTAL_TWO")
    _require(counts.get("href_match_count"), 2, "HREF_TWO")
    _require(counts.get("action_match_count"), 0, "ACTION_ZERO")
    _require(counts.get("fragment_only_match_count"), 2, "FRAGMENT_TWO")
    _require(counts.get("resolves_to_application_document_match_count"), 2, "APPLICATION_TWO")
    for key in (
        "relative_nonfragment_match_count",
        "same_origin_absolute_match_count",
        "contains_all_parameter_names_match_count",
        "ordered_callable_parameter_sequence_match_count",
        "query_present_match_count",
        "parentheses_present_match_count",
        "callable_parameter_contract_like_match_count",
        "same_origin_contract_like_match_count",
    ):
        _require(counts.get(key), 0, f"ZERO_{key.upper()}")

    safety = evidence.get("safety") or {}
    for key in (
        "dynamic_candidate_network_sent",
        "pilot_limeira_values_sent",
        "resource_data_request_performed",
        "resource_get_authorized",
        "collection_authorized",
        "processing_authorized",
        "recurrence_authorized",
        "schedule_enabled",
        "dom_interaction_performed",
        "navigation_executed",
        "post_request_performed",
        "head_request_performed",
        "raw_navigation_value_returned",
        "route_synthesized_or_guessed",
        "automatic_route_promotion",
    ):
        _require(safety.get(key), False, f"SAFETY_{key.upper()}")
    _require(safety.get("browser_download_denied"), True, "DOWNLOAD_DENIED")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS_REVIEW",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "review_mode": config["mode"],
        "evidence_run_id": config["pinned_run_id"],
        "evidence_artifact_id": config["pinned_artifact_id"],
        "navigation_match_cardinality_status": "EXACTLY_TWO_MATCHES_ON_PINNED_RUN",
        "navigation_attribute_partition_status": "TWO_HREF_ZERO_ACTION",
        "navigation_value_class_status": "BOTH_FRAGMENT_ONLY_AND_RESOLVE_TO_APPLICATION_DOCUMENT",
        "navigation_parameter_contract_status": "NOT_OBSERVED_IN_EITHER_MATCH",
        "navigation_attribute_resource_route_status": "REJECTED_AS_RESOURCE_ROUTE_BOTH_MATCHES_ARE_INTERNAL_APPLICATION_FRAGMENTS",
        "navigation_attribute_strategy_status": "EXHAUSTED_FOR_RESOURCE_ROUTE_ON_PINNED_RUN",
        "resource_route_contract_status": "UNPROVEN",
        "callable_semantics_status": "UNPROVEN",
        "cross_surface_name_identity_status": "UNPROVEN",
        "network_called": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
