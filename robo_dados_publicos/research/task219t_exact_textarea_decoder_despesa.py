from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

START = "https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418"
HOST = "transparencia.limeira.sp.gov.br"
ROUTE = "/awsgetcontentareas.aspx"
TARGET_NAME = "Despesa"
TARGET_ORIGIN = "2_92_guestuser_207_6_DSL0_VIS1343"
TERMS = [
    "despesa",
    "empenho",
    "credor",
    "fornecedor",
    "pagamento",
    "liquidacao",
    "liquidação",
    "contrato",
    "processo",
    "pregao",
    "pregão",
]


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


def sha(text: object) -> str:
    return hashlib.sha256(str(text).encode("utf-8", errors="replace")).hexdigest()


def short(text: object, limit: int = 240):
    if text is None:
        return None
    s = re.sub(r"\s+", " ", str(text)).strip()
    if len(s) <= limit:
        return s
    return {"length": len(s), "sha256": sha(s)}


def portal_areas(portal: object) -> list[dict]:
    portal = decode_jsonish(portal)
    rows: list[dict] = []
    layers = field(portal, "Layers", []) if isinstance(portal, dict) else []
    if not isinstance(layers, list):
        return rows
    for layer_index, layer in enumerate(layers, 1):
        areas = field(layer, "Areas", []) if isinstance(layer, dict) else []
        if not isinstance(areas, list):
            continue
        for area_index, area in enumerate(areas, 1):
            if not isinstance(area, dict):
                continue
            rows.append(
                {
                    "layer_index": layer_index,
                    "area_index": area_index,
                    "AreaId": str(field(area, "AreaId", "") or ""),
                    "AreaName": str(field(area, "AreaName", "") or ""),
                    "AreaOrigin": str(field(area, "AreaOrigin", "") or ""),
                    "AreaType": str(field(area, "AreaType", "") or ""),
                }
            )
    return rows


def normalized_term_counts(text: str) -> dict[str, int]:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(c for c in normalized if not unicodedata.combining(c)).casefold()
    counts: dict[str, int] = {}
    for term in TERMS:
        token = unicodedata.normalize("NFKD", term)
        token = "".join(c for c in token if not unicodedata.combining(c)).casefold()
        counts[term] = len(
            re.findall(r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])", normalized)
        )
    return counts


def python_action(attrs: dict) -> dict | None:
    onclick = str(attrs.get("onclick") or "")
    href = str(attrs.get("href") or "")
    sources = [onclick]
    if href.lower().startswith("javascript:"):
        sources.append(href[len("javascript:") :])
    for source in sources:
        match = re.search(
            r"doPortalAction\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]*)['\"]\s*\)",
            source,
            re.I,
        )
        if match:
            return {"kind": "doPortalAction", "action": match.group(1), "parm": match.group(2)}
        match = re.search(r"doAreaLink\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", source, re.I)
        if match:
            return {"kind": "doAreaLink", "parm": match.group(1)}
        match = re.search(r"doLink\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", source, re.I)
        if match:
            return {"kind": "doLink", "parm": match.group(1)}
    if href and href not in ("#", "") and not href.lower().startswith("javascript:"):
        parsed = urlparse(urljoin(START, href))
        if (parsed.hostname or "").lower() == HOST and parsed.scheme in ("http", "https"):
            return {
                "kind": "href",
                "href": href,
                "path": parsed.path,
                "query_keys": sorted(parse_qs(parsed.query, keep_blank_values=True).keys()),
            }
    return None


def chrome_options() -> Options:
    options = Options()
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
        options.add_argument(arg)
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return options


def run() -> dict:
    out: dict = {
        "task": "TASK_219T_EXACT_TEXTAREA_DECODER_DESPESA",
        "issue": 729,
        "base_main_sha": "92370c3b27520854a993560ca7a80fba094700b5",
        "execution_head_sha": os.environ.get("GITHUB_SHA"),
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
            "raw_info_persisted": False,
            "raw_transformed_html_persisted": False,
            "raw_page_source_persisted": False,
            "raw_har_persisted": False,
        },
        "status": "RUNNING",
    }

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options())
        driver.set_page_load_timeout(35)
        driver.execute_cdp_cmd("Network.enable", {})
        driver.get(START)
        time.sleep(8)

        raw_state = driver.execute_script(
            """
            try {
              const v=gx.fn.getControlValue('vSDT_TDAPORTAL');
              return {ok:true,json:JSON.stringify(v)};
            } catch(e) { return {ok:false,error:e.name}; }
            """
        )
        portal = None
        if raw_state.get("ok"):
            try:
                portal = decode_jsonish(json.loads(raw_state.get("json", "null")))
            except Exception:
                portal = None
        areas = portal_areas(portal)
        targets = [
            area
            for area in areas
            if area["AreaName"] == TARGET_NAME and area["AreaOrigin"] == TARGET_ORIGIN
        ]
        out["state"] = {
            "portal_read": portal is not None,
            "area_count": len(areas),
            "target_match_count": len(targets),
            "area_names": [area["AreaName"] for area in areas],
        }
        if len(targets) != 1:
            out["status"] = "STOP_DESPESA_STATE_NOT_UNIQUE"
            return out

        target = targets[0]
        current_id = target["AreaId"]
        out["current_despesa"] = {**target, "same_session_selector": True}

        logs = driver.get_log("performance")
        requests: list[dict] = []
        for entry in logs:
            try:
                message = json.loads(entry["message"])["message"]
            except Exception:
                continue
            if message.get("method") != "Network.requestWillBeSent":
                continue
            params = message.get("params") or {}
            request = params.get("request") or {}
            parsed_url = urlparse(request.get("url") or "")
            if (
                (parsed_url.hostname or "").lower() == HOST
                and parsed_url.path == ROUTE
                and (request.get("method") or "").upper() == "POST"
            ):
                requests.append(
                    {
                        "requestId": params.get("requestId"),
                        "postData": request.get("postData") or "",
                    }
                )

        matches: list[dict] = []
        for ordinal, event in enumerate(requests, 1):
            form = parse_qs(event["postData"], keep_blank_values=True)
            values = form.get("LayerInfo", [])
            if len(values) != 1:
                continue
            try:
                parsed = json.loads(values[0])
                request_obj = (
                    parsed[0]
                    if isinstance(parsed, list) and len(parsed) == 1 and isinstance(parsed[0], dict)
                    else None
                )
            except Exception:
                request_obj = None
            if not request_obj or str(request_obj.get("id") or "") != current_id:
                continue

            response_obj = None
            try:
                body = driver.execute_cdp_cmd(
                    "Network.getResponseBody", {"requestId": event["requestId"]}
                )
                raw_body = (
                    base64.b64decode(body.get("body", "").encode("ascii"), validate=False)
                    if body.get("base64Encoded")
                    else body.get("body", "").encode("utf-8")
                )
                parsed = json.loads(raw_body.decode("utf-8"))
                response_obj = (
                    parsed[0]
                    if isinstance(parsed, list) and len(parsed) == 1 and isinstance(parsed[0], dict)
                    else None
                )
            except Exception:
                response_obj = None
            matches.append(
                {
                    "ordinal": ordinal,
                    "request_obj": request_obj,
                    "response_obj": response_obj,
                }
            )

        out["automatic_binding"] = {
            "automatic_request_count": len(requests),
            "same_session_request_match_count": len(matches),
        }
        if len(matches) != 1:
            out["status"] = "STOP_DESPESA_LAYERINFO_NOT_UNIQUE"
            return out

        match = matches[0]
        request_obj = match["request_obj"]
        response_obj = match["response_obj"]
        if not isinstance(response_obj, dict) or str(response_obj.get("id") or "") != current_id:
            out["status"] = "STOP_DESPESA_RESPONSE_ID_MISMATCH"
            return out

        info = response_obj.get("info")
        if not isinstance(info, str):
            out["status"] = "STOP_DESPESA_INFO_NOT_TEXT"
            return out

        decoded = driver.execute_script(
            r"""
            const input=arguments[0];
            const jq=(typeof window.jQuery==='function') ? window.jQuery :
                     ((typeof window.$==='function') ? window.$ : null);
            if(!jq || !jq.fn){
              return {ok:false,error:'JQUERY_NOT_AVAILABLE'};
            }
            let output=null, error=null;
            try {
              output=jq('<textarea />').html(input).text();
            } catch(e) {
              error={name:e.name,message:String(e.message||'').slice(0,160)};
            }
            return {
              ok:typeof output==='string',
              jqueryVersion:String(jq.fn.jquery||''),
              inputType:typeof input,
              outputType:typeof output,
              output,
              error
            };
            """,
            info,
        )
        transformed = decoded.get("output")
        out["decoder"] = {
            "expression": "$(\u0027<textarea />\u0027).html(v.info).text()",
            "jquery_available": bool(decoded.get("ok")),
            "jquery_version": decoded.get("jqueryVersion"),
            "input_length": len(info),
            "input_sha256": sha(info),
            "input_persisted": False,
            "output_type": decoded.get("outputType"),
            "output_length": len(transformed) if isinstance(transformed, str) else None,
            "output_sha256": sha(transformed) if isinstance(transformed, str) else None,
            "output_persisted": False,
            "error": decoded.get("error"),
        }
        if not decoded.get("ok") or not isinstance(transformed, str):
            out["status"] = "STOP_EXACT_TEXTAREA_DECODER_NO_TEXT_OUTPUT"
            return out

        inspection = driver.execute_script(
            r"""
            const s=arguments[0];
            const tpl=document.createElement('template');
            tpl.innerHTML=s;
            const all=[...tpl.content.querySelectorAll('*')];
            const tagCounts={};
            for(const el of all){
              const tag=el.tagName.toLowerCase();
              tagCounts[tag]=(tagCounts[tag]||0)+1;
            }
            const forms=[...tpl.content.querySelectorAll('form')];
            const nodes=[...tpl.content.querySelectorAll('a,button,form,input,select,textarea,[onclick],[href]')].slice(0,500);
            const interesting=[];
            for(let i=0;i<nodes.length;i++){
              const el=nodes[i];
              const attrs={};
              for(const name of ['id','class','name','type','title','aria-label','href','onclick','role','placeholder','method','action','target','value']){
                if(el.hasAttribute(name)){
                  if(name==='value' && (el.getAttribute('type')||'').toLowerCase()==='hidden') continue;
                  attrs[name]=el.getAttribute(name)||'';
                }
              }
              const form=el.closest('form');
              interesting.push({
                index:i+1,
                tag:el.tagName.toLowerCase(),
                formIndex:form ? forms.indexOf(form)+1 : null,
                attrs,
                text:(el.textContent||'').replace(/\s+/g,' ').trim().slice(0,160)
              });
            }
            const scriptMeta=[...tpl.content.querySelectorAll('script')].map((el,idx)=>({
              index:idx+1,
              src:el.getAttribute('src')||'',
              type:el.getAttribute('type')||'',
              inlineLength:(el.textContent||'').length
            }));
            const plainText=(tpl.content.textContent||'').replace(/\s+/g,' ').trim();
            return {
              allTagCount:all.length,
              tagCounts,
              formCount:forms.length,
              interesting,
              scriptMeta,
              plainText,
              hasHtmlLikeTags:/<\s*[a-zA-Z][^>]*>/.test(s),
              percentEncodedHtml:/%(?:3C|3E|22|27)/i.test(s),
              queryLike:/&[^\s]{0,80}=/.test(s)
            };
            """,
            transformed,
        )

        sanitized_nodes: list[dict] = []
        explicit_actions: list[dict] = []
        seen_actions: set[str] = set()
        form_submit_counts: dict[int, int] = {}
        form_actions: list[dict] = []

        for node in inspection.get("interesting") or []:
            attrs = {
                key: short(value, 240)
                for key, value in (node.get("attrs") or {}).items()
            }
            record = {
                "index": node.get("index"),
                "tag": node.get("tag"),
                "form_index": node.get("formIndex"),
                "attrs": attrs,
                "text": short(node.get("text"), 160),
            }
            sanitized_nodes.append(record)

            if node.get("tag") in ("button", "input"):
                node_type = str((node.get("attrs") or {}).get("type") or "").lower()
                if node.get("tag") == "button" or node_type in ("submit", "button", "image"):
                    form_index = node.get("formIndex")
                    if isinstance(form_index, int) and form_index > 0:
                        form_submit_counts[form_index] = form_submit_counts.get(form_index, 0) + 1

            action = python_action(node.get("attrs") or {})
            if action:
                key = json.dumps(action, ensure_ascii=False, sort_keys=True)
                if key not in seen_actions:
                    seen_actions.add(key)
                    explicit_actions.append(
                        {"node_index": node.get("index"), "action": action, "node": record}
                    )

        for node in inspection.get("interesting") or []:
            if node.get("tag") != "form":
                continue
            attrs = node.get("attrs") or {}
            action = str(attrs.get("action") or "")
            if not action:
                continue
            parsed = urlparse(urljoin(START, action))
            if (parsed.hostname or "").lower() != HOST or parsed.scheme not in ("http", "https"):
                continue
            form_index = node.get("formIndex") or node.get("index")
            submit_count = form_submit_counts.get(form_index, 0)
            candidate = {
                "kind": "form",
                "method": str(attrs.get("method") or "GET").upper(),
                "action": action,
                "path": parsed.path,
                "query_keys": sorted(parse_qs(parsed.query, keep_blank_values=True).keys()),
                "form_index": form_index,
                "submit_count": submit_count,
            }
            if submit_count == 1:
                key = json.dumps(candidate, ensure_ascii=False, sort_keys=True)
                if key not in seen_actions:
                    seen_actions.add(key)
                    form_actions.append(candidate)
                    explicit_actions.append(
                        {"node_index": node.get("index"), "action": candidate, "node": sanitize_form_node(node)}
                    )

        plain_text = str(inspection.get("plainText") or "")
        runafter = str(response_obj.get("runafter") or "")
        scripts = []
        for script in inspection.get("scriptMeta") or []:
            src = str(script.get("src") or "")
            src_meta = None
            if src:
                parsed = urlparse(urljoin(START, src))
                if (parsed.hostname or "").lower() == HOST and parsed.scheme in ("http", "https"):
                    src_meta = {"src": short(src, 240), "path": parsed.path}
                else:
                    src_meta = {"src_persisted": False, "src_sha256": sha(src), "src_length": len(src)}
            scripts.append(
                {
                    "index": script.get("index"),
                    "type": short(script.get("type"), 120),
                    "src": src_meta,
                    "inline_length": script.get("inlineLength"),
                    "inline_body_persisted": False,
                }
            )

        out["binding"] = {
            "request_ordinal": match["ordinal"],
            "current_AreaId": current_id,
            "request_LayerInfo_id": str(request_obj.get("id") or ""),
            "response_LayerInfo_id": str(response_obj.get("id") or ""),
            "all_three_equal": current_id
            == str(request_obj.get("id") or "")
            == str(response_obj.get("id") or ""),
        }
        out["transformed_inspection"] = {
            "output_serialization": (
                "HTML_LIKE"
                if inspection.get("hasHtmlLikeTags")
                else "PERCENT_ENCODED_LIKE"
                if inspection.get("percentEncodedHtml")
                else "QUERY_LIKE_DELIMITED"
                if inspection.get("queryLike")
                else "OPAQUE_OR_TEXT"
            ),
            "all_tag_count": inspection.get("allTagCount"),
            "tag_counts": inspection.get("tagCounts") or {},
            "form_count": inspection.get("formCount"),
            "interactive_node_count": len(sanitized_nodes),
            "interactive_nodes": sanitized_nodes,
            "script_count": len(scripts),
            "scripts": scripts,
            "plain_text_length": len(plain_text),
            "plain_text_sha256": sha(plain_text),
            "plain_text_persisted": False,
            "accounting_term_counts": normalized_term_counts(plain_text),
            "explicit_action_count": len(explicit_actions),
            "explicit_actions": explicit_actions,
            "unique_explicit_action": len(explicit_actions) == 1,
            "runafter_present": bool(runafter),
            "runafter_length": len(runafter),
            "runafter_sha256": sha(runafter) if runafter else None,
            "runafter_short_public_value": short(runafter, 240) if runafter else None,
            "runafter_executed_by_task": False,
        }
        out["adjudication"] = {
            "same_session_despesa_response_binding_proven": True,
            "exact_textarea_decoder_applied_in_loaded_public_page": True,
            "transformed_output_html_like": inspection.get("hasHtmlLikeTags") is True,
            "official_action_contract_proven": len(explicit_actions) == 1,
            "official_action_contract": explicit_actions[0]["action"] if len(explicit_actions) == 1 else None,
            "official_action_ambiguous": len(explicit_actions) > 1,
            "official_action_absence_proven": len(explicit_actions) == 0 and inspection.get("hasHtmlLikeTags") is True,
        }
        out["status"] = "PASS_TASK219T_EXACT_TEXTAREA_DECODER_APPLIED"
        return out
    except Exception as exc:
        out["status"] = "STOP_TASK219T_RUNTIME"
        out["error_type"] = type(exc).__name__
        out["error_message"] = short(str(exc), 240)
        return out
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def sanitize_form_node(node: dict) -> dict:
    attrs = {
        key: short(value, 240)
        for key, value in (node.get("attrs") or {}).items()
        if key in ("id", "class", "name", "type", "title", "aria-label", "role", "method", "action", "target")
    }
    return {
        "index": node.get("index"),
        "tag": node.get("tag"),
        "form_index": node.get("formIndex"),
        "attrs": attrs,
        "text": short(node.get("text"), 160),
    }


def main() -> None:
    result = run()
    output = Path(os.environ.get("TASK219T_OUTPUT", "runtime/task219t_result.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary = {
        "status": result.get("status"),
        "current_despesa": result.get("current_despesa"),
        "automatic_binding": result.get("automatic_binding"),
        "binding": result.get("binding"),
        "decoder": result.get("decoder"),
        "transformed_inspection": {
            key: value
            for key, value in (result.get("transformed_inspection") or {}).items()
            if key not in ("interactive_nodes", "scripts")
        },
        "adjudication": result.get("adjudication"),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
