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
from .siope_official_olinda_api_application_dom_syntax_skeleton_diagnostics import (
    COUNT_FIELDS,
    ERROR,
    SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError,
    _validate_counts,
)


def _evaluation_value_or_stop(evaluation: dict) -> dict:
    """Return only a by-value mapping; never surface exception/source material."""
    if not isinstance(evaluation, dict):
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(
            f"{ERROR}_DOM_EVALUATION_RESPONSE"
        )
    if evaluation.get("exceptionDetails") is not None:
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(
            f"{ERROR}_DOM_EVALUATION_EXCEPTION",
            diagnostics={"javascript_exception_observed": True},
        )
    remote = evaluation.get("result") or {}
    value = remote.get("value")
    if not isinstance(value, dict):
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(
            f"{ERROR}_DOM_EVALUATION_VALUE",
            diagnostics={"javascript_exception_observed": False},
        )
    return value


class SystemChromeCdpDomSyntaxSkeletonRuntimeV2:
    """Rendered-DOM diagnostics with string-only known-syntax comparisons.

    The browser returns only the fixed integer count contract. DOM text is read
    transiently inside Runtime.evaluate and never crosses the CDP boundary.
    """

    def _find_browser(self, config: dict) -> str:
        for name in config["browser_binary_candidates"]:
            path = shutil.which(name)
            if path:
                return path
        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(
            f"{ERROR}_BROWSER_UNAVAILABLE"
        )

    def run_probe(self, config: dict) -> dict:
        browser = self._find_browser(config)
        process = page_session = browser_session = None
        blocked: list[dict] = []
        static_assets_continued = 0
        initial_document_continued = 0
        local_requests_continued = 0
        try:
            with tempfile.TemporaryDirectory(
                prefix="siope-olinda-dom-syntax-v2-", ignore_cleanup_errors=True
            ) as profile_text:
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
                process = subprocess.Popen(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env
                )
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
                    elif (
                        _matches_exact_application_document(url, method, resource_type, config)
                        and initial_document_continued == 0
                    ):
                        initial_document_continued += 1
                        page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                    elif _is_allowed_static_asset(url, method, resource_type, config):
                        static_assets_continued += 1
                        page_session.send_no_wait("Fetch.continueRequest", {"requestId": request_id})
                    else:
                        blocked.append({"url": url, "method": method, "resource_type": resource_type})
                        page_session.send_no_wait(
                            "Fetch.failRequest", {"requestId": request_id, "errorReason": "Aborted"}
                        )

                page_session.event_handler = handle_event
                page_session.command("Page.enable")
                page_session.command("Runtime.enable")
                page_session.command(
                    "Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]}
                )
                page_session.command("Page.navigate", {"url": config["exact_application_url"]})

                scheme_literal = json.dumps(config["expected_scheme"] + ":")
                host_literal = json.dumps(config["expected_host"])
                path_literal = json.dumps(config["expected_path"])
                surface_expr = f"""(() => ({{
                  scheme_matches: window.location.protocol === {scheme_literal},
                  host_matches: window.location.hostname === {host_literal},
                  path_matches: window.location.pathname === {path_literal},
                  query_empty: window.location.search === '',
                  fragment_present: window.location.hash.length > 0,
                  ready_eligible: document.readyState === 'interactive' || document.readyState === 'complete'
                }}))()"""
                surface = None
                deadline = time.monotonic() + float(config["page_load_timeout_ms"]) / 1000.0
                while time.monotonic() < deadline:
                    evaluation = page_session.command(
                        "Runtime.evaluate", {"expression": surface_expr, "returnByValue": True}
                    )
                    if evaluation.get("exceptionDetails") is not None:
                        raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(
                            f"{ERROR}_SURFACE_EVALUATION_EXCEPTION",
                            diagnostics={"javascript_exception_observed": True},
                        )
                    surface = ((evaluation.get("result") or {}).get("value") or {})
                    if all(
                        surface.get(k) is True
                        for k in (
                            "scheme_matches",
                            "host_matches",
                            "path_matches",
                            "query_empty",
                            "ready_eligible",
                        )
                    ):
                        break
                    page_session.pump(0.15)
                if not surface or not all(
                    surface.get(k) is True
                    for k in (
                        "scheme_matches",
                        "host_matches",
                        "path_matches",
                        "query_empty",
                        "ready_eligible",
                    )
                ):
                    shapes, candidates = summarize_blocked_requests(blocked, config)
                    raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(
                        f"{ERROR}_APPLICATION_SURFACE_NOT_VERIFIED",
                        diagnostics={"blocked_shapes": shapes, "candidate_shapes": candidates},
                    )

                page_session.pump(float(config["capture_window_ms"]) / 1000.0)
                callable_literal = json.dumps(config["technical_callable_pattern_name"])
                parameter_literals = ",".join(
                    json.dumps(v) for v in config["technical_parameter_names"]
                )
                analysis_window = int(config["analysis_window_chars"])
                param_window = int(config["parameter_sequence_window_chars"])
                count_fields_json = json.dumps(COUNT_FIELDS)

                # Deliberately avoids dynamically constructed regular expressions.
                # Whitespace is removed only inside the bounded local window used
                # for known public syntax-token comparisons.
                expr = f"""(() => {{
                  const callableName = {callable_literal};
                  const params = [{parameter_literals}];
                  const analysisWindow = {analysis_window};
                  const paramWindow = {param_window};
                  const fields = {count_fields_json};
                  const counts = Object.fromEntries(fields.map((k) => [k, 0]));
                  const elements = Array.from(document.querySelectorAll('*'));
                  const textOf = (el) => String((el && el.textContent) || '');
                  const hasAll = (el) => {{
                    const t = textOf(el);
                    return [callableName, ...params].every((x) => t.includes(x));
                  }};
                  const containers = elements.filter(hasAll);
                  const minimal = containers.filter((el) =>
                    !Array.from(el.children || []).some(hasAll)
                  );
                  counts.minimal_contract_container_count = minimal.length;

                  const isWord = (c) => {{
                    if (!c) return false;
                    const n = c.charCodeAt(0);
                    return (n >= 48 && n <= 57) || (n >= 65 && n <= 90) ||
                           (n >= 97 && n <= 122) || c === '_';
                  }};
                  const occurrences = (text, token) => {{
                    const out = [];
                    let p = 0;
                    while (p <= text.length - token.length) {{
                      const i = text.indexOf(token, p);
                      if (i < 0) break;
                      const a = i === 0 ? '' : text[i - 1];
                      const b = i + token.length >= text.length ? '' : text[i + token.length];
                      if (!isWord(a) && !isWord(b)) out.push(i);
                      p = i + token.length;
                    }}
                    return out;
                  }};
                  const orderedParams = (text) => {{
                    let p = 0;
                    const ends = [];
                    for (const token of params) {{
                      const i = text.indexOf(token, p);
                      if (i < 0) return null;
                      ends.push(i + token.length);
                      p = i + token.length;
                    }}
                    return ends;
                  }};
                  const compact = (text) => text.split(/\\s+/).join('');
                  const bindingToken = (p) => p + '=@' + p;
                  const aliasTokens = (p) => ['?@' + p + '=', '&@' + p + '='];
                  const orderedStrings = (text, tokens) => {{
                    let p = 0;
                    for (const token of tokens) {{
                      const i = text.indexOf(token, p);
                      if (i < 0) return false;
                      p = i + token.length;
                    }}
                    return true;
                  }};
                  const hasAlias = (text, p) => aliasTokens(p).some((token) => text.includes(token));

                  for (const el of minimal) {{
                    const text = textOf(el);
                    for (const i of occurrences(text, callableName)) {{
                      counts.callable_occurrence_in_minimal_container_count += 1;
                      const after = text.slice(
                        i + callableName.length,
                        i + callableName.length + analysisWindow
                      );
                      const pwin = text.slice(
                        i + callableName.length,
                        i + callableName.length + paramWindow
                      );
                      const compactAfter = compact(after);
                      const open = after.trimStart().startsWith('(');
                      const ordered = orderedParams(pwin);
                      const close = !!ordered && pwin.slice(ordered[ordered.length - 1]).includes(')');
                      const bindingTokens = params.map(bindingToken);
                      const bs = bindingTokens.map((token) => compactAfter.includes(token));
                      const allB = bs.every(Boolean);
                      const ordB = orderedStrings(compactAfter, bindingTokens);
                      const qs = params.map((p) => hasAlias(compactAfter, p));
                      const allQ = qs.every(Boolean);
                      const fmt = compactAfter.includes('$format=');

                      if (open) counts.callable_open_paren_in_minimal_container_count += 1;
                      if (ordered) counts.callable_ordered_parameter_names_512_in_minimal_container_count += 1;
                      if (close) counts.callable_close_paren_after_ordered_parameters_512_in_minimal_container_count += 1;
                      if (bs[0]) counts.callable_ano_at_binding_4096_in_minimal_container_count += 1;
                      if (bs[1]) counts.callable_num_at_binding_4096_in_minimal_container_count += 1;
                      if (bs[2]) counts.callable_sig_at_binding_4096_in_minimal_container_count += 1;
                      if (allB) counts.callable_all_three_at_bindings_4096_in_minimal_container_count += 1;
                      if (ordB) counts.callable_ordered_all_three_at_bindings_4096_in_minimal_container_count += 1;
                      if (qs[0]) counts.callable_query_alias_ano_4096_in_minimal_container_count += 1;
                      if (qs[1]) counts.callable_query_alias_num_4096_in_minimal_container_count += 1;
                      if (qs[2]) counts.callable_query_alias_sig_4096_in_minimal_container_count += 1;
                      if (allQ) counts.callable_all_three_query_aliases_4096_in_minimal_container_count += 1;
                      if (fmt) counts.callable_format_assignment_4096_in_minimal_container_count += 1;
                      if (open && close && ordB && allQ && fmt) {{
                        counts.callable_full_known_signature_skeleton_4096_in_minimal_container_count += 1;
                      }}
                    }}
                  }}
                  return counts;
                }})()"""
                evaluation = page_session.command(
                    "Runtime.evaluate", {"expression": expr, "returnByValue": True}
                )
                counts = _evaluation_value_or_stop(evaluation)
                _validate_counts(counts, config)

                final_eval = page_session.command(
                    "Runtime.evaluate", {"expression": surface_expr, "returnByValue": True}
                )
                if final_eval.get("exceptionDetails") is not None:
                    raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(
                        f"{ERROR}_FINAL_SURFACE_EVALUATION_EXCEPTION",
                        diagnostics={"javascript_exception_observed": True},
                    )
                final_surface = ((final_eval.get("result") or {}).get("value") or {})
                if not all(
                    final_surface.get(k) is True
                    for k in (
                        "scheme_matches",
                        "host_matches",
                        "path_matches",
                        "query_empty",
                        "ready_eligible",
                    )
                ):
                    raise SiopeOfficialOlindaApiApplicationDomSyntaxSkeletonDiagnosticsError(
                        f"{ERROR}_FINAL_SURFACE"
                    )
                shapes, candidates = summarize_blocked_requests(blocked, config)
                return {
                    "application_surface_verified": True,
                    "fragment_present": bool(final_surface.get("fragment_present")),
                    "dom_syntax_skeleton_counts": counts,
                    "initial_document_continued_count": initial_document_continued,
                    "official_static_asset_network_sent_count": static_assets_continued,
                    "local_request_count": local_requests_continued,
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
            if process is not None:
                try:
                    process.terminate()
                    process.wait(timeout=2)
                except Exception:
                    try:
                        process.kill()
                    except Exception:
                        pass
