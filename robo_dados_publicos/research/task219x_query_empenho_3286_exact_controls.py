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
TOP_NAME = "Despesa"
TOP_ORIGIN = "2_92_guestuser_207_6_DSL0_VIS1343"
TOP_SUFFIX = "**##**V1343[vl]"
TARGET_AREA_NAME = "Empenhado"
TARGET_YEAR = "2026"
TARGET_EMPENHO = "3286"
STRONG_CONTRACT = "45/2026"
STRONG_PROCESS = "902.281/2025"
CORROBORATION = ("10/2026", "Med Doctor", "37457979000131", "endoscopia")
MAX_ROW_CHARS = 1600
MAX_SNIPPET_CHARS = 320


def sha256_text(text: str) -> str:
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
    out: list[dict] = []
    layers = field(portal, "Layers", []) if isinstance(portal, dict) else []
    if not isinstance(layers, list):
        return out
    for li, layer in enumerate(layers, 1):
        areas = field(layer, "Areas", []) if isinstance(layer, dict) else []
        if not isinstance(areas, list):
            continue
        for ai, area in enumerate(areas, 1):
            if not isinstance(area, dict):
                continue
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
        "--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
        "--disable-background-networking", "--disable-default-apps", "--disable-sync",
        "--disable-component-update", "--disable-domain-reliability", "--metrics-recording-only",
        "--safebrowsing-disable-auto-update", "--window-size=1500,1100",
    ):
        o.add_argument(arg)
    return o


def read_portal(driver):
    raw = driver.execute_script("""
    try {
      const v=gx.fn.getControlValue('vSDT_TDAPORTAL');
      return {ok:true,json:JSON.stringify(v)};
    } catch(e) { return {ok:false,error:e.name}; }
    """)
    if not raw or not raw.get("ok"):
        return None
    try:
        return decode_jsonish(json.loads(raw.get("json", "null")))
    except Exception:
        return None


def normalize_visible(text: object, limit: int) -> str:
    s = re.sub(r"\s+", " ", str(text or "")).strip()
    return s[:limit]


def bounded_matches(text: str) -> dict:
    literals = [TARGET_EMPENHO, f"{TARGET_EMPENHO}/2026", f"{TARGET_EMPENHO}-2026", STRONG_CONTRACT, STRONG_PROCESS, *CORROBORATION]
    hits = {}
    folded = text.casefold()
    for lit in literals:
        pos = folded.find(lit.casefold())
        if pos < 0:
            continue
        a = max(0, pos - 120)
        b = min(len(text), pos + len(lit) + 180)
        snippet = normalize_visible(text[a:b], MAX_SNIPPET_CHARS)
        hits[lit] = {"count": folded.count(lit.casefold()), "snippet": snippet, "snippet_sha256": sha256_text(snippet)}
    return hits


def run() -> dict:
    result = {
        "task": "TASK_219X_QUERY_EMPENHO_3286_EXACT_CONTROLS",
        "issue": 738,
        "parent_issue": 691,
        "base_main_sha": "72c03422ad43f9ced6162d0fe68188f4d22bba64",
        "execution_head_sha": os.environ.get("GITHUB_SHA"),
        "authorization_sequence": "LEAP_1_OF_3_CURRENT_AUTHORIZATION",
        "boundary": {
            "browser_sessions": 1,
            "initial_navigations": 0,
            "top_level_doLink_invocations": 0,
            "controlled_query_field_assignments": 0,
            "same_area_filter_invocations": 0,
            "same_record_detail_drilldowns": 0,
            "manual_fetch_xhr": 0,
            "direct_endpoint_calls": 0,
            "layerinfo_replay": 0,
            "retries": 0,
            "raw_page_source_persisted": False,
            "raw_har_persisted": False,
            "full_html_persisted": False,
            "hidden_values_persisted": False,
            "control_values_persisted": False,
            "cookies_tokens_persisted": False,
        },
        "status": "RUNNING",
    }
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options())
        driver.set_page_load_timeout(35)
        driver.get(START)
        result["boundary"]["initial_navigations"] = 1
        time.sleep(10)

        portal = read_portal(driver)
        areas = portal_areas(portal)
        top = [a for a in areas if a["AreaName"] == TOP_NAME and a["AreaOrigin"] == TOP_ORIGIN]
        result["top_level_precheck"] = {
            "portal_read": portal is not None,
            "area_count": len(areas),
            "target_match_count": len(top),
        }
        if len(top) != 1:
            result["status"] = "STOP_TOP_LEVEL_DESPESA_NOT_UNIQUE"
            return result

        top_id = top[0]["AreaId"]
        expected = top_id + TOP_SUFFIX
        validation = driver.execute_script(r"""
        const id=arguments[0], suffix=arguments[1];
        const root=document.getElementById(id);
        if(!root) return {ok:false,reason:'ROOT_MISSING'};
        const scripts=[...root.querySelectorAll('script')].map(s=>s.textContent||'');
        const expected=id+suffix;
        const checks=scripts.map((s,i)=>({ordinal:i+1,link:s.includes("doLink('"+expected+"')"),click:/\.on\s*\(\s*['\"]click['\"]/.test(s)}));
        return {ok:scripts.length===4 && checks.every(x=>x.link&&x.click) && typeof window.doLink==='function',script_count:scripts.length,checks};
        """, top_id, TOP_SUFFIX)
        result["top_level_contract_revalidation"] = validation
        if not validation.get("ok"):
            result["status"] = "STOP_TOP_LEVEL_DOLINK_NOT_REVALIDATED"
            return result

        driver.execute_script("window.doLink(arguments[0]);", expected)
        result["boundary"]["top_level_doLink_invocations"] = 1
        time.sleep(10)

        detailed_portal = read_portal(driver)
        detailed_areas = portal_areas(detailed_portal)
        target = [a for a in detailed_areas if a["AreaName"] == TARGET_AREA_NAME]
        result["detailed_state"] = {
            "portal_read": detailed_portal is not None,
            "area_count": len(detailed_areas),
            "area_names": [a["AreaName"] for a in detailed_areas],
            "empenhado_area_match_count": len(target),
        }
        if len(target) != 1:
            result["status"] = "STOP_EMPENHADO_AREA_NOT_UNIQUE"
            return result

        area_id = target[0]["AreaId"]
        result["target_area"] = {
            "AreaName": target[0]["AreaName"],
            "AreaId": area_id,
            "AreaOrigin": target[0]["AreaOrigin"],
            "session_scoped": True,
        }

        controls = driver.execute_script(r"""
        const areaId=arguments[0], yearText=arguments[1];
        const root=document.getElementById(areaId);
        if(!root) return {ok:false,reason:'ROOT_MISSING'};
        const safe=s=>String(s||'').replace(/\s+/g,' ').trim().slice(0,180);
        const labelText=el=>{
          const xs=[];
          if(el.id){ for(const l of document.querySelectorAll('label[for="'+CSS.escape(el.id)+'"]')) xs.push(safe(l.textContent)); }
          const p=el.closest('label'); if(p) xs.push(safe(p.textContent));
          let a=el.parentElement; for(let i=0;i<3 && a;i++,a=a.parentElement) xs.push(safe(a.innerText));
          return [...new Set(xs.filter(Boolean))];
        };
        const inputs=[...root.querySelectorAll('input[type="text"],input:not([type])')];
        const numberCandidates=inputs.filter(el=>{
          const name=safe(el.getAttribute('name')); const id=safe(el.id); const ph=safe(el.getAttribute('placeholder'));
          const labels=labelText(el).join(' | ');
          return name==='Nro Empenho' || /nro\s*empenho/i.test(name+' '+id+' '+ph+' '+labels);
        });
        const selects=[...root.querySelectorAll('select')];
        const yearCandidates=selects.filter(el=>{
          const labels=labelText(el).join(' | ');
          const hasYear=[...el.options].some(o=>safe(o.textContent)===yearText);
          return hasYear && (/exerc[ií]cio/i.test(labels+' '+safe(el.getAttribute('name'))+' '+safe(el.id)) || selects.filter(x=>[...x.options].some(o=>safe(o.textContent)===yearText)).length===1);
        });
        const actionNodes=[...root.querySelectorAll('[onclick],button,a,input[type="button"],input[type="submit"]')];
        const filterCandidates=[];
        for(const el of actionNodes){
          const onclick=safe(el.getAttribute('onclick'),500);
          if(onclick.includes("submmitApply('"+areaId+"')") || onclick.includes('submmitApply("'+areaId+'")')){
            filterCandidates.push({tag:el.tagName.toLowerCase(),id:safe(el.id),name:safe(el.getAttribute('name')),text:safe(el.innerText||el.getAttribute('value')),onclick});
          }
        }
        const scripts=[...root.querySelectorAll('script')].map(s=>s.textContent||'');
        let scriptBindingCount=0;
        for(const s of scripts){
          const literal1="submmitApply('"+areaId+"')";
          const literal2='submmitApply("'+areaId+'")';
          if(s.includes(literal1)||s.includes(literal2)) scriptBindingCount++;
        }
        return {
          ok:numberCandidates.length===1 && yearCandidates.length===1 && (filterCandidates.length===1 || (filterCandidates.length===0 && scriptBindingCount===1)) && typeof window.submmitApply==='function',
          number_count:numberCandidates.length,
          year_count:yearCandidates.length,
          year_options:yearCandidates.length===1?[...yearCandidates[0].options].map(o=>safe(o.textContent)).slice(0,40):[],
          filter_node_count:filterCandidates.length,
          filter_nodes:filterCandidates,
          script_binding_count:scriptBindingCount,
          submmitApply_type:typeof window.submmitApply,
          number_fingerprint:numberCandidates.length===1?{tag:numberCandidates[0].tagName.toLowerCase(),name:safe(numberCandidates[0].getAttribute('name')),id:safe(numberCandidates[0].id),labels:labelText(numberCandidates[0]).slice(0,6)}:null,
          year_fingerprint:yearCandidates.length===1?{tag:'select',name:safe(yearCandidates[0].getAttribute('name')),id:safe(yearCandidates[0].id),labels:labelText(yearCandidates[0]).slice(0,6)}:null
        };
        """, area_id, TARGET_YEAR)
        result["same_area_control_contract"] = controls
        if not controls.get("ok"):
            result["status"] = "STOP_EXACT_QUERY_CONTROL_CONTRACT_NOT_UNIQUE"
            return result

        assignment = driver.execute_script(r"""
        const areaId=arguments[0], yearText=arguments[1], empenho=arguments[2];
        const root=document.getElementById(areaId);
        const safe=s=>String(s||'').replace(/\s+/g,' ').trim();
        const labelText=el=>{
          const xs=[];
          if(el.id){ for(const l of document.querySelectorAll('label[for="'+CSS.escape(el.id)+'"]')) xs.push(safe(l.textContent)); }
          const p=el.closest('label'); if(p) xs.push(safe(p.textContent));
          let a=el.parentElement; for(let i=0;i<3 && a;i++,a=a.parentElement) xs.push(safe(a.innerText));
          return xs.join(' | ');
        };
        const inputs=[...root.querySelectorAll('input[type="text"],input:not([type])')];
        const numberCandidates=inputs.filter(el=>{
          const hay=[el.getAttribute('name'),el.id,el.getAttribute('placeholder'),labelText(el)].map(safe).join(' ');
          return safe(el.getAttribute('name'))==='Nro Empenho' || /nro\s*empenho/i.test(hay);
        });
        const selects=[...root.querySelectorAll('select')];
        const yearRaw=selects.filter(el=>[...el.options].some(o=>safe(o.textContent)===yearText));
        const yearCandidates=yearRaw.filter(el=>/exerc[ií]cio/i.test(labelText(el)+' '+safe(el.getAttribute('name'))+' '+safe(el.id)) || yearRaw.length===1);
        if(numberCandidates.length!==1 || yearCandidates.length!==1) return {ok:false};
        const input=numberCandidates[0], select=yearCandidates[0];
        const opt=[...select.options].find(o=>safe(o.textContent)===yearText);
        if(!opt) return {ok:false};
        input.focus(); input.value=empenho; input.dispatchEvent(new Event('input',{bubbles:true})); input.dispatchEvent(new Event('change',{bubbles:true}));
        select.value=opt.value; select.dispatchEvent(new Event('input',{bubbles:true})); select.dispatchEvent(new Event('change',{bubbles:true}));
        return {ok:true,assignments:2,year_option_selected_by_label:true,number_input_selected_by_exact_area:true};
        """, area_id, TARGET_YEAR, TARGET_EMPENHO)
        result["query_assignment"] = assignment
        if not assignment.get("ok"):
            result["status"] = "STOP_QUERY_ASSIGNMENT_FAILED"
            return result
        result["boundary"]["controlled_query_field_assignments"] = 2

        driver.execute_script("window.submmitApply(arguments[0]);", area_id)
        result["boundary"]["same_area_filter_invocations"] = 1
        time.sleep(10)

        first_capture = driver.execute_script(r"""
        const areaId=arguments[0];
        const root=document.getElementById(areaId);
        if(!root) return {ok:false,reason:'ROOT_MISSING_AFTER_FILTER'};
        const safe=(s,n=1600)=>String(s||'').replace(/\s+/g,' ').trim().slice(0,n);
        const rows=[...root.querySelectorAll('tr')].map((tr,i)=>({ordinal:i+1,text:safe(tr.innerText,1600),html_actions:[...tr.querySelectorAll('[onclick],a[href],button')].map(el=>({tag:el.tagName.toLowerCase(),text:safe(el.innerText||el.getAttribute('value'),180),onclick:safe(el.getAttribute('onclick'),420),href:safe(el.getAttribute('href'),420)})).filter(a=>a.onclick||a.href)}));
        const exactRows=rows.filter(r=>/(^|\D)3286(?:\s*[-\/]\s*2026)?(\D|$)/.test(r.text));
        return {ok:true,root_text:safe(root.innerText,12000),row_count:rows.length,exact_rows:exactRows.slice(0,20)};
        """, area_id)
        if not first_capture.get("ok"):
            result["status"] = "STOP_FILTER_RESULT_ROOT_MISSING"
            return result

        root_text = normalize_visible(first_capture.get("root_text"), 12000)
        rows = []
        for r in first_capture.get("exact_rows") or []:
            text = normalize_visible(r.get("text"), MAX_ROW_CHARS)
            rows.append({
                "ordinal": r.get("ordinal"),
                "text": text,
                "text_sha256": sha256_text(text),
                "actions": r.get("html_actions") or [],
                "matches": bounded_matches(text),
            })
        result["filtered_result"] = {
            "target_area_still_present": True,
            "table_row_count": first_capture.get("row_count"),
            "exact_3286_row_count": len(rows),
            "exact_3286_rows": rows,
            "root_match_summary": bounded_matches(root_text),
            "root_text_sha256": sha256_text(root_text),
        }

        # Optional same-record detail: allowed only when there is exactly one 3286 row and exactly one
        # explicit row-local action whose onclick calls one of the already-loaded public navigation helpers.
        unique_detail = None
        if len(rows) == 1:
            candidates = []
            for a in rows[0].get("actions") or []:
                onclick = str(a.get("onclick") or "")
                if re.search(r"\b(?:doLink|doAreaLink|doPortalAction)\s*\(", onclick):
                    candidates.append(a)
            if len(candidates) == 1:
                unique_detail = candidates[0]
        result["detail_gate"] = {
            "unique_same_record_detail_action_proven": unique_detail is not None,
            "candidate": unique_detail,
        }

        detail_text = ""
        if unique_detail is not None:
            clicked = driver.execute_script(r"""
            const areaId=arguments[0], ordinal=arguments[1], onclick=arguments[2];
            const root=document.getElementById(areaId); if(!root) return false;
            const rows=[...root.querySelectorAll('tr')]; const tr=rows[ordinal-1]; if(!tr) return false;
            const candidates=[...tr.querySelectorAll('[onclick],a[href],button')].filter(el=>(el.getAttribute('onclick')||'')===onclick);
            if(candidates.length!==1) return false;
            candidates[0].click(); return true;
            """, area_id, rows[0]["ordinal"], unique_detail.get("onclick") or "")
            if clicked:
                result["boundary"]["same_record_detail_drilldowns"] = 1
                time.sleep(8)
                detail_text = driver.execute_script(r"""
                const safe=(s,n=12000)=>String(s||'').replace(/\s+/g,' ').trim().slice(0,n);
                const candidates=[...document.querySelectorAll('body *')].filter(el=>{
                  const t=safe(el.innerText,12000); return /(^|\D)3286(?:\s*[-\/]\s*2026)?(\D|$)/.test(t) && el.children.length<80;
                });
                candidates.sort((a,b)=>(a.innerText||'').length-(b.innerText||'').length);
                return candidates.length?safe(candidates[0].innerText,12000):safe(document.body.innerText,12000);
                """)
                detail_text = normalize_visible(detail_text, 12000)

        combined = root_text + " " + detail_text
        strong_contract_count = combined.casefold().count(STRONG_CONTRACT.casefold())
        strong_process_count = combined.casefold().count(STRONG_PROCESS.casefold())
        result["detail_result"] = {
            "executed": result["boundary"]["same_record_detail_drilldowns"] == 1,
            "visible_text_sha256": sha256_text(detail_text) if detail_text else None,
            "matches": bounded_matches(detail_text) if detail_text else {},
        }
        result["identity_adjudication"] = {
            "exact_municipal_empenho_query_executed": True,
            "strong_contract_literal_count": strong_contract_count,
            "strong_process_literal_count": strong_process_count,
            "contract_45_2026_to_empenho_3286_2026_proven": (strong_contract_count > 0 or strong_process_count > 0) and len(rows) >= 1,
            "proof_rule": "EXACT_45_2026_OR_902_281_2025_INSIDE_EXACT_3286_MUNICIPAL_RESULT_OR_UNIQUE_DETAIL",
            "corroboration_does_not_create_identity": True,
            "tce_payment_attribution_eligible": (strong_contract_count > 0 or strong_process_count > 0) and len(rows) >= 1,
        }
        result["status"] = "PASS_TASK219X_EXACT_EMPENHO_QUERY_COMPLETED"
        return result
    finally:
        if driver is not None:
            driver.quit()


def main() -> int:
    result = run()
    path = Path(os.environ.get("TASK219X_OUTPUT", "runtime/task219x_result.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("status", "").startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
