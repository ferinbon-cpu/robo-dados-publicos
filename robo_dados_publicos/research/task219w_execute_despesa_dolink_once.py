from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

START = "https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418"
HOST = "transparencia.limeira.sp.gov.br"
TARGET_NAME = "Despesa"
TARGET_ORIGIN = "2_92_guestuser_207_6_DSL0_VIS1343"
SUFFIX = "**##**V1343[vl]"
TERMS = ["empenho", "credor", "fornecedor", "contrato", "processo", "pagamento", "liquidacao", "liquidação", "exercicio", "exercício", "valor", "numero", "número"]


def ckey(key: object) -> str:
    s = str(key)
    if s.casefold().startswith("gxtpr_"):
        s = s[6:]
    return re.sub(r"[^a-z0-9]", "", s.casefold())


def field(obj: object, name: str, default=None):
    if not isinstance(obj, dict):
        return default
    wanted = ckey(name)
    for k, v in obj.items():
        if ckey(k) == wanted:
            return v
    return default


def decode_jsonish(v: object, depth: int = 0):
    if depth > 3:
        return v
    if isinstance(v, str):
        s = v.strip()
        if s and s[0] in '[{"':
            try:
                return decode_jsonish(json.loads(s), depth + 1)
            except Exception:
                return v
    return v


def portal_areas(portal: object) -> list[dict]:
    portal = decode_jsonish(portal)
    out = []
    layers = field(portal, "Layers", []) if isinstance(portal, dict) else []
    if not isinstance(layers, list):
        return out
    for li, layer in enumerate(layers, 1):
        areas = field(layer, "Areas", []) if isinstance(layer, dict) else []
        if not isinstance(areas, list):
            continue
        for ai, area in enumerate(areas, 1):
            if isinstance(area, dict):
                out.append({
                    "layer_index": li,
                    "area_index": ai,
                    "AreaId": str(field(area, "AreaId", "") or ""),
                    "AreaName": str(field(area, "AreaName", "") or ""),
                    "AreaOrigin": str(field(area, "AreaOrigin", "") or ""),
                    "AreaType": str(field(area, "AreaType", "") or ""),
                })
    return out


def chrome_options() -> Options:
    o = Options()
    for arg in (
        "--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-background-networking",
        "--disable-default-apps", "--disable-sync", "--disable-component-update", "--disable-domain-reliability",
        "--metrics-recording-only", "--safebrowsing-disable-auto-update", "--window-size=1365,1000"
    ):
        o.add_argument(arg)
    o.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return o


def read_portal(driver):
    raw = driver.execute_script("""
    try { const v=gx.fn.getControlValue('vSDT_TDAPORTAL'); return {ok:true,json:JSON.stringify(v)}; }
    catch(e){ return {ok:false,error:e.name}; }
    """)
    if not raw or not raw.get("ok"):
        return None
    try:
        return decode_jsonish(json.loads(raw.get("json", "null")))
    except Exception:
        return None


def short(s: object, limit: int = 160):
    if s is None:
        return None
    text = re.sub(r"\s+", " ", str(s)).strip()
    return text[:limit]


def public_interface(driver) -> dict:
    return driver.execute_script(r"""
    const safe=(s,n=160)=>String(s||'').replace(/\s+/g,' ').trim().slice(0,n);
    const nodes=[...document.querySelectorAll('form,input,select,textarea,button,a[href],[onclick],[role="button"]')].slice(0,800);
    const rows=[];
    for(let i=0;i<nodes.length;i++){
      const el=nodes[i]; const tag=el.tagName.toLowerCase(); const type=(el.getAttribute('type')||'').toLowerCase();
      const attrs={};
      for(const name of ['id','name','type','title','aria-label','placeholder','href','onclick','role','method','action','target']){
        if(el.hasAttribute(name)) attrs[name]=safe(el.getAttribute(name),220);
      }
      if(tag==='select'){
        attrs.option_labels=[...el.options].slice(0,50).map(o=>safe(o.textContent,100));
      }
      const labels=[];
      if(el.id){ for(const lab of document.querySelectorAll('label[for="'+CSS.escape(el.id)+'"]')) labels.push(safe(lab.textContent)); }
      const parentLabel=el.closest('label'); if(parentLabel) labels.push(safe(parentLabel.textContent));
      rows.push({index:i+1,tag,type,attrs,labels:[...new Set(labels)].slice(0,5),text:(type==='hidden'?null:safe(el.textContent||el.value||'',160))});
    }
    const bodyText=safe(document.body ? document.body.innerText : '',12000);
    return {title:safe(document.title,200), nodes:rows, bodyText};
    """)


def sanitize_network(logs: list[dict]) -> list[dict]:
    rows = []
    for entry in logs:
        try:
            msg = json.loads(entry["message"])["message"]
        except Exception:
            continue
        if msg.get("method") != "Network.requestWillBeSent":
            continue
        req = (msg.get("params") or {}).get("request") or {}
        u = urlparse(req.get("url") or "")
        if (u.hostname or "").lower() != HOST:
            continue
        method = str(req.get("method") or "").upper()
        row = {"method": method, "path": u.path, "query_keys": sorted(parse_qs(u.query, keep_blank_values=True).keys())}
        if method == "POST":
            post = req.get("postData") or ""
            try:
                row["post_keys"] = sorted(parse_qs(post, keep_blank_values=True).keys())
            except Exception:
                row["post_keys"] = []
        rows.append(row)
    # stable de-dup
    out=[]; seen=set()
    for r in rows:
        key=json.dumps(r,sort_keys=True,ensure_ascii=False)
        if key not in seen:
            seen.add(key); out.append(r)
    return out[:100]


def run() -> dict:
    out = {
        "task": "TASK_219W_EXECUTE_DESPESA_DOLINK_ONCE",
        "issue": 736,
        "parent_issue": 691,
        "base_main_sha": "83d1389249368ed3f65c7be029e0d0d78e881e26",
        "execution_head_sha": os.environ.get("GITHUB_SHA"),
        "authorization_sequence": "LEAP_2_OF_3",
        "boundary": {"browser_sessions":1,"manual_navigations":1,"proven_doLink_invocations":0,"element_clicks":0,"typing":0,"form_submissions":0,"manual_fetch_xhr":0,"direct_endpoint_calls":0,"retries":0,"empenho_lookup":0,"raw_har_persisted":False,"raw_page_source_persisted":False,"full_html_persisted":False,"hidden_values_persisted":False},
        "status": "RUNNING",
    }
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options())
        driver.set_page_load_timeout(35)
        driver.execute_cdp_cmd("Network.enable", {})
        driver.get(START)
        time.sleep(10)
        portal = read_portal(driver)
        areas = portal_areas(portal)
        targets = [a for a in areas if a["AreaName"] == TARGET_NAME and a["AreaOrigin"] == TARGET_ORIGIN]
        out["pre_action_state"] = {"portal_read": portal is not None, "area_count": len(areas), "area_names": [a["AreaName"] for a in areas], "target_match_count": len(targets)}
        if len(targets) != 1:
            out["status"] = "STOP_DESPESA_STATE_NOT_UNIQUE"; return out
        target = targets[0]
        area_id = target["AreaId"]
        expected = area_id + SUFFIX
        out["current_despesa"] = target

        validation = driver.execute_script(r"""
        const id=arguments[0], suffix=arguments[1]; const root=document.getElementById(id);
        if(!root) return {ok:false,reason:'ROOT_MISSING'};
        const scripts=[...root.querySelectorAll('script')].map(s=>s.textContent||'');
        const expected=id+suffix;
        const matches=scripts.map((s,i)=>({ordinal:i+1,hasDoLink:s.includes("doLink('"+expected+"')"),hasClick:/\.on\s*\(\s*['\"]click['\"]/.test(s)}));
        return {ok:scripts.length===4 && matches.every(x=>x.hasDoLink&&x.hasClick),script_count:scripts.length,matches,doLink_type:typeof window.doLink};
        """, area_id, SUFFIX)
        out["contract_revalidation"] = validation
        if not validation.get("ok") or validation.get("doLink_type") != "function":
            out["status"] = "STOP_CANONICAL_DOLINK_CONTRACT_NOT_REVALIDATED"; return out

        # Clear all pre-action performance events, then execute the proven loaded public action exactly once.
        driver.get_log("performance")
        before_url = driver.current_url
        result = driver.execute_script("return window.doLink(arguments[0]);", expected)
        out["boundary"]["proven_doLink_invocations"] = 1
        out["action_execution"] = {"kind":"doLink","parameter_suffix":SUFFIX,"fresh_AreaId_used":True,"return_type":type(result).__name__}
        time.sleep(10)
        after_url = driver.current_url
        logs = driver.get_log("performance")

        iface = public_interface(driver)
        portal_after = read_portal(driver)
        areas_after = portal_areas(portal_after)
        body = str(iface.pop("bodyText", "") or "")
        counts = {term: len(re.findall(re.escape(term), body, flags=re.I)) for term in TERMS}
        out["post_action"] = {
            "url_changed": before_url != after_url,
            "url_path_before": urlparse(before_url).path,
            "url_path_after": urlparse(after_url).path,
            "title": iface.get("title"),
            "portal_read": portal_after is not None,
            "area_count": len(areas_after),
            "area_names": [a["AreaName"] for a in areas_after],
            "interactive_nodes": iface.get("nodes") or [],
            "term_counts": counts,
            "public_text_excerpt": short(body, 1200),
        }
        out["automatic_network"] = sanitize_network(logs)
        # Conservative signal only: exact query contract is not promoted here without explicit field/action evidence.
        nodes = iface.get("nodes") or []
        empenho_nodes=[]
        for n in nodes:
            hay = json.dumps(n, ensure_ascii=False).casefold()
            if "empenho" in hay:
                empenho_nodes.append(n)
        out["empenho_interface_candidates"] = empenho_nodes[:50]
        out["adjudication"] = {
            "proven_dolink_executed_exactly_once": True,
            "detailed_interface_observed": bool(nodes) or len(areas_after) != len(areas),
            "explicit_empenho_candidate_count": len(empenho_nodes),
            "empenho_lookup_executed": False,
        }
        out["status"] = "PASS_TASK219W_PROVEN_DOLINK_EXECUTED_ONCE"
        return out
    finally:
        if driver:
            driver.quit()


def main() -> int:
    result = run()
    path = Path(os.environ.get("TASK219W_OUTPUT", "runtime/task219w_result.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status", "").startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
