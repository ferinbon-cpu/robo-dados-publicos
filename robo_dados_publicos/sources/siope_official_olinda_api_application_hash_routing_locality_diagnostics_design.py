from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_LOCALITY_DIAGNOSTICS_DESIGN"
RADII = [1024, 4096, 16384, 65536]
METRICS = ["any_routing_signal", "location_hash", "route_provider", "ngroute", "hashchange", "hash_prefix", "all_parameter_names", "all_parameter_names_and_any_routing_signal"]
COUNT_FIELDS = ["parsed_script_count", "source_read_count", "source_read_failure_count", "callable_occurrence_count"] + [f"{metric}_window_{radius}_count" for radius in RADII for metric in METRICS]

class SiopeOfficialOlindaApiApplicationHashRoutingLocalityDiagnosticsDesignError(RuntimeError):
    pass

def load_json(path: str | Path) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SiopeOfficialOlindaApiApplicationHashRoutingLocalityDiagnosticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return value

def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationHashRoutingLocalityDiagnosticsDesignError(f"{ERROR}_{code}")

def run_design(config: dict, review_result: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_LOCALITY_DIAGNOSTICS_DESIGN_0_8_0", "GATE")
    _require(config.get("mode"), "OFFLINE_BOUNDED_HASH_ROUTING_LOCALITY_COUNT_DIAGNOSTICS_DESIGN", "MODE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMS")
    _require(config.get("known_routing_tokens"), ["hashchange", "location.hash", "onhashchange", "$routeProvider", "ngRoute", "hashPrefix", "$locationProvider"], "TOKENS")
    _require(config.get("window_radii_chars"), RADII, "RADII")
    _require(config.get("returned_observations"), COUNT_FIELDS, "FIELDS")
    _require(review_result.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS_REVIEW", "REVIEW")
    _require(review_result.get("callable_routing_colocation_status"), "ALL_2_CALLABLE_SCRIPTS_ALSO_HAVE_ROUTING_SIGNALS", "COLOCATION")
    _require(review_result.get("hash_routing_locality_status"), "UNPROVEN_SAME_SCRIPT_ONLY", "LOCALITY")
    _require(review_result.get("fragment_route_semantics_status"), "UNPROVEN", "FRAGMENT")
    _require(review_result.get("resource_route_contract_status"), "UNPROVEN", "RESOURCE")
    _require(config.get("script_source_transient_read"), "ALLOWED_EPHEMERAL_MEMORY_ONLY_AFTER_SCRIPT_ALREADY_LOADED", "TRANSIENT")
    for key in (
        "script_source_return_authorized", "script_source_persistence_authorized", "script_url_return_authorized", "script_id_return_authorized",
        "source_snippet_return_authorized", "source_offset_return_authorized", "fragment_value_read_authorized",
        "new_script_network_request_authorized", "resource_data_request_authorized", "pilot_limeira_values_send_authorized",
        "dom_interaction_authorized", "navigation_execution_authorized", "history_state_mutation_authorized",
        "route_synthesis_or_guessing_authorized", "automatic_route_promotion", "resource_get_authorized",
        "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled",
    ):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_LOCALITY_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"], "software_version": config["software_version"], "design_mode": config["mode"],
        "window_radii_chars": RADII, "returned_observations": COUNT_FIELDS,
        "observation_semantics": "CALLABLE_CENTERED_EXPANDING_WINDOW_FIXED_HASH_ROUTING_AND_PARAMETER_INTEGER_COUNTS_ONLY",
        "script_source_transient_read_authorized": True, "fragment_value_read_authorized": False,
        "script_source_return_authorized": False, "new_script_network_request_authorized": False,
        "navigation_execution_authorized": False, "history_state_mutation_authorized": False,
        "resource_get_authorized": False, "collection_authorized": False, "processing_authorized": False,
        "recurrence_authorized": False, "schedule_enabled": False, "network_called": False, "next_gate": config["next_gate"],
    }
