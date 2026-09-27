from __future__ import annotations

import re
from pathlib import Path

from . import siope_official_olinda_api_application_loaded_script_signature_diagnostics as base

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_GLOBAL_RELATION_DIAGNOSTICS"
COUNT_FIELDS = [
    "parsed_script_count",
    "source_read_count",
    "source_read_failure_count",
    "callable_occurrence_count",
    "callable_exact_string_literal_occurrence_count",
    "callable_name_script_count",
    "service_document_name_script_count",
    "both_names_same_script_count",
    "callable_and_all_parameter_names_same_script_count",
    "callable_and_all_parameter_exact_string_literals_same_script_count",
    "callable_and_all_at_parameter_names_same_script_count",
    "callable_and_odata_literal_same_script_count",
    "callable_and_format_token_same_script_count",
    "callable_and_odata_and_format_same_script_count",
    "callable_and_all_parameter_names_and_odata_and_format_same_script_count",
    "callable_and_all_at_params_and_odata_and_format_same_script_count",
]


class SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def load_json(path: str | Path) -> dict:
    return base.load_json(path)


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(f"{ERROR}_{code}")


def _empty_counts() -> dict[str, int]:
    return {field: 0 for field in COUNT_FIELDS}


def _is_exact_string_literal(source: str, match: re.Match[str]) -> bool:
    if match.start() < 1 or match.end() >= len(source):
        return False
    quote = source[match.start() - 1]
    return quote in {"'", '"', '`'} and source[match.end()] == quote


def _token_has_exact_string_literal(source: str, token: str) -> bool:
    return any(_is_exact_string_literal(source, match) for match in base._identifier_pattern(token).finditer(source))


def _analyze_source_into_counts(source: str, config: dict, counts: dict[str, int]) -> None:
    callable_name = config["technical_callable_pattern_name"]
    service_name = config["service_document_declared_name"]
    params = list(config["technical_parameter_names"])
    callable_matches = list(base._identifier_pattern(callable_name).finditer(source))
    callable_present = bool(callable_matches)
    service_present = bool(base._identifier_pattern(service_name).search(source))
    counts["callable_occurrence_count"] += len(callable_matches)
    counts["callable_exact_string_literal_occurrence_count"] += sum(
        1 for match in callable_matches if _is_exact_string_literal(source, match)
    )
    if callable_present:
        counts["callable_name_script_count"] += 1
    if service_present:
        counts["service_document_name_script_count"] += 1
    if callable_present and service_present:
        counts["both_names_same_script_count"] += 1
    if not callable_present:
        return

    all_params = all(base._identifier_pattern(value).search(source) is not None for value in params)
    all_param_literals = all(_token_has_exact_string_literal(source, value) for value in params)
    all_at_params = all(("@" + value) in source for value in params)
    odata_literal = config["known_contract_tokens"][0] in source
    format_token = config["known_contract_tokens"][1] in source

    if all_params:
        counts["callable_and_all_parameter_names_same_script_count"] += 1
    if all_param_literals:
        counts["callable_and_all_parameter_exact_string_literals_same_script_count"] += 1
    if all_at_params:
        counts["callable_and_all_at_parameter_names_same_script_count"] += 1
    if odata_literal:
        counts["callable_and_odata_literal_same_script_count"] += 1
    if format_token:
        counts["callable_and_format_token_same_script_count"] += 1
    if odata_literal and format_token:
        counts["callable_and_odata_and_format_same_script_count"] += 1
    if all_params and odata_literal and format_token:
        counts["callable_and_all_parameter_names_and_odata_and_format_same_script_count"] += 1
    if all_at_params and odata_literal and format_token:
        counts["callable_and_all_at_params_and_odata_and_format_same_script_count"] += 1


def validate_config(config: dict, design_result: dict) -> None:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_GLOBAL_RELATION_DIAGNOSTICS_0_8_0", "GATE")
    _require(config.get("mode"), "PASSIVE_ALREADY_LOADED_SCRIPT_GLOBAL_RELATION_DIAGNOSTICS", "MODE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("service_document_declared_name"), "_Dados_Gerais_Siope", "SERVICE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMS")
    _require(config.get("known_contract_tokens"), ["/odata/", "$format"], "TOKENS")
    _require(config.get("returned_count_fields"), COUNT_FIELDS, "FIELDS")
    _require(config.get("max_parsed_scripts"), 128, "MAX_SCRIPTS")
    _require(config.get("max_callable_occurrences"), 128, "MAX_OCCURRENCES")
    _require(config.get("max_source_bytes_per_script"), 5000000, "MAX_SCRIPT_BYTES")
    _require(config.get("max_total_source_bytes"), 32000000, "MAX_TOTAL_BYTES")
    _require(design_result.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_GLOBAL_RELATION_DIAGNOSTICS_DESIGN", "DESIGN")
    _require(design_result.get("returned_observations"), COUNT_FIELDS, "DESIGN_FIELDS")
    for key in (
        "new_script_network_request", "script_source_return", "script_source_persistence", "script_url_return",
        "script_id_return", "source_snippet_return", "source_offset_return", "dom_text_return",
        "fragment_value_capture", "html_capture", "response_body_capture", "request_body_capture",
        "query_value_persistence", "dynamic_candidate_network_send", "resource_data_request",
        "pilot_limeira_values_send", "dom_interaction", "navigation_execution", "form_submission",
        "post_request_send", "head_request", "authentication", "captcha_bypass", "credential_capture",
        "cookie_capture", "artifact_download", "remote_writes", "route_synthesis_or_guessing", "automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")


def _validate_counts(counts: dict, config: dict) -> None:
    if set(counts) != set(COUNT_FIELDS):
        raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(f"{ERROR}_COUNT_FIELDS")
    for key, value in counts.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(f"{ERROR}_COUNT_TYPE_{key.upper()}")
    if not (1 <= counts["parsed_script_count"] <= config["max_parsed_scripts"]):
        raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(f"{ERROR}_PARSED_SCRIPT_COUNT")
    if counts["source_read_count"] + counts["source_read_failure_count"] != counts["parsed_script_count"]:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(f"{ERROR}_SOURCE_PARTITION")
    if counts["source_read_count"] < 1:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(f"{ERROR}_SOURCE_READ_ZERO")
    if counts["callable_occurrence_count"] > config["max_callable_occurrences"]:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(f"{ERROR}_CALLABLE_COUNT")
    if counts["callable_exact_string_literal_occurrence_count"] > counts["callable_occurrence_count"]:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(f"{ERROR}_CALLABLE_LITERAL_COUNT")
    for key in ("callable_name_script_count", "service_document_name_script_count", "both_names_same_script_count"):
        if counts[key] > counts["source_read_count"]:
            raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(f"{ERROR}_SCRIPT_RELATION_{key.upper()}")
    for key in COUNT_FIELDS[8:]:
        if counts[key] > counts["callable_name_script_count"]:
            raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(f"{ERROR}_CALLABLE_SCRIPT_RELATION_{key.upper()}")


def _run_probe_with_global_analyzer(config: dict, runtime=None) -> dict:
    if runtime is not None:
        return runtime.run_probe(config)
    original_empty = base._empty_counts
    original_analyze = base._analyze_source_into_counts
    base._empty_counts = _empty_counts
    base._analyze_source_into_counts = _analyze_source_into_counts
    try:
        return base.SystemChromeCdpLoadedScriptSignatureRuntime().run_probe(config)
    except base.SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError as exc:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(
            f"{ERROR}_BASE_RUNTIME_{str(exc)}", diagnostics=getattr(exc, "diagnostics", {})
        ) from None
    finally:
        base._empty_counts = original_empty
        base._analyze_source_into_counts = original_analyze


def dry_run(config: dict, design_result: dict) -> dict:
    validate_config(config, design_result)
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_GLOBAL_RELATION_DIAGNOSTICS_DRY_RUN",
        "gate_id": config["gate_id"],
        "network_called": False,
        "script_source_transient_read_performed": False,
        "script_source_returned": False,
        "script_source_persisted": False,
        "new_script_network_request_performed": False,
        "dynamic_candidate_network_sent": False,
        "pilot_limeira_values_sent": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def run_global_relation_diagnostics(config: dict, design_result: dict, *, runtime=None) -> dict:
    validate_config(config, design_result)
    probe = _run_probe_with_global_analyzer(config, runtime=runtime)
    _require(probe.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(probe.get("application_surface_verified"), True, "SURFACE")
    _require(probe.get("browser_download_denied"), True, "DOWNLOAD_DENIAL")
    _require(probe.get("script_source_transient_read_performed"), True, "TRANSIENT_READ")
    counts = probe.get("loaded_script_signature_counts") or {}
    _validate_counts(counts, config)
    shapes = probe.get("blocked_shapes") or []
    candidates = probe.get("candidate_shapes") or []
    if any(shape.get("network_sent") for shape in shapes):
        raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(f"{ERROR}_BLOCKED_NETWORK_SENT")
    if candidates:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptGlobalRelationDiagnosticsError(
            f"{ERROR}_UNEXPECTED_DYNAMIC_CANDIDATE", diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates}
        )
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_GLOBAL_RELATION_DIAGNOSTICS",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "runtime_status": "BOUNDED_TRANSIENT_ALREADY_LOADED_SCRIPT_GLOBAL_RELATION_COUNTS_OBSERVED_WITH_UNAPPROVED_NETWORK_BLOCKED",
        "application_surface_verified": True,
        "fragment_present": bool(probe.get("fragment_present")),
        "loaded_script_global_relation_counts": counts,
        "initial_document_continued_count": 1,
        "official_static_asset_network_sent_count": int(probe.get("static_assets_continued_count", 0)),
        "local_request_count": int(probe.get("local_requests_continued_count", 0)),
        "blocked_shape_count": len(shapes),
        "blocked_shapes": shapes,
        "candidate_shape_count": 0,
        "candidate_shapes": [],
        "initial_document_network_sent": True,
        "dynamic_candidate_network_sent": False,
        "script_source_transient_read_performed": True,
        "script_source_returned": False,
        "script_source_persisted": False,
        "script_url_returned": False,
        "script_id_returned": False,
        "source_snippet_returned": False,
        "source_offset_returned": False,
        "new_script_network_request_performed": False,
        "dom_interaction_performed": False,
        "navigation_executed": False,
        "pilot_limeira_values_sent": False,
        "resource_data_request_performed": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "form_submission": False,
        "post_request_performed": False,
        "head_request_performed": False,
        "authentication_performed": False,
        "captcha_bypass": False,
        "credentials_captured": False,
        "cookies_captured": False,
        "artifact_downloaded": False,
        "browser_download_denied": True,
        "dom_text_returned": False,
        "fragment_value_returned": False,
        "html_returned": False,
        "response_body_persisted": False,
        "request_body_persisted": False,
        "query_values_persisted": False,
        "remote_writes": "NONE",
        "route_synthesized_or_guessed": False,
        "automatic_route_promotion": False,
        "next_gate": config["next_gate"],
    }
