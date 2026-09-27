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
from .siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError
from .siope_public_get_runtime_route_diagnostics import (
    ERROR,
    SiopePublicGetRuntimeRouteDiagnosticsError,
    _is_allowed_static_asset,
    _matches_exact_indexed_document,
    summarize_blocked_requests,
)

_SAFE_QUERY_KEY = re.compile(r"^[A-Za-z0-9_.:-]{1,80}$")


def _sanitize_dom_route(route: object, config: dict) -> dict:
    route = route if isinstance(route, dict) else {}
    raw_path = str(route.get("path", "/"))[:512]
    path = raw_path.split("?", 1)[0].split("#", 1)[0] or "/"
    raw_keys = route.get("query_keys") if isinstance(route.get("query_keys"), list) else []
    query_keys = sorted(
        {
            str(key)
            for key in raw_keys[:64]
            if isinstance(key, str) and _SAFE_QUERY_KEY.fullmatch(key)
        }
    )[:32]
    host = str(route.get("host", "")).lower()[:253]
    scheme = str(route.get("scheme", "")).lower()[:16]
    return {
        "scheme": scheme,
        "host": host,
        "path": path,
        "query_present": bool(route.get("query_present")),
        "query_keys": query_keys,
        "official_host": host in set(config["allowed_hosts"]),
    }


def _failure_diagnostics(
    *,
    page_state: object,
    navigate_result: object,
    blocked: list[dict],
    initial_document_continued: int,
    static_assets_continued: int,
    local_requests_continued: int,
    config: dict,
) -> dict:
    page_state = page_state if isinstance(page_state, dict) else {}
    navigate_result = navigate_result if isinstance(navigate_result, dict) else {}
    shapes, candidates = summarize_blocked_requests(blocked, config)
    limit = int(config["max_blocked_shapes"])
    count = max(0, int(initial_document_continued))
    return {
        "initial_document_continued_count": count,
        "initial_document_network_sent": count > 0,
        "initial_document_contract_exactly_once": count == 1,
        "static_assets_continued_count": max(0, int(static_assets_continued)),
        "local_requests_continued_count": max(0, int(local_requests_continued)),
        "navigation_error_present": bool(navigate_result.get("errorText")),
        "page_ready_state": str(page_state.get("ready", ""))[:24],
        "loading_marker_a_present": bool(page_state.get("loadingA")),
        "loading_marker_b_present": bool(page_state.get("loadingB")),
        "human_challenge_active_dom": bool(page_state.get("challenge")),
        "final_surface": _sanitize_dom_route(page_state.get("route"), config),
        "blocked_request_event_count": len(blocked),
        "blocked_shape_count": len(shapes),
        "candidate_shape_count": len(candidates),
        "blocked_shapes": shapes[:limit],
        "candidate_shapes": candidates[:limit],
        "dynamic_candidate_network_sent": False,
        "browser_download_denied": True,
        "query_values_persisted": False,
        "request_body_persisted": False,
        "response_body_persisted": False,
    }


class SystemChromeCdpPublicGetRuntimeWithFailureTelemetry:
    """Same fail-closed network policy as the original runtime, with sanitized STOP telemetry."""

    def _find_browser(self, config: dict) -> str:
        for name in config["browser_binary_candidates"]:
            path = shutil.which(name)
            if path:
                return path
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_BROWSER_UNAVAILABLE")

    def run_probe(self, config: dict) -> dict:
        browser = self._find_browser(config)
        try:
            browser_version = subprocess.check_output([browser, "--version"], text=True, timeout=3).strip()[:160]
        except Exception:
            browser_version = "SYSTEM_CHROME_VERSION_UNAVAILABLE"

        process = page_session = browser_session = None
        blocked: list[dict] = []
        static_assets_continued = 0
        initial_document_continued = 0
        local_requests_continued = 0
        page_state: dict = {}
        navigate_result: dict = {}
        try:
            with tempfile.TemporaryDirectory(prefix="siope-public-get-runtime-", ignore_cleanup_errors=True) as profile_text:
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
                    str(version_info["webSocketDebuggerUrl"]),
                    command_timeout_s=timeout_s,
                    process=process,
                )
                browser_session.command("Browser.setDownloadBehavior", {"behavior": "deny"})
                target = _create_page_target(port)
                page_session = _connect_cdp_with_retry(
                    str(target["webSocketDebuggerUrl"]),
                    command_timeout_s=timeout_s,
                    process=process,
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
                    parsed = urlparse(url)

                    if parsed.scheme in {"about", "data", "blob"}:
                        local_requests_continued += 1
                        page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                        return
                    if _matches_exact_indexed_document(url, method, resource_type, config):
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
                navigate_result = page_session.command("Page.navigate", {"url": config["public_indexed_example_url"]})

                loading_literals = [json.dumps(marker, ensure_ascii=False) for marker in config["expected_loading_markers"]]
                challenge_literal = json.dumps(config["human_challenge_required_markers"][0], ensure_ascii=False)
                inspect_expr = f"""(() => {{
                  const text = document.body ? (document.body.innerText || '') : '';
                  const lower = text.toLowerCase();
                  const params = new URLSearchParams(location.search || '');
                  return {{
                    ready: document.readyState,
                    loadingA: text.includes({loading_literals[0]}),
                    loadingB: text.includes({loading_literals[1]}),
                    challenge: lower.includes(({challenge_literal}).toLowerCase()),
                    route: {{
                      scheme: (location.protocol || '').replace(':', ''),
                      host: location.hostname || '',
                      path: location.pathname || '/',
                      query_present: Boolean(location.search),
                      query_keys: Array.from(new Set(Array.from(params.keys()))).sort()
                    }}
                  }};
                }})()"""
                deadline = time.monotonic() + float(config["page_load_timeout_ms"]) / 1000.0
                while time.monotonic() < deadline:
                    result = page_session.command("Runtime.evaluate", {"expression": inspect_expr, "returnByValue": True})
                    page_state = ((result.get("result") or {}).get("value") or {})
                    if page_state.get("loadingA") and page_state.get("loadingB"):
                        break
                    page_session.pump(0.15)

                if not page_state or not (page_state.get("loadingA") and page_state.get("loadingB")):
                    raise SiopePublicGetRuntimeRouteDiagnosticsError(
                        f"{ERROR}_PUBLIC_SURFACE_NOT_VERIFIED",
                        diagnostics=_failure_diagnostics(
                            page_state=page_state,
                            navigate_result=navigate_result,
                            blocked=blocked,
                            initial_document_continued=initial_document_continued,
                            static_assets_continued=static_assets_continued,
                            local_requests_continued=local_requests_continued,
                            config=config,
                        ),
                    )

                page_session.pump(float(config["capture_window_ms"]) / 1000.0)
                final_state_result = page_session.command("Runtime.evaluate", {"expression": inspect_expr, "returnByValue": True})
                final_state = ((final_state_result.get("result") or {}).get("value") or {})
                return {
                    "browser_binary_name": Path(browser).name,
                    "browser_version": browser_version,
                    "page_surface_verified": True,
                    "initial_document_continued_count": initial_document_continued,
                    "initial_document_network_sent": initial_document_continued == 1,
                    "static_assets_continued_count": static_assets_continued,
                    "local_requests_continued_count": local_requests_continued,
                    "dynamic_candidate_network_sent": False,
                    "browser_download_denied": True,
                    "human_challenge_active_dom": bool(final_state.get("challenge")),
                    "blocked_requests": blocked,
                }
        except SiopePublicGetRuntimeRouteDiagnosticsError:
            raise
        except SiopeRuntimeRouteProbeError as exc:
            diagnostics = _failure_diagnostics(
                page_state=page_state,
                navigate_result=navigate_result,
                blocked=blocked,
                initial_document_continued=initial_document_continued,
                static_assets_continued=static_assets_continued,
                local_requests_continued=local_requests_continued,
                config=config,
            )
            diagnostics["runtime_stop"] = str(exc)[:160]
            raise SiopePublicGetRuntimeRouteDiagnosticsError(
                f"{ERROR}_BROWSER_RUNTIME",
                diagnostics=diagnostics,
            ) from None
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
                        process.wait(timeout=2)
                    except Exception:
                        pass
