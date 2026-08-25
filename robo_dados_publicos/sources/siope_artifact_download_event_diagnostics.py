from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from urllib.parse import quote, urlparse

from .siope_artifact_download_runtime_route_probe import (
    _is_allowed_static_asset,
    _is_allowed_verified_metadata,
)
from .siope_export_runtime_route_probe import (
    SiopeRuntimeRouteProbeError,
    _CdpSession,
    _local_json,
    sanitize_intercepted_url,
)

ERROR = "STOP_SIOPE_ARTIFACT_DOWNLOAD_EVENT_DIAGNOSTICS"


def _sanitize_download_event(url: str, suggested_filename: str, config: dict) -> dict:
    parsed = urlparse(url)
    declared_name = Path(config["required_artifact_path"]).name
    out = {
        "scheme": parsed.scheme,
        "host": parsed.hostname or "",
        "suggested_filename_matches_declared": suggested_filename == declared_name,
        "download_behavior": "DENY",
        "artifact_downloaded": False,
    }
    sanitized = sanitize_intercepted_url(url)
    if sanitized is None:
        out.update({"route_without_query": None, "query_keys": [], "query_present": bool(parsed.query)})
    else:
        out.update(sanitized)
    return out


def _read_devtools_active_port(profile: Path) -> tuple[int, str] | None:
    marker = profile / "DevToolsActivePort"
    if not marker.is_file():
        return None
    try:
        lines = marker.read_text(encoding="utf-8").splitlines()
        if len(lines) < 2:
            return None
        port = int(lines[0].strip())
        ws_path = lines[1].strip()
    except Exception:
        return None
    if not (1 <= port <= 65535):
        return None
    if not ws_path.startswith("/devtools/browser/") or any(ch.isspace() for ch in ws_path):
        return None
    return port, ws_path


def _wait_devtools_active_port(profile: Path, process, *, timeout_s: float = 12.0) -> tuple[int, str]:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise SiopeRuntimeRouteProbeError(f"{ERROR}_BROWSER_EXITED")
        resolved = _read_devtools_active_port(profile)
        if resolved is not None:
            return resolved
        time.sleep(0.1)
    raise SiopeRuntimeRouteProbeError(f"{ERROR}_DEVTOOLS_ACTIVE_PORT")


def _create_page_target(port: int, *, timeout_s: float = 3.0) -> dict:
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    url = f"http://127.0.0.1:{port}/json/new?{quote('about:blank', safe='')}"
    while time.monotonic() < deadline:
        try:
            target = _local_json(url, method="PUT")
            if target.get("webSocketDebuggerUrl"):
                return target
        except Exception as exc:
            last_error = exc
        time.sleep(0.1)
    raise SiopeRuntimeRouteProbeError(f"{ERROR}_PAGE_TARGET") from last_error


class SystemChromeCdpArtifactDownloadEventRuntime:
    def _find_browser(self, config: dict) -> str:
        for name in config["browser_binary_candidates"]:
            path = shutil.which(name)
            if path:
                return path
        raise SiopeRuntimeRouteProbeError(f"{ERROR}_BROWSER_UNAVAILABLE")

    def run_probe(self, config: dict) -> dict:
        browser = self._find_browser(config)
        try:
            browser_version = subprocess.check_output([browser, "--version"], text=True, timeout=3).strip()[:160]
        except Exception:
            browser_version = "SYSTEM_CHROME_VERSION_UNAVAILABLE"

        process = page_session = browser_session = None
        download_events: list[dict] = []
        with tempfile.TemporaryDirectory(prefix="siope-artifact-download-event-") as profile_text:
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
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                port, browser_ws_path = _wait_devtools_active_port(profile, process)
                timeout_s = float(config["cdp_command_timeout_ms"]) / 1000.0
                browser_session = _CdpSession(
                    f"ws://127.0.0.1:{port}{browser_ws_path}",
                    command_timeout_s=timeout_s,
                )

                def handle_browser_event(payload: dict) -> None:
                    if payload.get("method") != "Browser.downloadWillBegin":
                        return
                    params = payload.get("params") or {}
                    download_events.append(
                        _sanitize_download_event(
                            str(params.get("url", "")),
                            str(params.get("suggestedFilename", "")),
                            config,
                        )
                    )

                browser_session.event_handler = handle_browser_event
                browser_session.command("Browser.setDownloadBehavior", {"behavior": "deny", "eventsEnabled": True})

                target = _create_page_target(port)
                page_session = _CdpSession(target["webSocketDebuggerUrl"], command_timeout_s=timeout_s)

                phase = {"value": "PRE_CLICK"}
                allowed_hosts = set(config["initial_allowed_hosts"])
                metadata_continued = 0
                static_continued = 0
                blocked: list[dict] = []

                def handle_page_event(payload: dict) -> None:
                    nonlocal metadata_continued, static_continued
                    if payload.get("method") != "Fetch.requestPaused":
                        return
                    params = payload.get("params") or {}
                    request_id = params.get("requestId")
                    request = params.get("request") or {}
                    url = str(request.get("url", ""))
                    method = str(request.get("method", "")).upper()
                    resource_type = str(params.get("resourceType", "Other"))
                    parsed = urlparse(url)

                    if phase["value"] == "PRE_CLICK":
                        local = parsed.scheme in {"about", "data", "blob"}
                        if local or (parsed.scheme in {"http", "https"} and parsed.hostname in allowed_hosts):
                            page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                        else:
                            page_session.send_no_wait("Fetch.failRequest", {"requestId": request_id, "errorReason": "Aborted"})
                        return

                    if _is_allowed_static_asset(url, method, resource_type, config):
                        static_continued += 1
                        page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                        return

                    if _is_allowed_verified_metadata(url, method, resource_type, config) and metadata_continued < config["max_verified_metadata_requests"]:
                        metadata_continued += 1
                        page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                        return

                    blocked.append({"url": url, "method": method, "resource_type": resource_type})
                    page_session.send_no_wait("Fetch.failRequest", {"requestId": request_id, "errorReason": "Aborted"})

                page_session.event_handler = handle_page_event
                page_session.command("Page.enable")
                page_session.command("Runtime.enable")
                page_session.command("Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]})
                page_session.command("Page.navigate", {"url": config["page_url"]})

                product = json.dumps(config["required_product_name"], ensure_ascii=False)
                artifact = json.dumps(config["required_artifact_path"], ensure_ascii=False)
                button = json.dumps(config["export_control_text"], ensure_ascii=False)
                inspect_expr = f"""(() => {{ const r=document.documentElement; const t=r?(r.innerText||''):''; const h=r?(r.innerHTML||''):''; const b=[...document.querySelectorAll('button,a,[role=button]')]; return {{ready:document.readyState,product:t.includes({product}),artifact:h.includes({artifact}),exportControl:b.some(e=>((e.innerText||e.textContent||'').trim()).includes({button}))}}; }})()"""
                page_state = None
                page_deadline = time.monotonic() + float(config["page_load_timeout_ms"]) / 1000.0
                while time.monotonic() < page_deadline:
                    result = page_session.command("Runtime.evaluate", {"expression": inspect_expr, "returnByValue": True})
                    page_state = ((result.get("result") or {}).get("value") or {})
                    if page_state.get("ready") in {"interactive", "complete"} and page_state.get("product") and page_state.get("artifact") and page_state.get("exportControl"):
                        break
                    page_session.pump(0.15)

                if not page_state or not page_state.get("product"):
                    raise SiopeRuntimeRouteProbeError(f"{ERROR}_PRODUCT_NOT_VERIFIED")
                if not page_state.get("artifact"):
                    raise SiopeRuntimeRouteProbeError(f"{ERROR}_ARTIFACT_NOT_DECLARED")
                if not page_state.get("exportControl"):
                    raise SiopeRuntimeRouteProbeError(f"{ERROR}_EXPORT_CONTROL_NOT_FOUND")

                page_session.pump(0.5)
                phase["value"] = "POST_CLICK"
                click_expr = f"""(() => {{ const b=[...document.querySelectorAll('button,a,[role=button]')]; const e=b.find(x=>((x.innerText||x.textContent||'').trim()).includes({button})); if(!e)return {{clicked:false}}; e.scrollIntoView({{block:'center'}}); e.click(); return {{clicked:true}}; }})()"""
                clicked = page_session.command("Runtime.evaluate", {"expression": click_expr, "returnByValue": True})
                click_value = ((clicked.get("result") or {}).get("value") or {})
                if not click_value.get("clicked"):
                    raise SiopeRuntimeRouteProbeError(f"{ERROR}_CLICK_NOT_EXECUTED")

                page_session.pump(float(config["post_click_capture_window_ms"]) / 1000.0)
                browser_session.pump(1.0)

                return {
                    "browser_version": browser_version,
                    "page_verified": True,
                    "artifact_declared": True,
                    "export_control_found": True,
                    "click_executed": True,
                    "browser_download_denied": True,
                    "download_events_enabled": True,
                    "verified_metadata_network_sent": metadata_continued > 0,
                    "verified_metadata_request_count": metadata_continued,
                    "post_click_static_assets_continued_count": static_continued,
                    "blocked_requests": blocked,
                    "download_events": download_events,
                    "candidate_route_network_sent": False,
                    "artifact_downloaded": False,
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


def diagnose_artifact_download_event(config: dict, *, runtime=None) -> dict:
    runtime = runtime or SystemChromeCdpArtifactDownloadEventRuntime()
    raw = runtime.run_probe(config)
    for key in (
        "page_verified",
        "artifact_declared",
        "export_control_found",
        "click_executed",
        "browser_download_denied",
        "download_events_enabled",
    ):
        if raw.get(key) is not True:
            raise SiopeRuntimeRouteProbeError(f"{ERROR}_RUNTIME_CONTRACT")
    if raw.get("candidate_route_network_sent") is not False or raw.get("artifact_downloaded") is not False:
        raise SiopeRuntimeRouteProbeError(f"{ERROR}_SAFETY_CONTRACT")
    metadata_count = int(raw.get("verified_metadata_request_count", 0))
    if not 1 <= metadata_count <= config["max_verified_metadata_requests"] or raw.get("verified_metadata_network_sent") is not True:
        raise SiopeRuntimeRouteProbeError(f"{ERROR}_VERIFIED_METADATA_NOT_OBSERVED")

    events = list(raw.get("download_events") or [])
    if len(events) > 8:
        raise SiopeRuntimeRouteProbeError(f"{ERROR}_EVENT_OVERFLOW")

    status = "BROWSER_DOWNLOAD_EVENT_OBSERVED_DENIED" if events else "NO_BROWSER_DOWNLOAD_EVENT_OBSERVED"
    return {
        "status": "PASS_M7_SIOPE_ARTIFACT_DOWNLOAD_EVENT_DIAGNOSTICS_GATE",
        "diagnostic_status": status,
        "verified_metadata_request_count": metadata_count,
        "verified_metadata_network_sent": True,
        "download_event_count": len(events),
        "download_events": events,
        "blocked_request_count": len(list(raw.get("blocked_requests") or [])),
        "candidate_route_network_sent": False,
        "browser_download_denied": True,
        "artifact_downloaded": False,
        "response_body_captured": False,
        "request_body_captured": False,
        "request_headers_captured": False,
        "cookies_captured": False,
        "head_request_performed": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": (
            "M7_SIOPE_ARTIFACT_DOWNLOAD_EVENT_EVIDENCE_REVIEW_0_8_0"
            if events
            else "M7_SIOPE_ARTIFACT_DOWNLOAD_DOM_INTENT_DIAGNOSTICS_0_8_0"
        ),
    }
