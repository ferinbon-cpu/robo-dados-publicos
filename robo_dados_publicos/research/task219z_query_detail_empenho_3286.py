from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

START="https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418"
TOP_NAME="Despesa"
TOP_ORIGIN="2_92_guestuser_207_6_DSL0_VIS1343"
TOP_SUFFIX="**##**V1343[vl]"
TARGET_NAME="Detalhe do Empenho"
TARGET_ORIGIN="2_92_guestuser_200_8_DSL0_VIS706"
YEAR="2026"
EMPENHO="3286"
STRONG=("45/2026","902.281/2025")
CORROBORATION=("10/2026","37457979000131","Med Doctor","endoscopia")


def sha(t:str)->str: return hashlib.sha256(t.encode("utf-8",errors="replace")).hexdigest()
def norm(t:object,n:int=12000)->str: return re.sub(r"\s+"," ",str(t or "")).strip()[:n]
def ckey(k:object)->str:
    s=str(k); s=s[6:] if s.casefold().startswith("gxtpr_") else s
    return re.sub(r"[^a-z0-9]","",s.casefold())
def field(o:object,name:str,default=None):
    if not isinstance(o,dict): return default
    w=ckey(name)
    for k,v in o.items():
        if ckey(k)==w:return v
    return default
def dec(v:object,d:int=0):
    if d>3:return v
    if isinstance(v,str):
        s=v.strip()
        if s and s[0] in '[{"':
            try:return dec(json.loads(s),d+1)
            except Exception:return v
    return v
def areas(portal:object)->list[dict]:
    portal=dec(portal); out=[]; ls=field(portal,"Layers",[]) if isinstance(portal,dict) else []
    if not isinstance(ls,list):return out
    for li,l in enumerate(ls,1):
        aa=field(l,"Areas",[]) if isinstance(l,dict) else []
        if not isinstance(aa,list):continue
        for ai,a in enumerate(aa,1):
            if isinstance(a,dict):out.append({"layer_index":li,"area_index":ai,"AreaId":str(field(a,"AreaId","") or ""),"AreaName":str(field(a,"AreaName","") or ""),"AreaOrigin":str(field(a,"AreaOrigin","") or "")})
    return out
def opts()->Options:
    o=Options()
    for a in ("--headless=new","--no-sandbox","--disable-dev-shm-usage","--disable-background-networking","--disable-default-apps","--disable-sync","--disable-component-update","--disable-domain-reliability","--metrics-recording-only","--safebrowsing-disable-auto-update","--window-size=1500,1100"):o.add_argument(a)
    return o
def portal(d):
    r=d.execute_script("""try{return {ok:true,json:JSON.stringify(gx.fn.getControlValue('vSDT_TDAPORTAL'))};}catch(e){return {ok:false,error:e.name};}""")
    if not r or not r.get("ok"):return None
    try:return dec(json.loads(r.get("json","null")))
    except Exception:return None

def literal_hits(text:str)->dict:
    out={}; f=text.casefold()
    for lit in (EMPENHO,f"{EMPENHO}/2026",f"{EMPENHO}-2026",*STRONG,*CORROBORATION):
        c=f.count(lit.casefold())
        if c:
            p=f.find(lit.casefold()); sn=norm(text[max(0,p-130):min(len(text),p+len(lit)+190)],360)
            out[lit]={"count":c,"snippet":sn,"snippet_sha256":sha(sn)}
    return out

def run()->dict:
    out={"task":"TASK_219Z_QUERY_DETAIL_EMPENHO_3286","issue":742,"parent_issue":691,"derived_from_task219y_head":"6b456b74833e8da796fd647eb58fcc75da218a54","execution_head_sha":os.environ.get("GITHUB_SHA"),"authorization_sequence":"LEAP_3_OF_3_CURRENT_AUTHORIZATION","boundary":{"browser_sessions":1,"initial_navigations":0,"top_level_doLink_invocations":0,"query_field_assignments":0,"target_filter_invocations":0,"same_record_drilldowns":0,"manual_fetch_xhr":0,"direct_endpoint_calls":0,"layerinfo_replay":0,"retries":0,"control_values_persisted":False,"hidden_values_persisted":False,"cookies_tokens_persisted":False,"raw_page_source_persisted":False,"raw_har_persisted":False,"full_scripts_persisted":False},"status":"RUNNING"}
    d=None
    try:
        d=webdriver.Chrome(options=opts());d.set_page_load_timeout(35);d.get(START);out["boundary"]["initial_navigations"]=1;time.sleep(10)
        a=areas(portal(d));top=[x for x in a if x["AreaName"]==TOP_NAME and x["AreaOrigin"]==TOP_ORIGIN]
        out["top_precheck"]={"area_count":len(a),"match_count":len(top)}
        if len(top)!=1:out["status"]="STOP_TOP_DESPESA_NOT_UNIQUE";return out
        tid=top[0]["AreaId"]
        chk=d.execute_script(r"""const id=arguments[0],s=arguments[1],r=document.getElementById(id);if(!r)return {ok:false};const ss=[...r.querySelectorAll('script')].map(x=>x.textContent||''),e=id+s;return {ok:ss.length===4&&ss.every(x=>x.includes("doLink('"+e+"')")&&/\.on\s*\(\s*['\"]click['\"]/.test(x))&&typeof window.doLink==='function',count:ss.length};""",tid,TOP_SUFFIX)
        out["top_contract_revalidation"]=chk
        if not chk.get("ok"):out["status"]="STOP_TOP_DOLINK_NOT_REVALIDATED";return out
        d.execute_script("window.doLink(arguments[0]);",tid+TOP_SUFFIX);out["boundary"]["top_level_doLink_invocations"]=1;time.sleep(10)
        a2=areas(portal(d));tar=[x for x in a2 if x["AreaName"]==TARGET_NAME and x["AreaOrigin"]==TARGET_ORIGIN]
        out["detail_area_precheck"]={"area_count":len(a2),"match_count":len(tar)}
        if len(tar)!=1:out["status"]="STOP_DETAIL_AREA_NOT_UNIQUE";return out
        aid=tar[0]["AreaId"];fid="AREAFILTER_"+aid
        gate=d.execute_script(r"""
        const aid=arguments[0],fid=arguments[1],year=arguments[2];
        const root=document.getElementById(aid),filter=document.getElementById(fid),safe=(s,n=420)=>String(s||'').replace(/\s+/g,' ').trim().slice(0,n);
        if(!root||!filter)return {ok:false,reason:'ROOT_MISSING',root:!!root,filter:!!filter};
        const labelText=el=>{const x=[];if(el.id)for(const l of document.querySelectorAll('label[for="'+CSS.escape(el.id)+'"]'))x.push(safe(l.textContent,180));const p=el.closest('label');if(p)x.push(safe(p.textContent,180));let a=el.parentElement;for(let i=0;i<3&&a;i++,a=a.parentElement){const t=safe(a.innerText,260);if(t)x.push(t)}return [...new Set(x)]};
        const txt=[...filter.querySelectorAll('input[type="text"],input:not([type])')];
        const nro=txt.filter(el=>/nro\s*empenho/i.test([el.getAttribute('name'),el.id,el.getAttribute('placeholder'),...labelText(el)].map(safe).join(' ')));
        const sels=[...filter.querySelectorAll('select')];
        const yrs=sels.filter(el=>[...el.options].some(o=>safe(o.textContent,100)===year)&&/exerc[ií]cio/i.test([el.getAttribute('name'),el.id,...labelText(el)].map(safe).join(' ')));
        const exact="submmitApply('"+fid+"')", exact2='submmitApply("'+fid+'")';
        const nodes=[...document.querySelectorAll('[onclick]')].filter(el=>{const o=el.getAttribute('onclick')||'';return o.includes(exact)||o.includes(exact2)}).map(el=>({tag:el.tagName.toLowerCase(),id:safe(el.id,180),text:safe(el.innerText||el.getAttribute('value'),180),onclick:safe(el.getAttribute('onclick'),420)}));
        const scripts=[];for(const s of document.querySelectorAll('script')){const t=s.textContent||'';let p=t.indexOf(exact);if(p<0)p=t.indexOf(exact2);if(p>=0)scripts.push({snippet:safe(t.slice(Math.max(0,p-120),Math.min(t.length,p+exact.length+180)),360)});}
        const bindingCount=nodes.length+scripts.length;
        return {ok:nro.length===1&&yrs.length===1&&bindingCount===1&&typeof window.submmitApply==='function',content_root_exists:true,filter_root_exists:true,text_input_total:txt.length,select_total:sels.length,nro_count:nro.length,nro:{id:nro.length===1?safe(nro[0].id,180):null,name:nro.length===1?safe(nro[0].getAttribute('name'),180):null,labels:nro.length===1?labelText(nro[0]).slice(0,6):[]},year_count:yrs.length,year:{id:yrs.length===1?safe(yrs[0].id,180):null,labels:yrs.length===1?labelText(yrs[0]).slice(0,6):[],option_labels:yrs.length===1?[...yrs[0].options].map(o=>safe(o.textContent,100)).slice(0,40):[]},onclick_bindings:nodes,script_bindings:scripts,binding_count:bindingCount,submmitApply_type:typeof window.submmitApply};
        """,aid,fid,YEAR)
        out["exact_submit_gate"]={"AreaName":TARGET_NAME,"AreaOrigin":TARGET_ORIGIN,"runtime_AreaId":aid,"filter_id":fid,**gate}
        if not gate.get("ok"):out["status"]="STOP_EXACT_DETAIL_SUBMIT_BINDING_NOT_UNIQUE";return out
        assign=d.execute_script(r"""
        const fid=arguments[0],year=arguments[1],num=arguments[2],f=document.getElementById(fid),safe=s=>String(s||'').replace(/\s+/g,' ').trim();if(!f)return {ok:false};
        const labelText=el=>{const x=[];if(el.id)for(const l of document.querySelectorAll('label[for="'+CSS.escape(el.id)+'"]'))x.push(safe(l.textContent));const p=el.closest('label');if(p)x.push(safe(p.textContent));let a=el.parentElement;for(let i=0;i<3&&a;i++,a=a.parentElement)x.push(safe(a.innerText));return x.join(' ')};
        const nro=[...f.querySelectorAll('input[type="text"],input:not([type])')].filter(el=>/nro\s*empenho/i.test([el.getAttribute('name'),el.id,el.getAttribute('placeholder'),labelText(el)].map(safe).join(' ')));
        const yrs=[...f.querySelectorAll('select')].filter(el=>[...el.options].some(o=>safe(o.textContent)===year)&&/exerc[ií]cio/i.test([el.getAttribute('name'),el.id,labelText(el)].map(safe).join(' ')));
        if(nro.length!==1||yrs.length!==1)return {ok:false};const opt=[...yrs[0].options].find(o=>safe(o.textContent)===year);if(!opt)return {ok:false};
        nro[0].focus();nro[0].value=num;nro[0].dispatchEvent(new Event('input',{bubbles:true}));nro[0].dispatchEvent(new Event('change',{bubbles:true}));yrs[0].value=opt.value;yrs[0].dispatchEvent(new Event('input',{bubbles:true}));yrs[0].dispatchEvent(new Event('change',{bubbles:true}));return {ok:true,assignments:2,number_selected_by_filter_contract:true,year_selected_by_visible_label:true};
        """,fid,YEAR,EMPENHO)
        out["query_assignment"]=assign
        if not assign.get("ok"):out["status"]="STOP_QUERY_ASSIGNMENT_FAILED";return out
        out["boundary"]["query_field_assignments"]=2
        d.execute_script("window.submmitApply(arguments[0]);",fid);out["boundary"]["target_filter_invocations"]=1;time.sleep(10)
        a3=areas(portal(d));tar3=[x for x in a3 if x["AreaName"]==TARGET_NAME and x["AreaOrigin"]==TARGET_ORIGIN]
        if len(tar3)!=1:out["status"]="STOP_DETAIL_AREA_NOT_UNIQUE_AFTER_QUERY";return out
        aid3=tar3[0]["AreaId"]
        cap=d.execute_script(r"""
        const id=arguments[0],safe=(s,n=12000)=>String(s||'').replace(/\s+/g,' ').trim().slice(0,n),root=document.getElementById(id);if(!root)return {ok:false};
        const rows=[...root.querySelectorAll('tr')].map((tr,i)=>({ordinal:i+1,text:safe(tr.innerText,1800),actions:[...tr.querySelectorAll('[onclick],a[href],button')].map(el=>({tag:el.tagName.toLowerCase(),text:safe(el.innerText||el.getAttribute('value'),180),onclick:safe(el.getAttribute('onclick'),420),href:safe(el.getAttribute('href'),420)})).filter(x=>x.onclick||x.href)}));
        const exact=rows.filter(r=>/(^|\D)3286(?:\s*[-\/]\s*2026)?(\D|$)/.test(r.text));return {ok:true,text:safe(root.innerText,12000),row_count:rows.length,exact_rows:exact.slice(0,20)};
        """,aid3)
        if not cap.get("ok"):out["status"]="STOP_DETAIL_RESULT_ROOT_MISSING";return out
        text=norm(cap.get("text"),12000); exact_rows=[]
        for r in cap.get("exact_rows") or []:
            rt=norm(r.get("text"),1800);exact_rows.append({"ordinal":r.get("ordinal"),"text":rt,"text_sha256":sha(rt),"matches":literal_hits(rt),"actions":r.get("actions") or []})
        out["query_result"]={"post_query_runtime_AreaId":aid3,"content_text_sha256":sha(text),"row_count":cap.get("row_count"),"exact_3286_row_count":len(exact_rows),"exact_3286_rows":exact_rows,"visible_matches":literal_hits(text)}
        # Optional drilldown only from exactly one exact 3286 row with exactly one explicit navigation helper action.
        detail=""; drill=None
        if len(exact_rows)==1:
            cs=[]
            for a in exact_rows[0]["actions"]:
                oc=str(a.get("onclick") or "")
                if re.search(r"\b(?:doLink|doAreaLink|doPortalAction)\s*\(",oc) and "submmitApply" not in oc:cs.append(a)
            if len(cs)==1:drill=cs[0]
        out["drilldown_gate"]={"unique_same_record_navigation_action":drill is not None,"candidate":drill}
        if drill is not None:
            clicked=d.execute_script(r"""const id=arguments[0],ord=arguments[1],oc=arguments[2],r=document.getElementById(id);if(!r)return false;const tr=[...r.querySelectorAll('tr')][ord-1];if(!tr)return false;const xs=[...tr.querySelectorAll('[onclick],a[href],button')].filter(el=>(el.getAttribute('onclick')||'')===oc);if(xs.length!==1)return false;xs[0].click();return true;""",aid3,exact_rows[0]["ordinal"],drill.get("onclick") or "")
            if clicked:
                out["boundary"]["same_record_drilldowns"]=1;time.sleep(8);detail=norm(d.execute_script("return document.body?document.body.innerText:'';"),12000)
        combined=text+" "+detail
        strong={lit:combined.casefold().count(lit.casefold()) for lit in STRONG}
        out["detail_after_optional_drilldown"]={"executed":out["boundary"]["same_record_drilldowns"]==1,"visible_text_sha256":sha(detail) if detail else None,"matches":literal_hits(detail) if detail else {}}
        proven=len(exact_rows)>=1 and any(v>0 for v in strong.values())
        out["identity_adjudication"]={"exact_municipal_3286_query_executed":True,"strong_literal_counts":strong,"contract_45_2026_to_empenho_3286_2026_proven":proven,"proof_rule":"EXACT_45_2026_OR_902_281_2025_INSIDE_EXACT_3286_RESULT_OR_UNIQUE_SAME_RECORD_DETAIL","corroboration_does_not_create_identity":True,"tce_payment_attribution_eligible":proven}
        out["status"]="PASS_TASK219Z_EXACT_DETAIL_QUERY_COMPLETED";return out
    finally:
        if d:d.quit()

def main()->int:
    r=run();p=Path(os.environ.get("TASK219Z_OUTPUT","runtime/task219z_result.json"));p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True),encoding="utf-8");print(json.dumps(r,ensure_ascii=False,sort_keys=True));return 0 if r.get("status","").startswith("PASS_") else 1
if __name__=="__main__":raise SystemExit(main())
