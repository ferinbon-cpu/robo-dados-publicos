from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from urllib.parse import urlparse

from .siope_artifact_download_event_diagnostics import _connect_cdp_with_retry, _wait_devtools_active_port
from .siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError
from .siope_public_get_runtime_cdp_direct import (
    RUNTIME_STABLE_SURFACE_MARKERS,
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


ERROR = "STOP_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY"
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.:\-\[\]]{0,120}$")
_SAFE_HOST = re.compile(r"^[A-Za-z0-9.-]{0,253}$")


class SiopePublicRuntimeControlInventoryError(RuntimeError):
    def __init__(self, message: str, *, diagnostics: dict | None = None):
        super().__init__(message)
        self.diagnostics = diagnostics or {}


def load_json(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SiopePublicRuntimeControlInventoryError(f"{ERROR}_JSON_OBJECT_REQUIRED")
    return payload


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise SiopePublicRuntimeControlInventoryError(f"{ERROR}_{code}")


def validate_inventory_config(config: dict, public_config: dict, design_config: dict) -> None:
    exact = {
        "gate_id": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_0_8_0",
        "source_id": "FNDE_SIOPE_DADOS_INFORMADOS_MUNICIPIOS_LIMEIRA",
        "software_version": "0.8.0",
        "release_status": "CANDIDATE",
        "mode": "PUBLIC_INDEXED_GET_DOM_CONTROL_INVENTORY_NO_INTERACTION",
        "prerequisite_design_gate_id": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INTERACTION_DIAGNOSTICS_DESIGN_0_8_0",
        "public_runtime_config_path": "config/source_expansion.siope_public_get_runtime_route_diagnostics_gate.json",
        "design_config_path": "config/source_expansion.siope_public_runtime_control_interaction_diagnostics_design.json",
        "stable_surface_labels": ["Exibir:", "Ano:", "UF:", "Planilha:"],
        "allowed_control_tags": ["select", "input", "button"],
        "allowed_persisted_fields": [
            "associated_stable_label", "tag_name", "type", "id", "name", "disabled", "option_count",
            "form_method", "form_action_scheme", "form_action_host", "form_action_path",
        ],
        "max_controls": 64,
        "browser_backend": "SYSTEM_CHROME_CDP",
        "browser_profile": "EPHEMERAL_TEMP_ONLY",
        "browser_download_or_install": "PROHIBITED",
        "initial_document_send": "EXACT_PINNED_PUBLIC_INDEXED_EXAMPLE_ONCE_ONLY",
        "official_static_assets": "GET_ONLY_ALLOWLISTED_HOST_AND_EXTENSION",
        "all_other_requests": "ABORT_BEFORE_NETWORK",
        "dom_interaction": "PROHIBITED",
        "control_value_capture": "PROHIBITED",
        "option_text_capture": "PROHIBITED",
        "option_value_capture": "PROHIBITED",
        "html_capture": "PROHIBITED",
        "free_text_capture": "PROHIBITED",
        "navigation_after_initial_document": "PROHIBITED",
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
        "route_synthesis_or_guessing": "PROHIBITED",
        "control_identity_promotion": "PROHIBITED",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY_REVIEW_0_8_0",
    }
    for key, expected in exact.items():
        _require(config.get(key), expected, f"CONFIG_{key.upper()}")

    _require(design_config.get("gate_id"), config["prerequisite_design_gate_id"], "DESIGN_GATE")
    _require(design_config.get("next_gate"), config["gate_id"], "DESIGN_NEXT_GATE")
    _require(design_config.get("control_interaction_authorized"), False, "DESIGN_INTERACTION_AUTH")
    _require(design_config.get("control_inventory_required"), True, "DESIGN_INVENTORY_REQUIRED")
    _require(design_config.get("control_identity_status"), "UNPROVEN", "DESIGN_CONTROL_IDENTITY")
    _require(public_config.get("gate_id"), "M7_SIOPE_PUBLIC_GET_RUNTIME_ROUTE_DIAGNOSTICS_0_8_0", "PUBLIC_CONFIG_GATE")
    _require(public_config.get("pilot_limeira_values_send"), "PROHIBITED", "PUBLIC_CONFIG_LIMEIRA")
    if "352690" in str(public_config.get("public_indexed_example_url", "")):
        raise SiopePublicRuntimeControlInventoryError(f"{ERROR}_PUBLIC_CONFIG_PILOT_VALUE")


def _safe_identifier(value: object) -> str:
    text = str(value or "")[:120]
    return text if _SAFE_IDENTIFIER.fullmatch(text) else ""


def _safe_type(value: object) -> str:
    text = str(value or "").strip().lower()[:40]
    return text if re.fullmatch(r"[a-z0-9_-]{0,40}", text) else ""


def _safe_path(value: object) -> str:
    text = str(value or "")[:512]
    if not text.startswith("/") or "?" in text or "#" in text or any(ch in text for ch in "\r\n\t"):
        return ""
    return text


def sanitize_control(raw: dict, config: dict) -> dict:
    marker = str(raw.get("associated_stable_label", ""))
    if marker not in set(config["stable_surface_labels"]):
        marker = ""
    tag = str(raw.get("tag_name", "")).lower()
    if tag not in set(config["allowed_control_tags"]):
        tag = ""
    method = str(raw.get("form_method", "")).upper()
    if method not in {"", "GET", "POST"}:
        method = ""
    scheme = str(raw.get("form_action_scheme", "")).lower()
    if scheme not in {"", "http", "https"}:
        scheme = ""
    host = str(raw.get("form_action_host", ""))[:253].lower()
    if not _SAFE_HOST.fullmatch(host):
        host = ""
    try:
        option_count = int(raw.get("option_count", 0))
    except (TypeError, ValueError):
        option_count = 0
    option_count = max(0, min(option_count, 10000))
    return {
        "associated_stable_label": marker,
        "tag_name": tag,
        "type": _safe_type(raw.get("type")),
        "id": _safe_identifier(raw.get("id")),
        "name": _safe_identifier(raw.get("name")),
        "disabled": bool(raw.get("disabled")),
        "option_count": option_count if tag == "select" else 0,
        "form_method": method,
        "form_action_scheme": scheme,
        "form_action_host": host,
        "form_action_path": _safe_path(raw.get("form_action_path")),
    }


def sanitize_controls(raw_controls: list[dict], config: dict) -> list[dict]:
    controls = [sanitize_control(raw if isinstance(raw, dict) else {}, config) for raw in raw_controls]
    return controls[: int(config["max_controls"])]


def _surface_expression(public_config: dict) -> str:
    stable_literals = [json.dumps(marker, ensure_ascii=True) for marker in RUNTIME_STABLE_SURFACE_MARKERS]
    challenge_literal = json.dumps(public_config["human_challenge_required_markers"][0], ensure_ascii=False)
    return f"""(() => {{
      const text = document.body ? (document.body.innerText || '') : '';
      const lower = text.toLowerCase();
      const params = new URLSearchParams(location.search || '');
      return {{
        ready: document.readyState,
        stableMarkers: [{', '.join(f'text.includes({literal})' for literal in stable_literals)}],
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


def _inventory_expression(config: dict) -> str:
    labels = json.dumps(config["stable_surface_labels"], ensure_ascii=True)
    max_controls = int(config["max_controls"])
    tags = ",".join(config["allowed_control_tags"])
    return f"""(() => {{
      const stableLabels = {labels};
      const controls = Array.from(document.querySelectorAll({json.dumps(tags)}));
      const association = new Map();
      for (const label of Array.from(document.querySelectorAll('label'))) {{
        const observed = String(label.innerText || label.textContent || '').replace(/\\s+/g, ' ').trim();
        const marker = stableLabels.find((m) => observed === m || observed.startsWith(m + ' '));
        if (!marker) continue;
        let target = null;
        const htmlFor = String(label.htmlFor || '');
        if (htmlFor) target = document.getElementById(htmlFor);
        if (!target) target = label.querySelector('select,input,button');
        if (target && controls.includes(target)) association.set(target, marker);
      }}
      const rows = controls.slice(0, {max_controls + 1}).map((el) => {{
        const tag = String(el.tagName || '').toLowerCase();
        const form = el.form || null;
        let actionScheme = '';
        let actionHost = '';
        let actionPath = '';
        if (form) {{
          try {{
            const u = new URL(form.getAttribute('action') || location.href, location.href);
            actionScheme = String(u.protocol || '').replace(':', '');
            actionHost = String(u.hostname || '');
            actionPath = String(u.pathname || '/');
          }} catch (_) {{}}
        }}
        return {{
          associated_stable_label: association.get(el) || '',
          tag_name: tag,
          type: String(el.getAttribute('type') || (tag === 'select' ? 'select' : tag === 'button' ? 'button' : '')).slice(0, 40),
          id: String(el.id || '').slice(0, 120),
          name: String(el.getAttribute('name') || '').slice(0, 120),
          disabled: Boolean(el.disabled),
          option_count: tag === 'select' && el.options ? Number(el.options.length || 0) : 0,
          form_method: form ? String(form.method || 'get').toUpperCase().slice(0, 16) : '',
          form_action_scheme: actionScheme,
          form_action_host: actionHost,
          form_action_path: actionPath
        }};
      }});
      return {{total_count: controls.length, truncated: controls.length > {max_controls}, controls: rows.slice(0, {max_controls})}};
    }})()"""


class SystemChromeCdpPublicRuntimeControlInventory(SystemChromeCdpPublicGetRuntimeWithFailureTelemetry):
    def run_inventory(self, config: dict, public_config: dict) -> dict:
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
        navigate_result: dict = {}
        try:
            with tempfile.TemporaryDirectory(prefix="siope-public-control-inventory-", ignore_cleanup_errors=True) as profile_text:
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
                navigate_result = page_session.command("Page.navigate", {"url": public_config["public_indexed_example_url"]})
                surface_expr = _surface_expression(public_config)
                deadline = time.monotonic() + float(public_config["page_load_timeout_ms"]) / 1000.0
                while time.monotonic() < deadline:
                    evaluated = page_session.command("Runtime.evaluate", {"expression": surface_expr, "returnByValue": True})
                    page_state = ((evaluated.get("result") or {}).get("value") or {})
                    if _stable_surface_contract_matches(page_state, public_config):
                        break
                    page_session.pump(0.15)
                if not _stable_surface_contract_matches(page_state, public_config):
                    raise SiopePublicRuntimeControlInventoryError(
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
                inventory_eval = page_session.command(
                    "Runtime.evaluate", {"expression": _inventory_expression(config), "returnByValue": True}
                )
                inventory = ((inventory_eval.get("result") or {}).get("value") or {})
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
                    "inventory_total_count": int(inventory.get("total_count", 0)),
                    "inventory_truncated": bool(inventory.get("truncated")),
                    "raw_controls": list(inventory.get("controls") or []),
                }
        except SiopePublicRuntimeControlInventoryError:
            raise
        except SiopeRuntimeRouteProbeError as exc:
            raise SiopePublicRuntimeControlInventoryError(
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


def inventory_public_runtime_controls(config: dict, public_config: dict, design_config: dict, *, runtime=None) -> dict:
    validate_inventory_config(config, public_config, design_config)
    runtime = runtime or SystemChromeCdpPublicRuntimeControlInventory()
    raw = runtime.run_inventory(config, public_config)

    _require(raw.get("page_surface_verified"), True, "RUNTIME_SURFACE")
    _require(raw.get("initial_document_network_sent"), True, "INITIAL_DOCUMENT_SENT")
    _require(raw.get("initial_document_continued_count"), 1, "INITIAL_DOCUMENT_COUNT")
    _require(raw.get("browser_download_denied"), True, "DOWNLOAD_DENIAL")
    _require(raw.get("dom_interaction_performed"), False, "DOM_INTERACTION")
    _require(raw.get("form_submission"), False, "FORM_SUBMISSION")
    _require(raw.get("navigation_after_initial_document"), False, "SECOND_NAVIGATION")
    _require(raw.get("dynamic_candidate_network_sent"), False, "DYNAMIC_NETWORK_SENT")
    if raw.get("human_challenge_active_dom") is True:
        raise SiopePublicRuntimeControlInventoryError(f"{ERROR}_HUMAN_CHALLENGE_ACTIVE")
    if raw.get("inventory_truncated") is True or int(raw.get("inventory_total_count", 0)) > int(config["max_controls"]):
        raise SiopePublicRuntimeControlInventoryError(
            f"{ERROR}_CONTROL_LIMIT",
            diagnostics={"inventory_total_count": int(raw.get("inventory_total_count", 0)), "max_controls": config["max_controls"]},
        )

    blocked_shapes, candidates = summarize_blocked_requests(list(raw.get("blocked_requests") or []), public_config)
    if candidates:
        raise SiopePublicRuntimeControlInventoryError(
            f"{ERROR}_UNEXPECTED_DYNAMIC_CANDIDATE",
            diagnostics={"candidate_shape_count": len(candidates), "candidate_shapes": candidates},
        )

    controls = sanitize_controls(list(raw.get("raw_controls") or []), config)
    serialized = json.dumps(controls, sort_keys=True)
    if "352690" in serialized:
        raise SiopePublicRuntimeControlInventoryError(f"{ERROR}_PILOT_VALUE_IN_INVENTORY")

    associated = [control for control in controls if control["associated_stable_label"]]
    return {
        "status": "PASS_M7_SIOPE_PUBLIC_RUNTIME_CONTROL_INVENTORY",
        "gate_id": config["gate_id"],
        "source_id": config["source_id"],
        "software_version": config["software_version"],
        "runtime_status": "PUBLIC_INDEXED_GET_LOADED_CONTROLS_INVENTORIED_WITHOUT_INTERACTION",
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
        "control_count": len(controls),
        "associated_stable_label_control_count": len(associated),
        "controls": controls,
        "control_identity_promoted": False,
        "dom_interaction_performed": False,
        "control_values_captured": False,
        "option_text_captured": False,
        "option_values_captured": False,
        "html_captured": False,
        "free_text_captured": False,
        "navigation_after_initial_document": False,
        "pilot_limeira_values_sent": False,
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
        "route_synthesized_or_guessed": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": config["next_gate"],
    }
