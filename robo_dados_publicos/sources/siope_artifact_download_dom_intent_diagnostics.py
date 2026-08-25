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
from .siope_artifact_download_runtime_route_probe import (
    _is_allowed_static_asset,
    _is_allowed_verified_metadata,
)
from .siope_export_runtime_route_probe import SiopeRuntimeRouteProbeError

ERROR = "STOP_SIOPE_ARTIFACT_DOWNLOAD_DOM_INTENT_DIAGNOSTICS"


def _dom_snapshot_expression() -> str:
    return r'''(() => {
      const norm = (s, n) => String(s || '').replace(/\s+/g, ' ').trim().slice(0, n);
      const visible = (e) => {
        const s = getComputedStyle(e), r = e.getBoundingClientRect();
        return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0;
      };
      const hrefShape = (href) => {
        if (!href) return null;
        try {
          const u = new URL(href, location.href);
          const scheme = u.protocol.replace(':', '');
          if (scheme !== 'http' && scheme !== 'https') {
            return {scheme, host: '', path: null, query_keys: []};
          }
          return {
            scheme,
            host: u.hostname,
            path: u.pathname || '/',
            query_keys: [...new Set([...u.searchParams.keys()])].sort()
          };
        } catch (_) { return null; }
      };
      const controls = [...document.querySelectorAll('button,a,[role="button"],[role="link"]')]
        .filter(visible).slice(0, 64).map((e) => ({
          tag: e.tagName.toLowerCase(),
          role: e.getAttribute('role') || '',
          text: norm(e.innerText || e.textContent || e.getAttribute('aria-label'), 160),
          href: hrefShape(e.getAttribute('href')),
          disabled: !!e.disabled || e.getAttribute('aria-disabled') === 'true'
        }));
      const dialogs = [...document.querySelectorAll('dialog,[role="dialog"],[aria-modal="true"]')]
        .filter(visible).slice(0, 8).map((e) => ({
          tag: e.tagName.toLowerCase(),
          role: e.getAttribute('role') || '',
          text: norm(e.innerText || e.textContent || e.getAttribute('aria-label'), 240)
        }));
      return {controls, dialogs};
    })()'''


def _clean_href(value) -> dict | None:
    if not isinstance(value, dict):
        return None
    scheme = str(value.get("scheme", ""))[:12]
    host = str(value.get("host", ""))[:255]
    path = value.get("path")
    if path is not None:
        path = str(path)[:1024]
    keys = value.get("query_keys") or []
    if not isinstance(keys, list):
        keys = []
    keys = sorted({str(k)[:128] for k in keys if str(k)})[:32]
    return {"scheme": scheme, "host": host, "path": path, "query_keys": keys}


def sanitize_dom_snapshot(raw: dict) -> dict:
    controls = []
    for item in list(raw.get("controls") or [])[:64]:
        if not isinstance(item, dict):
            continue
        controls.append({
            "tag": str(item.get("tag", ""))[:32],
            "role": str(item.get("role", ""))[:64],
            "text": str(item.get("text", ""))[:160],
            "href": _clean_href(item.get("href")),
            "disabled": bool(item.get("disabled", False)),
        })
    dialogs = []
    for item in list(raw.get("dialogs") or [])[:8]:
        if not isinstance(item, dict):
            continue
        dialogs.append({
            "tag": str(item.get("tag", ""))[:32],
            "role": str(item.get("role", ""))[:64],
            "text": str(item.get("text", ""))[:240],
        })
    return {"controls": controls, "dialogs": dialogs}


def _control_key(item: dict) -> tuple:
    href = item.get("href") or {}
    return (
        item.get("tag", ""), item.get("role", ""), item.get("text", ""),
        href.get("scheme", ""), href.get("host", ""), href.get("path"),
        tuple(href.get("query_keys") or ()), bool(item.get("disabled", False)),
    )


def summarize_dom_intent(before: dict, after: dict) -> dict:
    before = sanitize_dom_snapshot(before)
    after = sanitize_dom_snapshot(after)
    prior_controls = {_control_key(x) for x in before["controls"]}
    new_controls = [x for x in after["controls"] if _control_key(x) not in prior_controls][:16]
    prior_dialogs = {(x["tag"], x["role"], x["text"]) for x in before["dialogs"]}
    new_dialogs = [x for x in after["dialogs"] if (x["tag"], x["role"], x["text"]) not in prior_dialogs][:8]
    return {
        "before_control_count": len(before["controls"]),
        "after_control_count": len(after["controls"]),
        "before_dialog_count": len(before["dialogs"]),
        "after_dialog_count": len(after["dialogs"]),
        "new_control_count": len(new_controls),
        "new_dialog_count": len(new_dialogs),
        "new_controls": new_controls,
        "new_dialogs": new_dialogs,
    }


class SystemChromeCdpArtifactDownloadDomIntentRuntime:
    def _find_browser(self, config: dict) -> str:
        for name in config["browser_binary_candidates"]:
            path = shutil.which(name)
            if path:
                return path
        raise SiopeRuntimeRouteProbeError(f"{ERROR}_BROWSER_UNAVAILABLE")

    def run_probe(self, config: dict) -> dict:
        browser = self._find_browser(config)
        process = page_session = browser_session = None
        with tempfile.TemporaryDirectory(prefix="siope-artifact-download-dom-") as profile_text:
            profile = Path(profile_text)
            cmd = [
                browser, "--headless=new", "--remote-debugging-port=0",
                "--remote-debugging-address=127.0.0.1", "--remote-allow-origins=*",
                f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check",
                "--disable-background-networking", "--disable-component-update", "--disable-sync",
                "--disable-default-apps", "--disable-extensions", "--disable-features=MediaRouter",
                "--metrics-recording-only", "--no-sandbox", "about:blank",
            ]
            env = {k: v for k, v in os.environ.items() if k != "CHROME_LOG_FILE"}
            try:
                process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                port, _ = _wait_devtools_active_port(profile, process)
                version = _wait_browser_debug_version(port, process)
                timeout_s = float(config["cdp_command_timeout_ms"]) / 1000.0
                browser_session = _connect_cdp_with_retry(
                    str(version["webSocketDebuggerUrl"]), command_timeout_s=timeout_s, process=process
                )
                browser_session.command("Browser.setDownloadBehavior", {"behavior": "deny", "eventsEnabled": True})

                target = _create_page_target(port)
                page_session = _connect_cdp_with_retry(
                    str(target["webSocketDebuggerUrl"]), command_timeout_s=timeout_s, process=process
                )
                phase = {"value": "PRE_CLICK"}
                metadata_continued = 0
                static_continued = 0
                blocked_count = 0
                allowed_hosts = set(config["initial_allowed_hosts"])

                def handle_page_event(payload: dict) -> None:
                    nonlocal metadata_continued, static_continued, blocked_count
                    if payload.get("method") != "Fetch.requestPaused":
                        return
                    params = payload.get("params") or {}
                    req = params.get("request") or {}
                    request_id = params.get("requestId")
                    url = str(req.get("url", ""))
                    method = str(req.get("method", "")).upper()
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
                    blocked_count += 1
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
                state = None
                deadline = time.monotonic() + float(config["page_load_timeout_ms"]) / 1000.0
                while time.monotonic() < deadline:
                    result = page_session.command("Runtime.evaluate", {"expression": inspect_expr, "returnByValue": True})
                    state = ((result.get("result") or {}).get("value") or {})
                    if state.get("ready") in {"interactive", "complete"} and state.get("product") and state.get("artifact") and state.get("exportControl"):
                        break
                    page_session.pump(0.15)
                if not state or not state.get("product"):
                    raise SiopeRuntimeRouteProbeError(f"{ERROR}_PRODUCT_NOT_VERIFIED")
                if not state.get("artifact"):
                    raise SiopeRuntimeRouteProbeError(f"{ERROR}_ARTIFACT_NOT_DECLARED")
                if not state.get("exportControl"):
                    raise SiopeRuntimeRouteProbeError(f"{ERROR}_EXPORT_CONTROL_NOT_FOUND")

                page_session.pump(0.5)
                snap_expr = _dom_snapshot_expression()
                before_result = page_session.command("Runtime.evaluate", {"expression": snap_expr, "returnByValue": True})
                before = ((before_result.get("result") or {}).get("value") or {})

                phase["value"] = "POST_CLICK"
                click_expr = f"""(() => {{ const b=[...document.querySelectorAll('button,a,[role=button]')]; const e=b.find(x=>((x.innerText||x.textContent||'').trim()).includes({button})); if(!e)return {{clicked:false}}; e.scrollIntoView({{block:'center'}}); e.click(); return {{clicked:true}}; }})()"""
                clicked = page_session.command("Runtime.evaluate", {"expression": click_expr, "returnByValue": True})
                click_value = ((clicked.get("result") or {}).get("value") or {})
                if not click_value.get("clicked"):
                    raise SiopeRuntimeRouteProbeError(f"{ERROR}_CLICK_NOT_EXECUTED")

                page_session.pump(float(config["post_click_capture_window_ms"]) / 1000.0)
                after_result = page_session.command("Runtime.evaluate", {"expression": snap_expr, "returnByValue": True})
                after = ((after_result.get("result") or {}).get("value") or {})
                return {
                    "page_verified": True,
                    "artifact_declared": True,
                    "export_control_found": True,
                    "click_executed": True,
                    "browser_download_denied": True,
                    "verified_metadata_network_sent": metadata_continued > 0,
                    "verified_metadata_request_count": metadata_continued,
                    "post_click_static_assets_continued_count": static_continued,
                    "blocked_request_count": blocked_count,
                    "dom_before": sanitize_dom_snapshot(before),
                    "dom_after": sanitize_dom_snapshot(after),
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
                        process.terminate(); process.wait(timeout=2)
                    except Exception:
                        try: process.kill()
                        except Exception: pass


def diagnose_artifact_download_dom_intent(config: dict, *, runtime=None) -> dict:
    raw = (runtime or SystemChromeCdpArtifactDownloadDomIntentRuntime()).run_probe(config)
    for key in ("page_verified", "artifact_declared", "export_control_found", "click_executed", "browser_download_denied"):
        if raw.get(key) is not True:
            raise SiopeRuntimeRouteProbeError(f"{ERROR}_RUNTIME_CONTRACT")
    if raw.get("candidate_route_network_sent") is not False or raw.get("artifact_downloaded") is not False:
        raise SiopeRuntimeRouteProbeError(f"{ERROR}_SAFETY_CONTRACT")
    metadata_count = int(raw.get("verified_metadata_request_count", 0))
    if not 1 <= metadata_count <= config["max_verified_metadata_requests"] or raw.get("verified_metadata_network_sent") is not True:
        raise SiopeRuntimeRouteProbeError(f"{ERROR}_VERIFIED_METADATA_NOT_OBSERVED")
    summary = summarize_dom_intent(raw.get("dom_before") or {}, raw.get("dom_after") or {})
    changed = summary["new_control_count"] > 0 or summary["new_dialog_count"] > 0
    return {
        "status": "PASS_M7_SIOPE_ARTIFACT_DOWNLOAD_DOM_INTENT_DIAGNOSTICS_GATE",
        "diagnostic_status": "DOM_INTENT_CHANGE_OBSERVED" if changed else "NO_DOM_INTENT_CHANGE_OBSERVED",
        "verified_metadata_request_count": metadata_count,
        "verified_metadata_network_sent": True,
        "blocked_request_count": int(raw.get("blocked_request_count", 0)),
        "dom_change": summary,
        "single_click_only": True,
        "second_click_executed": False,
        "candidate_route_network_sent": False,
        "browser_download_denied": True,
        "artifact_downloaded": False,
        "response_body_captured": False,
        "request_body_captured": False,
        "request_headers_captured": False,
        "cookies_captured": False,
        "input_values_captured": False,
        "html_captured": False,
        "head_request_performed": False,
        "remote_writes": "NONE",
        "collection_authorized": False,
        "processing_authorized": False,
        "recurrence_authorized": False,
        "schedule_enabled": False,
        "next_gate": "M7_SIOPE_ARTIFACT_DOWNLOAD_DOM_INTENT_EVIDENCE_REVIEW_0_8_0",
    }
