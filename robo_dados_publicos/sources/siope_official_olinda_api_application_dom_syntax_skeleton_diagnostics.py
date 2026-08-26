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
from .siope_official_olinda_api_application_loaded_script_signature_diagnostics import _identifier_pattern

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS"
COUNT_FIELDS = [
    "minimal_contract_container_count",
    "callable_occurrence_in_minimal_container_count",
    "callable_open_paren_in_minimal_container_count",
    "callable_ordered_parameter_names_512_in_minimal_container_count",
    "callable_close_paren_after_ordered_parameters_512_in_minimal_container_count",
    "callable_ano_at_binding_4096_in_minimal_container_count",
    "callable_num_at_binding_4096_in_minimal_container_count",
    "callable_sig_at_binding_4096_in_minimal_container_count",
    "callable_all_three_at_bindings_4096_in_minimal_container_count",
    "callable_ordered_all_three_at_bindings_4096_in_minimal_container_count",
    "callable_query_alias_ano_4096_in_minimal_container_count",
    "callable_query_alias_num_4096_in_minimal_container_count",
    "callable_query_alias_sig_4096_in_minimal_container_count",
    "callable_all_three_query_aliases_4096_in_minimal_container_count",
    "callable_format_assignment_4096_in_minimal_container_count",
    "callable_full_known_signature_skeleton_4096_in_minimal_container_count",
]


class SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_{code}")


def _empty_counts() -> dict[str, int]:
    return {field: 0 for field in COUNT_FIELDS}


def _binding_pattern(name: str) -> re.Pattern[str]:
    token = re.escape(name)
    return re.compile(rf"\b{token}\b\s*=\s*@\s*{token}\b")


def _query_alias_pattern(name: str) -> re.Pattern[str]:
    token = re.escape(name)
    return re.compile(rf"[?&]\s*@\s*{token}\b\s*=")


def _ordered_identifier_matches(text: str, names: list[str]):
    pos = 0
    matches = []
    for name in names:
        match = _identifier_pattern(name).search(text, pos)
        if match is None:
            return None
        matches.append(match)
        pos = match.end()
    return matches


def _ordered_patterns(text: str, patterns: list[re.Pattern[str]]) -> bool:
    pos = 0
    for pattern in patterns:
        match = pattern.search(text, pos)
        if match is None:
            return False
        pos = match.end()
    return True


def _analyze_minimal_container_texts(texts: list[str], config: dict) -> dict[str, int]:
    counts = _empty_counts()
    counts["minimal_contract_container_count"] = len(texts)
    callable_name = config["technical_callable_pattern_name"]
    params = list(config["technical_parameter_names"])
    bind_patterns = [_binding_pattern(name) for name in params]
    query_patterns = [_query_alias_pattern(name) for name in params]
    format_pattern = re.compile(r"\$format\s*=")
    for text in texts:
        for match in _identifier_pattern(callable_name).finditer(text):
            counts["callable_occurrence_in_minimal_container_count"] += 1
            analysis = text[match.end(): match.end() + int(config["analysis_window_chars"])]
            param_window = text[match.end(): match.end() + int(config["parameter_sequence_window_chars"])]
            open_paren = re.match(r"\s*\(", analysis) is not None
            ordered_params = _ordered_identifier_matches(param_window, params)
            close_after = bool(ordered_params and ")" in param_window[ordered_params[-1].end():])
            bindings = [pattern.search(analysis) is not None for pattern in bind_patterns]
            all_bindings = all(bindings)
            ordered_bindings = _ordered_patterns(analysis, bind_patterns)
            aliases = [pattern.search(analysis) is not None for pattern in query_patterns]
            all_aliases = all(aliases)
            format_assignment = format_pattern.search(analysis) is not None
            full = open_paren and close_after and ordered_bindings and all_aliases and format_assignment
            if open_paren:
                counts["callable_open_paren_in_minimal_container_count"] += 1
            if ordered_params:
                counts["callable_ordered_parameter_names_512_in_minimal_container_count"] += 1
            if close_after:
                counts["callable_close_paren_after_ordered_parameters_512_in_minimal_container_count"] += 1
            for present, field in zip(bindings, COUNT_FIELDS[5:8]):
                if present:
                    counts[field] += 1
            if all_bindings:
                counts["callable_all_three_at_bindings_4096_in_minimal_container_count"] += 1
            if ordered_bindings:
                counts["callable_ordered_all_three_at_bindings_4096_in_minimal_container_count"] += 1
            for present, field in zip(aliases, COUNT_FIELDS[10:13]):
                if present:
                    counts[field] += 1
            if all_aliases:
                counts["callable_all_three_query_aliases_4096_in_minimal_container_count"] += 1
            if format_assignment:
                counts["callable_format_assignment_4096_in_minimal_container_count"] += 1
            if full:
                counts["callable_full_known_signature_skeleton_4096_in_minimal_container_count"] += 1
    return counts


def validate_config(config: dict, design_result: dict) -> None:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS_0_8_0", "GATE")
    _require(config.get("mode"), "PASSIVE_RENDERED_DOM_KNOWN_SYNTAX_SKELETON_COUNT_DIAGNOSTICS", "MODE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMETERS")
    _require(config.get("analysis_window_chars"), 4096, "WINDOW")
    _require(config.get("parameter_sequence_window_chars"), 512, "PARAM_WINDOW")
    _require(config.get("returned_count_fields"), COUNT_FIELDS, "FIELDS")
    _require(config.get("max_minimal_contract_containers"), 32, "MAX_CONTAINERS")
    _require(config.get("max_callable_occurrences"), 128, "MAX_OCCURRENCES")
    _require(design_result.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS_DESIGN", "DESIGN")
    _require(design_result.get("returned_observations"), COUNT_FIELDS, "DESIGN_FIELDS")
    parsed = urlparse(config["exact_application_url"])
    _require(parsed.scheme, config["expected_scheme"], "SCHEME")
    _require(parsed.hostname, config["expected_host"], "HOST")
    _require(parsed.path, config["expected_path"], "PATH")
    _require(parsed.query, "", "QUERY")
    _require(parsed.fragment, "", "FRAGMENT")
    if "352690" in config["exact_application_url"] or "Limeira" in config["exact_application_url"]:
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_PILOT_VALUE")
    for key in (
        "dom_text_return", "dom_attribute_value_return", "element_text_return", "element_attribute_return",
        "tag_name_return", "fragment_value_capture", "html_capture", "script_source_capture",
        "response_body_capture", "request_body_capture", "query_value_persistence", "dynamic_candidate_network_send",
        "resource_data_request", "pilot_limeira_values_send", "dom_interaction", "navigation_execution",
        "form_submission", "post_request_send", "head_request", "authentication", "captcha_bypass",
        "credential_capture", "cookie_capture", "artifact_download", "remote_writes",
        "route_synthesis_or_guessing", "automatic_route_promotion",
    ):
        _require(config.get(key), "PROHIBITED", f"CONFIG_{key.upper()}")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")


def _validate_counts(counts: dict, config: dict) -> None:
    if set(counts) != set(COUNT_FIELDS):
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_COUNT_FIELDS")
    for key, value in counts.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_COUNT_TYPE_{key.upper()}")
    containers = counts["minimal_contract_container_count"]
    callable_count = counts["callable_occurrence_in_minimal_container_count"]
    if not (1 <= containers <= config["max_minimal_contract_containers"]):
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_MINIMAL_CONTAINER_COUNT")
    if not (1 <= callable_count <= config["max_callable_occurrences"]):
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_CALLABLE_COUNT")
    for field in COUNT_FIELDS[2:]:
        if counts[field] > callable_count:
            raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_METRIC_GT_CALLABLE_{field.upper()}")
    if counts["callable_close_paren_after_ordered_parameters_512_in_minimal_container_count"] > counts["callable_ordered_parameter_names_512_in_minimal_container_count"]:
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_CLOSE_SUBSET")
    if counts["callable_all_three_at_bindings_4096_in_minimal_container_count"] > min(counts[field] for field in COUNT_FIELDS[5:8]):
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_BINDING_SUBSET")
    if counts["callable_ordered_all_three_at_bindings_4096_in_minimal_container_count"] > counts["callable_all_three_at_bindings_4096_in_minimal_container_count"]:
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_ORDERED_BINDING_SUBSET")
    if counts["callable_all_three_query_aliases_4096_in_minimal_container_count"] > min(counts[field] for field in COUNT_FIELDS[10:13]):
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_ALIAS_SUBSET")
    if counts["callable_full_known_signature_skeleton_4096_in_minimal_container_count"] > min(
        counts["callable_open_paren_in_minimal_container_count"],
        counts["callable_close_paren_after_ordered_parameters_512_in_minimal_container_count"],
        counts["callable_ordered_all_three_at_bindings_4096_in_minimal_container_count"],
        counts["callable_all_three_query_aliases_4096_in_minimal_container_count"],
        counts["callable_format_assignment_4096_in_minimal_container_count"],
    ):
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_FULL_SKELETON_SUBSET")


class SystemChromeCdpDomSyntaxSkeletonRuntime:
    def _find_browser(self, config: dict) -> str:
        for name in config["browser_binary_candidates"]:
            path = shutil.which(name)
            if path:
                return path
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_BROWSER_UNAVAILABLE")

    def run_probe(self, config: dict) -> dict:
        browser = self._find_browser(config)
        process = page_session = browser_session = None
        blocked: list[dict] = []
        static_assets_continued = 0
        initial_document_continued = 0
        local_requests_continued = 0
        try:
            with tempfile.TemporaryDirectory(prefix="siope-olinda-dom-syntax-", ignore_cleanup_errors=True) as profile_text:
                profile = Path(profile_text)
                cmd = [browser, "--headless=new", "--remote-debugging-port=0", "--remote-debugging-address=127.0.0.1",
                       "--remote-allow-origins=*", f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check",
                       "--disable-background-networking", "--disable-component-update", "--disable-sync", "--disable-default-apps",
                       "--disable-extensions", "--disable-features=MediaRouter", "--metrics-recording-only", "--no-sandbox", "about:blank"]
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
                    parsed = urlparse(url)
                    if parsed.scheme in {"about", "data", "blob"}:
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

                scheme_literal = json.dumps(config["expected_scheme"] + ":")
                host_literal = json.dumps(config["expected_host"])
                path_literal = json.dumps(config["expected_path"])
                surface_expr = f"""(() => ({{scheme_matches: window.location.protocol === {scheme_literal}, host_matches: window.location.hostname === {host_literal}, path_matches: window.location.pathname === {path_literal}, query_empty: window.location.search === '', fragment_present: window.location.hash.length > 0, ready_eligible: document.readyState === 'interactive' || document.readyState === 'complete'}}))()"""
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
                    raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_APPLICATION_SURFACE_NOT_VERIFIED", diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates})

                page_session.pump(float(config["capture_window_ms"]) / 1000.0)
                callable_literal = json.dumps(config["technical_callable_pattern_name"])
                parameter_literals = ",".join(json.dumps(v) for v in config["technical_parameter_names"])
                analysis_window = int(config["analysis_window_chars"])
                param_window = int(config["parameter_sequence_window_chars"])
                count_fields_json = json.dumps(COUNT_FIELDS)
                expr = f"""(() => {{
                  const callableName = {callable_literal}; const params = [{parameter_literals}];
                  const analysisWindow = {analysis_window}; const paramWindow = {param_window};
                  const fields = {count_fields_json}; const counts = Object.fromEntries(fields.map((k) => [k, 0]));
                  const elements = Array.from(document.querySelectorAll('*'));
                  const textOf = (el) => String((el && el.textContent) || '');
                  const hasAll = (el) => {{ const t = textOf(el); return [callableName, ...params].every((x) => t.includes(x)); }};
                  const containers = elements.filter(hasAll);
                  const minimal = containers.filter((el) => !Array.from(el.children || []).some(hasAll));
                  counts.minimal_contract_container_count = minimal.length;
                  const word = (c) => !!c && /[A-Za-z0-9_]/.test(c);
                  const occurrences = (text, token) => {{ const out=[]; let p=0; while (p <= text.length-token.length) {{ const i=text.indexOf(token,p); if(i<0) break; const a=i===0?'':text[i-1], b=i+token.length>=text.length?'':text[i+token.length]; if(!word(a)&&!word(b)) out.push(i); p=i+token.length; }} return out; }};
                  const orderedParams = (text) => {{ let p=0; const ends=[]; for(const token of params) {{ const i=text.indexOf(token,p); if(i<0) return null; ends.push(i+token.length); p=i+token.length; }} return ends; }};
                  const esc = (s) => s.replace(/[.*+?^${{}}()|[\]\\]/g, '\\$&');
                  const bind = params.map((p) => new RegExp('\\b'+esc(p)+'\\b\\s*=\\s*@\\s*'+esc(p)+'\\b'));
                  const alias = params.map((p) => new RegExp('[?&]\\s*@\\s*'+esc(p)+'\\b\\s*='));
                  const orderedPatterns = (text, patterns) => {{ let p=0; for(const r of patterns) {{ const m=r.exec(text.slice(p)); if(!m) return false; p += m.index+m[0].length; }} return true; }};
                  for(const el of minimal) {{ const text=textOf(el); for(const i of occurrences(text, callableName)) {{
                    counts.callable_occurrence_in_minimal_container_count += 1;
                    const after=text.slice(i+callableName.length, i+callableName.length+analysisWindow);
                    const pwin=text.slice(i+callableName.length, i+callableName.length+paramWindow);
                    const open=/^\\s*\(/.test(after); const ordered=orderedParams(pwin); const close=!!ordered && pwin.slice(ordered[ordered.length-1]).includes(')');
                    const bs=bind.map((r)=>r.test(after)); const allB=bs.every(Boolean); const ordB=orderedPatterns(after,bind);
                    const qs=alias.map((r)=>r.test(after)); const allQ=qs.every(Boolean); const fmt=/\$format\\s*=/.test(after);
                    if(open) counts.callable_open_paren_in_minimal_container_count += 1;
                    if(ordered) counts.callable_ordered_parameter_names_512_in_minimal_container_count += 1;
                    if(close) counts.callable_close_paren_after_ordered_parameters_512_in_minimal_container_count += 1;
                    if(bs[0]) counts.callable_ano_at_binding_4096_in_minimal_container_count += 1; if(bs[1]) counts.callable_num_at_binding_4096_in_minimal_container_count += 1; if(bs[2]) counts.callable_sig_at_binding_4096_in_minimal_container_count += 1;
                    if(allB) counts.callable_all_three_at_bindings_4096_in_minimal_container_count += 1; if(ordB) counts.callable_ordered_all_three_at_bindings_4096_in_minimal_container_count += 1;
                    if(qs[0]) counts.callable_query_alias_ano_4096_in_minimal_container_count += 1; if(qs[1]) counts.callable_query_alias_num_4096_in_minimal_container_count += 1; if(qs[2]) counts.callable_query_alias_sig_4096_in_minimal_container_count += 1;
                    if(allQ) counts.callable_all_three_query_aliases_4096_in_minimal_container_count += 1; if(fmt) counts.callable_format_assignment_4096_in_minimal_container_count += 1;
                    if(open && close && ordB && allQ && fmt) counts.callable_full_known_signature_skeleton_4096_in_minimal_container_count += 1;
                  }} }}
                  return counts;
                }})()"""
                evaluation = page_session.command("Runtime.evaluate", {"expression": expr, "returnByValue": True})
                counts = ((evaluation.get("result") or {}).get("value") or {})
                _validate_counts(counts, config)
                final_eval = page_session.command("Runtime.evaluate", {"expression": surface_expr, "returnByValue": True})
                final_surface = ((final_eval.get("result") or {}).get("value") or {})
                if not all(final_surface.get(k) is True for k in ("scheme_matches", "host_matches", "path_matches", "query_empty", "ready_eligible")):
                    raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_FINAL_SURFACE")
                shapes, candidates = summarize_blocked_requests(blocked, config)
                return {
                    "application_surface_verified": True, "fragment_present": bool(final_surface.get("fragment_present")),
                    "dom_syntax_skeleton_counts": counts, "initial_document_continued_count": initial_document_continued,
                    "official_static_asset_network_sent_count": static_assets_continued, "local_request_count": local_requests_continued,
                    "blocked_shapes": shapes, "candidate_shapes": candidates, "browser_download_denied": True,
                }
        finally:
            for session in (page_session, browser_session):
                if session is not None:
                    try: session.close()
                    except Exception: pass
            if process is not None:
                try:
                    process.terminate(); process.wait(timeout=2)
                except Exception:
                    try: process.kill()
                    except Exception: pass


def dry_run(config: dict, design_result: dict) -> dict:
    validate_config(config, design_result)
    return {"status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS_DRY_RUN", "gate_id": config["gate_id"], "network_called": False, "dom_text_returned": False, "dynamic_candidate_network_sent": False, "pilot_limeira_values_sent": False, "resource_get_authorized": False, "collection_authorized": False, "processing_authorized": False, "recurrence_authorized": False, "schedule_enabled": False}


def run_dom_syntax_skeleton_diagnostics(config: dict, design_result: dict, *, runtime=None) -> dict:
    validate_config(config, design_result)
    probe = (runtime or SystemChromeCdpDomSyntaxSkeletonRuntime()).run_probe(config)
    _require(probe.get("application_surface_verified"), True, "SURFACE")
    _require(probe.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(probe.get("browser_download_denied"), True, "DOWNLOAD_DENIED")
    counts = probe.get("dom_syntax_skeleton_counts") or {}
    _validate_counts(counts, config)
    shapes = probe.get("blocked_shapes") or []
    candidates = probe.get("candidate_shapes") or []
    if any(shape.get("network_sent") for shape in shapes):
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_BLOCKED_NETWORK_SENT")
    if candidates:
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(f"{ERROR}_UNEXPECTED_DYNAMIC_CANDIDATE", diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates})
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_SYNTAX_SKELETON_DIAGNOSTICS",
        "gate_id": config["gate_id"], "runtime_status": "BOUNDED_TRANSIENT_RENDERED_DOM_KNOWN_SYNTAX_SKELETON_COUNTS_OBSERVED_WITH_UNAPPROVED_NETWORK_BLOCKED",
        "application_surface_verified": True, "fragment_present": bool(probe.get("fragment_present")),
        "dom_syntax_skeleton_counts": counts, "initial_document_continued_count": 1,
        "official_static_asset_network_sent_count": int(probe.get("official_static_asset_network_sent_count", 0)),
        "local_request_count": int(probe.get("local_request_count", 0)), "blocked_shape_count": len(shapes), "blocked_shapes": shapes,
        "candidate_shape_count": 0, "candidate_shapes": [],
        "safety": {"initial_document_network_sent": True, "dynamic_candidate_network_sent": False, "pilot_limeira_values_sent": False,
            "resource_data_request_performed": False, "resource_get_authorized": False, "collection_authorized": False, "processing_authorized": False,
            "recurrence_authorized": False, "schedule_enabled": False, "dom_interaction_performed": False, "navigation_executed": False,
            "form_submission": False, "post_request_performed": False, "head_request_performed": False, "authentication_performed": False,
            "captcha_bypass": False, "credentials_captured": False, "cookies_captured": False, "artifact_downloaded": False,
            "browser_download_denied": True, "dom_text_transient_analysis_performed": True, "dom_text_returned": False,
            "dom_attribute_values_returned": False, "element_text_returned": False, "element_attribute_returned": False,
            "tag_name_returned": False, "fragment_value_returned": False, "html_returned": False, "script_source_returned": False,
            "response_body_persisted": False, "request_body_persisted": False, "query_values_persisted": False,
            "remote_writes": "NONE", "route_synthesized_or_guessed": False, "automatic_route_promotion": False},
        "next_review": config["next_gate"],
    }
