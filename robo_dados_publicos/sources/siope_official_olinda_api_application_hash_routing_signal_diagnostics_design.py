from __future__ import annotations

from pathlib import Path
import json

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS_DESIGN"
COUNT_FIELDS = [
    "parsed_script_count",
    "source_read_count",
    "source_read_failure_count",
    "hashchange_token_occurrence_count",
    "location_hash_token_occurrence_count",
    "onhashchange_token_occurrence_count",
    "route_provider_token_occurrence_count",
    "ngroute_token_occurrence_count",
    "hash_prefix_token_occurrence_count",
    "location_provider_token_occurrence_count",
    "routing_signal_script_count",
    "callable_name_script_count",
    "callable_and_routing_signal_same_script_count",
    "all_parameter_names_and_routing_signal_same_script_count",
    "service_document_name_and_routing_signal_same_script_count",
    "callable_parameter_and_routing_signal_same_script_count",
]


class SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return value


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsDesignError(f"{ERROR}_{code}")


def run_design(config: dict, review_result: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS_DESIGN_0_8_0", "GATE")
    _require(config.get("mode"), "OFFLINE_PASSIVE_ALREADY_LOADED_SCRIPT_HASH_ROUTING_SIGNAL_DIAGNOSTICS_DESIGN", "MODE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("known_routing_tokens"), ["hashchange", "location.hash", "onhashchange", "$routeProvider", "ngRoute", "hashPrefix", "$locationProvider"], "TOKENS")
    _require(config.get("returned_count_fields"), COUNT_FIELDS, "FIELDS")
    _require(review_result.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS_REVIEW", "REVIEW")
    _require(review_result.get("fragment_shape_status"), "BOTH_OBSERVED_FRAGMENTS_ROUTE_LIKE_NOT_ANCHOR_LIKE_ON_PINNED_RUN", "ROUTE_LIKE")
    _require(review_result.get("existing_dom_target_status"), "NO_EXISTING_DOM_TARGET_RESOLVED_ON_PINNED_RUN", "TARGET")
    _require(review_result.get("known_contract_syntax_status"), "NOT_OBSERVED_IN_FRAGMENT_VALUES_OR_EXISTING_TARGETS_ON_PINNED_RUN", "SYNTAX")
    _require(review_result.get("fragment_route_semantics_status"), "UNPROVEN_RAW_FRAGMENT_VALUES_NOT_RETURNED_OR_EXECUTED", "SEMANTICS")
    _require(review_result.get("resource_route_contract_status"), "UNPROVEN", "RESOURCE")
    for key in (
        "new_script_network_request", "script_source_return", "script_source_persistence", "script_url_return",
        "script_id_return", "source_snippet_return", "source_offset_return", "fragment_value_capture",
        "dom_text_return", "html_capture", "response_body_capture", "request_body_capture",
        "query_value_persistence", "dynamic_candidate_network_send", "resource_data_request",
        "pilot_limeira_values_send", "dom_interaction", "navigation_execution", "history_state_mutation",
        "form_submission", "post_request_send", "head_request", "authentication", "captcha_bypass",
        "credential_capture", "cookie_capture", "artifact_download", "remote_writes",
        "route_synthesis_or_guessing", "automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "returned_observations": COUNT_FIELDS,
        "observation_semantics": config["observation_semantics"],
        "fragment_value_read_authorized": False,
        "script_source_transient_read_authorized": True,
        "script_source_return_authorized": False,
        "new_script_network_request_authorized": False,
        "navigation_execution_authorized": False,
        "history_state_mutation_authorized": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "network_called": False,
        "next_gate": config["next_gate"],
    }
