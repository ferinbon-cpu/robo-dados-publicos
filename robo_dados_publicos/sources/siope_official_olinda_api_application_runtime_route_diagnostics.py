from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from urllib.parse import parse_qsl, urlparse

from .siope_artifact_download_event_diagnostics import (
    _connect_cdp_with_retry,
    _create_page_target,
    _wait_browser_debug_version,
    _wait_devtools_active_port,
)


ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS"


class SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError(f"{ERROR}_{code}")


def validate_config(config: dict, design: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "PASSIVE_OFFICIAL_APPLICATION_RUNTIME_REQUEST_INTERCEPT",
        "design_config_path": "config/source_expansion.siope_official_olinda_api_application_runtime_route_diagnostics_design.json",
        "design_config_git_blob_sha": "2a527ba673db771e8232875381f3322f381f5ca7",
        "exact_application_url": "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/aplicacao",
        "expected_scheme": "https",
        "expected_host": "www.fnde.gov.br",
        "expected_path": "/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/aplicacao",
        "browser_backend": "SYSTEM_CHROME_CDP",
        "browser_download_or_install": "PROHIBITED",
        "browser_profile": "EPHEMERAL_TEMP_ONLY",
        "initial_document_policy": "CONTINUE_EXACT_APPLICATION_DOCUMENT_ONCE",
        "static_asset_policy": "CONTINUE_OFFICIAL_GET_STATIC_ASSETS_ONLY",
        "dynamic_request_policy": "ABORT_ALL_DYNAMIC_BEFORE_NETWORK_AND_RECORD_SANITIZED_SHAPES",
        "allowed_hosts": ["www.fnde.gov.br"],
        "static_asset_methods": ["GET"],
        "static_asset_resource_types": ["Script", "Stylesheet", "Image", "Font"],
        "candidate_methods": ["GET", "POST"],
        "candidate_resource_types": ["XHR", "Fetch"],
        "surface_verification": "DOCUMENT_LOCATION_AND_READY_STATE_BOOLEAN_ONLY",
        "body_text_capture": "PROHIBITED",
        "html_capture": "PROHIBITED",
        "script_source_capture": "PROHIBITED",
        "response_body_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "query_value_persistence": "PROHIBITED",
        "dynamic_candidate_network_send": "PROHIBITED",
        "resource_data_request": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "dom_interaction": "PROHIBITED",
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
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_REVIEW_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(config.get("browser_binary_candidates"), ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"], "CONFIG_BROWSER_BINARIES")
    extensions = config.get("static_asset_extensions")
    if not isinstance(extensions, list) or not extensions or any(not isinstance(v, str) or not v.startswith(".") for v in extensions):
        raise SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_STATIC_EXTENSIONS")

    parsed = urlparse(config["exact_application_url"])
    _require(parsed.scheme, config["expected_scheme"], "APPLICATION_SCHEME")
    _require(parsed.hostname, config["expected_host"], "APPLICATION_HOST")
    _require(parsed.path, config["expected_path"], "APPLICATION_PATH")
    _require(parsed.query, "", "APPLICATION_QUERY")
    _require(parsed.fragment, "", "APPLICATION_FRAGMENT")
    if "352690" in config["exact_application_url"]:
        raise SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError(f"{ERROR}_PILOT_VALUE")

    for key, minimum, maximum in (
        ("page_load_timeout_ms", 1000, 30000),
        ("capture_window_ms", 1000, 10000),
        ("cdp_command_timeout_ms", 1000, 10000),
        ("max_blocked_shapes", 1, 256),
    ):
        value = config.get(key)
        if not isinstance(value, int) or not minimum <= value <= maximum:
            raise SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_{key.upper()}")

    _require(design.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_DESIGN_0_8_0", "DESIGN_GATE")
    _require(design.get("dynamic_request_policy"), config["dynamic_request_policy"], "DESIGN_DYNAMIC_POLICY")
    _require(design.get("resource_data_request"), "PROHIBITED", "DESIGN_RESOURCE_REQUEST")
    _require(design.get("pilot_limeira_values_send"), "PROHIBITED", "DESIGN_PILOT")
    _require(design.get("collection_authorized"), False, "DESIGN_COLLECTION")
    _require(design.get("next_gate"), config["gate_id"], "DESIGN_NEXT_GATE")


def _route_shape(url: str, method: str, resource_type: str, config: dict) -> dict | None:
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    route_without_query = f"{parsed.scheme}://{parsed.hostname}{parsed.path or '/'}"
    query_keys = sorted({key for key, _ in parse_qsl(parsed.query, keep_blank_values=True)})
    method = str(method).upper()[:16]
    resource_type = str(resource_type)[:40]
    official = parsed.hostname in set(config["allowed_hosts"])
    candidate = method in set(config["candidate_methods"]) and resource_type in set(config["candidate_resource_types"]) and official
    return {
        "method": method,
        "resource_type": resource_type,
        "scheme": parsed.scheme,
        "host": parsed.hostname,
        "route_without_query": route_without_query,
        "query_present": bool(parsed.query),
        "query_keys": query_keys,
        "official_host": official,
        "candidate_dynamic_request": candidate,
        "network_sent": False,
        "intercepted_before_network": True,
    }


def summarize_blocked_requests(events: list[dict], config: dict) -> tuple[list[dict], list[dict]]:
    dedup: dict[tuple[str, str, str], dict] = {}
    for event in events:
        shaped = _route_shape(str(event.get("url", "")), str(event.get("method", "")), str(event.get("resource_type", "Other")), config)
        if shaped is None:
            continue
        key = (shaped["method"], shaped["resource_type"], shaped["route_without_query"])
        if key not in dedup:
            dedup[key] = {**shaped, "occurrences": 0}
        dedup[key]["occurrences"] += 1
        dedup[key]["query_keys"] = sorted(set(dedup[key]["query_keys"]).union(shaped["query_keys"]))
        dedup[key]["query_present"] = bool(dedup[key]["query_present"] or shaped["query_present"])
    shapes = [dedup[key] for key in sorted(dedup)]
    candidates = [shape for shape in shapes if shape["candidate_dynamic_request"]]
    return shapes, candidates


def _matches_exact_application_document(url: str, method: str, resource_type: str, config: dict) -> bool:
    if method.upper() != "GET" or resource_type != "Document":
        return False
    expected = urlparse(config["exact_application_url"])
    observed = urlparse(url)
    return (
        observed.scheme == expected.scheme
        and observed.hostname == expected.hostname
        and observed.path == expected.path
        and not observed.query
        and not observed.fragment
        and not observed.username
        and not observed.password
    )


def _is_allowed_static_asset(url: str, method: str, resource_type: str, config: dict) -> bool:
    parsed = urlparse(url)
    if (
        method.upper() not in set(config["static_asset_methods"])
        or resource_type not in set(config["static_asset_resource_types"])
        or parsed.scheme != "https"
        or parsed.hostname not in set(config["allowed_hosts"])
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        return False
    path = parsed.path.casefold()
    return any(path.endswith(ext.casefold()) for ext in config["static_asset_extensions"])


class SystemChromeCdpApplicationRouteRuntime:
    def _find_browser(self, config: dict) -> str:
        for name in config["browser_binary_candidates"]:
            path = shutil.which(name)
            if path:
                return path
        raise SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError(f"{ERROR}_BROWSER_UNAVAILABLE")

    def run_probe(self, config: dict) -> dict:
        browser = self._find_browser(config)
        process = page_session = browser_session = None
        blocked: list[dict] = []
        static_assets_continued = 0
        initial_document_continued = 0
        local_requests_continued = 0
        try:
            with tempfile.TemporaryDirectory(prefix="siope-olinda-application-runtime-", ignore_cleanup_errors=True) as profile_text:
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

                target_url_literal = json.dumps(config["exact_application_url"])
                inspect_expr = f"""(() => ({{
                  location_matches: window.location.href === {target_url_literal},
                  ready: document.readyState === 'interactive' || document.readyState === 'complete'
                }}))()"""
                surface = None
                deadline = time.monotonic() + float(config["page_load_timeout_ms"]) / 1000.0
                while time.monotonic() < deadline:
                    evaluation = page_session.command("Runtime.evaluate", {"expression": inspect_expr, "returnByValue": True})
                    surface = ((evaluation.get("result") or {}).get("value") or {})
                    if surface.get("location_matches") and surface.get("ready"):
                        break
                    page_session.pump(0.15)
                if not surface or not (surface.get("location_matches") and surface.get("ready")):
                    shapes, candidates = summarize_blocked_requests(blocked, config)
                    raise SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError(
                        f"{ERROR}_APPLICATION_SURFACE_NOT_VERIFIED",
                        diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates},
                    )

                page_session.pump(float(config["capture_window_ms"]) / 1000.0)
                shapes, candidates = summarize_blocked_requests(blocked, config)
                if len(shapes) > config["max_blocked_shapes"]:
                    raise SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError(
                        f"{ERROR}_SHAPE_LIMIT",
                        diagnostics={"blocked_shape_count": len(shapes)},
                    )
                return {
                    "initial_document_continued_count": initial_document_continued,
                    "static_assets_continued_count": static_assets_continued,
                    "local_requests_continued_count": local_requests_continued,
                    "application_surface_verified": True,
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


def dry_run(config: dict, design: dict) -> dict:
    validate_config(config, design)
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_DRY_RUN",
        "gate_id": config["gate_id"],
        "network_called": False,
        "initial_document_network_sent": False,
        "dynamic_candidate_network_sent": False,
        "pilot_limeira_values_sent": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def run_application_route_diagnostics(config: dict, design: dict, *, runtime=None) -> dict:
    validate_config(config, design)
    runtime = runtime or SystemChromeCdpApplicationRouteRuntime()
    probe = runtime.run_probe(config)
    _require(probe.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(probe.get("application_surface_verified"), True, "APPLICATION_SURFACE")
    _require(probe.get("browser_download_denied"), True, "DOWNLOAD_DENIAL")

    shapes = probe.get("blocked_shapes") or []
    candidates = probe.get("candidate_shapes") or []
    if len(shapes) > config["max_blocked_shapes"]:
        raise SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError(f"{ERROR}_SHAPE_LIMIT")
    if any(shape.get("network_sent") is not False or shape.get("intercepted_before_network") is not True for shape in shapes):
        raise SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError(f"{ERROR}_BLOCK_POLICY")
    if any(candidate.get("candidate_dynamic_request") is not True for candidate in candidates):
        raise SiopeOfficialOlindaApiApplicationRuntimeRouteDiagnosticsError(f"{ERROR}_CANDIDATE_CLASSIFICATION")

    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "release_status": config["release_status"],
        "runtime_status": "OFFICIAL_APPLICATION_DYNAMIC_ROUTES_INTERCEPTED_BEFORE_NETWORK",
        "application_surface_verified": True,
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
        "body_text_returned": False,
        "html_returned": False,
        "script_source_returned": False,
        "response_body_persisted": False,
        "request_body_persisted": False,
        "query_values_persisted": False,
        "resource_data_request_performed": False,
        "pilot_limeira_values_sent": False,
        "dom_interaction_performed": False,
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
