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
from .siope_export_runtime_route_probe import (
    SiopeRuntimeRouteProbeError,
    _CdpSession,
    sanitize_intercepted_url,
)

ERROR = "STOP_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS"


class SiopePublicGetRuntimeRouteDiagnosticsError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def _validate_config(config: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "PUBLIC_INDEXED_GET_RUNTIME_REQUEST_INTERCEPT",
        "browser_backend": "SYSTEM_CHROME_CDP",
        "browser_download_or_install": "PROHIBITED",
        "browser_profile": "EPHEMERAL_TEMP_ONLY",
        "expected_path": "/siope/dadosInformadosMunicipio.do",
        "network_policy": "CONTINUE_EXACT_INDEXED_DOCUMENT_AND_OFFICIAL_STATIC_ASSETS_ABORT_ALL_OTHER_BEFORE_NETWORK",
        "initial_document_send": "EXACT_PUBLIC_INDEXED_EXAMPLE_ONLY",
        "pilot_limeira_values_send": "PROHIBITED",
        "dynamic_candidate_network_send": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "captcha_bypass": "PROHIBITED",
        "authentication": "PROHIBITED",
        "credential_capture": "PROHIBITED",
        "cookie_capture": "PROHIBITED",
        "request_body_capture": "PROHIBITED",
        "response_body_capture": "PROHIBITED",
        "query_value_persistence": "PROHIBITED",
        "head_request": "PROHIBITED",
        "artifact_download": "PROHIBITED",
        "remote_writes": "PROHIBITED",
        "source_collection": "PROHIBITED",
        "source_processing": "PROHIBITED",
        "recurrence": "PROHIBITED",
        "schedule": "DISABLED",
        "next_gate_after_review": "M7_SIOPE_PUBLIC_RUNTIME_ROUTE_CONTRACT_REVIEW_0_8_0",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
    }
    for key, expected in exact.items():
        if config.get(key) != expected:
            raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_{key.upper()}")

    if config.get("allowed_hosts") != ["www.fnde.gov.br"]:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_ALLOWED_HOSTS")
    if config.get("expected_query_keys") != [
        "acao", "admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"
    ]:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_QUERY_KEYS")
    if config.get("expected_loading_markers") != ["Buscando planilhas", "Buscando dados"]:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_LOADING_MARKERS")
    if config.get("human_challenge_required_markers") != ["validar o captcha"]:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_HUMAN_CHALLENGE_MARKERS")
    if config.get("browser_binary_candidates") != [
        "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"
    ]:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_BROWSER_BINARIES")
    if config.get("static_asset_methods") != ["GET"]:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_STATIC_METHODS")
    if config.get("static_asset_resource_types") != ["Script", "Stylesheet", "Image", "Font"]:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_STATIC_TYPES")
    if config.get("candidate_methods") != ["GET", "POST"]:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_CANDIDATE_METHODS")
    if config.get("candidate_resource_types") != ["XHR", "Fetch"]:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_CANDIDATE_TYPES")

    extensions = config.get("static_asset_extensions")
    if not isinstance(extensions, list) or not extensions or any(not isinstance(v, str) or not v.startswith(".") for v in extensions):
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_STATIC_EXTENSIONS")

    raw_url = str(config.get("public_indexed_example_url", ""))
    parsed = urlparse(raw_url)
    if parsed.scheme != "https" or parsed.hostname != "www.fnde.gov.br" or parsed.path != config["expected_path"]:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_EXAMPLE_URL")
    query_keys = sorted({key for key, _ in parse_qsl(parsed.query, keep_blank_values=True)})
    if query_keys != config["expected_query_keys"]:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_EXAMPLE_QUERY_KEYS")
    if "352690" in raw_url:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_PILOT_LIMEIRA_VALUE")

    limits = {
        "page_load_timeout_ms": (1000, 30000),
        "capture_window_ms": (1000, 10000),
        "cdp_command_timeout_ms": (1000, 10000),
        "max_blocked_shapes": (1, 256),
    }
    for key, (minimum, maximum) in limits.items():
        value = config.get(key)
        if not isinstance(value, int) or not minimum <= value <= maximum:
            raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_CONFIG_{key.upper()}")


def load_public_get_runtime_route_diagnostics_config(path: str | Path) -> dict:
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    _validate_config(config)
    return config


def _query_pairs(url: str) -> list[tuple[str, str]]:
    parsed = urlparse(url)
    return sorted(parse_qsl(parsed.query, keep_blank_values=True))


def _matches_exact_indexed_document(url: str, method: str, resource_type: str, config: dict) -> bool:
    if method.upper() != "GET" or resource_type != "Document":
        return False
    expected = urlparse(config["public_indexed_example_url"])
    observed = urlparse(url)
    return (
        observed.scheme == expected.scheme == "https"
        and observed.hostname == expected.hostname == "www.fnde.gov.br"
        and observed.path == expected.path
        and not observed.username
        and not observed.password
        and not observed.fragment
        and _query_pairs(url) == _query_pairs(config["public_indexed_example_url"])
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


def _shape(event: dict, config: dict) -> dict | None:
    sanitized = sanitize_intercepted_url(str(event.get("url", "")))
    if sanitized is None:
        return None
    parsed = urlparse(sanitized["route_without_query"])
    resource_type = str(event.get("resource_type", "Other"))[:40]
    method = str(event.get("method", "")).upper()[:16]
    candidate = (
        method in set(config["candidate_methods"])
        and resource_type in set(config["candidate_resource_types"])
        and parsed.scheme == "https"
        and parsed.hostname in set(config["allowed_hosts"])
    )
    return {
        "method": method,
        "resource_type": resource_type,
        "scheme": parsed.scheme,
        "host": parsed.hostname or "",
        **sanitized,
        "official_host": parsed.hostname in set(config["allowed_hosts"]),
        "candidate_dynamic_data_request": candidate,
        "network_sent": False,
        "intercepted_before_network": True,
    }


def summarize_blocked_requests(events: list[dict], config: dict) -> tuple[list[dict], list[dict]]:
    dedup: dict[tuple[str, str, str], dict] = {}
    for event in events:
        shaped = _shape(event, config)
        if shaped is None:
            continue
        key = (shaped["method"], shaped["resource_type"], shaped["route_without_query"])
        if key not in dedup:
            dedup[key] = {**shaped, "occurrences": 0}
        dedup[key]["occurrences"] += 1
        dedup[key]["query_keys"] = sorted(set(dedup[key]["query_keys"]).union(shaped["query_keys"]))
        dedup[key]["query_present"] = bool(dedup[key]["query_present"] or shaped["query_present"])
    shapes = [dedup[key] for key in sorted(dedup)]
    candidates = [shape for shape in shapes if shape["candidate_dynamic_data_request"]]
    return shapes, candidates


class SystemChromeCdpPublicGetRuntime:
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
                page_session.command("Page.navigate", {"url": config["public_indexed_example_url"]})

                loading_literals = [json.dumps(marker, ensure_ascii=False) for marker in config["expected_loading_markers"]]
                challenge_literal = json.dumps(config["human_challenge_required_markers"][0], ensure_ascii=False)
                inspect_expr = f"""(() => {{
                  const text = document.body ? (document.body.innerText || '') : '';
                  const lower = text.toLowerCase();
                  return {{
                    ready: document.readyState,
                    loadingA: text.includes({loading_literals[0]}),
                    loadingB: text.includes({loading_literals[1]}),
                    challenge: lower.includes(({challenge_literal}).toLowerCase())
                  }};
                }})()"""
                page_state = None
                deadline = time.monotonic() + float(config["page_load_timeout_ms"]) / 1000.0
                while time.monotonic() < deadline:
                    result = page_session.command("Runtime.evaluate", {"expression": inspect_expr, "returnByValue": True})
                    page_state = ((result.get("result") or {}).get("value") or {})
                    if page_state.get("loadingA") and page_state.get("loadingB"):
                        break
                    page_session.pump(0.15)
                if not page_state or not (page_state.get("loadingA") and page_state.get("loadingB")):
                    raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_PUBLIC_SURFACE_NOT_VERIFIED")

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
            raise SiopePublicGetRuntimeRouteDiagnosticsError(
                f"{ERROR}_BROWSER_RUNTIME",
                diagnostics={"runtime_stop": str(exc)[:160]},
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


def probe_public_get_runtime_routes(config: dict, *, runtime=None) -> dict:
    _validate_config(config)
    runtime = runtime or SystemChromeCdpPublicGetRuntime()
    raw = runtime.run_probe(config)

    if raw.get("page_surface_verified") is not True:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_RUNTIME_SURFACE")
    if raw.get("initial_document_network_sent") is not True or int(raw.get("initial_document_continued_count", 0)) != 1:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_INITIAL_DOCUMENT_CONTRACT")
    if raw.get("dynamic_candidate_network_sent") is not False:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_DYNAMIC_NETWORK_SENT")
    if raw.get("browser_download_denied") is not True:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(f"{ERROR}_DOWNLOAD_NOT_DENIED")

    shapes, candidates = summarize_blocked_requests(list(raw.get("blocked_requests") or []), config)
    if len(shapes) > int(config["max_blocked_shapes"]):
        raise SiopePublicGetRuntimeRouteDiagnosticsError(
            f"{ERROR}_SHAPE_LIMIT",
            diagnostics={"blocked_shape_count": len(shapes), "max_blocked_shapes": config["max_blocked_shapes"]},
        )
    if raw.get("human_challenge_active_dom") is True:
        raise SiopePublicGetRuntimeRouteDiagnosticsError(
            f"{ERROR}_HUMAN_CHALLENGE_ACTIVE",
            diagnostics={
                "blocked_shape_count": len(shapes),
                "candidate_shape_count": len(candidates),
                "blocked_shapes": shapes[: int(config["max_blocked_shapes"])],
            },
        )

    return {
        "status": "PASS_M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "runtime_status": "PUBLIC_INDEXED_GET_LOADED_DYNAMIC_REQUESTS_INTERCEPTED_BEFORE_NETWORK",
        "browser_backend": config["browser_backend"],
        "browser_binary_name": str(raw.get("browser_binary_name", "SYSTEM_CHROME"))[:80],
        "browser_version": str(raw.get("browser_version", "SYSTEM_CHROME_VERSION_UNAVAILABLE"))[:160],
        "page_surface_verified": True,
        "initial_document_network_sent": True,
        "initial_document_continued_count": 1,
        "pilot_limeira_values_sent": False,
        "static_assets_continued_count": int(raw.get("static_assets_continued_count", 0)),
        "local_requests_continued_count": int(raw.get("local_requests_continued_count", 0)),
        "blocked_request_event_count": len(list(raw.get("blocked_requests") or [])),
        "blocked_shape_count": len(shapes),
        "candidate_shape_count": len(candidates),
        "blocked_shapes": shapes,
        "candidate_shapes": candidates,
        "dynamic_candidate_network_sent": False,
        "form_submission": False,
        "captcha_bypass": False,
        "human_challenge_active": False,
        "authentication_performed": False,
        "credentials_captured": False,
        "cookies_captured": False,
        "request_body_persisted": False,
        "response_body_persisted": False,
        "query_values_persisted": False,
        "head_request_performed": False,
        "browser_download_denied": True,
        "artifact_downloaded": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate_after_review"],
    }
