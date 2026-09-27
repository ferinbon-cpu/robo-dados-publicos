from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

START = "https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418"
TARGET_NAME = "Despesa"
TARGET_ORIGIN = "2_92_guestuser_207_6_DSL0_VIS1343"
MAX_SNIPPET = 240
KEYWORDS = (
    "doPortalAction", "doAreaLink", "doLink", "PortalAction", "Despesa", "Empenho",
    "click", "chart", "highchart", "plotOptions", "point", "series", ".aspx", "aws", "tdaportal"
)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def ckey(key: object) -> str:
    s = str(key)
    if s.casefold().startswith("gxtpr_"):
        s = s[6:]
    return re.sub(r"[^a-z0-9]", "", s.casefold())


def field(obj: object, name: str, default=None):
    if not isinstance(obj, dict):
        return default
    wanted = ckey(name)
    for key, value in obj.items():
        if ckey(key) == wanted:
            return value
    return default


def decode_jsonish(value: object, depth: int = 0):
    if depth > 3:
        return value
    if isinstance(value, str):
        s = value.strip()
        if s and s[0] in '[{"':
            try:
                return decode_jsonish(json.loads(s), depth + 1)
            except Exception:
                return value
    return value


def portal_areas(portal: object) -> list[dict]:
    portal = decode_jsonish(portal)
    rows = []
    layers = field(portal, "Layers", []) if isinstance(portal, dict) else []
    if not isinstance(layers, list):
        return rows
    for li, layer in enumerate(layers, 1):
        areas = field(layer, "Areas", []) if isinstance(layer, dict) else []
        if not isinstance(areas, list):
            continue
        for ai, area in enumerate(areas, 1):
            if not isinstance(area, dict):
                continue
            rows.append({
                "layer_index": li,
                "area_index": ai,
                "AreaId": str(field(area, "AreaId", "") or ""),
                "AreaName": str(field(area, "AreaName", "") or ""),
                "AreaOrigin": str(field(area, "AreaOrigin", "") or ""),
                "AreaType": str(field(area, "AreaType", "") or ""),
            })
    return rows


def chrome_options() -> Options:
    o = Options()
    for arg in (
        "--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking",
        "--disable-default-apps", "--disable-sync", "--disable-component-update", "--disable-domain-reliability",
        "--metrics-recording-only", "--safebrowsing-disable-auto-update", "--window-size=1365,900"
    ):
        o.add_argument(arg)
    return o


def bounded_snippets(source: str) -> list[dict]:
    out = []
    seen = set()
    for kw in KEYWORDS:
        for m in re.finditer(re.escape(kw), source, re.I):
            start = max(0, m.start() - 90)
            end = min(len(source), m.end() + 130)
            snippet = re.sub(r"\s+", " ", source[start:end]).strip()
            if len(snippet) > MAX_SNIPPET:
                snippet = snippet[:MAX_SNIPPET]
            key = sha(snippet)
            if key in seen:
                continue
            seen.add(key)
            out.append({"keyword": kw, "snippet": snippet, "sha256": key})
            if len(out) >= 40:
                return out
    return out


def call_contracts(source: str) -> list[dict]:
    found = []
    patterns = [
        ("doPortalAction", r"doPortalAction\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]*)['\"]\s*\)"),
        ("doAreaLink", r"doAreaLink\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"),
        ("doLink", r"doLink\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"),
    ]
    for kind, pat in patterns:
        for m in re.finditer(pat, source, re.I):
            vals = [g for g in m.groups()]
            found.append({"kind": kind, "args": vals})
    for m in re.finditer(r"['\"]([^'\"\n]{1,160}\.aspx(?:\?[^'\"\n]{0,160})?)['\"]", source, re.I):
        found.append({"kind": "route_literal", "value": m.group(1)})
    return found[:40]


def listener_sources(driver, expression: str, label: str) -> list[dict]:
    result = []
    try:
        ev = driver.execute_cdp_cmd("Runtime.evaluate", {
            "expression": expression, "objectGroup": "task219v", "returnByValue": False
        })
        oid = ((ev.get("result") or {}).get("objectId"))
        if not oid:
            return result
        listeners = driver.execute_cdp_cmd("DOMDebugger.getEventListeners", {"objectId": oid, "depth": 1}).get("listeners") or []
        for idx, item in enumerate([x for x in listeners if x.get("type") == "click"][:20], 1):
            handler = item.get("handler") or {}
            source = ""
            handler_oid = handler.get("objectId")
            if handler_oid:
                try:
                    call = driver.execute_cdp_cmd("Runtime.callFunctionOn", {
                        "objectId": handler_oid,
                        "functionDeclaration": "function(){ return Function.prototype.toString.call(this); }",
                        "returnByValue": True,
                        "silent": True,
                    })
                    source = str((((call.get("result") or {}).get("value"))) or "")
                except Exception:
                    source = ""
            if not source and item.get("scriptId"):
                try:
                    script = driver.execute_cdp_cmd("Debugger.getScriptSource", {"scriptId": str(item.get("scriptId"))})
                    full = str(script.get("scriptSource") or "")
                    lines = full.splitlines()
                    line = int(item.get("lineNumber") or 0)
                    source = "\n".join(lines[max(0, line-4): min(len(lines), line+8)])
                except Exception:
                    source = ""
            result.append({
                "target": label,
                "ordinal": idx,
                "scriptId": str(item.get("scriptId") or ""),
                "lineNumber": item.get("lineNumber"),
                "columnNumber": item.get("columnNumber"),
                "source_length": len(source),
                "source_sha256": sha(source) if source else None,
                "snippets": bounded_snippets(source),
                "contracts": call_contracts(source),
            })
    except Exception as exc:
        result.append({"target": label, "read_error": exc.__class__.__name__})
    return result


def run() -> dict:
    out = {
        "task": "TASK_219V_DESPESA_SCRIPT_SEMANTICS",
        "issue": 734,
        "parent_issue": 691,
        "base_main_sha": "7a625973cac03d820f6a729e4da7e09c129c7350",
        "execution_head_sha": os.environ.get("GITHUB_SHA"),
        "authorization_sequence": "LEAP_1_OF_3",
        "boundary": {
            "browser_sessions": 1, "manual_navigations": 1, "clicks": 0, "typing": 0,
            "form_submissions": 0, "manual_fetch_xhr": 0, "direct_endpoint_calls": 0,
            "portal_action_triggers": 0, "layerinfo_replay": 0, "retries": 0,
            "empenho_lookup": 0, "full_script_bodies_persisted": False,
            "raw_page_source_persisted": False, "raw_har_persisted": False,
        },
        "status": "RUNNING",
    }
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options())
        driver.set_page_load_timeout(35)
        driver.execute_cdp_cmd("Debugger.enable", {})
        driver.get(START)
        time.sleep(10)

        raw = driver.execute_script("""
        try { const v=gx.fn.getControlValue('vSDT_TDAPORTAL'); return {ok:true,json:JSON.stringify(v)}; }
        catch(e){ return {ok:false,error:e.name}; }
        """)
        portal = decode_jsonish(json.loads(raw.get("json", "null"))) if raw and raw.get("ok") else None
        areas = portal_areas(portal)
        targets = [a for a in areas if a["AreaName"] == TARGET_NAME and a["AreaOrigin"] == TARGET_ORIGIN]
        out["state"] = {"portal_read": portal is not None, "area_count": len(areas), "target_match_count": len(targets)}
        if len(targets) != 1:
            out["status"] = "STOP_DESPESA_STATE_NOT_UNIQUE"
            return out
        target = targets[0]
        area_id = target["AreaId"]
        out["current_despesa"] = target

        script_rows = driver.execute_script("""
        const root=document.getElementById(arguments[0]);
        if(!root) return null;
        return [...root.querySelectorAll('script')].map((s,i)=>({ordinal:i+1,text:s.textContent||'',src:s.getAttribute('src')||''}));
        """, area_id)
        if script_rows is None:
            out["status"] = "STOP_LIVE_ROOT_NOT_FOUND"
            return out

        scripts = []
        contracts = []
        for row in script_rows:
            text = str(row.get("text") or "")
            c = call_contracts(text)
            scripts.append({
                "ordinal": row.get("ordinal"), "src": row.get("src") or None,
                "length": len(text), "sha256": sha(text), "snippets": bounded_snippets(text), "contracts": c,
            })
            for item in c:
                contracts.append({"source": f"inline_script_{row.get('ordinal')}", **item})

        listeners = []
        for expr, label in ((f"document.getElementById({json.dumps(area_id)})", "root"), ("document", "document"), ("window", "window")):
            rows = listener_sources(driver, expr, label)
            listeners.extend(rows)
            for row in rows:
                for item in row.get("contracts") or []:
                    contracts.append({"source": f"{label}_click_listener_{row.get('ordinal')}", **item})

        unique = []
        seen = set()
        for item in contracts:
            key = json.dumps({k:v for k,v in item.items() if k != "source"}, sort_keys=True, ensure_ascii=False)
            if key not in seen:
                seen.add(key)
                unique.append(item)

        out["inline_scripts"] = scripts
        out["click_listeners"] = listeners
        out["contract_candidates"] = {"occurrences": len(contracts), "unique_count": len(unique), "unique": unique[:40]}
        out["adjudication"] = {
            "unique_explicit_action_contract_proven": len(unique) == 1,
            "ambiguous_multiple_contracts": len(unique) > 1,
            "no_explicit_contract_found": len(unique) == 0,
            "action_executed": False,
        }
        out["status"] = "PASS_TASK219V_SCRIPT_SEMANTICS_INSPECTED"
        return out
    finally:
        if driver:
            driver.quit()


def main() -> int:
    result = run()
    path = Path(os.environ.get("TASK219V_OUTPUT", "runtime/task219v_result.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status", "").startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
