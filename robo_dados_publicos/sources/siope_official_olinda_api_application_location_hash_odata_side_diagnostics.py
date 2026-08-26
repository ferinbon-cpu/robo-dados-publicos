from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from . import siope_official_olinda_api_application_loaded_script_signature_diagnostics as base
from .siope_official_olinda_api_application_hash_routing_contract_association_diagnostics import _classify_family
from .siope_official_olinda_api_application_location_hash_odata_side_diagnostics_design import COUNT_FIELDS

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOCATION_HASH_ODATA_SIDE_DIAGNOSTICS"

class SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}

def load_json(path: str | Path) -> dict:
    return base.load_json(path)

def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(f"{ERROR}_{code}")

def _empty_counts() -> dict[str, int]:
    return {field: 0 for field in COUNT_FIELDS}

def _token_positions(source: str, token: str, lo: int, hi: int) -> list[int]:
    positions: list[int] = []
    pos = source.find(token, lo, hi)
    while pos != -1:
        positions.append(pos)
        pos = source.find(token, pos + 1, hi)
    return positions

def _nearest_side(source: str, match, token: str, radius: int) -> str:
    lo = max(0, match.start() - radius)
    hi = min(len(source), match.end() + radius)
    left: list[int] = []
    right: list[int] = []
    for pos in _token_positions(source, token, lo, hi):
        end = pos + len(token)
        if end <= match.start():
            left.append(match.start() - end)
        elif pos >= match.end():
            right.append(pos - match.end())
    if not left and not right:
        return "none"
    left_min = min(left) if left else None
    right_min = min(right) if right else None
    if left_min is None:
        return "right"
    if right_min is None:
        return "left"
    if left_min == right_min:
        return "tie"
    return "left" if left_min < right_min else "right"

def _analyze_source_into_counts(source: str, config: dict, counts: dict[str, int]) -> None:
    callable_name = config["technical_callable_pattern_name"]
    params = list(config["technical_parameter_names"])
    matches = list(base._identifier_pattern(callable_name).finditer(source))
    counts["callable_occurrence_count"] += len(matches)
    if counts["callable_occurrence_count"] > config["max_callable_occurrences"]:
        raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(f"{ERROR}_CALLABLE_OCCURRENCE_LIMIT")

    family_radius = int(config["family_classification_window_chars"])
    param_radius = int(config["parameter_window_chars"])
    for match in matches:
        family_window = source[max(0, match.start() - family_radius):min(len(source), match.end() + family_radius)]
        family = _classify_family(family_window)
        if family == "location_hash":
            counts["location_hash_family_count"] += 1
        elif family == "ngroute":
            counts["ngroute_family_count"] += 1
        else:
            counts["ambiguous_family_count"] += 1
            continue

        if family != "location_hash":
            continue
        param_window = source[max(0, match.start() - param_radius):min(len(source), match.end() + param_radius)]
        if all(base._identifier_pattern(name).search(param_window) is not None for name in params):
            counts["location_hash_family_all_parameter_names_1024_count"] += 1

        hash_side = _nearest_side(source, match, "location.hash", int(config["location_hash_window_chars"]))
        format_side = _nearest_side(source, match, "$format", int(config["format_window_chars"]))
        odata_side = _nearest_side(source, match, "/odata/", int(config["odata_window_chars"]))

        if hash_side == "none":
            raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(f"{ERROR}_LOCATION_HASH_FAMILY_WITHOUT_HASH_TOKEN")
        counts[f"location_hash_token_nearest_{hash_side}_4096_count"] += 1
        if format_side == "none":
            counts["format_absent_16384_count"] += 1
        else:
            counts[f"format_nearest_{format_side}_16384_count"] += 1
        if odata_side == "none":
            counts["odata_absent_65536_count"] += 1
        else:
            counts[f"odata_nearest_{odata_side}_65536_count"] += 1

        if hash_side in {"left", "right"} and hash_side == format_side:
            counts["nearest_location_hash_and_format_same_side_count"] += 1
        if format_side in {"left", "right"} and format_side == odata_side:
            counts["nearest_format_and_odata_same_side_count"] += 1
        if hash_side in {"left", "right"} and hash_side == format_side == odata_side:
            counts["nearest_all_three_same_side_count"] += 1
            counts[f"nearest_all_three_{hash_side}_count"] += 1

def validate_config(config: dict, design_result: dict) -> None:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOCATION_HASH_ODATA_SIDE_DIAGNOSTICS_0_8_0", "GATE")
    _require(config.get("mode"), "PASSIVE_ALREADY_LOADED_SCRIPT_LOCATION_HASH_ODATA_NEAREST_SIDE_DIAGNOSTICS", "MODE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
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
    _require(config.get("max_parsed_scripts"), 128, "MAX_SCRIPTS")
    _require(config.get("max_callable_occurrences"), 128, "MAX_OCCURRENCES")
    _require(config.get("max_source_bytes_per_script"), 5000000, "MAX_SCRIPT_BYTES")
    _require(config.get("max_total_source_bytes"), 32000000, "MAX_TOTAL_BYTES")
    _require(config.get("script_source_transient_read"), "ALLOWED_EPHEMERAL_MEMORY_ONLY_AFTER_SCRIPT_ALREADY_LOADED", "TRANSIENT")
    _require(config.get("script_source_read_method"), "CDP_DEBUGGER_GET_SCRIPT_SOURCE_FOR_ALREADY_PARSED_SCRIPT_IDS_ONLY", "READ_METHOD")
    _require(design_result.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOCATION_HASH_ODATA_SIDE_DIAGNOSTICS_DESIGN", "DESIGN")
    _require(design_result.get("returned_observations"), COUNT_FIELDS, "DESIGN_FIELDS")
    parsed = urlparse(config["exact_application_url"])
    _require(parsed.scheme, config["expected_scheme"], "SCHEME")
    _require(parsed.hostname, config["expected_host"], "HOST")
    _require(parsed.path, config["expected_path"], "PATH")
    _require(parsed.query, "", "QUERY")
    _require(parsed.fragment, "", "FRAGMENT")
    if "352690" in config["exact_application_url"] or "Limeira" in config["exact_application_url"]:
        raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(f"{ERROR}_PILOT_VALUE")
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

def _validate_counts(counts: dict, config: dict) -> None:
    if set(counts) != set(COUNT_FIELDS):
        raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(f"{ERROR}_COUNT_FIELDS")
    for key, value in counts.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(f"{ERROR}_COUNT_TYPE_{key.upper()}")
    if not (1 <= counts["parsed_script_count"] <= config["max_parsed_scripts"]):
        raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(f"{ERROR}_PARSED_SCRIPT_COUNT")
    if counts["source_read_count"] + counts["source_read_failure_count"] != counts["parsed_script_count"]:
        raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(f"{ERROR}_SOURCE_PARTITION")
    _require(counts["callable_occurrence_count"], 4, "CALLABLE_COUNT_DRIFT")
    _require(counts["location_hash_family_count"], 2, "LOCATION_HASH_FAMILY_DRIFT")
    _require(counts["ngroute_family_count"], 2, "NGROUTE_FAMILY_DRIFT")
    _require(counts["ambiguous_family_count"], 0, "AMBIGUOUS_FAMILY")
    _require(counts["location_hash_family_all_parameter_names_1024_count"], 2, "PARAMETER_DRIFT")
    _require(counts["location_hash_token_nearest_left_4096_count"] + counts["location_hash_token_nearest_right_4096_count"] + counts["location_hash_token_nearest_tie_4096_count"], 2, "HASH_SIDE_PARTITION")
    _require(counts["format_nearest_left_16384_count"] + counts["format_nearest_right_16384_count"] + counts["format_nearest_tie_16384_count"] + counts["format_absent_16384_count"], 2, "FORMAT_SIDE_PARTITION")
    _require(counts["odata_nearest_left_65536_count"] + counts["odata_nearest_right_65536_count"] + counts["odata_nearest_tie_65536_count"] + counts["odata_absent_65536_count"], 2, "ODATA_SIDE_PARTITION")
    _require(counts["format_absent_16384_count"], 0, "FORMAT_LOCALITY_DRIFT")
    _require(counts["odata_absent_65536_count"], 0, "ODATA_LOCALITY_DRIFT")
    if counts["nearest_all_three_same_side_count"] > min(counts["nearest_location_hash_and_format_same_side_count"], counts["nearest_format_and_odata_same_side_count"]):
        raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(f"{ERROR}_ALL_THREE_SUBSET")
    _require(counts["nearest_all_three_left_count"] + counts["nearest_all_three_right_count"], counts["nearest_all_three_same_side_count"], "ALL_THREE_SIDE_PARTITION")
    for field in COUNT_FIELDS[8:]:
        if counts[field] > 2:
            raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(f"{ERROR}_{field.upper()}_GT_LOCATION_HASH_FAMILY")

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
        raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(
            f"{ERROR}_BASE_RUNTIME_{str(exc)}", diagnostics=getattr(exc, "diagnostics", {})
        ) from None
    finally:
        base._empty_counts = original_empty
        base._analyze_source_into_counts = original_analyze

def dry_run(config: dict, design_result: dict) -> dict:
    validate_config(config, design_result)
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOCATION_HASH_ODATA_SIDE_DIAGNOSTICS_DRY_RUN",
        "gate_id": config["gate_id"], "network_called": False, "script_source_transient_read_performed": False,
        "fragment_value_read_performed": False, "navigation_executed": False, "history_state_mutated": False,
        "resource_get_authorized": False, "collection_authorized": False, "processing_authorized": False,
        "recurrence_authorized": False, "schedule_enabled": False,
    }

def run_location_hash_odata_side_diagnostics(config: dict, design_result: dict, *, runtime=None) -> dict:
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
        raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(f"{ERROR}_BLOCKED_NETWORK_SENT")
    if candidates:
        raise SiopeOfficialOlindaApiApplicationLocationHashOdataSideDiagnosticsError(
            f"{ERROR}_UNEXPECTED_DYNAMIC_CANDIDATE", diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates}
        )
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOCATION_HASH_ODATA_SIDE_DIAGNOSTICS",
        "gate_id": config["gate_id"], "source_id": config["source_id"], "software_version": config["software_version"],
        "runtime_status": "BOUNDED_TRANSIENT_ALREADY_LOADED_SCRIPT_LOCATION_HASH_ODATA_NEAREST_SIDE_COUNTS_OBSERVED_WITH_UNAPPROVED_NETWORK_BLOCKED",
        "application_surface_verified": True, "fragment_present": bool(probe.get("fragment_present")),
        "family_classification_window_chars": 4096, "parameter_window_chars": 1024,
        "location_hash_window_chars": 4096, "format_window_chars": 16384, "odata_window_chars": 65536,
        "location_hash_odata_side_counts": counts,
        "initial_document_continued_count": 1,
        "official_static_asset_network_sent_count": int(probe.get("static_assets_continued_count", 0)),
        "local_request_count": int(probe.get("local_requests_continued_count", 0)),
        "blocked_shape_count": len(shapes), "blocked_shapes": shapes, "candidate_shape_count": 0, "candidate_shapes": [],
        "safety": {
            "initial_document_network_sent": True, "dynamic_candidate_network_sent": False,
            "script_source_transient_read_performed": True, "script_source_returned": False, "script_source_persisted": False,
            "script_url_returned": False, "script_id_returned": False, "source_snippet_returned": False, "source_offset_returned": False,
            "new_script_network_request_performed": False, "fragment_value_read_performed": False, "fragment_value_returned": False,
            "dom_interaction_performed": False, "navigation_executed": False, "history_state_mutated": False,
            "pilot_limeira_values_sent": False, "resource_data_request_performed": False, "resource_get_authorized": False,
            "collection_authorized": False, "processing_authorized": False, "recurrence_authorized": False, "schedule_enabled": False,
            "form_submission": False, "post_request_performed": False, "head_request_performed": False, "authentication_performed": False,
            "captcha_bypass": False, "credentials_captured": False, "cookies_captured": False, "artifact_downloaded": False,
            "browser_download_denied": True, "dom_text_returned": False, "html_returned": False,
            "response_body_persisted": False, "request_body_persisted": False, "query_values_persisted": False,
            "remote_writes": "NONE", "route_synthesized_or_guessed": False, "automatic_route_promotion": False,
        },
        "next_review": config["next_review"],
    }
