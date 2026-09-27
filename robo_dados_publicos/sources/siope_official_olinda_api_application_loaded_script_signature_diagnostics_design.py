from __future__ import annotations

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_DESIGN"


class SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsDesignError(RuntimeError):
    pass


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsDesignError(f"{ERROR}_{code}")


def run_design(config: dict, navigation_distribution_review: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_DESIGN_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("network_called"), False, "NETWORK")
    _require(navigation_distribution_review.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS_REVIEW", "REVIEW")
    _require(navigation_distribution_review.get("navigation_attribute_strategy_status"), "EXHAUSTED_FOR_RESOURCE_ROUTE_ON_PINNED_RUN", "NAV_STRATEGY")
    _require(navigation_distribution_review.get("resource_route_contract_status"), "UNPROVEN", "ROUTE")
    _require(navigation_distribution_review.get("callable_semantics_status"), "UNPROVEN", "CALLABLE_SEMANTICS")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("service_document_declared_name"), "_Dados_Gerais_Siope", "SERVICE_NAME")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMS")
    _require(config.get("known_contract_tokens"), ["/odata/", "$format"], "TOKENS")
    if config.get("max_parsed_scripts") != 128 or config.get("max_callable_occurrences") != 128:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsDesignError(f"{ERROR}_COUNT_LIMITS")
    if config.get("max_source_bytes_per_script") != 5000000 or config.get("max_total_source_bytes") != 32000000:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsDesignError(f"{ERROR}_BYTE_LIMITS")
    _require(config.get("local_window_chars"), 1024, "WINDOW")
    _require(config.get("future_runtime_backend"), "SYSTEM_CHROME_CDP_DEBUGGER_ALREADY_LOADED_SCRIPTS_ONLY", "BACKEND")
    _require(config.get("future_script_source_transient_read"), "ALLOWED_EPHEMERAL_MEMORY_ONLY_AFTER_SCRIPT_ALREADY_LOADED", "TRANSIENT_READ")
    for key in (
        "future_new_script_network_request",
        "future_script_source_return",
        "future_script_source_persistence",
        "future_script_url_return",
        "future_script_id_return",
        "future_source_snippet_return",
        "future_source_offset_return",
        "future_response_body_capture",
        "future_request_body_capture",
        "future_query_value_persistence",
        "future_dynamic_candidate_network_send",
        "future_resource_data_request",
        "future_pilot_limeira_values_send",
        "future_dom_interaction",
        "future_navigation_execution",
        "future_form_submission",
        "future_post_request_send",
        "future_head_request",
        "future_authentication",
        "future_captcha_bypass",
        "future_credential_capture",
        "future_cookie_capture",
        "future_artifact_download",
        "future_remote_writes",
        "future_route_synthesis_or_guessing",
        "future_automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", key.upper())
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, key.upper())

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "observation_semantics": "TRANSIENT_ALREADY_LOADED_SCRIPT_SOURCE_SCAN_WITH_BOUNDED_INTEGER_COUNTS_ONLY",
        "known_public_identifiers": [config["technical_callable_pattern_name"], config["service_document_declared_name"], *config["technical_parameter_names"], *config["known_contract_tokens"]],
        "returned_observations": config["returned_count_fields"],
        "script_source_transient_read_scope": config["future_script_source_transient_read"],
        "new_script_network_request_authorized": False,
        "script_source_return_authorized": False,
        "script_source_persistence_authorized": False,
        "script_url_return_authorized": False,
        "source_snippet_return_authorized": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
