from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_GLOBAL_RELATION_DIAGNOSTICS_DESIGN"


class SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsDesignError(f"{ERROR}_{code}")


def run_design(config: dict, review_result: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_GLOBAL_RELATION_DIAGNOSTICS_DESIGN_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_SAME_SCRIPT_GLOBAL_RELATION_COUNT_DIAGNOSTICS_DESIGN", "MODE")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("service_document_declared_name"), "_Dados_Gerais_Siope", "SERVICE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMS")
    _require(config.get("known_contract_tokens"), ["/odata/", "$format"], "TOKENS")
    _require(review_result.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_REVIEW", "REVIEW")
    _require(review_result.get("local_executable_contract_status"), "NOT_OBSERVED_NO_PAREN_QUERY_AT_PARAMS_ODATA_OR_FORMAT_TOKEN", "LOCAL_CONTRACT")
    _require(review_result.get("resource_route_contract_status"), "UNPROVEN", "ROUTE")
    _require(review_result.get("callable_semantics_status"), "STRUCTURAL_NAME_PARAMETER_BINDING_CORROBORATED_EXECUTABLE_CALL_SYNTAX_UNPROVEN", "SEMANTICS")
    for key in (
        "script_source_return_authorized", "script_source_persistence_authorized", "script_url_return_authorized",
        "script_id_return_authorized", "source_snippet_return_authorized", "source_offset_return_authorized",
        "new_script_network_request_authorized", "resource_data_request_authorized", "pilot_limeira_values_send_authorized",
        "dom_interaction_authorized", "navigation_execution_authorized", "route_synthesis_or_guessing_authorized",
        "automatic_route_promotion", "resource_get_authorized", "collection_authorized", "processing_authorized",
        "recurrence_authorized", "schedule_enabled",
    ):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")
    returned = config.get("returned_observations")
    if not isinstance(returned, list) or len(returned) != 16 or len(set(returned)) != 16:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsDesignError(f"{ERROR}_RETURNED_OBSERVATIONS")
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_GLOBAL_RELATION_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "observation_semantics": "ALREADY_LOADED_SCRIPT_WHOLE_SOURCE_KNOWN_IDENTIFIER_RELATION_COUNTS_ONLY",
        "returned_observations": returned,
        "script_source_transient_read": config["script_source_transient_read"],
        "script_source_return_authorized": False,
        "script_source_persistence_authorized": False,
        "new_script_network_request_authorized": False,
        "resource_data_request_authorized": False,
        "pilot_limeira_values_send_authorized": False,
        "dom_interaction_authorized": False,
        "navigation_execution_authorized": False,
        "route_synthesis_or_guessing_authorized": False,
        "automatic_route_promotion": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "resource_route_contract_status": "UNPROVEN",
        "next_gate": config["next_gate"],
    }
