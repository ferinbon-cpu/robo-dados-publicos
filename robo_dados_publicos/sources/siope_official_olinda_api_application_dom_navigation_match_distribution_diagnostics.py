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

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS"
COUNT_FIELDS = [
    "navigation_match_count",
    "href_match_count",
    "action_match_count",
    "fragment_only_match_count",
    "relative_nonfragment_match_count",
    "same_origin_absolute_match_count",
    "resolves_to_application_document_match_count",
    "contains_all_parameter_names_match_count",
    "ordered_callable_parameter_sequence_match_count",
    "query_present_match_count",
    "parentheses_present_match_count",
    "callable_parameter_contract_like_match_count",
    "same_origin_contract_like_match_count",
]


class SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_{code}")


def validate_config(config: dict, design_result: dict) -> None:
    _require(config.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS_0_8_0", "GATE")
    _require(config.get("mode"), "PASSIVE_COUNT_ONLY_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS", "MODE")
    _require(config.get("software_version"), "0.8.0", "VERSION")
    _require(config.get("technical_callable_pattern_name"), "Dados_Gerais_Siope", "CALLABLE")
    _require(config.get("technical_parameter_names"), ["Ano_Consulta", "Num_Peri", "Sig_UF"], "PARAMS")
    _require(config.get("allowed_navigation_attribute_names"), ["href", "action"], "ATTRS")
    _require(config.get("returned_count_fields"), COUNT_FIELDS, "FIELDS")
    _require(config.get("max_navigation_matches"), 32, "MAX")
    _require(config.get("minimum_navigation_matches"), 2, "MIN")
    _require(design_result.get("status"), "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS_DESIGN", "DESIGN")
    _require(design_result.get("returned_observations"), COUNT_FIELDS, "DESIGN_FIELDS")
    _require(design_result.get("raw_navigation_value_return_authorized"), False, "DESIGN_RAW")
    _require(design_result.get("navigation_execution_authorized"), False, "DESIGN_NAV")
    _require(design_result.get("resource_get_authorized"), False, "DESIGN_RESOURCE")
    parsed = urlparse(config["exact_application_url"])
    _require(parsed.scheme, config["expected_scheme"], "SCHEME")
    _require(parsed.hostname, config["expected_host"], "HOST")
    _require(parsed.path, config["expected_path"], "PATH")
    _require(parsed.query, "", "QUERY")
    _require(parsed.fragment, "", "FRAGMENT")
    if "352690" in config["exact_application_url"] or "Limeira" in config["exact_application_url"]:
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_PILOT_VALUE")
    for key in ("resource_get_authorized", "collection_authorized", "processing_authorized", "recurrence_authorized", "schedule_enabled"):
        _require(config.get(key), False, f"CONFIG_{key.upper()}")


class SystemChromeCdpDomNavigationMatchDistributionRuntime:
    def _find_browser(self, config: dict) -> str:
        for name in config["browser_binary_candidates"]:
            path = shutil.which(name)
            if path:
                return path
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_BROWSER_UNAVAILABLE")

    def run_probe(self, config: dict) -> dict:
        browser = self._find_browser(config)
        process = page_session = browser_session = None
        blocked: list[dict] = []
        static_assets_continued = 0
        initial_document_continued = 0
        local_requests_continued = 0
        try:
            with tempfile.TemporaryDirectory(prefix="siope-olinda-nav-dist-", ignore_cleanup_errors=True) as profile_text:
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
                    raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_APPLICATION_SURFACE_NOT_VERIFIED", diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates})

                page_session.pump(float(config["capture_window_ms"]) / 1000.0)
                callable_literal = json.dumps(config["technical_callable_pattern_name"])
                parameter_literals = ",".join(json.dumps(value) for value in config["technical_parameter_names"])
                count_expr = f"""(() => {{
                  const callableName = {callable_literal};
                  const params = [{parameter_literals}];
                  const matches = [];
                  for (const el of Array.from(document.querySelectorAll('*'))) {{
                    for (const name of ['href', 'action']) {{
                      const value = el.getAttribute && el.getAttribute(name);
                      if (typeof value === 'string' && value.includes(callableName)) matches.push({{name, value}});
                    }}
                  }}
                  const counts = Object.fromEntries({json.dumps(COUNT_FIELDS)}.map((k) => [k, 0]));
                  counts.navigation_match_count = matches.length;
                  for (const match of matches) {{
                    const value = match.value;
                    const absoluteHttp = value.startsWith('http://') || value.startsWith('https://');
                    const protocolRelative = value.startsWith('//');
                    const fragmentOnly = value.startsWith('#');
                    const hasScheme = /^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(value);
                    const relativeNonfragment = !fragmentOnly && !absoluteHttp && !protocolRelative && !hasScheme;
                    let resolved = null;
                    try {{ resolved = new URL(value, document.baseURI); }} catch (_) {{ resolved = null; }}
                    const sameOriginAbsolute = absoluteHttp && !!resolved && resolved.origin === window.location.origin;
                    const resolvesApplication = !!resolved && resolved.origin === window.location.origin && resolved.pathname === window.location.pathname && resolved.search === window.location.search;
                    const allParams = params.every((param) => value.includes(param));
                    const positions = [callableName, ...params].map((token) => value.indexOf(token));
                    const ordered = positions.every((position) => position >= 0) && positions.every((position, index) => index === 0 || position > positions[index - 1]);
                    const queryPresent = !!resolved && resolved.search.length > 0;
                    const parens = value.includes('(') && value.includes(')');
                    const contractLike = allParams && ordered && parens;
                    const sameOriginContractLike = contractLike && !!resolved && resolved.origin === window.location.origin;
                    if (match.name === 'href') counts.href_match_count++;
                    if (match.name === 'action') counts.action_match_count++;
                    if (fragmentOnly) counts.fragment_only_match_count++;
                    if (relativeNonfragment) counts.relative_nonfragment_match_count++;
                    if (sameOriginAbsolute) counts.same_origin_absolute_match_count++;
                    if (resolvesApplication) counts.resolves_to_application_document_match_count++;
                    if (allParams) counts.contains_all_parameter_names_match_count++;
                    if (ordered) counts.ordered_callable_parameter_sequence_match_count++;
                    if (queryPresent) counts.query_present_match_count++;
                    if (parens) counts.parentheses_present_match_count++;
                    if (contractLike) counts.callable_parameter_contract_like_match_count++;
                    if (sameOriginContractLike) counts.same_origin_contract_like_match_count++;
                  }}
                  return counts;
                }})()"""
                evaluation = page_session.command("Runtime.evaluate", {"expression": count_expr, "returnByValue": True})
                counts = ((evaluation.get("result") or {}).get("value") or {})
                final_eval = page_session.command("Runtime.evaluate", {"expression": surface_expr, "returnByValue": True})
                final_surface = ((final_eval.get("result") or {}).get("value") or {})
                if not all(final_surface.get(k) is True for k in ("scheme_matches", "host_matches", "path_matches", "query_empty", "ready_eligible")):
                    raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_SURFACE_DRIFT")
                shapes, candidates = summarize_blocked_requests(blocked, config)
                if len(shapes) > config["max_blocked_shapes"]:
                    raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_SHAPE_LIMIT")
                return {
                    "initial_document_continued_count": initial_document_continued,
                    "static_assets_continued_count": static_assets_continued,
                    "local_requests_continued_count": local_requests_continued,
                    "application_surface_verified": True,
                    "fragment_present": bool(final_surface.get("fragment_present")),
                    "navigation_match_distribution_counts": counts,
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
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS_DRY_RUN",
        "gate_id": config["gate_id"],
        "network_called": False,
        "initial_document_network_sent": False,
        "dynamic_candidate_network_sent": False,
        "dom_interaction_performed": False,
        "navigation_executed": False,
        "raw_navigation_value_returned": False,
        "pilot_limeira_values_sent": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def run_navigation_match_distribution_diagnostics(config: dict, design_result: dict, *, runtime=None) -> dict:
    validate_config(config, design_result)
    runtime = runtime or SystemChromeCdpDomNavigationMatchDistributionRuntime()
    probe = runtime.run_probe(config)
    _require(probe.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(probe.get("application_surface_verified"), True, "SURFACE")
    _require(probe.get("browser_download_denied"), True, "DOWNLOAD_DENIAL")
    counts = probe.get("navigation_match_distribution_counts") or {}
    if set(counts) != set(COUNT_FIELDS) or any(type(counts[k]) is not int for k in COUNT_FIELDS):
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_COUNT_CONTRACT")
    total = counts["navigation_match_count"]
    if total < config["minimum_navigation_matches"]:
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_MULTIPLE_MATCH_PREREQUISITE_LOST")
    if total > config["max_navigation_matches"]:
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_MATCH_LIMIT")
    if counts["href_match_count"] + counts["action_match_count"] != total:
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_ATTRIBUTE_PARTITION")
    if any(value < 0 or value > total for value in counts.values()):
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_COUNT_RANGE")
    if counts["callable_parameter_contract_like_match_count"] > counts["contains_all_parameter_names_match_count"]:
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_CONTRACT_SUBSET")
    if counts["same_origin_contract_like_match_count"] > counts["callable_parameter_contract_like_match_count"]:
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_SAME_ORIGIN_SUBSET")
    shapes = probe.get("blocked_shapes") or []
    candidates = probe.get("candidate_shapes") or []
    if any(shape.get("network_sent") is not False or shape.get("intercepted_before_network") is not True for shape in shapes):
        raise SiopeOfficialOlindaApiApplicationDomNavigationMatchDistributionDiagnosticsError(f"{ERROR}_BLOCK_POLICY")
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_MATCH_DISTRIBUTION_DIAGNOSTICS",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "runtime_status": "BOUNDED_COUNT_ONLY_NAVIGATION_MATCH_DISTRIBUTION_OBSERVED_WITH_UNAPPROVED_NETWORK_BLOCKED",
        "application_surface_verified": True,
        "fragment_present": bool(probe.get("fragment_present")),
        "fragment_value_returned": False,
        "navigation_match_distribution_counts": counts,
        "initial_document_network_sent": True,
        "initial_document_continued_count": 1,
        "official_static_asset_network_sent_count": int(probe.get("static_assets_continued_count", 0)),
        "local_request_count": int(probe.get("local_requests_continued_count", 0)),
        "blocked_shape_count": len(shapes),
        "blocked_shapes": shapes,
        "candidate_shape_count": len(candidates),
        "candidate_shapes": candidates,
        "dynamic_candidate_network_sent": False,
        "browser_download_denied": True,
        "dom_interaction_performed": False,
        "navigation_executed": False,
        "raw_navigation_value_returned": False,
        "navigation_path_returned": False,
        "navigation_query_returned": False,
        "navigation_fragment_returned": False,
        "element_material_returned": False,
        "tag_name_returned": False,
        "dom_text_returned": False,
        "html_returned": False,
        "script_source_returned": False,
        "response_body_persisted": False,
        "request_body_persisted": False,
        "query_values_persisted": False,
        "resource_data_request_performed": False,
        "resource_get_authorized": False,
        "pilot_limeira_values_sent": False,
        "form_submission": False,
        "post_request_performed": False,
        "head_request_performed": False,
        "authentication_performed": False,
        "captcha_bypass": False,
        "credentials_captured": False,
        "cookies_captured": False,
        "artifact_downloaded": False,
        "remote_writes": "NONE",
        "route_synthesized_or_guessed": False,
        "automatic_route_promotion": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
