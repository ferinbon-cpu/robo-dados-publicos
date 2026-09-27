from __future__ import annotations

import json
import os
from pathlib import Path
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
from .siope_official_olinda_api_application_fragment_target_structure_diagnostics_design import COUNT_FIELDS

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS"


class SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_{code}")


def validate_config(config: dict, design_result: dict) -> None:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS_0_8_0", "GATE")
    _require(config.get("mode"), "PASSIVE_SAME_DOCUMENT_FRAGMENT_TARGET_STRUCTURE_COUNT_DIAGNOSTICS", "MODE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMETERS")
    _require(config.get("matching_attribute_name"), "href", "ATTRIBUTE")
    _require(config.get("returned_count_fields"), COUNT_FIELDS, "FIELDS")
    _require(config.get("minimum_fragment_matches"), 2, "MIN_MATCH")
    _require(config.get("max_fragment_matches"), 8, "MAX_MATCH")
    _require(design_result.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS_DESIGN", "DESIGN")
    _require(design_result.get("returned_observations"), COUNT_FIELDS, "DESIGN_FIELDS")
    _require(design_result.get("navigation_execution_authorized"), False, "DESIGN_NAV")
    _require(design_result.get("history_state_mutation_authorized"), False, "DESIGN_HISTORY")
    _require(design_result.get("resource_get_authorized"), False, "DESIGN_RESOURCE")
    parsed = urlparse(config["exact_application_url"])
    _require(parsed.scheme, config["expected_scheme"], "SCHEME")
    _require(parsed.hostname, config["expected_host"], "HOST")
    _require(parsed.path, config["expected_path"], "PATH")
    _require(parsed.query, "", "QUERY")
    _require(parsed.fragment, "", "FRAGMENT")
    if "352690" in config["exact_application_url"] or "Limeira" in config["exact_application_url"]:
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_PILOT_VALUE")
    _require(config.get("fragment_value_transient_read"), "ALLOWED_EPHEMERAL_MEMORY_ONLY_FOR_FIXED_COUNT_CLASSIFICATION", "TRANSIENT_FRAGMENT")
    _require(config.get("fragment_target_text_transient_read"), "ALLOWED_EPHEMERAL_MEMORY_ONLY_FOR_FIXED_COUNT_CLASSIFICATION", "TRANSIENT_TARGET")
    for key in (
        "raw_navigation_value_return", "navigation_fragment_return", "fragment_target_identifier_return",
        "fragment_target_text_return", "dom_text_return", "dom_attribute_value_return", "element_text_return",
        "element_attribute_return", "tag_name_return", "html_capture", "script_source_capture",
        "response_body_capture", "request_body_capture", "query_value_persistence", "dom_interaction",
        "navigation_execution", "history_state_mutation", "form_submission", "dynamic_candidate_network_send",
        "resource_data_request", "pilot_limeira_values_send", "post_request_send", "head_request",
        "authentication", "captcha_bypass", "credential_capture", "cookie_capture", "artifact_download",
        "remote_writes", "route_synthesis_or_guessing", "automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")


def _validate_counts(counts: dict, config: dict) -> None:
    if set(counts) != set(COUNT_FIELDS):
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_COUNT_FIELDS")
    for key, value in counts.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_COUNT_TYPE_{key.upper()}")
    total = counts["fragment_navigation_match_count"]
    if not (config["minimum_fragment_matches"] <= total <= config["max_fragment_matches"]):
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_FRAGMENT_MATCH_COUNT")
    if counts["distinct_fragment_value_count"] > total:
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_DISTINCT_GT_TOTAL")
    if counts["fragment_route_like_count"] + counts["fragment_anchor_like_count"] > total:
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_FRAGMENT_PARTITION")
    target_total = counts["fragment_target_resolved_count"]
    for field in COUNT_FIELDS[5:12]:
        if counts[field] > target_total:
            raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_TARGET_METRIC_GT_RESOLVED_{field.upper()}")
    for field in COUNT_FIELDS[12:]:
        if counts[field] > total:
            raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_VALUE_METRIC_GT_TOTAL_{field.upper()}")
    if counts["fragment_target_contract_like_count"] > min(
        counts["fragment_target_contains_callable_name_count"],
        counts["fragment_target_contains_all_parameter_names_count"],
        counts["fragment_target_ordered_parameter_sequence_count"],
        counts["fragment_target_open_parenthesis_count"],
    ):
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_TARGET_CONTRACT_SUBSET")


class SystemChromeCdpFragmentTargetStructureRuntime:
    def _find_browser(self, config: dict) -> str:
        for name in config["browser_binary_candidates"]:
            path = shutil.which(name)
            if path:
                return path
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_BROWSER_UNAVAILABLE")

    def run_probe(self, config: dict) -> dict:
        browser = self._find_browser(config)
        process = page_session = browser_session = None
        blocked: list[dict] = []
        static_assets_continued = 0
        initial_document_continued = 0
        local_requests_continued = 0
        try:
            with tempfile.TemporaryDirectory(prefix="siope-olinda-fragment-target-", ignore_cleanup_errors=True) as profile_text:
                profile = Path(profile_text)
                cmd = [
                    browser, "--headless=new", "--remote-debugging-port=0", "--remote-debugging-address=127.0.0.1",
                    "--remote-allow-origins=*", f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check",
                    "--disable-background-networking", "--disable-component-update", "--disable-sync", "--disable-default-apps",
                    "--disable-extensions", "--disable-features=MediaRouter", "--metrics-recording-only", "--no-sandbox", "about:blank",
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
                    if payload.get("method") != "Fetch.requestPaused":
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
                page_session.command("Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]})
                page_session.command("Page.navigate", {"url": config["exact_application_url"]})

                surface_expr = f"""(() => ({{
                  scheme_matches: window.location.protocol === {json.dumps(config['expected_scheme'] + ':')},
                  host_matches: window.location.hostname === {json.dumps(config['expected_host'])},
                  path_matches: window.location.pathname === {json.dumps(config['expected_path'])},
                  query_empty: window.location.search === '',
                  fragment_present: window.location.hash.length > 0,
                  ready_eligible: document.readyState === 'interactive' || document.readyState === 'complete'
                }}))()"""
                surface = None
                deadline = time.monotonic() + float(config["page_load_timeout_ms"]) / 1000.0
                while time.monotonic() < deadline:
                    evaluation = page_session.command("Runtime.evaluate", {"expression": surface_expr, "returnByValue": True})
                    if evaluation.get("exceptionDetails") is not None:
                        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_SURFACE_EVALUATION_EXCEPTION", diagnostics={"javascript_exception_observed": True})
                    surface = ((evaluation.get("result") or {}).get("value") or {})
                    if all(surface.get(k) is True for k in ("scheme_matches", "host_matches", "path_matches", "query_empty", "ready_eligible")):
                        break
                    page_session.pump(0.15)
                if not surface or not all(surface.get(k) is True for k in ("scheme_matches", "host_matches", "path_matches", "query_empty", "ready_eligible")):
                    shapes, candidates = summarize_blocked_requests(blocked, config)
                    raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_APPLICATION_SURFACE_NOT_VERIFIED", diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates})

                page_session.pump(float(config["capture_window_ms"]) / 1000.0)
                callable_literal = json.dumps(config["technical_callable_pattern_name"])
                parameter_literals = ",".join(json.dumps(v) for v in config["technical_parameter_names"])
                fields_literal = json.dumps(COUNT_FIELDS)
                expr = f"""(() => {{
                  const callableName = {callable_literal};
                  const params = [{parameter_literals}];
                  const fields = {fields_literal};
                  const counts = Object.fromEntries(fields.map((k) => [k, 0]));
                  const values = [];
                  for (const el of Array.from(document.querySelectorAll('*'))) {{
                    const value = el.getAttribute && el.getAttribute('href');
                    if (typeof value === 'string' && value.startsWith('#') && value.includes(callableName)) values.push(value);
                  }}
                  counts.fragment_navigation_match_count = values.length;
                  counts.distinct_fragment_value_count = new Set(values).size;
                  const orderedTokens = (text, tokens) => {{
                    let pos = 0;
                    for (const token of tokens) {{
                      const i = text.indexOf(token, pos);
                      if (i < 0) return false;
                      pos = i + token.length;
                    }}
                    return true;
                  }};
                  for (const value of values) {{
                    const rawFragment = value.slice(1);
                    const routeLike = rawFragment.startsWith('/') || rawFragment.startsWith('!/');
                    if (routeLike) counts.fragment_route_like_count += 1;
                    else if (rawFragment.length > 0) counts.fragment_anchor_like_count += 1;
                    const valueAllParams = params.every((p) => rawFragment.includes(p));
                    if (valueAllParams) counts.fragment_value_contains_all_parameter_names_count += 1;
                    if (rawFragment.includes('(') && rawFragment.includes(')')) counts.fragment_value_parentheses_present_count += 1;
                    if (rawFragment.includes('?')) counts.fragment_value_query_marker_present_count += 1;
                    if (rawFragment.includes('$format')) counts.fragment_value_format_token_present_count += 1;

                    let key = rawFragment;
                    try {{ key = decodeURIComponent(rawFragment); }} catch (_) {{ key = rawFragment; }}
                    let target = document.getElementById(key);
                    if (!target) {{
                      for (const candidate of Array.from(document.getElementsByName(key))) {{ target = candidate; break; }}
                    }}
                    if (!target) continue;
                    counts.fragment_target_resolved_count += 1;
                    const text = String(target.textContent || '');
                    const hasCallable = text.includes(callableName);
                    const allParams = params.every((p) => text.includes(p));
                    const ordered = orderedTokens(text, [callableName, ...params]);
                    const openParen = text.includes(callableName + '(') || text.includes(callableName + ' (');
                    const queryMarker = text.includes('?');
                    const formatToken = text.includes('$format');
                    if (hasCallable) counts.fragment_target_contains_callable_name_count += 1;
                    if (allParams) counts.fragment_target_contains_all_parameter_names_count += 1;
                    if (ordered) counts.fragment_target_ordered_parameter_sequence_count += 1;
                    if (openParen) counts.fragment_target_open_parenthesis_count += 1;
                    if (queryMarker) counts.fragment_target_query_marker_count += 1;
                    if (formatToken) counts.fragment_target_format_token_count += 1;
                    if (hasCallable && allParams && ordered && openParen) counts.fragment_target_contract_like_count += 1;
                  }}
                  return counts;
                }})()"""
                evaluation = page_session.command("Runtime.evaluate", {"expression": expr, "returnByValue": True})
                if evaluation.get("exceptionDetails") is not None:
                    raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_DOM_EVALUATION_EXCEPTION", diagnostics={"javascript_exception_observed": True})
                counts = ((evaluation.get("result") or {}).get("value") or {})
                if not isinstance(counts, dict):
                    raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_DOM_EVALUATION_VALUE")
                _validate_counts(counts, config)

                final_eval = page_session.command("Runtime.evaluate", {"expression": surface_expr, "returnByValue": True})
                final_surface = ((final_eval.get("result") or {}).get("value") or {})
                if not all(final_surface.get(k) is True for k in ("scheme_matches", "host_matches", "path_matches", "query_empty", "ready_eligible")):
                    raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_FINAL_SURFACE")
                shapes, candidates = summarize_blocked_requests(blocked, config)
                if len(shapes) > config["max_blocked_shapes"]:
                    raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_SHAPE_LIMIT")
                return {
                    "application_surface_verified": True,
                    "fragment_present": bool(final_surface.get("fragment_present")),
                    "fragment_target_structure_counts": counts,
                    "initial_document_continued_count": initial_document_continued,
                    "official_static_asset_network_sent_count": static_assets_continued,
                    "local_request_count": local_requests_continued,
                    "blocked_shapes": shapes,
                    "candidate_shapes": candidates,
                    "browser_download_denied": True,
                }
        finally:
            for session in (page_session, browser_session):
                if session is not None:
                    try:
                        session.close()
                    except Exception:
                        pass
            if process is not None:
                try:
                    process.terminate(); process.wait(timeout=2)
                except Exception:
                    try: process.kill()
                    except Exception: pass


def dry_run(config: dict, design_result: dict) -> dict:
    validate_config(config, design_result)
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS_DRY_RUN",
        "gate_id": config["gate_id"],
        "network_called": False,
        "fragment_value_transient_read_performed": False,
        "fragment_target_text_transient_read_performed": False,
        "dynamic_candidate_network_sent": False,
        "pilot_limeira_values_sent": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def run_fragment_target_structure_diagnostics(config: dict, design_result: dict, *, runtime=None) -> dict:
    validate_config(config, design_result)
    probe = (runtime or SystemChromeCdpFragmentTargetStructureRuntime()).run_probe(config)
    _require(probe.get("application_surface_verified"), True, "SURFACE")
    _require(probe.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(probe.get("browser_download_denied"), True, "DOWNLOAD_DENIED")
    counts = probe.get("fragment_target_structure_counts") or {}
    _validate_counts(counts, config)
    shapes = probe.get("blocked_shapes") or []
    candidates = probe.get("candidate_shapes") or []
    if any(shape.get("network_sent") for shape in shapes):
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_BLOCKED_NETWORK_SENT")
    if candidates:
        raise SiopeOfficialOlindaApiApplicationFragmentTargetStructureDiagnosticsError(f"{ERROR}_UNEXPECTED_DYNAMIC_CANDIDATE", diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates})
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_FRAGMENT_TARGET_STRUCTURE_DIAGNOSTICS",
        "gate_id": config["gate_id"],
        "runtime_status": "BOUNDED_TRANSIENT_FRAGMENT_AND_EXISTING_DOM_TARGET_STRUCTURE_COUNTS_OBSERVED_WITHOUT_NAVIGATION_AND_WITH_UNAPPROVED_NETWORK_BLOCKED",
        "application_surface_verified": True,
        "fragment_present": bool(probe.get("fragment_present")),
        "fragment_target_structure_counts": counts,
        "initial_document_continued_count": 1,
        "official_static_asset_network_sent_count": int(probe.get("official_static_asset_network_sent_count", 0)),
        "local_request_count": int(probe.get("local_request_count", 0)),
        "blocked_shape_count": len(shapes),
        "blocked_shapes": shapes,
        "candidate_shape_count": 0,
        "candidate_shapes": [],
        "safety": {
            "initial_document_network_sent": True,
            "dynamic_candidate_network_sent": False,
            "pilot_limeira_values_sent": False,
            "resource_data_request_performed": False,
            "resource_get_authorized": False,
            "collection_authorized": False,
            "processing_authorized": False,
            "recurrence_authorized": False,
            "schedule_enabled": False,
            "fragment_value_transient_read_performed": True,
            "fragment_target_text_transient_read_performed": True,
            "raw_navigation_value_returned": False,
            "navigation_fragment_returned": False,
            "fragment_target_identifier_returned": False,
            "fragment_target_text_returned": False,
            "dom_text_returned": False,
            "dom_attribute_values_returned": False,
            "element_text_returned": False,
            "element_attribute_returned": False,
            "tag_name_returned": False,
            "html_returned": False,
            "script_source_returned": False,
            "response_body_persisted": False,
            "request_body_persisted": False,
            "query_values_persisted": False,
            "dom_interaction_performed": False,
            "navigation_executed": False,
            "history_state_mutated": False,
            "form_submission": False,
            "post_request_performed": False,
            "head_request_performed": False,
            "authentication_performed": False,
            "captcha_bypass": False,
            "credentials_captured": False,
            "cookies_captured": False,
            "artifact_downloaded": False,
            "browser_download_denied": True,
            "remote_writes": "NONE",
            "route_synthesized_or_guessed": False,
            "automatic_route_promotion": False,
        },
        "next_review": config["next_gate"],
    }
