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

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS"


class SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(f"{ERROR}_{code}")


def validate_config(config: dict, design_result: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "PASSIVE_BOOLEAN_ONLY_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS",
        "surface_verification": "EXPECTED_SCHEME_HOST_PATH_EMPTY_QUERY_AND_READY_ELIGIBLE_FRAGMENT_NOT_USED_FOR_IDENTITY",
        "technical_callable_pattern_name": "Dados_Gerais_Siope",
        "technical_parameter_names": ["Ano_Consulta", "Num_Peri", "Sig_UF"],
        "allowed_navigation_attribute_names": ["href", "action"],
        "browser_backend": "SYSTEM_CHROME_CDP",
        "browser_download_or_install": "PROHIBITED",
        "browser_profile": "EPHEMERAL_TEMP_ONLY",
        "initial_document_policy": "CONTINUE_EXACT_APPLICATION_DOCUMENT_ONCE",
        "static_asset_policy": "CONTINUE_OFFICIAL_GET_STATIC_ASSETS_ONLY",
        "dynamic_request_policy": "ABORT_ALL_UNAPPROVED_REQUESTS_BEFORE_NETWORK_AND_RECORD_SANITIZED_SHAPES",
        "allowed_hosts": ["www.fnde.gov.br"],
        "static_asset_methods": ["GET"],
        "static_asset_resource_types": ["Script", "Stylesheet", "Image", "Font"],
        "candidate_methods": ["GET", "POST"],
        "candidate_resource_types": ["XHR", "Fetch"],
        "navigation_attribute_transient_read": "ALLOWED_MATCHING_HREF_ACTION_CLASSIFICATION_BOOLEAN_ONLY",
        "navigation_attribute_value_return": "PROHIBITED",
        "navigation_path_return": "PROHIBITED",
        "navigation_query_return": "PROHIBITED",
        "navigation_fragment_return": "PROHIBITED",
        "element_material_return": "PROHIBITED",
        "tag_name_return": "PROHIBITED",
        "dom_text_return": "PROHIBITED",
        "fragment_value_capture": "PROHIBITED",
        "html_capture": "PROHIBITED",
        "script_source_capture": "PROHIBITED",
        "response_body_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "query_value_persistence": "PROHIBITED",
        "dynamic_candidate_network_send": "PROHIBITED",
        "resource_data_request": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "dom_interaction": "PROHIBITED",
        "navigation_execution": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "post_request_send": "PROHIBITED",
        "head_request": "PROHIBITED",
        "authentication": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "credential_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "remote_writes": "PROHIBITED",
        "route_synthesis_or_guessing": "PROHIBITED",
        "automatic_route_promotion": "PROHIBITED",
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_REVIEW_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(
        design_result.get("status"),
        "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_DESIGN",
        "DESIGN_STATUS",
    )
    _require(design_result.get("returned_observations"), config["returned_boolean_fields"], "DESIGN_FIELDS")
    _require(design_result.get("navigation_execution_authorized"), False, "DESIGN_NAVIGATION_EXECUTION")
    _require(design_result.get("raw_navigation_value_return_authorized"), False, "DESIGN_VALUE_RETURN")
    _require(design_result.get("resource_get_authorized"), False, "DESIGN_RESOURCE_AUTH")

    expected_fields = [
        "navigation_match_present",
        "navigation_match_unique",
        "navigation_attribute_is_href",
        "navigation_attribute_is_action",
        "navigation_value_fragment_only",
        "navigation_value_relative_nonfragment",
        "navigation_value_same_origin_absolute",
        "navigation_value_resolves_to_application_document",
        "navigation_value_contains_callable_name",
        "navigation_value_contains_all_parameter_names",
        "navigation_value_ordered_callable_parameter_sequence",
        "navigation_value_query_present",
        "navigation_value_parentheses_present",
    ]
    _require(config.get("returned_boolean_fields"), expected_fields, "RETURN_FIELDS")

    parsed = urlparse(config["exact_application_url"])
    _require(parsed.scheme, config["expected_scheme"], "SCHEME")
    _require(parsed.hostname, config["expected_host"], "HOST")
    _require(parsed.path, config["expected_path"], "PATH")
    _require(parsed.query, "", "QUERY")
    _require(parsed.fragment, "", "FRAGMENT")
    if "352690" in config["exact_application_url"] or "Limeira" in config["exact_application_url"]:
        raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(f"{ERROR}_PILOT_VALUE")


class SystemChromeCdpDomNavigationAttributeContractRuntime:
    def _find_browser(self, config: dict) -> str:
        for name in config["browser_binary_candidates"]:
            path = shutil.which(name)
            if path:
                return path
        raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(f"{ERROR}_BROWSER_UNAVAILABLE")

    def run_probe(self, config: dict) -> dict:
        browser = self._find_browser(config)
        process = page_session = browser_session = None
        blocked: list[dict] = []
        static_assets_continued = 0
        initial_document_continued = 0
        local_requests_continued = 0
        try:
            with tempfile.TemporaryDirectory(prefix="siope-olinda-nav-contract-", ignore_cleanup_errors=True) as profile_text:
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
                browser_session = _connect_cdp_with_retry(
                    str(version_info["webSocketDebuggerUrl"]), command_timeout_s=timeout_s, process=process
                )
                browser_session.command("Browser.setDownloadBehavior", {"behavior": "deny"})
                target = _create_page_target(port)
                page_session = _connect_cdp_with_retry(
                    str(target["webSocketDebuggerUrl"]), command_timeout_s=timeout_s, process=process
                )

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
                        return
                    if _matches_exact_application_document(url, method, resource_type, config) and initial_document_continued == 0:
                        initial_document_continued += 1
                        page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                        return
                    if _is_allowed_static_asset(url, method, resource_type, config):
                        static_assets_continued += 1
                        page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                        return
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
                    raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(
                        f"{ERROR}_APPLICATION_SURFACE_NOT_VERIFIED",
                        diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates},
                    )

                page_session.pump(float(config["capture_window_ms"]) / 1000.0)
                callable_literal = json.dumps(config["technical_callable_pattern_name"])
                parameter_literals = ",".join(json.dumps(value) for value in config["technical_parameter_names"])
                nav_expr = f"""(() => {{
                  const callableName = {callable_literal};
                  const params = [{parameter_literals}];
                  const names = ['href', 'action'];
                  const matches = [];
                  for (const el of Array.from(document.querySelectorAll('*'))) {{
                    for (const name of names) {{
                      const value = el.getAttribute && el.getAttribute(name);
                      if (typeof value === 'string' && value.includes(callableName)) {{
                        matches.push({{name, value}});
                      }}
                    }}
                  }}
                  const unique = matches.length === 1;
                  const match = unique ? matches[0] : null;
                  const value = match ? match.value : '';
                  let resolved = null;
                  if (match) {{
                    try {{ resolved = new URL(value, document.baseURI); }} catch (_) {{ resolved = null; }}
                  }}
                  const absoluteHttp = /^https?:\/\//i.test(value);
                  const protocolRelative = /^\/\//.test(value);
                  const fragmentOnly = value.startsWith('#');
                  const relativeNonfragment = !!match && !fragmentOnly && !absoluteHttp && !protocolRelative && !/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(value);
                  const positions = [callableName, ...params].map((token) => value.indexOf(token));
                  const ordered = positions.every((position) => position >= 0) && positions.every((position, index) => index === 0 || position > positions[index - 1]);
                  const sameOriginAbsolute = !!match && absoluteHttp && !!resolved && resolved.origin === window.location.origin;
                  const resolvesApplication = !!match && !!resolved && resolved.origin === window.location.origin && resolved.pathname === window.location.pathname && resolved.search === window.location.search;
                  return {{
                    navigation_match_present: matches.length > 0,
                    navigation_match_unique: unique,
                    navigation_attribute_is_href: unique && match.name === 'href',
                    navigation_attribute_is_action: unique && match.name === 'action',
                    navigation_value_fragment_only: unique && fragmentOnly,
                    navigation_value_relative_nonfragment: unique && relativeNonfragment,
                    navigation_value_same_origin_absolute: unique && sameOriginAbsolute,
                    navigation_value_resolves_to_application_document: unique && resolvesApplication,
                    navigation_value_contains_callable_name: unique && value.includes(callableName),
                    navigation_value_contains_all_parameter_names: unique && params.every((param) => value.includes(param)),
                    navigation_value_ordered_callable_parameter_sequence: unique && ordered,
                    navigation_value_query_present: unique && !!resolved && resolved.search.length > 0,
                    navigation_value_parentheses_present: unique && value.includes('(') && value.includes(')')
                  }};
                }})()"""
                evaluation = page_session.command("Runtime.evaluate", {"expression": nav_expr, "returnByValue": True})
                signature = ((evaluation.get("result") or {}).get("value") or {})
                expected_keys = set(config["returned_boolean_fields"])
                if set(signature) != expected_keys or any(type(signature[k]) is not bool for k in expected_keys):
                    raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(f"{ERROR}_BOOLEAN_SIGNATURE_CONTRACT")

                final_eval = page_session.command("Runtime.evaluate", {"expression": surface_expr, "returnByValue": True})
                final_surface = ((final_eval.get("result") or {}).get("value") or {})
                if not all(final_surface.get(k) is True for k in ("scheme_matches", "host_matches", "path_matches", "query_empty", "ready_eligible")):
                    raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(f"{ERROR}_SURFACE_DRIFT")

                shapes, candidates = summarize_blocked_requests(blocked, config)
                if len(shapes) > config["max_blocked_shapes"]:
                    raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(f"{ERROR}_SHAPE_LIMIT")
                return {
                    "initial_document_continued_count": initial_document_continued,
                    "static_assets_continued_count": static_assets_continued,
                    "local_requests_continued_count": local_requests_continued,
                    "application_surface_verified": True,
                    "fragment_present": bool(final_surface.get("fragment_present")),
                    "navigation_boolean_signature": signature,
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
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS_DRY_RUN",
        "gate_id": config["gate_id"],
        "network_called": False,
        "initial_document_network_sent": False,
        "dynamic_candidate_network_sent": False,
        "dom_interaction_performed": False,
        "navigation_executed": False,
        "navigation_attribute_value_returned": False,
        "navigation_path_returned": False,
        "navigation_query_returned": False,
        "navigation_fragment_returned": False,
        "element_material_returned": False,
        "pilot_limeira_values_sent": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def run_navigation_attribute_contract_diagnostics(config: dict, design_result: dict, *, runtime=None) -> dict:
    validate_config(config, design_result)
    runtime = runtime or SystemChromeCdpDomNavigationAttributeContractRuntime()
    probe = runtime.run_probe(config)
    _require(probe.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(probe.get("application_surface_verified"), True, "SURFACE")
    _require(probe.get("browser_download_denied"), True, "DOWNLOAD_DENIAL")

    signature = probe.get("navigation_boolean_signature") or {}
    expected_keys = set(config["returned_boolean_fields"])
    if set(signature) != expected_keys or any(type(signature[k]) is not bool for k in expected_keys):
        raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(f"{ERROR}_BOOLEAN_SIGNATURE_CONTRACT")
    if signature["navigation_match_unique"] and not signature["navigation_match_present"]:
        raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(f"{ERROR}_UNIQUE_WITHOUT_MATCH")
    if signature["navigation_attribute_is_href"] and signature["navigation_attribute_is_action"]:
        raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(f"{ERROR}_ATTRIBUTE_KIND_CONFLICT")
    if not signature["navigation_match_unique"] and any(signature[key] for key in expected_keys - {"navigation_match_present", "navigation_match_unique"}):
        raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(f"{ERROR}_DETAIL_WITHOUT_UNIQUE_MATCH")

    shapes = probe.get("blocked_shapes") or []
    candidates = probe.get("candidate_shapes") or []
    if any(shape.get("network_sent") is not False or shape.get("intercepted_before_network") is not True for shape in shapes):
        raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(f"{ERROR}_BLOCK_POLICY")
    if any(candidate.get("candidate_dynamic_request") is not True for candidate in candidates):
        raise SiopeOfficialOlindaApiApplicationDomNavigationAttributeContractDiagnosticsError(f"{ERROR}_CANDIDATE_CLASSIFICATION")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_DOM_NAVIGATION_ATTRIBUTE_CONTRACT_DIAGNOSTICS",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "runtime_status": "BOOLEAN_ONLY_NAVIGATION_ATTRIBUTE_CONTRACT_OBSERVED_WITH_UNAPPROVED_NETWORK_BLOCKED",
        "application_surface_verified": True,
        "fragment_present": bool(probe.get("fragment_present")),
        "fragment_value_returned": False,
        "navigation_boolean_signature": signature,
        "matched_navigation_relation_count": sum(1 for value in signature.values() if value),
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
        "navigation_attribute_value_returned": False,
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
