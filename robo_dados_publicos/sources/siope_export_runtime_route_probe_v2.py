from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from urllib.parse import quote, urlparse

from .siope_export_runtime_route_probe import (
    SiopeRuntimeRouteProbeError,
    _CdpSession,
    _free_local_port,
    _local_json,
    sanitize_intercepted_url,
)


def load_runtime_route_probe_v2_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    exact = {
        "schema_version": 1,
        "gate_id": "M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_V2_GATE_0_8_0",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "active_validated_version": "0.7.0",
        "mode": "RUNTIME_EXPORT_REQUEST_INTERCEPT_STATIC_ASSET_AWARE",
        "browser_backend": "SYSTEM_CHROME_CDP",
        "browser_download_or_install": "PROHIBITED",
        "browser_profile": "EPHEMERAL_TEMP_ONLY",
        "required_product_name": "Dados Gerais - SIOPE",
        "required_artifact_path": "exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz",
        "export_control_text": "Exportar artefato",
        "static_asset_host": "www.fnde.gov.br",
        "static_asset_path_prefix": "/plataforma-antonieta-de-barros/assets/",
        "max_clicks": 1,
        "interception_protocol": "CDP_FETCH_REQUEST_STAGE",
        "post_click_network_policy": "CONTINUE_EXACT_STATIC_ASSET_ALLOWLIST_ABORT_ALL_OTHER_BEFORE_NETWORK",
        "download_behavior": "DENY",
        "candidate_deduplication": "METHOD_ROUTE_WITHOUT_QUERY",
        "unique_candidate_required_for_pass": True,
        "response_body_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "request_headers_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "query_value_capture": "PROHIBITED",
        "candidate_route_network_send": "PROHIBITED",
        "head_request": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "remote_writes": "PROHIBITED",
        "drive_oauth": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "source_collection": "PROHIBITED",
        "source_processing": "PROHIBITED",
        "recurrence": "PROHIBITED",
        "schedule": "DISABLED",
        "next_gate_if_unique_intercepted_route": "M7_SIOPE_ANTONIETA_ARTIFACT_ROUTE_VERIFICATION_DESIGN_0_8_0",
        "next_gate_if_runtime_route_unproven": "STOP_REVIEW_RUNTIME_ROUTE_V2_EVIDENCE",
    }
    for key, expected in exact.items():
        if config.get(key) != expected:
            raise SiopeRuntimeRouteProbeError(f"STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_CONFIG_{key.upper()}")
    if config.get("browser_binary_candidates") != ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_CONFIG_BROWSER_BINARIES")
    if config.get("initial_allowed_hosts") != ["www.fnde.gov.br"]:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_CONFIG_ALLOWED_HOSTS")
    if config.get("static_asset_methods") != ["GET"]:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_CONFIG_STATIC_METHODS")
    if config.get("static_asset_resource_types") != ["Script", "Stylesheet"]:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_CONFIG_STATIC_TYPES")
    if config.get("candidate_methods") != ["GET", "POST"]:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_CONFIG_CANDIDATE_METHODS")
    page = urlparse(str(config.get("page_url", "")))
    if page.scheme != "https" or page.hostname != "www.fnde.gov.br" or not page.path.endswith("/visualizar/20"):
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_CONFIG_PAGE_URL")
    if not isinstance(config.get("page_load_timeout_ms"), int) or not 1000 <= config["page_load_timeout_ms"] <= 30000:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_CONFIG_PAGE_TIMEOUT")
    if not isinstance(config.get("post_click_capture_window_ms"), int) or not 1000 <= config["post_click_capture_window_ms"] <= 10000:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_CONFIG_CAPTURE_WINDOW")
    return config


def _is_allowed_static_asset(url: str, method: str, resource_type: str, config: dict) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname == config["static_asset_host"]
        and parsed.path.startswith(config["static_asset_path_prefix"])
        and method.upper() in set(config["static_asset_methods"])
        and resource_type in set(config["static_asset_resource_types"])
        and not parsed.username
        and not parsed.password
    )


def summarize_blocked_candidates(events: list[dict], config: dict) -> list[dict]:
    dedup: dict[tuple[str, str], dict] = {}
    for event in events:
        method = str(event.get("method", "")).upper()
        if method not in set(config["candidate_methods"]):
            continue
        sanitized = sanitize_intercepted_url(str(event.get("url", "")))
        if sanitized is None:
            continue
        route = sanitized["route_without_query"]
        parsed = urlparse(route)
        if parsed.hostname == config["static_asset_host"] and parsed.path == "/plataforma-antonieta-de-barros/favicon.ico":
            continue
        key = (method, route)
        if key not in dedup:
            dedup[key] = {
                "method": method,
                "resource_type": str(event.get("resource_type", "Other")),
                "scheme": parsed.scheme,
                "host": parsed.hostname or "",
                **sanitized,
                "occurrences": 0,
                "network_sent": False,
                "intercepted_before_network": True,
            }
        dedup[key]["occurrences"] += 1
        dedup[key]["query_keys"] = sorted(set(dedup[key]["query_keys"]).union(sanitized["query_keys"]))
        dedup[key]["query_present"] = bool(dedup[key]["query_present"] or sanitized["query_present"])
    return [dedup[key] for key in sorted(dedup)]


class SystemChromeCdpRuntimeV2:
    def _find_browser(self, config: dict) -> str:
        for name in config["browser_binary_candidates"]:
            path = shutil.which(name)
            if path:
                return path
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_BROWSER_UNAVAILABLE")

    def run_probe(self, config: dict) -> dict:
        browser = self._find_browser(config)
        try:
            version = subprocess.check_output([browser, "--version"], text=True, timeout=3).strip()[:160]
        except Exception:
            version = "SYSTEM_CHROME_VERSION_UNAVAILABLE"

        port = _free_local_port()
        process = None
        page_session = None
        browser_session = None
        with tempfile.TemporaryDirectory(prefix="siope-runtime-probe-v2-") as profile:
            cmd = [
                browser,
                "--headless=new",
                f"--remote-debugging-port={port}",
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
            env = {key: value for key, value in os.environ.items() if key != "CHROME_LOG_FILE"}
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                version_info = None
                deadline = time.monotonic() + 8.0
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_BROWSER_EXITED")
                    try:
                        version_info = _local_json(f"http://127.0.0.1:{port}/json/version")
                        break
                    except Exception:
                        time.sleep(0.1)
                if not version_info:
                    raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_DEBUG_ENDPOINT")

                timeout_s = float(config["cdp_command_timeout_ms"]) / 1000.0
                browser_session = _CdpSession(version_info["webSocketDebuggerUrl"], command_timeout_s=timeout_s)
                browser_session.command("Browser.setDownloadBehavior", {"behavior": "deny"})
                target = _local_json(
                    f"http://127.0.0.1:{port}/json/new?{quote('about:blank', safe='')}",
                    method="PUT",
                )
                page_session = _CdpSession(target["webSocketDebuggerUrl"], command_timeout_s=timeout_s)

                phase = {"value": "PRE_CLICK"}
                blocked: list[dict] = []
                cross_origin_initial_aborted = 0
                post_click_static_assets_continued = 0
                post_click_nonstatic_aborted = 0
                allowed_hosts = set(config["initial_allowed_hosts"])

                def handle_event(payload: dict) -> None:
                    nonlocal cross_origin_initial_aborted, post_click_static_assets_continued, post_click_nonstatic_aborted
                    if payload.get("method") != "Fetch.requestPaused":
                        return
                    params = payload.get("params") or {}
                    request_id = params.get("requestId")
                    request = params.get("request") or {}
                    url = str(request.get("url", ""))
                    req_method = str(request.get("method", "")).upper()
                    resource_type = str(params.get("resourceType", "Other"))
                    parsed = urlparse(url)
                    if phase["value"] == "PRE_CLICK":
                        local_scheme = parsed.scheme in {"about", "data", "blob"}
                        if local_scheme or (parsed.scheme in {"http", "https"} and parsed.hostname in allowed_hosts):
                            page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                        else:
                            cross_origin_initial_aborted += 1
                            page_session.send_no_wait("Fetch.failRequest", {"requestId": request_id, "errorReason": "Aborted"})
                        return

                    if _is_allowed_static_asset(url, req_method, resource_type, config):
                        post_click_static_assets_continued += 1
                        page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                        return

                    post_click_nonstatic_aborted += 1
                    blocked.append({"url": url, "method": req_method, "resource_type": resource_type})
                    page_session.send_no_wait("Fetch.failRequest", {"requestId": request_id, "errorReason": "Aborted"})

                page_session.event_handler = handle_event
                page_session.command("Page.enable")
                page_session.command("Runtime.enable")
                page_session.command("Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]})
                page_session.command("Page.navigate", {"url": config["page_url"]})

                product_literal = json.dumps(config["required_product_name"], ensure_ascii=False)
                artifact_literal = json.dumps(config["required_artifact_path"], ensure_ascii=False)
                button_literal = json.dumps(config["export_control_text"], ensure_ascii=False)
                inspect_expr = f"""(() => {{
                  const root = document.documentElement;
                  const text = root ? (root.innerText || '') : '';
                  const html = root ? (root.innerHTML || '') : '';
                  const buttons = [...document.querySelectorAll('button,a,[role=button]')];
                  return {{
                    ready: document.readyState,
                    product: text.includes({product_literal}),
                    artifact: html.includes({artifact_literal}),
                    exportControl: buttons.some(e => ((e.innerText || e.textContent || '').trim()).includes({button_literal}))
                  }};
                }})()"""
                page_deadline = time.monotonic() + float(config["page_load_timeout_ms"]) / 1000.0
                page_state = None
                while time.monotonic() < page_deadline:
                    result = page_session.command("Runtime.evaluate", {"expression": inspect_expr, "returnByValue": True})
                    page_state = ((result.get("result") or {}).get("value") or {})
                    if page_state.get("ready") in {"interactive", "complete"} and page_state.get("product") and page_state.get("artifact") and page_state.get("exportControl"):
                        break
                    page_session.pump(0.15)
                if not page_state or not page_state.get("product"):
                    raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_PRODUCT_NOT_VERIFIED")
                if not page_state.get("artifact"):
                    raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_ARTIFACT_NOT_DECLARED")
                if not page_state.get("exportControl"):
                    raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_EXPORT_CONTROL_NOT_FOUND")

                page_session.pump(0.5)
                phase["value"] = "POST_CLICK"
                click_expr = f"""(() => {{
                  const buttons = [...document.querySelectorAll('button,a,[role=button]')];
                  const el = buttons.find(e => ((e.innerText || e.textContent || '').trim()).includes({button_literal}));
                  if (!el) return {{clicked:false}};
                  el.scrollIntoView({{block:'center', inline:'center'}});
                  el.click();
                  return {{clicked:true, tag:el.tagName}};
                }})()"""
                click_result = page_session.command("Runtime.evaluate", {"expression": click_expr, "returnByValue": True})
                click_value = ((click_result.get("result") or {}).get("value") or {})
                if not click_value.get("clicked"):
                    raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_CLICK_NOT_EXECUTED")
                page_session.pump(float(config["post_click_capture_window_ms"]) / 1000.0)

                return {
                    "browser_binary_name": Path(browser).name,
                    "browser_version": version,
                    "page_verified": True,
                    "artifact_declared": True,
                    "export_control_found": True,
                    "click_executed": True,
                    "post_click_interception_active": True,
                    "browser_download_denied": True,
                    "candidate_route_network_sent": False,
                    "cross_origin_initial_aborted_count": cross_origin_initial_aborted,
                    "post_click_static_assets_continued_count": post_click_static_assets_continued,
                    "post_click_nonstatic_aborted_count": post_click_nonstatic_aborted,
                    "blocked_requests": blocked,
                }
            finally:
                if page_session is not None:
                    page_session.close()
                if browser_session is not None:
                    browser_session.close()
                if process is not None:
                    try:
                        process.terminate()
                        process.wait(timeout=2)
                    except Exception:
                        try:
                            process.kill()
                        except Exception:
                            pass


def probe_export_runtime_route_v2(config: dict, *, runtime=None) -> dict:
    runtime = runtime or SystemChromeCdpRuntimeV2()
    raw = runtime.run_probe(config)
    required_true = (
        "page_verified", "artifact_declared", "export_control_found", "click_executed",
        "post_click_interception_active", "browser_download_denied",
    )
    if any(raw.get(key) is not True for key in required_true):
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_RUNTIME_CONTRACT")
    if raw.get("candidate_route_network_sent") is not False:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_NETWORK_SENT")

    candidates = summarize_blocked_candidates(list(raw.get("blocked_requests") or []), config)
    diagnostics = {
        "cross_origin_initial_aborted_count": int(raw.get("cross_origin_initial_aborted_count", 0)),
        "post_click_static_assets_continued_count": int(raw.get("post_click_static_assets_continued_count", 0)),
        "post_click_nonstatic_aborted_count": int(raw.get("post_click_nonstatic_aborted_count", 0)),
        "candidate_count": len(candidates),
    }
    if len(candidates) == 0:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_ZERO_CANDIDATES", diagnostics=diagnostics)
    if len(candidates) != 1:
        raise SiopeRuntimeRouteProbeError(
            "STOP_SIOPE_RUNTIME_ROUTE_PROBE_V2_MULTIPLE_CANDIDATES",
            diagnostics={**diagnostics, "candidates": candidates[:16]},
        )

    return {
        "status": "PASS_M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_V2_GATE",
        "gate_id": config["gate_id"],
        "software_version": config["software_version"],
        "runtime_probe_status": "UNIQUE_NONSTATIC_REQUEST_OBSERVED_NOT_SENT",
        "browser_backend": config["browser_backend"],
        "browser_binary_name": str(raw.get("browser_binary_name", "SYSTEM_CHROME"))[:80],
        "browser_version": str(raw.get("browser_version", "SYSTEM_CHROME_VERSION_UNAVAILABLE"))[:160],
        "page_verified": True,
        "artifact_declared": True,
        "export_control_found": True,
        "browser_automation_performed": True,
        "click_executed": True,
        "post_click_interception_active": True,
        "browser_download_denied": True,
        "static_asset_allowlist_used": True,
        "post_click_static_assets_continued_count": diagnostics["post_click_static_assets_continued_count"],
        "post_click_nonstatic_aborted_count": diagnostics["post_click_nonstatic_aborted_count"],
        "cross_origin_initial_aborted_count": diagnostics["cross_origin_initial_aborted_count"],
        "candidate_count": 1,
        "candidate": candidates[0],
        "candidate_route_network_sent": False,
        "response_body_captured": False,
        "request_body_captured": False,
        "request_headers_captured": False,
        "cookies_captured": False,
        "artifact_downloaded": False,
        "head_request_performed": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate_if_unique_intercepted_route"],
    }
