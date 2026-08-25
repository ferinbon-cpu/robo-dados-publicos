from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from urllib.parse import urlparse

from .siope_artifact_download_event_diagnostics import _connect_cdp_with_retry, _wait_devtools_active_port
from .siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError
from .siope_public_get_runtime_cdp_direct import (
    _browser_ws_url_from_active_port,
    _create_attached_page_session,
    _stable_surface_contract_matches,
)
from .siope_public_get_runtime_failure_telemetry import SystemChromeCdpPublicGetRuntimeWithFailureTelemetry
from .siope_public_get_runtime_route_diagnostics import (
    _is_allowed_static_asset,
    _matches_exact_indexed_document,
    summarize_blocked_requests,
)
from .siope_public_runtime_control_inventory import _surface_expression


ERROR = "STOP_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS"


class SiopePublicRuntimeControlValueConsistencyDiagnosticsError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopePublicRuntimeControlValueConsistencyDiagnosticsError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopePublicRuntimeControlValueConsistencyDiagnosticsError(f"{ERROR}_{code}")


def validate_diagnostics_config(config: dict, public_config: dict, design_config: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "PUBLIC_INDEXED_GET_BROWSER_SIDE_BOOLEAN_VALUE_CONSISTENCY",
        "design_config_path": "config/source_expansion.siope_public_runtime_control_value_consistency_diagnostics_design.json",
        "public_runtime_config_path": "config/source_expansion.siope_public_get_runtime_route_diagnostics_gate.json",
        "prerequisite_design_gate_id": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS_DESIGN_0_8_0",
        "comparison_control_names": ["acao", "admin", "cod_muni", "cod_uf", "num_ano", "num_peri", "pag", "tp_relatorio"],
        "returned_comparison_fields": ["control_name", "control_present", "query_key_present", "value_matches_query"],
        "comparison_result": "BOOLEAN_ONLY",
        "actual_control_value_return": "PROHIBITED",
        "actual_query_value_return": "PROHIBITED",
        "option_text_return": "PROHIBITED",
        "option_value_return": "PROHIBITED",
        "html_return": "PROHIBITED",
        "free_text_return": "PROHIBITED",
        "browser_backend": "SYSTEM_CHROME_CDP",
        "browser_profile": "EPHEMERAL_TEMP_ONLY",
        "browser_download_or_install": "PROHIBITED",
        "initial_document_send": "EXACT_PINNED_PUBLIC_INDEXED_EXAMPLE_ONCE_ONLY",
        "official_static_assets": "GET_ONLY_ALLOWLISTED_HOST_AND_EXTENSION",
        "all_other_requests": "ABORT_BEFORE_NETWORK",
        "dom_interaction": "PROHIBITED",
        "form_submission": "PROHIBITED",
        "post_request": "PROHIBITED",
        "navigation_after_initial_document": "PROHIBITED",
        "pilot_limeira_values_send": "PROHIBITED",
        "dynamic_candidate_network_send": "PROHIBITED",
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
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_REVIEW_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(design_config.get("gate_id"), config["prerequisite_design_gate_id"], "DESIGN_GATE")
    _require(design_config.get("next_gate"), config["gate_id"], "DESIGN_NEXT_GATE")
    _require(design_config.get("comparison_control_names"), config["comparison_control_names"], "DESIGN_CONTROLS")
    _require(design_config.get("comparison_result_boolean_only"), None, "DESIGN_RESULT_FIELD_ABSENT") if False else None
    _require(design_config.get("actual_control_value_return"), "PROHIBITED", "DESIGN_CONTROL_VALUE")
    _require(design_config.get("actual_query_value_return"), "PROHIBITED", "DESIGN_QUERY_VALUE")
    _require(design_config.get("dom_interaction"), "PROHIBITED", "DESIGN_INTERACTION")
    _require(design_config.get("form_submission"), "PROHIBITED", "DESIGN_SUBMIT")
    _require(design_config.get("post_request"), "PROHIBITED", "DESIGN_POST")
    _require(design_config.get("pilot_limeira_values_send"), "PROHIBITED", "DESIGN_LIMEIRA")

    _require(public_config.get("gate_id"), "M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0", "PUBLIC_GATE")
    _require(public_config.get("expected_query_keys"), config["comparison_control_names"], "PUBLIC_QUERY_KEYS")
    _require(public_config.get("pilot_limeira_values_send"), "PROHIBITED", "PUBLIC_LIMEIRA")
    _require(public_config.get("dynamic_candidate_network_send"), "PROHIBITED", "PUBLIC_DYNAMIC_SEND")
    if "352690" in str(public_config.get("public_indexed_example_url", "")):
        raise SiopePublicRuntimeControlValueConsistencyDiagnosticsError(f"{ERROR}_PUBLIC_CONFIG_PILOT_VALUE")


def _comparison_expression(config: dict) -> str:
    names = json.dumps(config["comparison_control_names"], ensure_ascii=True)
    return f"""(() => {{
      const names = {names};
      const params = new URLSearchParams(location.search || '');
      return names.map((name) => {{
        const nodes = document.getElementsByName(name);
        const el = nodes.length === 1 ? nodes[0] : null;
        const queryPresent = params.has(name);
        return {{
          control_name: name,
          control_present: Boolean(el),
          query_key_present: Boolean(queryPresent),
          value_matches_query: Boolean(el && queryPresent && String(el.value) === String(params.get(name)))
        }};
      }});
    }})()"""


def sanitize_comparisons(raw: object, config: dict) -> list[dict]:
    if not isinstance(raw, list):
        raise SiopePublicRuntimeControlValueConsistencyDiagnosticsError(f"{ERROR}_COMPARISON_LIST_REQUIRED")
    expected_names = list(config["comparison_control_names"])
    if len(raw) != len(expected_names):
        raise SiopePublicRuntimeControlValueConsistencyDiagnosticsError(f"{ERROR}_COMPARISON_COUNT")
    rows: list[dict] = []
    for index, expected_name in enumerate(expected_names):
        item = raw[index]
        if not isinstance(item, dict):
            raise SiopePublicRuntimeControlValueConsistencyDiagnosticsError(f"{ERROR}_COMPARISON_OBJECT")
        _require(item.get("control_name"), expected_name, "COMPARISON_NAME")
        allowed = set(config["returned_comparison_fields"])
        if set(item.keys()) - allowed:
            raise SiopePublicRuntimeControlValueConsistencyDiagnosticsError(f"{ERROR}_COMPARISON_UNEXPECTED_FIELD")
        rows.append({
            "control_name": expected_name,
            "control_present": bool(item.get("control_present")),
            "query_key_present": bool(item.get("query_key_present")),
            "value_matches_query": bool(item.get("value_matches_query")),
        })
    return rows


class SystemChromeCdpPublicRuntimeControlValueConsistency(SystemChromeCdpPublicGetRuntimeWithFailureTelemetry):
    def run_consistency(self, config: dict, public_config: dict) -> dict:
        browser = self._find_browser(public_config)
        try:
            browser_version = subprocess.check_output([browser, "--version"], text=True, timeout=3).strip()[:160]
        except Exception:
            browser_version = "SYSTEM_CHROME_VERSION_UNAVAILABLE"

        process = page_session = browser_session = None
        blocked: list[dict] = []
        initial_document_continued = 0
        static_assets_continued = 0
        local_requests_continued = 0
        page_state: dict = {}
        try:
            with tempfile.TemporaryDirectory(prefix="siope-public-value-consistency-", ignore_cleanup_errors=True) as profile_text:
                profile = Path(profile_text)
                cmd = [
                    browser, "--headless=new", "--remote-debugging-port=0", "--remote-debugging-address=127.0.0.1",
                    "--remote-allow-origins=*", f"--user-data-dir={profile}", "--no-first-run",
                    "--no-default-browser-check", "--disable-background-networking", "--disable-component-update",
                    "--disable-sync", "--disable-default-apps", "--disable-extensions", "--disable-features=MediaRouter",
                    "--metrics-recording-only", "--no-sandbox", "about:blank",
                ]
                env = {k: v for k, v in os.environ.items() if k != "CHROME_LOG_FILE"}
                process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                port, browser_ws_path = _wait_devtools_active_port(profile, process)
                browser_session = _connect_cdp_with_retry(
                    _browser_ws_url_from_active_port(port, browser_ws_path),
                    command_timeout_s=float(public_config["cdp_command_timeout_ms"]) / 1000.0,
                    process=process,
                )
                browser_session.command("Browser.setDownloadBehavior", {"behavior": "deny"})
                page_session = _create_attached_page_session(browser_session)

                def handle_event(payload: dict) -> None:
                    nonlocal initial_document_continued, static_assets_continued, local_requests_continued
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
                    if _matches_exact_indexed_document(url, method, resource_type, public_config):
                        initial_document_continued += 1
                        page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                        return
                    if _is_allowed_static_asset(url, method, resource_type, public_config):
                        static_assets_continued += 1
                        page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                        return
                    blocked.append({"url": url, "method": method, "resource_type": resource_type})
                    page_session.send_no_wait("Fetch.failRequest", {"requestId": request_id, "errorReason": "Aborted"})

                page_session.event_handler = handle_event
                page_session.command("Page.enable")
                page_session.command("Runtime.enable")
                page_session.command("Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]})
                page_session.command("Page.navigate", {"url": public_config["public_indexed_example_url"]})
                surface_expr = _surface_expression(public_config)
                deadline = time.monotonic() + float(public_config["page_load_timeout_ms"]) / 1000.0
                while time.monotonic() < deadline:
                    evaluated = page_session.command("Runtime.evaluate", {"expression": surface_expr, "returnByValue": True})
                    page_state = ((evaluated.get("result") or {}).get("value") or {})
                    if _stable_surface_contract_matches(page_state, public_config):
                        break
                    page_session.pump(0.15)
                if not _stable_surface_contract_matches(page_state, public_config):
                    raise SiopePublicRuntimeControlValueConsistencyDiagnosticsError(
                        f"{ERROR}_PUBLIC_SURFACE_NOT_VERIFIED",
                        diagnostics={
                            "initial_document_continued_count": initial_document_continued,
                            "initial_document_network_sent": initial_document_continued == 1,
                            "browser_download_denied": True,
                        },
                    )
                page_session.pump(float(public_config["capture_window_ms"]) / 1000.0)
                final_eval = page_session.command("Runtime.evaluate", {"expression": surface_expr, "returnByValue": True})
                final_state = ((final_eval.get("result") or {}).get("value") or {})
                comparison_eval = page_session.command(
                    "Runtime.evaluate", {"expression": _comparison_expression(config), "returnByValue": True}
                )
                raw_comparisons = ((comparison_eval.get("result") or {}).get("value") or [])
                return {
                    "browser_binary_name": Path(browser).name,
                    "browser_version": browser_version,
                    "page_surface_verified": _stable_surface_contract_matches(final_state, public_config),
                    "human_challenge_active_dom": bool(final_state.get("challenge")),
                    "initial_document_continued_count": initial_document_continued,
                    "initial_document_network_sent": initial_document_continued == 1,
                    "static_assets_continued_count": static_assets_continued,
                    "local_requests_continued_count": local_requests_continued,
                    "blocked_requests": blocked,
                    "browser_download_denied": True,
                    "dom_interaction_performed": False,
                    "form_submission": False,
                    "navigation_after_initial_document": False,
                    "dynamic_candidate_network_sent": False,
                    "raw_comparisons": raw_comparisons,
                }
        except SiopePublicRuntimeControlValueConsistencyDiagnosticsError:
            raise
        except SiopeRuntimeRouteProbeError as exc:
            raise SiopePublicRuntimeControlValueConsistencyDiagnosticsError(
                f"{ERROR}_BROWSER_RUNTIME",
                diagnostics={
                    "runtime_stop": str(exc)[:160],
                    "initial_document_continued_count": initial_document_continued,
                    "initial_document_network_sent": initial_document_continued == 1,
                    "browser_download_denied": True,
                },
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


def diagnose_control_value_consistency(config: dict, public_config: dict, design_config: dict, *, runtime=None) -> dict:
    validate_diagnostics_config(config, public_config, design_config)
    runtime = runtime or SystemChromeCdpPublicRuntimeControlValueConsistency()
    raw = runtime.run_consistency(config, public_config)

    _require(raw.get("page_surface_verified"), True, "RUNTIME_SURFACE")
    _require(raw.get("initial_document_network_sent"), True, "INITIAL_DOCUMENT_SENT")
    _require(raw.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(raw.get("browser_download_denied"), True, "DOWNLOAD_DENIAL")
    _require(raw.get("dom_interaction_performed"), False, "DOM_INTERACTION")
    _require(raw.get("form_submission"), False, "FORM_SUBMISSION")
    _require(raw.get("navigation_after_initial_document"), False, "SECOND_NAVIGATION")
    _require(raw.get("dynamic_candidate_network_sent"), False, "DYNAMIC_NETWORK_SENT")
    if raw.get("human_challenge_active_dom") is True:
        raise SiopePublicRuntimeControlValueConsistencyDiagnosticsError(f"{ERROR}_HUMAN_CHALLENGE_ACTIVE")

    blocked_shapes, candidates = summarize_blocked_requests(list(raw.get("blocked_requests") or []), public_config)
    if candidates:
        raise SiopePublicRuntimeControlValueConsistencyDiagnosticsError(
            f"{ERROR}_UNEXPECTED_DYNAMIC_CANDIDATE",
            diagnostics={"candidate_shape_count": len(candidates), "candidate_shapes": candidates},
        )

    comparisons = sanitize_comparisons(raw.get("raw_comparisons"), config)
    return {
        "status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_VALUE_CONSISTENCY_DIAGNOSTICS",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "runtime_status": "PUBLIC_INDEXED_GET_CONTROL_VALUES_COMPARED_TO_QUERY_BOOLEAN_ONLY",
        "browser_backend": config["browser_backend"],
        "browser_binary_name": str(raw.get("browser_binary_name", "SYSTEM_CHROME"))[:80],
        "browser_version": str(raw.get("browser_version", "SYSTEM_CHROME_VERSION_UNAVAILABLE"))[:160],
        "page_surface_verified": True,
        "initial_document_network_sent": True,
        "initial_document_continued_count": 1,
        "static_assets_continued_count": int(raw.get("static_assets_continued_count", 0)),
        "local_requests_continued_count": int(raw.get("local_requests_continued_count", 0)),
        "blocked_request_event_count": len(list(raw.get("blocked_requests") or [])),
        "blocked_shape_count": len(blocked_shapes),
        "blocked_shapes": blocked_shapes,
        "candidate_shape_count": 0,
        "candidate_shapes": [],
        "comparison_count": len(comparisons),
        "comparison_results": comparisons,
        "all_controls_present": all(row["control_present"] for row in comparisons),
        "all_query_keys_present": all(row["query_key_present"] for row in comparisons),
        "all_values_match_query": all(row["value_matches_query"] for row in comparisons),
        "comparison_result_boolean_only": True,
        "actual_control_values_returned": False,
        "actual_query_values_returned": False,
        "option_text_returned": False,
        "option_values_returned": False,
        "html_returned": False,
        "free_text_returned": False,
        "dom_interaction_performed": False,
        "navigation_after_initial_document": False,
        "pilot_limeira_values_sent": False,
        "dynamic_candidate_network_sent": False,
        "form_submission": False,
        "post_request_performed": False,
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
        "next_gate": config["next_gate"],
    }
