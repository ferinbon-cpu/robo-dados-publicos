from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
from urllib.parse import parse_qsl, quote, urlparse, urlunparse
from urllib.request import ProxyHandler, Request, build_opener


class SiopeRuntimeRouteProbeError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def _validate_config(config: dict) -> None:
    exact = {
        "schema_version": 1,
        "gate_id": "M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_GATE_0_8_0",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "active_validated_version": "0.7.0",
        "mode": "RUNTIME_EXPORT_REQUEST_INTERCEPT_ONLY",
        "browser_backend": "SYSTEM_CHROME_CDP",
        "browser_download_or_install": "PROHIBITED",
        "browser_profile": "EPHEMERAL_TEMP_ONLY",
        "cross_origin_initial_requests": "ABORT",
        "export_control_text": "Exportar artefato",
        "max_clicks": 1,
        "post_click_capture_window_ms": 3000,
        "page_load_timeout_ms": 15000,
        "cdp_command_timeout_ms": 5000,
        "interception_protocol": "CDP_FETCH_REQUEST_STAGE",
        "post_click_network_policy": "ABORT_ALL_BEFORE_NETWORK",
        "download_behavior": "DENY",
        "candidate_signal_policy": "TARGET_IDENTIFIER_OR_EXPORT_ROUTE_MARKER",
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
        "fail_closed_on_interception_error": True,
        "fail_closed_on_browser_unavailable": True,
        "fail_closed_on_zero_candidates": True,
        "fail_closed_on_multiple_candidates": True,
        "next_gate_if_unique_intercepted_route": "M7_SIOPE_ANTONIETA_ARTIFACT_ROUTE_VERIFICATION_DESIGN_0_8_0",
        "next_gate_if_runtime_route_unproven": "STOP_REVIEW_RUNTIME_ROUTE_EVIDENCE",
    }
    for key, expected in exact.items():
        if config.get(key) != expected:
            raise SiopeRuntimeRouteProbeError(f"STOP_SIOPE_RUNTIME_ROUTE_PROBE_CONFIG_{key.upper()}")
    if config.get("browser_binary_candidates") != ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CONFIG_BROWSER_BINARIES")
    if config.get("initial_allowed_hosts") != ["www.fnde.gov.br"]:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CONFIG_ALLOWED_HOSTS")
    if config.get("candidate_resource_types") != ["XHR", "Fetch", "Document", "Other"]:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CONFIG_RESOURCE_TYPES")
    if config.get("candidate_methods") != ["GET", "POST"]:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CONFIG_METHODS")
    if config.get("target_identifiers") != ["getArtifactByDataProductId", "getArtifactMetadataByDataProductId", "downloadFile", "exportKey"]:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CONFIG_IDENTIFIERS")
    if config.get("export_route_markers") != ["plataforma-antonieta-de-barros-api", "artifact", "artefato", "download", "export"]:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CONFIG_ROUTE_MARKERS")
    page = urlparse(str(config.get("page_url", "")))
    if page.scheme != "https" or page.hostname != "www.fnde.gov.br" or not page.path.endswith("/visualizar/20"):
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CONFIG_PAGE_URL")
    if config.get("required_product_name") != "Dados Gerais - SIOPE":
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CONFIG_PRODUCT")
    if config.get("required_artifact_path") != "exports/SIOPE/SIOPE_DADOS_GERAIS_SIOPE.txt.gz":
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CONFIG_ARTIFACT")


def load_runtime_route_probe_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_config(config)
    return config


def sanitize_intercepted_url(url: str) -> dict | None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        return None
    route = urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", "", "", ""))
    query_keys = sorted({key for key, _value in parse_qsl(parsed.query, keep_blank_values=True) if key})
    return {
        "route_without_query": route,
        "query_keys": query_keys,
        "query_present": bool(parsed.query),
    }


def _candidate_signal(event: dict, sanitized: dict, config: dict) -> bool:
    method = str(event.get("method", "")).upper()
    resource_type = str(event.get("resource_type", ""))
    if method not in set(config["candidate_methods"]):
        return False
    if resource_type not in set(config["candidate_resource_types"]):
        return False
    initiators = set(event.get("initiator_functions") or ())
    if initiators.intersection(config["target_identifiers"]):
        return True
    route_lower = sanitized["route_without_query"].lower()
    return any(marker.lower() in route_lower for marker in config["export_route_markers"])


def classify_intercepted_requests(events: list[dict], config: dict) -> list[dict]:
    _validate_config(config)
    dedup: dict[tuple[str, str], dict] = {}
    for event in events:
        sanitized = sanitize_intercepted_url(str(event.get("url", "")))
        if sanitized is None or not _candidate_signal(event, sanitized, config):
            continue
        method = str(event.get("method", "")).upper()
        key = (method, sanitized["route_without_query"])
        initiators = sorted(set(event.get("initiator_functions") or ()).intersection(config["target_identifiers"]))
        dedup[key] = {
            "method": method,
            "resource_type": str(event.get("resource_type", "Other")),
            **sanitized,
            "matched_target_identifiers": initiators,
            "network_sent": False,
            "intercepted_before_network": True,
        }
    return [dedup[key] for key in sorted(dedup)]


def _extract_target_initiators(initiator: dict, targets: set[str]) -> list[str]:
    found: set[str] = set()
    stack = initiator.get("stack") if isinstance(initiator, dict) else None
    while isinstance(stack, dict):
        for frame in stack.get("callFrames") or []:
            name = str(frame.get("functionName", ""))
            if name in targets:
                found.add(name)
        stack = stack.get("parent")
    return sorted(found)


class _CdpSession:
    def __init__(self, ws_url: str, *, command_timeout_s: float):
        try:
            import websocket  # type: ignore
        except Exception as exc:
            raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_WEBSOCKET_DEPENDENCY") from exc
        self._websocket_mod = websocket
        try:
            self.ws = websocket.create_connection(
                ws_url,
                timeout=0.5,
                origin="http://127.0.0.1",
                http_proxy_host=None,
            )
        except Exception as exc:
            raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CDP_CONNECT") from exc
        self.command_timeout_s = command_timeout_s
        self.next_id = 0
        self.event_handler = None

    def close(self) -> None:
        try:
            self.ws.close()
        except Exception:
            pass

    def _send_raw(self, method: str, params: dict | None = None) -> int:
        self.next_id += 1
        msg_id = self.next_id
        self.ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}, separators=(",", ":")))
        return msg_id

    def send_no_wait(self, method: str, params: dict | None = None) -> None:
        self._send_raw(method, params)

    def _dispatch(self, payload: dict) -> None:
        if "method" in payload and self.event_handler is not None:
            self.event_handler(payload)

    def command(self, method: str, params: dict | None = None, *, timeout_s: float | None = None) -> dict:
        target_id = self._send_raw(method, params)
        deadline = time.monotonic() + (timeout_s or self.command_timeout_s)
        while time.monotonic() < deadline:
            try:
                raw = self.ws.recv()
            except self._websocket_mod.WebSocketTimeoutException:
                continue
            except Exception as exc:
                raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CDP_RECV") from exc
            if not raw:
                continue
            payload = json.loads(raw)
            self._dispatch(payload)
            if payload.get("id") != target_id:
                continue
            if "error" in payload:
                raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CDP_COMMAND")
            return payload.get("result") or {}
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CDP_COMMAND_TIMEOUT")

    def pump(self, duration_s: float) -> None:
        deadline = time.monotonic() + duration_s
        while time.monotonic() < deadline:
            try:
                raw = self.ws.recv()
            except self._websocket_mod.WebSocketTimeoutException:
                continue
            except Exception as exc:
                raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CDP_PUMP") from exc
            if not raw:
                continue
            self._dispatch(json.loads(raw))


def _local_json(url: str, *, method: str = "GET", timeout_s: float = 0.5) -> dict:
    opener = build_opener(ProxyHandler({}))
    req = Request(url, method=method)
    with opener.open(req, timeout=timeout_s) as response:
        return json.loads(response.read(1024 * 1024).decode("utf-8"))


def _free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class SystemChromeCdpRuntime:
    def _find_browser(self, config: dict) -> str:
        for name in config["browser_binary_candidates"]:
            path = shutil.which(name)
            if path:
                return path
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_BROWSER_UNAVAILABLE")

    def run_probe(self, config: dict) -> dict:
        _validate_config(config)
        browser = self._find_browser(config)
        try:
            version = subprocess.check_output([browser, "--version"], text=True, timeout=3).strip()[:160]
        except Exception:
            version = "SYSTEM_CHROME_VERSION_UNAVAILABLE"

        port = _free_local_port()
        process = None
        page_session = None
        browser_session = None
        with tempfile.TemporaryDirectory(prefix="siope-runtime-probe-") as profile:
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
            env = {key: value for key, value in os.environ.items() if key not in {"CHROME_LOG_FILE"}}
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                version_info = None
                deadline = time.monotonic() + 8.0
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_BROWSER_EXITED")
                    try:
                        version_info = _local_json(f"http://127.0.0.1:{port}/json/version")
                        break
                    except Exception:
                        time.sleep(0.1)
                if not version_info:
                    raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_DEBUG_ENDPOINT")

                command_timeout = float(config["cdp_command_timeout_ms"]) / 1000.0
                browser_session = _CdpSession(version_info["webSocketDebuggerUrl"], command_timeout_s=command_timeout)
                browser_session.command("Browser.setDownloadBehavior", {"behavior": "deny"})

                target = _local_json(
                    f"http://127.0.0.1:{port}/json/new?{quote('about:blank', safe='')}",
                    method="PUT",
                )
                page_session = _CdpSession(target["webSocketDebuggerUrl"], command_timeout_s=command_timeout)

                phase = {"value": "PRE_CLICK"}
                network_initiators: dict[str, list[str]] = {}
                intercepted: list[dict] = []
                cross_origin_aborted = 0
                post_click_aborted = 0
                targets = set(config["target_identifiers"])
                allowed_hosts = set(config["initial_allowed_hosts"])

                def handle_event(payload: dict) -> None:
                    nonlocal cross_origin_aborted, post_click_aborted
                    method = payload.get("method")
                    params = payload.get("params") or {}
                    if method == "Network.requestWillBeSent":
                        request_id = str(params.get("requestId", ""))
                        if request_id:
                            network_initiators[request_id] = _extract_target_initiators(params.get("initiator") or {}, targets)
                        return
                    if method != "Fetch.requestPaused":
                        return
                    request_id = params.get("requestId")
                    request = params.get("request") or {}
                    url = str(request.get("url", ""))
                    if phase["value"] == "PRE_CLICK":
                        parsed = urlparse(url)
                        local_scheme = parsed.scheme in {"about", "data", "blob"}
                        if local_scheme or (parsed.scheme in {"http", "https"} and parsed.hostname in allowed_hosts):
                            page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                        else:
                            cross_origin_aborted += 1
                            page_session.send_no_wait("Fetch.failRequest", {"requestId": request_id, "errorReason": "Aborted"})
                        return

                    post_click_aborted += 1
                    network_id = str(params.get("networkId", ""))
                    intercepted.append({
                        "url": url,
                        "method": str(request.get("method", "")),
                        "resource_type": str(params.get("resourceType", "Other")),
                        "initiator_functions": network_initiators.get(network_id, []),
                    })
                    page_session.send_no_wait("Fetch.failRequest", {"requestId": request_id, "errorReason": "Aborted"})

                page_session.event_handler = handle_event
                page_session.command("Page.enable")
                page_session.command("Runtime.enable")
                page_session.command("Network.enable")
                page_session.command("Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]})
                page_session.command("Page.navigate", {"url": config["page_url"]})

                page_deadline = time.monotonic() + float(config["page_load_timeout_ms"]) / 1000.0
                page_state = None
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
                while time.monotonic() < page_deadline:
                    result = page_session.command("Runtime.evaluate", {"expression": inspect_expr, "returnByValue": True})
                    page_state = ((result.get("result") or {}).get("value") or {})
                    if page_state.get("ready") in {"interactive", "complete"} and page_state.get("product") and page_state.get("artifact") and page_state.get("exportControl"):
                        break
                    page_session.pump(0.15)
                if not page_state or not page_state.get("product"):
                    raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_PRODUCT_NOT_VERIFIED")
                if not page_state.get("artifact"):
                    raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_ARTIFACT_NOT_DECLARED")
                if not page_state.get("exportControl"):
                    raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_EXPORT_CONTROL_NOT_FOUND")

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
                    raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_CLICK_NOT_EXECUTED")
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
                    "cross_origin_initial_aborted_count": cross_origin_aborted,
                    "post_click_aborted_request_count": post_click_aborted,
                    "intercepted_requests": intercepted,
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


def probe_export_runtime_route(config: dict, *, runtime=None) -> dict:
    _validate_config(config)
    runtime = runtime or SystemChromeCdpRuntime()
    raw = runtime.run_probe(config)
    required_true = ("page_verified", "artifact_declared", "export_control_found", "click_executed", "post_click_interception_active", "browser_download_denied")
    if any(raw.get(key) is not True for key in required_true):
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_RUNTIME_CONTRACT")
    if raw.get("candidate_route_network_sent") is not False:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_NETWORK_SENT")

    events = list(raw.get("intercepted_requests") or [])
    candidates = classify_intercepted_requests(events, config)
    diagnostics = {
        "post_click_aborted_request_count": int(raw.get("post_click_aborted_request_count", 0)),
        "candidate_count": len(candidates),
        "cross_origin_initial_aborted_count": int(raw.get("cross_origin_initial_aborted_count", 0)),
    }
    if not candidates:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_ZERO_CANDIDATES", diagnostics=diagnostics)
    if len(candidates) != 1:
        raise SiopeRuntimeRouteProbeError("STOP_SIOPE_RUNTIME_ROUTE_PROBE_MULTIPLE_CANDIDATES", diagnostics={**diagnostics, "candidates": candidates[:8]})

    return {
        "status": "PASS_M7_SIOPE_EXPORT_RUNTIME_ROUTE_PROBE_GATE",
        "gate_id": config["gate_id"],
        "software_version": config["software_version"],
        "runtime_probe_status": "UNIQUE_INTERCEPTED_EXPORT_REQUEST_OBSERVED_NOT_SENT",
        "browser_backend": config["browser_backend"],
        "browser_binary_name": str(raw.get("browser_binary_name", "SYSTEM_CHROME"))[:80],
        "browser_version": str(raw.get("browser_version", "SYSTEM_CHROME_VERSION_UNAVAILABLE"))[:160],
        "page_verified": True,
        "artifact_declared": True,
        "export_control_found": True,
        "browser_automation_performed": True,
        "click_executed": True,
        "export_request_attempt_observed": True,
        "post_click_interception_active": True,
        "post_click_aborted_request_count": diagnostics["post_click_aborted_request_count"],
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
