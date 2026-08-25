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

ERROR = "STOP_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS"


class SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_{code}")


def validate_config(config: dict, review: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "PASSIVE_OFFICIAL_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS",
        "review_config_path": "config/source_expansion.siope_official_olinda_api_application_runtime_route_diagnostics_review.json",
        "exact_application_url": "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/aplicacao",
        "expected_scheme": "https",
        "expected_host": "www.fnde.gov.br",
        "expected_path": "/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/aplicacao",
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
        "returned_surface_boolean_fields": ["scheme_matches", "host_matches", "path_matches", "query_empty", "fragment_empty", "href_exact", "ready_interactive", "ready_complete", "ready_eligible"],
        "observation_points": ["FIRST_POST_DOCUMENT_BOOLEAN_SNAPSHOT", "FINAL_PASSIVE_WINDOW_BOOLEAN_SNAPSHOT"],
        "body_text_capture": "PROHIBITED",
        "html_capture": "PROHIBITED",
        "script_source_capture": "PROHIBITED",
        "actual_location_return": "PROHIBITED",
        "ready_state_string_return": "PROHIBITED",
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
        "surface_authorized": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS_REVIEW_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")
    _require(config.get("browser_binary_candidates"), ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"], "CONFIG_BROWSER_BINARIES")
    extensions = config.get("static_asset_extensions")
    if not isinstance(extensions, list) or not extensions or any(not isinstance(v, str) or not v.startswith(".") for v in extensions):
        raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_CONFIG_STATIC_EXTENSIONS")
    for key, minimum, maximum in (("page_load_timeout_ms", 1000, 30000), ("capture_window_ms", 1000, 10000), ("cdp_command_timeout_ms", 1000, 10000), ("max_blocked_shapes", 1, 256)):
        value = config.get(key)
        if not isinstance(value, int) or not minimum <= value <= maximum:
            raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_CONFIG_{key.upper()}")
    parsed = urlparse(config["exact_application_url"])
    _require(parsed.scheme, config["expected_scheme"], "APPLICATION_SCHEME")
    _require(parsed.hostname, config["expected_host"], "APPLICATION_HOST")
    _require(parsed.path, config["expected_path"], "APPLICATION_PATH")
    _require(parsed.query, "", "APPLICATION_QUERY")
    _require(parsed.fragment, "", "APPLICATION_FRAGMENT")
    if "352690" in config["exact_application_url"]:
        raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_PILOT_VALUE")
    _require(review.get("gate_id"), "M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_RUNTIME_ROUTE_DIAGNOSTICS_REVIEW_0_8_0", "REVIEW_GATE")
    _require(review.get("surface_disposition"), "UNVERIFIED_ON_PINNED_RUN", "REVIEW_SURFACE")
    _require(review.get("failure_classification"), "INSUFFICIENT_BOOLEAN_TELEMETRY_TO_DISTINGUISH_LOCATION_FROM_READY_STATE", "REVIEW_FAILURE_CLASS")
    _require(review.get("collection_authorized"), False, "REVIEW_COLLECTION")
    _require(review.get("next_gate"), config["gate_id"], "REVIEW_NEXT_GATE")


def _sanitize_snapshot(value: dict, config: dict) -> dict:
    fields = config["returned_surface_boolean_fields"]
    if not isinstance(value, dict) or set(value) != set(fields):
        raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_SNAPSHOT_FIELDS")
    if any(type(value[field]) is not bool for field in fields):
        raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_SNAPSHOT_BOOLEAN_REQUIRED")
    if value["ready_eligible"] != (value["ready_interactive"] or value["ready_complete"]):
        raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_SNAPSHOT_READY_RELATION")
    return {field: value[field] for field in fields}


class SystemChromeCdpSurfaceBooleanRuntime:
    def _find_browser(self, config: dict) -> str:
        for name in config["browser_binary_candidates"]:
            path = shutil.which(name)
            if path:
                return path
        raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_BROWSER_UNAVAILABLE")

    def run_probe(self, config: dict) -> dict:
        browser = self._find_browser(config)
        process = page_session = browser_session = None
        blocked: list[dict] = []
        static_assets_continued = 0
        initial_document_continued = 0
        local_requests_continued = 0
        first_observation = None
        final_observation = None
        try:
            with tempfile.TemporaryDirectory(prefix="siope-olinda-surface-bool-", ignore_cleanup_errors=True) as profile_text:
                profile = Path(profile_text)
                cmd = [browser, "--headless=new", "--remote-debugging-port=0", "--remote-debugging-address=127.0.0.1", "--remote-allow-origins=*", f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check", "--disable-background-networking", "--disable-component-update", "--disable-sync", "--disable-default-apps", "--disable-extensions", "--disable-features=MediaRouter", "--metrics-recording-only", "--no-sandbox", "about:blank"]
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

                scheme_literal = json.dumps(config["expected_scheme"] + ":")
                host_literal = json.dumps(config["expected_host"])
                path_literal = json.dumps(config["expected_path"])
                href_literal = json.dumps(config["exact_application_url"])
                expression = f"""(() => ({{
                  scheme_matches: window.location.protocol === {scheme_literal},
                  host_matches: window.location.hostname === {host_literal},
                  path_matches: window.location.pathname === {path_literal},
                  query_empty: window.location.search === '',
                  fragment_empty: window.location.hash === '',
                  href_exact: window.location.href === {href_literal},
                  ready_interactive: document.readyState === 'interactive',
                  ready_complete: document.readyState === 'complete',
                  ready_eligible: document.readyState === 'interactive' || document.readyState === 'complete'
                }}))()"""

                deadline = time.monotonic() + float(config["page_load_timeout_ms"]) / 1000.0
                while time.monotonic() < deadline:
                    page_session.pump(0.15)
                    if initial_document_continued != 1:
                        continue
                    evaluation = page_session.command("Runtime.evaluate", {"expression": expression, "returnByValue": True})
                    raw = ((evaluation.get("result") or {}).get("value") or {})
                    first_observation = _sanitize_snapshot(raw, config)
                    break
                if initial_document_continued != 1 or first_observation is None:
                    shapes, candidates = summarize_blocked_requests(blocked, config)
                    raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_FIRST_SNAPSHOT_UNAVAILABLE", diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates})

                page_session.pump(float(config["capture_window_ms"]) / 1000.0)
                final_eval = page_session.command("Runtime.evaluate", {"expression": expression, "returnByValue": True})
                final_raw = ((final_eval.get("result") or {}).get("value") or {})
                final_observation = _sanitize_snapshot(final_raw, config)
                shapes, candidates = summarize_blocked_requests(blocked, config)
                if len(shapes) > config["max_blocked_shapes"]:
                    raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_SHAPE_LIMIT", diagnostics={"blocked_shape_count": len(shapes)})
                return {
                    "initial_document_continued_count": initial_document_continued,
                    "static_assets_continued_count": static_assets_continued,
                    "local_requests_continued_count": local_requests_continued,
                    "first_observation": first_observation,
                    "final_observation": final_observation,
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


def dry_run(config: dict, review: dict) -> dict:
    validate_config(config, review)
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS_DRY_RUN",
        "gate_id": config["gate_id"],
        "network_called": False,
        "initial_document_network_sent": False,
        "dynamic_candidate_network_sent": False,
        "pilot_limeira_values_sent": False,
        "surface_authorized": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }


def run_surface_boolean_diagnostics(config: dict, review: dict, *, runtime=None) -> dict:
    validate_config(config, review)
    runtime = runtime or SystemChromeCdpSurfaceBooleanRuntime()
    probe = runtime.run_probe(config)
    _require(probe.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(probe.get("browser_download_denied"), True, "DOWNLOAD_DENIAL")
    first = _sanitize_snapshot(probe.get("first_observation"), config)
    final = _sanitize_snapshot(probe.get("final_observation"), config)
    shapes = probe.get("blocked_shapes") or []
    candidates = probe.get("candidate_shapes") or []
    if len(shapes) > config["max_blocked_shapes"]:
        raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_SHAPE_LIMIT")
    if any(shape.get("network_sent") is not False or shape.get("intercepted_before_network") is not True for shape in shapes):
        raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_BLOCK_POLICY")
    if any(candidate.get("candidate_dynamic_request") is not True for candidate in candidates):
        raise SiopeOfficialOlindaApiApplicationSurfaceBooleanDiagnosticsError(f"{ERROR}_CANDIDATE_CLASSIFICATION")
    return {
        "status": "PASS_M7_SIOPE_OFFICIAL_OLINDA_API_APPLICATION_SURFACE_BOOLEAN_DIAGNOSTICS",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "release_status": config["release_status"],
        "runtime_status": "OFFICIAL_APPLICATION_SURFACE_BOOLEAN_RELATIONS_OBSERVED",
        "first_observation": first,
        "final_observation": final,
        "boolean_relation_state_changed": first != final,
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
        "actual_location_returned": False,
        "ready_state_string_returned": False,
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
        "surface_authorized": False,
        "resource_get_authorized": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
