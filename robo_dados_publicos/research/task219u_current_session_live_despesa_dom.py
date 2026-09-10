from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

START = "https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418"
HOST = "transparencia.limeira.sp.gov.br"
TARGET_NAME = "Despesa"
TARGET_ORIGIN = "2_92_guestuser_207_6_DSL0_VIS1343"


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
    rows: list[dict] = []
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
            rows.append(
                {
                    "layer_index": li,
                    "area_index": ai,
                    "AreaId": str(field(area, "AreaId", "") or ""),
                    "AreaName": str(field(area, "AreaName", "") or ""),
                    "AreaOrigin": str(field(area, "AreaOrigin", "") or ""),
                    "AreaType": str(field(area, "AreaType", "") or ""),
                }
            )
    return rows


def sha(text: object) -> str:
    return hashlib.sha256(str(text).encode("utf-8", errors="replace")).hexdigest()


def safe_scalar(value: object, limit: int = 240):
    if value is None:
        return None
    s = re.sub(r"\s+", " ", str(value)).strip()
    if len(s) <= limit:
        return s
    return {"length": len(s), "sha256": sha(s)}


def safe_href(value: str) -> dict | None:
    if not value or value == "#" or value.lower().startswith("javascript:"):
        return None
    parsed = urlparse(urljoin(START, value))
    if parsed.scheme not in ("http", "https") or (parsed.hostname or "").lower() != HOST:
        return None
    return {
        "raw": safe_scalar(value),
        "path": parsed.path,
        "query_keys": sorted(parse_qs(parsed.query, keep_blank_values=True).keys()),
    }


def explicit_action(node: dict) -> dict | None:
    attrs = node.get("attrs") or {}
    onclick = str(attrs.get("onclick") or "")
    href = str(attrs.get("href") or "")
    sources = [onclick]
    if href.lower().startswith("javascript:"):
        sources.append(href[len("javascript:") :])
    for source in sources:
        m = re.search(
            r"doPortalAction\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]*)['\"]\s*\)",
            source,
            re.I,
        )
        if m:
            return {"kind": "doPortalAction", "action": m.group(1), "parm": m.group(2)}
        m = re.search(r"doAreaLink\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", source, re.I)
        if m:
            return {"kind": "doAreaLink", "parm": m.group(1)}
        m = re.search(r"doLink\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", source, re.I)
        if m:
            return {"kind": "doLink", "parm": m.group(1)}
    href_info = safe_href(href)
    if href_info:
        return {"kind": "href", **href_info}
    return None


def chrome_options() -> Options:
    o = Options()
    for arg in (
        "--headless=new",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-background-networking",
        "--disable-default-apps",
        "--disable-sync",
        "--disable-component-update",
        "--disable-domain-reliability",
        "--metrics-recording-only",
        "--safebrowsing-disable-auto-update",
        "--disable-features=OptimizationHints,MediaRouter",
        "--window-size=1365,900",
    ):
        o.add_argument(arg)
    return o


def read_listeners(driver, expression: str) -> list[dict]:
    try:
        evaluated = driver.execute_cdp_cmd(
            "Runtime.evaluate",
            {"expression": expression, "objectGroup": "task219u", "returnByValue": False},
        )
        oid = ((evaluated.get("result") or {}).get("objectId"))
        if not oid:
            return []
        raw = driver.execute_cdp_cmd("DOMDebugger.getEventListeners", {"objectId": oid, "depth": 1})
        out = []
        for item in (raw.get("listeners") or [])[:100]:
            out.append(
                {
                    "type": item.get("type"),
                    "useCapture": bool(item.get("useCapture")),
                    "passive": bool(item.get("passive")),
                    "once": bool(item.get("once")),
                    "scriptId": str(item.get("scriptId") or ""),
                    "lineNumber": item.get("lineNumber"),
                    "columnNumber": item.get("columnNumber"),
                }
            )
        return out
    except Exception as exc:
        return [{"read_error": exc.__class__.__name__}]


def run() -> dict:
    out: dict = {
        "task": "TASK_219U_CURRENT_SESSION_LIVE_DESPESA_DOM",
        "issue": 732,
        "parent_issue": 691,
        "base_main_sha": "30db2414069565f8572aad1b32dd96d9cad5cd09",
        "execution_head_sha": os.environ.get("GITHUB_SHA"),
        "status": "RUNNING",
        "boundary": {
            "browser_sessions": 1,
            "manual_navigations": 1,
            "clicks": 0,
            "typing": 0,
            "form_submissions": 0,
            "manual_fetch_xhr": 0,
            "direct_endpoint_calls": 0,
            "portal_action_triggers": 0,
            "layerinfo_replay": 0,
            "layerinfo_synthesis": 0,
            "retries": 0,
            "commitment_lookup": 0,
            "raw_page_source_persisted": False,
            "raw_inner_html_persisted": False,
            "raw_har_persisted": False,
            "inline_script_bodies_persisted": False,
        },
    }
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options())
        driver.set_page_load_timeout(35)
        driver.get(START)
        time.sleep(10)

        raw_state = driver.execute_script(
            """
            try {
              const v=gx.fn.getControlValue('vSDT_TDAPORTAL');
              return {ok:true,json:JSON.stringify(v)};
            } catch(e) { return {ok:false,error:e.name}; }
            """
        )
        portal = None
        if raw_state and raw_state.get("ok"):
            try:
                portal = decode_jsonish(json.loads(raw_state.get("json", "null")))
            except Exception:
                portal = None
        areas = portal_areas(portal)
        targets = [a for a in areas if a["AreaName"] == TARGET_NAME and a["AreaOrigin"] == TARGET_ORIGIN]
        out["state"] = {
            "portal_read": portal is not None,
            "area_count": len(areas),
            "target_match_count": len(targets),
            "area_names": [a["AreaName"] for a in areas],
        }
        if len(targets) != 1:
            out["status"] = "STOP_DESPESA_STATE_NOT_UNIQUE"
            return out

        target = targets[0]
        current_id = target["AreaId"]
        out["current_despesa"] = {**target, "same_session_selector": True}

        snap = driver.execute_script(
            r"""
            const id=arguments[0], host=arguments[1];
            const root=document.getElementById(id);
            if(!root) return {exists:false};
            const all=[root, ...root.querySelectorAll('*')];
            const counts={};
            for(const el of all){const t=el.tagName.toLowerCase(); counts[t]=(counts[t]||0)+1;}
            const picked=[root, ...root.querySelectorAll('a,button,form,input,select,textarea,iframe,[href],[onclick],[role],[data-action],[data-link],[data-url]')];
            const nodes=[];
            for(const el of picked.slice(0,800)){
              const attrs={};
              const names=['id','class','name','type','title','aria-label','href','onclick','role','placeholder','method','action','target','src','data-action','data-link','data-url'];
              for(const n of names){if(el.hasAttribute(n)) attrs[n]=el.getAttribute(n)||'';}
              const data={};
              for(const a of [...el.attributes]){if(a.name.startsWith('data-')) data[a.name]=a.value||'';}
              const f=el.closest('form');
              nodes.push({
                tag:el.tagName.toLowerCase(), attrs, data,
                text:(el.innerText||el.textContent||'').replace(/\s+/g,' ').trim().slice(0,160),
                formId:f ? (f.id||null) : null
              });
            }
            const forms=[...root.querySelectorAll('form')].map(f=>({
              id:f.id||'', method:(f.getAttribute('method')||'').toLowerCase(), action:f.getAttribute('action')||'',
              controls:[...f.querySelectorAll('input,select,textarea,button')].slice(0,200).map(c=>({
                tag:c.tagName.toLowerCase(), id:c.id||'', name:c.getAttribute('name')||'', type:(c.getAttribute('type')||'').toLowerCase(),
                title:c.getAttribute('title')||'', ariaLabel:c.getAttribute('aria-label')||'', placeholder:c.getAttribute('placeholder')||'',
                text:(c.innerText||c.textContent||'').replace(/\s+/g,' ').trim().slice(0,160)
              }))
            }));
            const scripts=[...root.querySelectorAll('script')].map(s=>({src:s.getAttribute('src')||'',type:s.getAttribute('type')||'',inlineLength:(s.textContent||'').length}));
            return {exists:true, rootTag:root.tagName.toLowerCase(), tagCounts:counts, nodes, forms, scripts,
                    rootText:(root.innerText||root.textContent||'').replace(/\s+/g,' ').trim().slice(0,160)};
            """,
            current_id,
            HOST,
        )
        if not snap or not snap.get("exists"):
            out["live_dom"] = {"root_exists": False}
            out["status"] = "STOP_CURRENT_SESSION_LIVE_ROOT_NOT_FOUND"
            return out

        safe_nodes = []
        actions = []
        for idx, node in enumerate(snap.get("nodes") or [], 1):
            attrs = {k: safe_scalar(v) for k, v in (node.get("attrs") or {}).items()}
            data = {k: safe_scalar(v) for k, v in (node.get("data") or {}).items()}
            safe_node = {
                "index": idx,
                "tag": node.get("tag"),
                "attrs": attrs,
                "data": data,
                "text": safe_scalar(node.get("text"), 160),
                "formId": safe_scalar(node.get("formId"), 160),
            }
            action = explicit_action({"attrs": node.get("attrs") or {}})
            if action:
                action = {**action, "node_index": idx, "tag": node.get("tag")}
                actions.append(action)
                safe_node["explicit_action"] = action
            safe_nodes.append(safe_node)

        safe_forms = []
        form_actions = []
        for fi, form in enumerate(snap.get("forms") or [], 1):
            raw_action = str(form.get("action") or "")
            controls = form.get("controls") or []
            submits = [c for c in controls if c.get("tag") == "button" or c.get("type") in ("submit", "image")]
            f = {
                "index": fi,
                "id": safe_scalar(form.get("id"), 160),
                "method": safe_scalar(form.get("method"), 32),
                "action": safe_scalar(raw_action),
                "controls": [{k: safe_scalar(v, 160) for k, v in c.items()} for c in controls],
                "submit_control_count": len(submits),
            }
            href_info = safe_href(raw_action) if raw_action else None
            if href_info and len(submits) == 1:
                fa = {"kind": "form", "form_index": fi, "method": form.get("method") or "get", **href_info}
                form_actions.append(fa)
                f["explicit_action"] = fa
            safe_forms.append(f)

        unique_actions = []
        seen = set()
        for a in actions + form_actions:
            key = json.dumps({k: v for k, v in a.items() if k not in ("node_index", "tag", "form_index")}, sort_keys=True, ensure_ascii=False)
            if key not in seen:
                seen.add(key)
                unique_actions.append(a)

        scripts = []
        for item in snap.get("scripts") or []:
            src = str(item.get("src") or "")
            src_info = safe_href(src) if src else None
            scripts.append({"src": src_info, "type": safe_scalar(item.get("type"), 80), "inlineLength": item.get("inlineLength")})

        out["live_dom"] = {
            "root_exists": True,
            "root_tag": snap.get("rootTag"),
            "root_text": safe_scalar(snap.get("rootText"), 160),
            "tag_counts": snap.get("tagCounts") or {},
            "inspected_node_count": len(safe_nodes),
            "nodes": safe_nodes,
            "forms": safe_forms,
            "scripts": scripts,
        }
        escaped_id = json.dumps(current_id)
        out["event_listener_metadata"] = {
            "root": read_listeners(driver, f"document.getElementById({escaped_id})"),
            "document": read_listeners(driver, "document"),
            "window": read_listeners(driver, "window"),
            "listeners_executed": False,
            "listener_presence_can_promote_action": False,
        }
        out["action_adjudication"] = {
            "explicit_action_occurrences": len(actions) + len(form_actions),
            "unique_explicit_action_count": len(unique_actions),
            "unique_explicit_actions": unique_actions,
            "official_action_contract_proven": len(unique_actions) == 1,
            "official_action_ambiguous": len(unique_actions) > 1,
            "official_action_absence_proven": len(unique_actions) == 0,
            "action_executed": False,
        }
        out["status"] = "PASS_TASK219U_LIVE_DOM_INSPECTED"
        return out
    except Exception as exc:
        out["status"] = "ERROR_FAIL_CLOSED"
        out["error"] = {"type": exc.__class__.__name__, "message": safe_scalar(str(exc), 180)}
        return out
    finally:
        if driver is not None:
            try:
                driver.execute_cdp_cmd("Runtime.releaseObjectGroup", {"objectGroup": "task219u"})
            except Exception:
                pass
            driver.quit()


def main() -> int:
    result = run()
    path = Path(os.environ.get("TASK219U_OUTPUT", "runtime/task219u_result.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status", "").startswith(("PASS_", "STOP_")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
