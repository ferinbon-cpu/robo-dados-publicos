from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from . import siope_official_olinda_api_application_loaded_script_signature_diagnostics as base
from .siope_official_olinda_api_application_hash_routing_signal_diagnostics_design import COUNT_FIELDS

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS"


class SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def load_json(path: str | Path) -> dict:
    return base.load_json(path)


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(f"{ERROR}_{code}")


def _empty_counts() -> dict[str, int]:
    return {field: 0 for field in COUNT_FIELDS}


def _analyze_source_into_counts(source: str, config: dict, counts: dict[str, int]) -> None:
    callable_name = config["technical_callable_pattern_name"]
    service_name = config["service_document_declared_name"]
    params = list(config["technical_parameter_names"])
    token_to_field = {
        "hashchange": "hashchange_token_occurrence_count",
        "location.hash": "location_hash_token_occurrence_count",
        "onhashchange": "onhashchange_token_occurrence_count",
        "$routeProvider": "route_provider_token_occurrence_count",
        "ngRoute": "ngroute_token_occurrence_count",
        "hashPrefix": "hash_prefix_token_occurrence_count",
        "$locationProvider": "location_provider_token_occurrence_count",
    }
    token_counts = {token: source.count(token) for token in config["known_routing_tokens"]}
    for token, field in token_to_field.items():
        counts[field] += token_counts[token]
    routing_present = any(value > 0 for value in token_counts.values())
    callable_present = base._identifier_pattern(callable_name).search(source) is not None
    service_present = base._identifier_pattern(service_name).search(source) is not None
    all_params = all(base._identifier_pattern(value).search(source) is not None for value in params)
    if routing_present:
        counts["routing_signal_script_count"] += 1
    if callable_present:
        counts["callable_name_script_count"] += 1
    if callable_present and routing_present:
        counts["callable_and_routing_signal_same_script_count"] += 1
    if all_params and routing_present:
        counts["all_parameter_names_and_routing_signal_same_script_count"] += 1
    if service_present and routing_present:
        counts["service_document_name_and_routing_signal_same_script_count"] += 1
    if callable_present and all_params and routing_present:
        counts["callable_parameter_and_routing_signal_same_script_count"] += 1


def validate_config(config: dict, design_result: dict) -> None:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS_0_8_0", "GATE")
    _require(config.get("mode"), "PASSIVE_ALREADY_LOADED_SCRIPT_HASH_ROUTING_SIGNAL_DIAGNOSTICS", "MODE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("service_document_declared_name"), "_Dados_Gerais_Siope", "SERVICE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMS")
    _require(config.get("known_routing_tokens"), ["hashchange", "location.hash", "onhashchange", "$routeProvider", "ngRoute", "hashPrefix", "$locationProvider"], "TOKENS")
    _require(config.get("returned_count_fields"), COUNT_FIELDS, "FIELDS")
    _require(config.get("max_parsed_scripts"), 128, "MAX_SCRIPTS")
    _require(config.get("max_source_bytes_per_script"), 5000000, "MAX_SCRIPT_BYTES")
    _require(config.get("max_total_source_bytes"), 32000000, "MAX_TOTAL_BYTES")
    _require(config.get("script_source_transient_read"), "ALLOWED_EPHEMERAL_MEMORY_ONLY_AFTER_SCRIPT_ALREADY_LOADED", "TRANSIENT")
    _require(config.get("script_source_read_method"), "CDP_DEBUGGER_GET_SCRIPT_SOURCE_FOR_ALREADY_PARSED_SCRIPT_IDS_ONLY", "READ_METHOD")
    _require(design_result.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS_DESIGN", "DESIGN")
    _require(design_result.get("returned_observations"), COUNT_FIELDS, "DESIGN_FIELDS")
    _require(design_result.get("fragment_value_read_authorized"), False, "DESIGN_FRAGMENT")
    _require(design_result.get("navigation_execution_authorized"), False, "DESIGN_NAV")
    parsed = urlparse(config["exact_application_url"])
    _require(parsed.scheme, config["expected_scheme"], "SCHEME")
    _require(parsed.hostname, config["expected_host"], "HOST")
    _require(parsed.path, config["expected_path"], "PATH")
    _require(parsed.query, "", "QUERY")
    _require(parsed.fragment, "", "FRAGMENT")
    if "352690" in config["exact_application_url"] or "Limeira" in config["exact_application_url"]:
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(f"{ERROR}_PILOT_VALUE")
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


def _validate_counts(counts: dict, config: dict) -> None:
    if set(counts) != set(COUNT_FIELDS):
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(f"{ERROR}_COUNT_FIELDS")
    for key, value in counts.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(f"{ERROR}_COUNT_TYPE_{key.upper()}")
    if not (1 <= counts["parsed_script_count"] <= config["max_parsed_scripts"]):
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(f"{ERROR}_PARSED_SCRIPT_COUNT")
    if counts["source_read_count"] + counts["source_read_failure_count"] != counts["parsed_script_count"]:
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(f"{ERROR}_SOURCE_PARTITION")
    if counts["source_read_count"] < 1:
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(f"{ERROR}_SOURCE_READ_ZERO")
    for key in (
        "routing_signal_script_count", "callable_name_script_count",
        "callable_and_routing_signal_same_script_count",
        "all_parameter_names_and_routing_signal_same_script_count",
        "service_document_name_and_routing_signal_same_script_count",
        "callable_parameter_and_routing_signal_same_script_count",
    ):
        if counts[key] > counts["source_read_count"]:
            raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(f"{ERROR}_SCRIPT_RELATION_{key.upper()}")
    for key in ("callable_and_routing_signal_same_script_count", "callable_parameter_and_routing_signal_same_script_count"):
        if counts[key] > min(counts["callable_name_script_count"], counts["routing_signal_script_count"]):
            raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(f"{ERROR}_SUBSET_{key.upper()}")
    if counts["callable_parameter_and_routing_signal_same_script_count"] > counts["all_parameter_names_and_routing_signal_same_script_count"]:
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(f"{ERROR}_PARAM_SUBSET")


def _run_probe(config: dict, runtime=None) -> dict:
    if runtime is not None:
        return runtime.run_probe(config)
    original_empty = base._empty_counts
    original_analyze = base._analyze_source_into_counts
    base._empty_counts = _empty_counts
    base._analyze_source_into_counts = _analyze_source_into_counts
    try:
        return base.SystemChromeCdpLoadedScriptSignatureRuntime().run_probe(config)
    except base.SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError as exc:
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(
            f"{ERROR}_BASE_RUNTIME_{str(exc)}", diagnostics=getattr(exc, "diagnostics", {})
        ) from None
    finally:
        base._empty_counts = original_empty
        base._analyze_source_into_counts = original_analyze


def dry_run(config: dict, design_result: dict) -> dict:
    validate_config(config, design_result)
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS_DRY_RUN",
        "gate_id": config["gate_id"],
        "network_called": False,
        "script_source_transient_read_performed": False,
        "fragment_value_read_performed": False,
        "navigation_executed": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def run_hash_routing_signal_diagnostics(config: dict, design_result: dict, *, runtime=None) -> dict:
    validate_config(config, design_result)
    probe = _run_probe(config, runtime=runtime)
    _require(probe.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT")
    _require(probe.get("application_surface_verified"), True, "SURFACE")
    _require(probe.get("browser_download_denied"), True, "DOWNLOAD_DENIED")
    _require(probe.get("script_source_transient_read_performed"), True, "TRANSIENT_READ")
    counts = probe.get("loaded_script_signature_counts") or {}
    _validate_counts(counts, config)
    shapes = probe.get("blocked_shapes") or []
    candidates = probe.get("candidate_shapes") or []
    if any(shape.get("network_sent") for shape in shapes):
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(f"{ERROR}_BLOCKED_NETWORK_SENT")
    if candidates:
        raise SiopeOfficialOlindaApiApplicationHashRoutingSignalDiagnosticsError(
            f"{ERROR}_UNEXPECTED_DYNAMIC_CANDIDATE", diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates}
        )
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_HASH_ROUTING_SIGNAL_DIAGNOSTICS",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "runtime_status": "BOUNDED_TRANSIENT_ALREADY_LOADED_SCRIPT_HASH_ROUTING_SIGNAL_COUNTS_OBSERVED_WITH_UNAPPROVED_NETWORK_BLOCKED",
        "application_surface_verified": True,
        "fragment_present": bool(probe.get("fragment_present")),
        "hash_routing_signal_counts": counts,
        "initial_document_continued_count": 1,
        "official_static_asset_network_sent_count": int(probe.get("static_assets_continued_count", 0)),
        "local_request_count": int(probe.get("local_requests_continued_count", 0)),
        "blocked_shape_count": len(shapes),
        "blocked_shapes": shapes,
        "candidate_shape_count": 0,
        "candidate_shapes": [],
        "safety": {
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
            "fragment_value_read_performed": False,
            "fragment_value_returned": False,
            "dom_interaction_performed": False,
            "navigation_executed": False,
            "history_state_mutated": False,
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
            "html_returned": False,
            "response_body_persisted": False,
            "request_body_persisted": False,
            "query_values_persisted": False,
            "remote_writes": "NONE",
            "route_synthesized_or_guessed": False,
            "automatic_route_promotion": False
        },
        "next_review": config["next_review"]
    }
