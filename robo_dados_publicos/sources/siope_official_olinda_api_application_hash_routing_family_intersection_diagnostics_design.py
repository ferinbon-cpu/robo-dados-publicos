from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_FAMILY_INTERSECTION_DIAGNOSTICS_DESIGN"
RADII = [1024, 4096, 16384, 65536]
METRICS = [
    "any_known_routing",
    "primary_none",
    "location_hash_only",
    "ngroute_only",
    "route_provider_only",
    "location_hash_ngroute",
    "location_hash_route_provider",
    "ngroute_route_provider",
    "location_hash_ngroute_route_provider",
    "secondary_routing_without_primary",
    "all_parameter_names",
    "all_parameter_names_and_any_known_routing",
]
COUNT_FIELDS = [
    "parsed_script_count", "source_read_count", "source_read_failure_count", "callable_occurrence_count",
] + [f"{metric}_window_{radius}_count" for radius in RADII for metric in METRICS]

class SiopeOfficialOlindaApiApplicationHashRoutingFamilyIntersectionDiagnosticsDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SiopeOfficialOlindaApiApplicationHashRoutingFamilyIntersectionDiagnosticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return value


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationHashRoutingFamilyIntersectionDiagnosticsDesignError(f"{ERROR}_{code}")


def run_design(config: dict, review_result: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_FAMILY_INTERSECTION_DIAGNOSTICS_DESIGN_0_8_0", "GATE")
    _require(config.get("mode"), "OFFLINE_BOUNDED_HASH_ROUTING_FAMILY_INTERSECTION_COUNT_DIAGNOSTICS_DESIGN", "MODE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMS")
    _require(config.get("primary_routing_tokens"), ["location.hash", "ngRoute", "$routeProvider"], "PRIMARY")
    _require(config.get("secondary_routing_tokens"), ["hashchange", "onhashchange", "hashPrefix", "$locationProvider"], "SECONDARY")
    _require(config.get("window_radii_chars"), RADII, "RADII")
    _require(config.get("returned_count_fields"), COUNT_FIELDS, "FIELDS")
    _require(config.get("observation_semantics"), "CALLABLE_CENTERED_EXACT_PRIMARY_ROUTING_PRESENCE_MASK_PARTITION_AND_SECONDARY_ONLY_INTEGER_COUNTS", "SEMANTICS")
    _require(review_result.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_LOCALITY_DIAGNOSTICS_REVIEW", "REVIEW")
    _require(review_result.get("parameter_locality_status"), "ALL_FOUR_CALLABLE_OCCURRENCES_HAVE_ALL_THREE_PARAMETER_NAMES_WITHIN_1024_CHARS", "PARAM_LOCALITY")
    _require(review_result.get("routing_locality_status"), "ALL_FOUR_CALLABLE_OCCURRENCES_HAVE_AT_LEAST_ONE_KNOWN_ROUTING_SIGNAL_WITHIN_4096_CHARS", "ROUTING_LOCALITY")
    _require(review_result.get("routing_family_overlap_status"), "UNPROVEN_COUNTS_DO_NOT_IDENTIFY_WHETHER_LOCATION_HASH_AND_NGROUTE_OCCUR_ON_SAME_OR_DIFFERENT_CALLABLE_OCCURRENCES", "OVERLAP")
    _require(review_result.get("fragment_route_semantics_status"), "UNPROVEN", "FRAGMENT")
    _require(review_result.get("resource_route_contract_status"), "UNPROVEN", "RESOURCE")
    _require(review_result.get("next_safe_surface"), "PASSIVE_CALLABLE_CENTERED_PRIMARY_ROUTING_FAMILY_INTERSECTION_COUNTS_WITHOUT_FRAGMENT_OR_NAVIGATION", "NEXT_SURFACE")
    for key in (
        "script_source_return_authorized", "script_source_persistence_authorized", "script_url_return_authorized",
        "script_id_return_authorized", "source_snippet_return_authorized", "source_offset_return_authorized",
        "fragment_value_read_authorized", "new_script_network_request_authorized", "resource_data_request_authorized",
        "pilot_limeira_values_send_authorized", "dom_interaction_authorized", "navigation_execution_authorized",
        "history_state_mutation_authorized", "route_synthesis_or_guessing_authorized", "automatic_route_promotion",
        "resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled",
    ):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")
    _require(config.get("script_source_transient_read"), "ALLOWED_EPHEMERAL_MEMORY_ONLY_AFTER_SCRIPT_ALREADY_LOADED", "TRANSIENT")
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_FAMILY_INTERSECTION_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "window_radii_chars": RADII,
        "returned_observations": COUNT_FIELDS,
        "observation_semantics": config["observation_semantics"],
        "script_source_transient_read_authorized": True,
        "script_source_return_authorized": False,
        "fragment_value_read_authorized": False,
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
