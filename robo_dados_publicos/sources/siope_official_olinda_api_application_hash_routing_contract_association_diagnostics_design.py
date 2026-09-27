from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_CONTRACT_ASSOCIATION_DIAGNOSTICS_DESIGN"
FAMILIES = ["location_hash", "ngroute"]
CONTRACT_WINDOWS = [16384, 65536]
COUNT_FIELDS = [
    "parsed_script_count", "source_read_count", "source_read_failure_count", "callable_occurrence_count",
    "location_hash_family_count", "ngroute_family_count", "ambiguous_family_count",
    "location_hash_family_all_parameter_names_1024_count", "ngroute_family_all_parameter_names_1024_count",
]
for family in FAMILIES:
    for radius in CONTRACT_WINDOWS:
        COUNT_FIELDS.extend([
            f"{family}_family_format_window_{radius}_count",
            f"{family}_family_odata_window_{radius}_count",
            f"{family}_family_odata_format_window_{radius}_count",
        ])

class SiopeOfficialOlindaApiApplicationHashRoutingContractAssociationDiagnosticsDesignError(RuntimeError):
    pass

def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationHashRoutingContractAssociationDiagnosticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload

def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationHashRoutingContractAssociationDiagnosticsDesignError(f"{ERROR}_{code}")

def run_design(config: dict, review_result: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_CONTRACT_ASSOCIATION_DIAGNOSTICS_DESIGN_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_BOUNDED_ROUTING_FAMILY_ODATA_CONTRACT_ASSOCIATION_COUNT_DESIGN", "MODE")
    _require(review_result.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_FAMILY_INTERSECTION_DIAGNOSTICS_REVIEW", "REVIEW")
    _require(review_result.get("primary_family_partition_4096_status"), "EXACT_DISJOINT_TWO_LOCATION_HASH_ONLY_AND_TWO_NGROUTE_ONLY", "PARTITION")
    _require(review_result.get("resource_route_contract_status"), "UNPROVEN", "ROUTE_UNPROVEN")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMS")
    _require(config.get("family_classification_window_chars"), 4096, "FAMILY_WINDOW")
    _require(config.get("parameter_window_chars"), 1024, "PARAM_WINDOW")
    _require(config.get("contract_windows_chars"), CONTRACT_WINDOWS, "CONTRACT_WINDOWS")
    _require(config.get("primary_family_tokens"), ["location.hash", "ngRoute", "$routeProvider"], "FAMILY_TOKENS")
    _require(config.get("known_contract_tokens"), ["/odata/", "$format"], "CONTRACT_TOKENS")
    for key in ("script_source_return", "script_source_persistence", "script_url_return", "script_id_return", "source_snippet_return", "source_offset_return", "fragment_value_capture", "new_script_network_request", "dynamic_candidate_network_send", "resource_data_request", "pilot_limeira_values_send", "dom_interaction", "navigation_execution", "history_state_mutation", "form_submission", "post_request_send", "head_request", "authentication", "captcha_bypass", "credential_capture", "cookie_capture", "artifact_download", "remote_writes", "route_synthesis_or_guessing", "automatic_route_promotion"):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_CONTRACT_ASSOCIATION_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"], "software_version": config["software_version"], "design_mode": config["mode"],
        "observation_semantics": config["observation_semantics"], "family_classification_window_chars": 4096,
        "parameter_window_chars": 1024, "contract_windows_chars": CONTRACT_WINDOWS,
        "returned_observations": COUNT_FIELDS, "network_called": False, "script_source_transient_read_authorized": True,
        "fragment_value_read_authorized": False, "navigation_execution_authorized": False, "history_state_mutation_authorized": False,
        "new_script_network_request_authorized": False, "resource_get_authorized": False, "collection_authorized": False,
        "processing_authorized": False, "recurrence_authorized": False, "schedule_enabled": False, "next_gate": config["next_gate"],
    }
