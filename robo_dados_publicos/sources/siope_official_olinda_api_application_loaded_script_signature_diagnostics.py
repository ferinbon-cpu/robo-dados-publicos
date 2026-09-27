from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from urllib.parse import urlparse

from .siope_artifact_download_event_diagnostics import (
    _connect_cdp_with_retry,
    _create_page_target,
    _wait_browser_debug_version,
    _wait_devtools_active_port,
)
from .siope_official_olinda_api_application_runtime_route_diagnostics import (
    _is_allowed_static_asset,
    _matches_exact_application_document,
    summarize_blocked_requests,
)

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS"
COUNT_FIELDS = [
    "parsed_script_count",
    "source_read_count",
    "source_read_failure_count",
    "callable_occurrence_count",
    "callable_name_script_count",
    "service_document_name_script_count",
    "both_names_same_script_count",
    "callable_open_parenthesis_window_count",
    "all_parameter_names_window_count",
    "all_at_parameter_names_window_count",
    "ordered_callable_parameter_sequence_window_count",
    "odata_literal_window_count",
    "format_token_window_count",
    "query_marker_window_count",
    "contract_like_window_count",
]


class SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_{code}")


def _identifier_pattern(value: str) -> re.Pattern[str]:
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(value) + r"(?![A-Za-z0-9_])")


def _empty_counts() -> dict[str, int]:
    return {field: 0 for field in COUNT_FIELDS}


def _ordered_tokens(segment: str, tokens: list[str]) -> bool:
    cursor = 0
    for token in tokens:
        position = segment.find(token, cursor)
        if position < 0:
            return False
        cursor = position + len(token)
    return True


def _analyze_source_into_counts(source: str, config: dict, counts: dict[str, int]) -> None:
    callable_name = config["technical_callable_pattern_name"]
    service_name = config["service_document_declared_name"]
    params = list(config["technical_parameter_names"])
    at_params = ["@" + value for value in params]
    window_chars = int(config["local_window_chars"])
    callable_pattern = _identifier_pattern(callable_name)
    service_pattern = _identifier_pattern(service_name)
    callable_matches = list(callable_pattern.finditer(source))
    callable_present = bool(callable_matches)
    service_present = bool(service_pattern.search(source))
    if callable_present:
        counts["callable_name_script_count"] += 1
    if service_present:
        counts["service_document_name_script_count"] += 1
    if callable_present and service_present:
        counts["both_names_same_script_count"] += 1

    counts["callable_occurrence_count"] += len(callable_matches)
    if counts["callable_occurrence_count"] > config["max_callable_occurrences"]:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_CALLABLE_OCCURRENCE_LIMIT")

    for match in callable_matches:
        left = max(0, match.start() - window_chars)
        right = min(len(source), match.end() + window_chars)
        window = source[left:right]
        forward = source[match.start():right]
        after_name = source[match.end():min(len(source), match.end() + 64)]
        open_parenthesis = re.match(r"\s*\(", after_name) is not None
        all_params = all(value in window for value in params)
        all_at_params = all(value in window for value in at_params)
        ordered = _ordered_tokens(forward, [callable_name, *params])
        odata_literal = config["known_contract_tokens"][0] in window
        format_token = config["known_contract_tokens"][1] in window
        query_marker = "?" in window
        close_parenthesis = ")" in forward
        contract_like = open_parenthesis and close_parenthesis and all_params and all_at_params and ordered and query_marker
        if open_parenthesis:
            counts["callable_open_parenthesis_window_count"] += 1
        if all_params:
            counts["all_parameter_names_window_count"] += 1
        if all_at_params:
            counts["all_at_parameter_names_window_count"] += 1
        if ordered:
            counts["ordered_callable_parameter_sequence_window_count"] += 1
        if odata_literal:
            counts["odata_literal_window_count"] += 1
        if format_token:
            counts["format_token_window_count"] += 1
        if query_marker:
            counts["query_marker_window_count"] += 1
        if contract_like:
            counts["contract_like_window_count"] += 1


def validate_config(config: dict, design_result: dict) -> None:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_0_8_0", "GATE")
    _require(config.get("mode"), "PASSIVE_ALREADY_LOADED_SCRIPT_SOURCE_SIGNATURE_DIAGNOSTICS", "MODE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("service_document_declared_name"), "_Dados_Gerais_Siope", "SERVICE_NAME")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMS")
    _require(config.get("known_contract_tokens"), ["/odata/", "$format"], "TOKENS")
    _require(config.get("returned_count_fields"), COUNT_FIELDS, "FIELDS")
    _require(config.get("max_parsed_scripts"), 128, "MAX_SCRIPTS")
    _require(config.get("max_callable_occurrences"), 128, "MAX_OCCURRENCES")
    _require(config.get("max_source_bytes_per_script"), 5000000, "MAX_SCRIPT_BYTES")
    _require(config.get("max_total_source_bytes"), 32000000, "MAX_TOTAL_BYTES")
    _require(config.get("local_window_chars"), 1024, "WINDOW")
    _require(config.get("script_source_transient_read"), "ALLOWED_EPHEMERAL_MEMORY_ONLY_AFTER_SCRIPT_ALREADY_LOADED", "TRANSIENT_READ")
    _require(config.get("script_source_read_method"), "CDP_DEBUGGER_GET_SCRIPT_SOURCE_FOR_ALREADY_PARSED_SCRIPT_IDS_ONLY", "READ_METHOD")
    _require(design_result.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_DESIGN", "DESIGN")
    _require(design_result.get("returned_observations"), COUNT_FIELDS, "DESIGN_FIELDS")
    _require(design_result.get("script_source_return_authorized"), False, "DESIGN_SOURCE_RETURN")
    _require(design_result.get("script_source_persistence_authorized"), False, "DESIGN_SOURCE_PERSIST")
    _require(design_result.get("new_script_network_request_authorized"), False, "DESIGN_NETWORK")
    parsed = urlparse(config["exact_application_url"])
    _require(parsed.scheme, config["expected_scheme"], "SCHEME")
    _require(parsed.hostname, config["expected_host"], "HOST")
    _require(parsed.path, config["expected_path"], "PATH")
    _require(parsed.query, "", "QUERY")
    _require(parsed.fragment, "", "FRAGMENT")
    if "352690" in config["exact_application_url"] or "Limeira" in config["exact_application_url"]:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_PILOT_VALUE")
    for key in (
        "new_script_network_request",
        "script_source_return",
        "script_source_persistence",
        "script_url_return",
        "script_id_return",
        "source_snippet_return",
        "source_offset_return",
        "dom_text_return",
        "fragment_value_capture",
        "html_capture",
        "response_body_capture",
        "request_body_capture",
        "query_value_persistence",
        "dynamic_candidate_network_send",
        "resource_data_request",
        "pilot_limeira_values_send",
        "dom_interaction",
        "navigation_execution",
        "form_submission",
        "post_request_send",
        "head_request",
        "authentication",
        "captcha_bypass",
        "credential_capture",
        "cookie_capture",
        "artifact_download",
        "remote_writes",
        "route_synthesis_or_guessing",
        "automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")


class SystemChromeCdpLoadedScriptSignatureRuntime:
    def _find_browser(self, config: dict) -> str:
        for name in config["browser_binary_candidates"]:
            path = shutil.which(name)
            if path:
                return path
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_BROWSER_UNAVAILABLE")

    def run_probe(self, config: dict) -> dict:
        browser = self._find_browser(config)
        process = page_session = browser_session = None
        blocked: list[dict] = []
        static_assets_continued = 0
        initial_document_continued = 0
        local_requests_continued = 0
        script_ids: list[str] = []
        seen_script_ids: set[str] = set()
        try:
            with tempfile.TemporaryDirectory(prefix="siope-olinda-loaded-script-", ignore_cleanup_errors=True) as profile_text:
                profile = Path(profile_text)
                cmd = [
                    browser,
                    "--headless=new",
                    "--remote-debugging-port=0",
                    "--remote-debugging-address=127.0.0.1",
                    "--remote-allow-origins=*",
                    f"--user-data-dir={profile}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-background-networking",
                    "--disable-component-update",
                    "--disable-sync",
                    "--disable-default-apps",
                    "--disable-extensions",
                    "--disable-features=MediaRouter",
                    "--metrics-recording-only",
                    "--no-sandbox",
                    "about:blank",
                ]
                env = {k: v for k, v in os.environ.items() if k != "CHROME_LOG_FILE"}
                process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                port, _ = _wait_devtools_active_port(profile, process)
                version_info = _wait_browser_debug_version(port, process)
                timeout_s = float(config["cdp_command_timeout_ms"]) / 1000.0
                browser_session = _connect_cdp_with_retry(str(version_info["webSocketDebuggerUrl"]), command_timeout_s=timeout_s, process=process)
                browser_session.command("Browser.setDownloadBehavior", {"behavior": "deny"})
                target = _create_page_target(port)
                page_session = _connect_cdp_with_retry(str(target["webSocketDebuggerUrl"]), command_timeout_s=timeout_s, process=process)

                def handle_event(payload: dict) -> None:
                    nonlocal static_assets_continued, initial_document_continued, local_requests_continued
                    method_name = payload.get("method")
                    if method_name == "Debugger.scriptParsed":
                        params = payload.get("params") or {}
                        script_id = params.get("scriptId")
                        if isinstance(script_id, str) and script_id and script_id not in seen_script_ids:
                            seen_script_ids.add(script_id)
                            script_ids.append(script_id)
                        return
                    if method_name != "Fetch.requestPaused":
                        return
                    params = payload.get("params") or {}
                    request_id = params.get("requestId")
                    request = params.get("request") or {}
                    url = str(request.get("url", ""))
                    method = str(request.get("method", "")).upper()
                    resource_type = str(params.get("resourceType", "Other"))
                    parsed_request = urlparse(url)
                    if parsed_request.scheme in {"about", "data", "blob"}:
                        local_requests_continued += 1
                        page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                    elif _matches_exact_application_document(url, method, resource_type, config) and initial_document_continued == 0:
                        initial_document_continued += 1
                        page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                    elif _is_allowed_static_asset(url, method, resource_type, config):
                        static_assets_continued += 1
                        page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                    else:
                        blocked.append({"url": url, "method": method, "resource_type": resource_type})
                        page_session.send_no_wait("Fetch.failRequest", {"requestId": request_id, "errorReason": "Aborted"})

                page_session.event_handler = handle_event
                page_session.command("Page.enable")
                page_session.command("Runtime.enable")
                page_session.command("Debugger.enable")
                page_session.command("Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]})
                page_session.command("Page.navigate", {"url": config["exact_application_url"]})

                scheme_literal = json.dumps(config["expected_scheme"] + ":")
                host_literal = json.dumps(config["expected_host"])
                path_literal = json.dumps(config["expected_path"])
                surface_expr = f"""(() => ({{
                  scheme_matches: window.location.protocol === {scheme_literal},
                  host_matches: window.location.hostname === {host_literal},
                  path_matches: window.location.pathname === {path_literal},
                  query_empty: window.location.search === '',
                  fragment_present: window.location.hash.length > 0,
                  ready_eligible: document.readyState === 'interactive' || document.readyState === 'complete'
                }}))()"""
                surface = None
                deadline = time.monotonic() + float(config["page_load_timeout_ms"]) / 1000.0
                while time.monotonic() < deadline:
                    evaluation = page_session.command("Runtime.evaluate", {"expression": surface_expr, "returnByValue": True})
                    surface = ((evaluation.get("result") or {}).get("value") or {})
                    if all(surface.get(k) is True for k in ("scheme_matches", "host_matches", "path_matches", "query_empty", "ready_eligible")):
                        break
                    page_session.pump(0.15)
                if not surface or not all(surface.get(k) is True for k in ("scheme_matches", "host_matches", "path_matches", "query_empty", "ready_eligible")):
                    shapes, candidates = summarize_blocked_requests(blocked, config)
                    raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(
                        f"{ERROR}_APPLICATION_SURFACE_NOT_VERIFIED",
                        diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates},
                    )

                page_session.pump(float(config["capture_window_ms"]) / 1000.0)
                if not script_ids:
                    raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_NO_PARSED_SCRIPTS")
                if len(script_ids) > config["max_parsed_scripts"]:
                    raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_PARSED_SCRIPT_LIMIT")

                counts = _empty_counts()
                counts["parsed_script_count"] = len(script_ids)
                total_source_bytes = 0
                for script_id in script_ids:
                    source = None
                    try:
                        response = page_session.command("Debugger.getScriptSource", {"scriptId": script_id})
                        candidate = response.get("scriptSource")
                        if not isinstance(candidate, str):
                            counts["source_read_failure_count"] += 1
                            continue
                        source = candidate
                        source_bytes = len(source.encode("utf-8"))
                        if source_bytes > config["max_source_bytes_per_script"]:
                            raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_SCRIPT_SOURCE_BYTE_LIMIT")
                        total_source_bytes += source_bytes
                        if total_source_bytes > config["max_total_source_bytes"]:
                            raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_TOTAL_SOURCE_BYTE_LIMIT")
                        counts["source_read_count"] += 1
                        _analyze_source_into_counts(source, config, counts)
                    except SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError:
                        raise
                    except Exception:
                        counts["source_read_failure_count"] += 1
                    finally:
                        source = None
                if counts["source_read_count"] + counts["source_read_failure_count"] != counts["parsed_script_count"]:
                    raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_SOURCE_READ_PARTITION")
                if counts["source_read_count"] == 0:
                    raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_NO_READABLE_SCRIPT_SOURCE")

                final_eval = page_session.command("Runtime.evaluate", {"expression": surface_expr, "returnByValue": True})
                final_surface = ((final_eval.get("result") or {}).get("value") or {})
                if not all(final_surface.get(k) is True for k in ("scheme_matches", "host_matches", "path_matches", "query_empty", "ready_eligible")):
                    raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_SURFACE_DRIFT")
                shapes, candidates = summarize_blocked_requests(blocked, config)
                if len(shapes) > config["max_blocked_shapes"]:
                    raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_SHAPE_LIMIT")
                return {
                    "initial_document_continued_count": initial_document_continued,
                    "static_assets_continued_count": static_assets_continued,
                    "local_requests_continued_count": local_requests_continued,
                    "application_surface_verified": True,
                    "fragment_present": bool(final_surface.get("fragment_present")),
                    "loaded_script_signature_counts": counts,
                    "blocked_shapes": shapes,
                    "candidate_shapes": candidates,
                    "browser_download_denied": True,
                    "script_source_transient_read_performed": counts["source_read_count"] > 0,
                }
        finally:
            for session in (page_session, browser_session):
                if session is not None:
                    try:
                        session.close()
                    except Exception:
                        pass
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)


def dry_run(config: dict, design_result: dict) -> dict:
    validate_config(config, design_result)
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS_DRY_RUN",
        "gate_id": config["gate_id"],
        "network_called": False,
        "initial_document_network_sent": False,
        "dynamic_candidate_network_sent": False,
        "script_source_transient_read_performed": False,
        "script_source_returned": False,
        "script_source_persisted": False,
        "script_url_returned": False,
        "script_id_returned": False,
        "source_snippet_returned": False,
        "source_offset_returned": False,
        "dom_interaction_performed": False,
        "navigation_executed": False,
        "pilot_limeira_values_sent": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def _validate_counts(counts: dict, config: dict) -> None:
    if set(counts) != set(COUNT_FIELDS):
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_COUNT_FIELDS")
    for key, value in counts.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_COUNT_TYPE_{key.upper()}")
    if not (1 <= counts["parsed_script_count"] <= config["max_parsed_scripts"]):
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_PARSED_SCRIPT_COUNT")
    if counts["source_read_count"] + counts["source_read_failure_count"] != counts["parsed_script_count"]:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_SOURCE_PARTITION")
    if counts["source_read_count"] < 1:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_SOURCE_READ_ZERO")
    if counts["callable_occurrence_count"] > config["max_callable_occurrences"]:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_CALLABLE_COUNT")
    for key in ("callable_name_script_count", "service_document_name_script_count", "both_names_same_script_count"):
        if counts[key] > counts["source_read_count"]:
            raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_SCRIPT_RELATION_{key.upper()}")
    for key in (
        "callable_open_parenthesis_window_count",
        "all_parameter_names_window_count",
        "all_at_parameter_names_window_count",
        "ordered_callable_parameter_sequence_window_count",
        "odata_literal_window_count",
        "format_token_window_count",
        "query_marker_window_count",
        "contract_like_window_count",
    ):
        if counts[key] > counts["callable_occurrence_count"]:
            raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_WINDOW_RELATION_{key.upper()}")


def run_loaded_script_signature_diagnostics(config: dict, design_result: dict, *, runtime=None) -> dict:
    validate_config(config, design_result)
    runtime = runtime or SystemChromeCdpLoadedScriptSignatureRuntime()
    probe = runtime.run_probe(config)
    _require(probe.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(probe.get("application_surface_verified"), True, "SURFACE")
    _require(probe.get("browser_download_denied"), True, "DOWNLOAD_DENIAL")
    _require(probe.get("script_source_transient_read_performed"), True, "TRANSIENT_READ_NOT_PERFORMED")
    counts = probe.get("loaded_script_signature_counts") or {}
    _validate_counts(counts, config)
    shapes = probe.get("blocked_shapes") or []
    candidates = probe.get("candidate_shapes") or []
    if any(shape.get("network_sent") for shape in shapes):
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(f"{ERROR}_BLOCKED_NETWORK_SENT")
    if candidates:
        raise SiopeOfficialOlindaApiApplicationLoadedScriptSignatureDiagnosticsError(
            f"{ERROR}_UNEXPECTED_DYNAMIC_CANDIDATE",
            diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates},
        )
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_LOADED_SCRIPT_SIGNATURE_DIAGNOSTICS",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "runtime_status": "BOUNDED_TRANSIENT_ALREADY_LOADED_SCRIPT_SIGNATURE_COUNTS_OBSERVED_WITH_UNAPPROVED_NETWORK_BLOCKED",
        "application_surface_verified": True,
        "fragment_present": bool(probe.get("fragment_present")),
        "loaded_script_signature_counts": counts,
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
