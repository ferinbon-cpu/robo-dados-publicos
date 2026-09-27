from __future__ import annotations

from pathlib import Path

from .siope_official_olinda_api_application_hash_routing_contract_association_diagnostics_review import load_json

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOCATION_HASH_ODATA_SIDE_DIAGNOSTICS_DESIGN"
COUNT_FIELDS = [
    "parsed_script_count", "source_read_count", "source_read_failure_count", "callable_occurrence_count",
    "location_hash_family_count", "ngroute_family_count", "ambiguous_family_count",
    "location_hash_family_all_parameter_names_1024_count",
    "location_hash_token_nearest_left_4096_count", "location_hash_token_nearest_right_4096_count", "location_hash_token_nearest_tie_4096_count",
    "format_nearest_left_16384_count", "format_nearest_right_16384_count", "format_nearest_tie_16384_count", "format_absent_16384_count",
    "odata_nearest_left_65536_count", "odata_nearest_right_65536_count", "odata_nearest_tie_65536_count", "odata_absent_65536_count",
    "nearest_location_hash_and_format_same_side_count", "nearest_format_and_odata_same_side_count",
    "nearest_all_three_same_side_count", "nearest_all_three_left_count", "nearest_all_three_right_count",
]

class SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsDesignError(RuntimeError):
    pass

def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsDesignError(f"{ERROR}_{code}")

def run_design(config: dict, prerequisite_review: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOCATION_HASH_ODATA_SIDE_DIAGNOSTICS_DESIGN_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_BOUNDED_LOCATION_HASH_ODATA_NEAREST_SIDE_COUNT_DESIGN", "MODE")
    _require(prerequisite_review.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_CONTRACT_ASSOCIATION_DIAGNOSTICS_REVIEW", "PREREQUISITE")
    _require(prerequisite_review.get("contract_family_status"), "KNOWN_ODATA_CONTRACT_TOKENS_ARE_EXCLUSIVELY_ASSOCIATED_WITH_LOCATION_HASH_FAMILY_ON_PINNED_RUN", "CONTRACT_FAMILY")
    _require(prerequisite_review.get("resource_route_contract_status"), "UNPROVEN", "ROUTE_UNPROVEN")
    _require(prerequisite_review.get("fragment_route_semantics_status"), "UNPROVEN", "FRAGMENT_UNPROVEN")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMS")
    _require(config.get("family_classification_window_chars"), 4096, "FAMILY_WINDOW")
    _require(config.get("parameter_window_chars"), 1024, "PARAM_WINDOW")
    _require(config.get("location_hash_window_chars"), 4096, "HASH_WINDOW")
    _require(config.get("format_window_chars"), 16384, "FORMAT_WINDOW")
    _require(config.get("odata_window_chars"), 65536, "ODATA_WINDOW")
    _require(config.get("primary_family_tokens"), ["location.hash", "ngRoute", "$routeProvider"], "FAMILY_TOKENS")
    _require(config.get("known_contract_tokens"), ["/odata/", "$format"], "CONTRACT_TOKENS")
    _require(config.get("returned_count_fields"), COUNT_FIELDS, "FIELDS")
    _require(config.get("observation_semantics"), "LOCATION_HASH_FAMILY_ONLY_NEAREST_TOKEN_SIDE_CATEGORIES_AND_SAME_SIDE_INTEGER_COUNTS_WITHOUT_OFFSETS", "SEMANTICS")
    for key in (
        "new_script_network_request", "script_source_return", "script_source_persistence", "script_url_return", "script_id_return",
        "source_snippet_return", "source_offset_return", "fragment_value_capture", "dom_text_return", "html_capture",
        "response_body_capture", "request_body_capture", "query_value_persistence", "dynamic_candidate_network_send",
        "resource_data_request", "pilot_limeira_values_send", "dom_interaction", "navigation_execution", "history_state_mutation",
        "form_submission", "post_request_send", "head_request", "authentication", "captcha_bypass", "credential_capture",
        "cookie_capture", "artifact_download", "remote_writes", "route_synthesis_or_guessing", "automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOCATION_HASH_ODATA_SIDE_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"], "software_version": config["software_version"], "design_mode": config["mode"],
        "observation_semantics": config["observation_semantics"], "returned_observations": COUNT_FIELDS,
        "family_classification_window_chars": 4096, "parameter_window_chars": 1024,
        "location_hash_window_chars": 4096, "format_window_chars": 16384, "odata_window_chars": 65536,
        "network_called": False, "fragment_value_read_authorized": False, "navigation_execution_authorized": False,
        "history_state_mutation_authorized": False, "new_script_network_request_authorized": False,
        "script_source_transient_read_authorized": True, "resource_get_authorized": False, "collection_authorized": False,
        "processing_authorized": False, "recurrence_authorized": False, "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
