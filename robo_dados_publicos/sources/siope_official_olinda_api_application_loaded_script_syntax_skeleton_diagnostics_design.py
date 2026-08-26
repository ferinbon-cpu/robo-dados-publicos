from __future__ import annotations

import json
from pathlib import Path

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SYNTAX_SKELETON_DIAGNOSTICS_DESIGN"


class SiopeOfficialOlindaApiApplicationLoadedScriptSyntaxSkeletonDiagnosticsDesignError(RuntimeError):
    pass


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSyntaxSkeletonDiagnosticsDesignError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSyntaxSkeletonDiagnosticsDesignError(f"{ERROR}_{code}")


def run_design(config: dict, locality_review: dict) -> dict:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SYNTAX_SKELETON_DIAGNOSTICS_DESIGN_0_8_0", "GATE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("mode"), "OFFLINE_BOUNDED_KNOWN_SYNTAX_SKELETON_COUNT_DIAGNOSTICS_DESIGN", "MODE")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMS")
    _require(config.get("known_contract_tokens"), ["/odata/", "$format"], "TOKENS")
    _require(config.get("analysis_window_chars"), 4096, "WINDOW")
    _require(config.get("parameter_sequence_window_chars"), 512, "PARAM_WINDOW")
    _require(len(config.get("returned_observations") or []), 19, "OBSERVATION_COUNT")
    _require(locality_review.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_LOCALITY_DIAGNOSTICS_REVIEW", "LOCALITY_REVIEW")
    _require(locality_review.get("parameter_locality_status"), "PROVEN_ALL_FOUR_CALLABLE_OCCURRENCES_HAVE_ALL_THREE_PARAMETER_NAMES_AND_LITERALS_WITHIN_1024_CHARS", "PARAM_LOCALITY")
    _require(locality_review.get("executable_call_syntax_status"), "UNPROVEN", "SYNTAX_UNPROVEN")
    _require(locality_review.get("resource_route_contract_status"), "UNPROVEN", "ROUTE_UNPROVEN")
    for key in (
        "script_source_return_authorized", "script_source_persistence_authorized", "script_url_return_authorized",
        "script_id_return_authorized", "source_snippet_return_authorized", "source_offset_return_authorized",
        "new_script_network_request_authorized", "resource_data_request_authorized",
        "pilot_limeira_values_send_authorized", "dom_interaction_authorized", "navigation_execution_authorized",
        "route_synthesis_or_guessing_authorized", "automatic_route_promotion", "resource_get_authorized",
        "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled",
    ):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")
    _require(config.get("script_source_transient_read"), "ALLOWED_EPHEMERAL_MEMORY_ONLY_AFTER_SCRIPT_ALREADY_LOADED", "TRANSIENT_READ")
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SYNTAX_SKELETON_DIAGNOSTICS_DESIGN",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "design_mode": config["mode"],
        "observation_semantics": "TRANSIENT_ALREADY_LOADED_SCRIPT_KNOWN_SYNTAX_SKELETON_INTEGER_COUNTS_ONLY",
        "analysis_window_chars": config["analysis_window_chars"],
        "parameter_sequence_window_chars": config["parameter_sequence_window_chars"],
        "returned_observations": config["returned_observations"],
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
