from __future__ import annotations

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


def ckey(k: object) -> str:
    s = str(k)
    if s.casefold().startswith("gxtpr_"):
        s = s[6:]
    return re.sub(r"[^a-z0-9]", "", s.casefold())


def field(obj: object, name: str, default=None):
    if not isinstance(obj, dict): return default
    wanted = ckey(name)
    for k, v in obj.items():
        if ckey(k) == wanted: return v
    return default


def decode_jsonish(v: object, depth: int = 0):
    if depth > 3: return v
    if isinstance(v, str):
        s = v.strip()
        if s and s[0] in '[{"':
            try: return decode_jsonish(json.loads(s), depth + 1)
            except Exception: return v
    return v


def portal_areas(portal: object) -> list[dict]:
    portal = decode_jsonish(portal); out=[]
    layers = field(portal, "Layers", []) if isinstance(portal, dict) else []
    if not isinstance(layers, list): return out
    for li, layer in enumerate(layers, 1):
        areas = field(layer, "Areas", []) if isinstance(layer, dict) else []
        if not isinstance(areas, list): continue
        for ai, area in enumerate(areas, 1):
            if not isinstance(area, dict): continue
            out.append({
                "layer_index": li, "area_index": ai,
                "AreaId": str(field(area, "AreaId", "") or ""),
                "AreaName": str(field(area, "AreaName", "") or ""),
                "AreaOrigin": str(field(area, "AreaOrigin", "") or ""),
                "AreaType": str(field(area, "AreaType", "") or ""),
            })
    return out


def options() -> Options:
    o=Options()
    for a in ("--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-background-networking","--disable-default-apps","--disable-sync","--disable-component-update","--disable-domain-reliability","--metrics-recording-only","--safebrowsing-disable-auto-update","--window-size=1500,1100"):
        o.add_argument(a)
    return o


def read_portal(driver):
    raw=driver.execute_script("""
    try { return {ok:true,json:JSON.stringify(gx.fn.getControlValue('vSDT_TDAPORTAL'))}; }
    catch(e){ return {ok:false,error:e.name}; }
    """)
    if not raw or not raw.get("ok"): return None
    try: return decode_jsonish(json.loads(raw.get("json", "null")))
    except Exception: return None


def inspect_area(driver, area: dict) -> dict:
    return driver.execute_script(r"""
    const area=arguments[0], id=area.AreaId;
    const safe=(s,n=300)=>String(s||'').replace(/\s+/g,' ').trim().slice(0,n);
    const meta=el=>({tag:el.tagName.toLowerCase(),id:safe(el.id,180),name:safe(el.getAttribute('name'),180),type:safe(el.getAttribute('type'),80),placeholder:safe(el.getAttribute('placeholder'),180)});
    const labels=el=>{
      const xs=[];
      if(el.id){ for(const l of document.querySelectorAll('label[for="'+CSS.escape(el.id)+'"]')) xs.push(safe(l.textContent,180)); }
      const p=el.closest('label'); if(p) xs.push(safe(p.textContent,180));
      let a=el.parentElement; for(let i=0;i<3&&a;i++,a=a.parentElement){ const t=safe(a.innerText,260); if(t) xs.push(t); }
      return [...new Set(xs)].slice(0,8);
    };
    const inspect=root=>{
      if(!root) return {exists:false};
      const texts=[...root.querySelectorAll('input[type="text"],input:not([type])')].map(el=>({...meta(el),labels:labels(el)}));
      const nro=texts.filter(x=>/nro\s*empenho/i.test([x.name,x.id,x.placeholder,...x.labels].join(' ')));
      const sels=[...root.querySelectorAll('select')].map(el=>({...meta(el),labels:labels(el),option_labels:[...el.options].slice(0,50).map(o=>safe(o.textContent,100))}));
      const years=sels.filter(x=>x.option_labels.includes('2026') && /exerc[ií]cio/i.test([x.name,x.id,...x.labels].join(' ')));
      const actionNodes=[...root.querySelectorAll('[onclick],button,a,input[type="button"],input[type="submit"]')];
      const actionBindings=[];
      for(const el of actionNodes){
        const oc=safe(el.getAttribute('onclick'),420);
        if(/submmitApply/i.test(oc)) actionBindings.push({tag:el.tagName.toLowerCase(),id:safe(el.id,160),name:safe(el.getAttribute('name'),160),text:safe(el.innerText||el.getAttribute('value'),180),onclick:oc,same_area:oc.includes("submmitApply('"+id+"')")||oc.includes('submmitApply("'+id+'")')});
      }
      const scriptHits=[];
      for(const s of root.querySelectorAll('script')){
        const t=s.textContent||'';
        for(const term of ['submmitApply','Nro Empenho','Exercício']){
          const p=t.toLowerCase().indexOf(term.toLowerCase());
          if(p>=0){ const sn=safe(t.slice(Math.max(0,p-110),Math.min(t.length,p+term.length+170)),320); scriptHits.push({term,snippet:sn,same_area:sn.includes(id)}); }
        }
      }
      const sameNode=actionBindings.filter(x=>x.same_area).length;
      const sameScript=scriptHits.filter(x=>x.term==='submmitApply'&&x.same_area).length;
      return {exists:true,text_input_count:texts.length,nro_empenho_count:nro.length,nro_empenho:nro,select_count:sels.length,exercicio_2026_count:years.length,exercicio_2026:years,submmitApply_bindings:actionBindings,script_hits:scriptHits,same_area_submmitApply_binding_count:sameNode+sameScript};
    };
    return {AreaName:area.AreaName,AreaOrigin:area.AreaOrigin,AreaId:id,content:inspect(document.getElementById(id)),filter:inspect(document.getElementById('AREAFILTER_'+id))};
    """, area)


def run() -> dict:
    out={"task":"TASK_219Y_MAP_AREAFILTER_QUERY_CONTRACTS","issue":740,"parent_issue":691,"derived_from_task219x_head":"9aacd04ecc58d0b6d8b5f31cf9612c6c753420e8","execution_head_sha":os.environ.get("GITHUB_SHA"),"authorization_sequence":"LEAP_2_OF_3_CURRENT_AUTHORIZATION","boundary":{"browser_sessions":1,"initial_navigations":0,"top_level_doLink_invocations":0,"query_field_assignments":0,"filter_invocations":0,"result_clicks":0,"manual_fetch_xhr":0,"direct_endpoint_calls":0,"layerinfo_replay":0,"retries":0,"empenho_lookup":0,"control_values_persisted":False,"hidden_values_persisted":False,"raw_page_source_persisted":False,"raw_har_persisted":False,"full_scripts_persisted":False},"status":"RUNNING"}
    d=None
    try:
        d=webdriver.Chrome(options=options()); d.set_page_load_timeout(35); d.get(START); out["boundary"]["initial_navigations"]=1; time.sleep(10)
        p=read_portal(d); areas=portal_areas(p); top=[a for a in areas if a["AreaName"]==TOP_NAME and a["AreaOrigin"]==TOP_ORIGIN]
        out["top_precheck"]={"area_count":len(areas),"match_count":len(top)}
        if len(top)!=1: out["status"]="STOP_TOP_DESPESA_NOT_UNIQUE"; return out
        aid=top[0]["AreaId"]
        val=d.execute_script(r"""
        const id=arguments[0],suf=arguments[1],root=document.getElementById(arguments[0]); if(!root) return {ok:false};
        const ss=[...root.querySelectorAll('script')].map(x=>x.textContent||''), exp=id+suf;
        return {ok:ss.length===4&&ss.every(s=>s.includes("doLink('"+exp+"')")&&/\.on\s*\(\s*['\"]click['\"]/.test(s))&&typeof window.doLink==='function',count:ss.length};
        """,aid,TOP_SUFFIX)
        out["top_contract_revalidation"]=val
        if not val.get("ok"): out["status"]="STOP_TOP_DOLINK_NOT_REVALIDATED"; return out
        d.execute_script("window.doLink(arguments[0]);",aid+TOP_SUFFIX); out["boundary"]["top_level_doLink_invocations"]=1; time.sleep(10)
        p2=read_portal(d); a2=portal_areas(p2); out["detailed_area_count"]=len(a2)
        mapped=[inspect_area(d,a) for a in a2]
        contracts=[]
        for row in mapped:
            for kind in ("content","filter"):
                r=row[kind]
                if r.get("exists") and r.get("nro_empenho_count")==1 and r.get("exercicio_2026_count")==1 and r.get("same_area_submmitApply_binding_count")==1:
                    contracts.append({"AreaName":row["AreaName"],"AreaOrigin":row["AreaOrigin"],"AreaId":row["AreaId"],"root_kind":kind})
        # only retain areas with relevant signals to reduce noise, while preserving a compact all-area structural index
        relevant=[]; index=[]
        for row in mapped:
            sig=False
            for kind in ("content","filter"):
                r=row[kind]; sig=sig or bool(r.get("nro_empenho_count") or r.get("exercicio_2026_count") or r.get("submmitApply_bindings") or r.get("script_hits"))
            index.append({"AreaName":row["AreaName"],"AreaOrigin":row["AreaOrigin"],"AreaId":row["AreaId"],"content_exists":row["content"].get("exists",False),"filter_exists":row["filter"].get("exists",False)})
            if sig: relevant.append(row)
        out["area_index"]=index; out["relevant_area_mappings"]=relevant; out["proven_query_contracts"]=contracts
        emp=[c for c in contracts if c["AreaName"]=="Empenhado"]
        out["adjudication"]={"valid_contract_count":len(contracts),"empenhado_valid_contract_count":len(emp),"empenhado_filter_contract_proven":len(emp)==1 and emp[0]["root_kind"]=="filter","query_executed":False,"coverage_after":34}
        out["status"]="PASS_TASK219Y_PASSIVE_MAPPING_COMPLETED"; return out
    finally:
        if d: d.quit()


def main() -> int:
    r=run(); p=Path(os.environ.get("TASK219Y_OUTPUT","runtime/task219y_result.json")); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8"); print(json.dumps(r,ensure_ascii=False,sort_keys=True)); return 0 if r.get("status","").startswith("PASS_") else 1

if __name__=="__main__": raise SystemExit(main())
