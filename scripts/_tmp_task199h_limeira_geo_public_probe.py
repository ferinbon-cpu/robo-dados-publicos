from __future__ import annotations

import hashlib
import html.parser
import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OUT=Path('probe-output/task199h_limeira_geo_public_probe.json')
UA='robo-dados-publicos/TASK199H read-only js-contract-audit'
OLD_ROOT='https://limeira.geopixel.com.br/geopixelcidades3/'
NEW_ROOT='https://limeira.geoportal.geopixel.com.br/'
ALLOWED={'limeira.geopixel.com.br','limeira.geoportal.geopixel.com.br'}
MAX=16_000_000
LAZY_REF=re.compile(r'[\"\'](\./[^\"\']+?\.js)[\"\']')
IMPORT_REF=re.compile(r'(?:from\s*)?[\"\'](\./[^\"\']+?\.js)[\"\']')
STRING_RE=re.compile(r'[\"\']([^\"\'\n\r]{2,260})[\"\']')
TARGET_NAME=re.compile(r'(?:api|map|layer|theme|search|address|endereco|property|imovel|parcel|feature|geo|query|identify|consult|report|viewer|public|home|street|localiz)',re.I)
DEP_NAME=re.compile(r'(?:api|index|http|axios|request|client|config|service|fetch|map|geo|theme|layer)',re.I)
TARGET_TEXT=re.compile(r'(?:baseURL|axios|fetch\s*\(|withCredentials|/rest|/api|wms|wfs|geoserver|endpoint|feature|parcel|im[oó]vel|endere[cç]o|address|identify|theme|layer)',re.I)

class P(html.parser.HTMLParser):
    def __init__(self): super().__init__(); self.scripts=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag.lower()=='script' and d.get('src'): self.scripts.append(d['src'])

def safe(base,raw):
    u=urllib.parse.urljoin(base,raw); p=urllib.parse.urlparse(u)
    if p.scheme!='https' or p.hostname not in ALLOWED or p.username or p.password: return None
    return urllib.parse.urlunparse((p.scheme,p.netloc,p.path,'',p.query,''))

def fetch(url,limit=MAX):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/javascript,text/javascript,*/*;q=0.5'},method='GET')
    row={'requested_url':url}
    try:
        with urllib.request.urlopen(req,timeout=35,context=ssl.create_default_context()) as r:
            b=r.read(limit+1); tr=len(b)>limit; b=b[:limit]
            row.update(status=int(r.status),final_url=r.geturl(),content_type=r.headers.get('Content-Type'),bytes_captured=len(b),truncated=tr,sha256_captured=hashlib.sha256(b).hexdigest(),body=b)
    except urllib.error.HTTPError as e:
        try:b=e.read(limit+1)[:limit]
        except Exception:b=b''
        row.update(status=int(e.code),final_url=e.geturl(),content_type=e.headers.get('Content-Type') if e.headers else None,bytes_captured=len(b),sha256_captured=hashlib.sha256(b).hexdigest(),error=f'HTTPError:{e.code}',body=b)
    except Exception as e: row.update(status=None,error=f'{type(e).__name__}:{e}',body=b'')
    return row

def txt(b): return b.decode('utf-8',errors='replace')
def summ(r): return {k:v for k,v in r.items() if k!='body'}
def snips(s,limit=80):
    out=[]
    for m in TARGET_TEXT.finditer(s):
        z=re.sub(r'\s+',' ',s[max(0,m.start()-280):min(len(s),m.end()+700)])
        if z not in out:out.append(z)
        if len(out)>=limit:break
    return out

def strings(s,limit=300):
    out=[]
    for x in STRING_RE.findall(s):
        if TARGET_TEXT.search(x) or x.startswith(('/api','/rest','/v1','/v2','http')):
            if x not in out:out.append(x)
            if len(out)>=limit:break
    return out

def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    res={'schema':'TASK199H_LIMEIRA_GEO_JS_CONTRACT_TRACE_V3','mode':'EPHEMERAL_READ_ONLY_DECLARED_JS_ONLY','auth_attempted':False,'registration_attempted':False,'post_requests':0,'write_requests':0,'tinyfish_used':False,'roots':[],'declared_bundles':[],'all_old_lazy_names':[],'selected_chunks':[],'dependency_chunks':[],'findings':[],'status':'PASS_JS_CONTRACT_TRACE_COMPLETE'}
    declared=[]
    for root in [NEW_ROOT,OLD_ROOT]:
        r=fetch(root); res['roots'].append(summ(r))
        if r.get('status')!=200:continue
        p=P(); p.feed(txt(r.get('body') or b''))
        urls=[]
        for raw in p.scripts:
            u=safe(root,raw)
            if u and u not in urls:urls.append(u)
        res['declared_bundles'].append({'root':root,'scripts':p.scripts,'resolved':urls}); declared+=urls

    bundle_rows=[]; selected=[]
    for u in dict.fromkeys(declared):
        r=fetch(u); s=txt(r.get('body') or b''); bundle_rows.append((u,r,s))
        lazy=LAZY_REF.findall(s)
        if urllib.parse.urlparse(u).hostname=='limeira.geopixel.com.br':
            for rel in lazy:
                name=rel.rsplit('/',1)[-1]
                if name not in res['all_old_lazy_names']:res['all_old_lazy_names'].append(name)
                if TARGET_NAME.search(name):
                    x=safe(u,rel)
                    if x and x not in selected:selected.append(x)
        res['findings'].append({**summ(r),'role':'DECLARED_MAIN_BUNDLE','head_prefix':s[:5000],'target_strings':strings(s,250),'target_snippets':snips(s,45)})

    res['selected_chunks']=selected[:100]
    deps=[]
    for u in selected[:100]:
        r=fetch(u,8_000_000); s=txt(r.get('body') or b'')
        imports=[]
        for rel in IMPORT_REF.findall(s):
            x=safe(u,rel)
            if x and x not in imports:imports.append(x)
            if x and DEP_NAME.search(rel.rsplit('/',1)[-1]) and x not in deps:deps.append(x)
        res['findings'].append({**summ(r),'role':'SELECTED_LAZY_CHUNK','head_prefix':s[:7000],'imports':imports[:150],'target_strings':strings(s,250),'target_snippets':snips(s,65)})

    res['dependency_chunks']=deps[:120]
    for u in deps[:120]:
        r=fetch(u,8_000_000); s=txt(r.get('body') or b'')
        res['findings'].append({**summ(r),'role':'DIRECT_DEPENDENCY','head_prefix':s[:7000],'imports':[safe(u,x) for x in IMPORT_REF.findall(s)[:100] if safe(u,x)],'target_strings':strings(s,300),'target_snippets':snips(s,80)})

    res['network_contract_candidates']=[]
    for f in res['findings']:
        blob=' '.join((f.get('target_strings') or []))+' '+' '.join((f.get('target_snippets') or []))
        if re.search(r'(?:baseURL|axios|withCredentials|/rest|/api|wms|wfs|geoserver)',blob,re.I):
            res['network_contract_candidates'].append(f['requested_url'])
    res['network_contract_candidates']=list(dict.fromkeys(res['network_contract_candidates']))
    res['absence_inference_allowed']=False
    res['next_step']='derive exact public GET contract only from literal client/base-path evidence; do not guess routes'
    OUT.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':res['status'],'all_lazy_names':len(res['all_old_lazy_names']),'selected':len(selected),'dependencies':len(deps),'contract_candidates':len(res['network_contract_candidates']),'out':str(OUT)},ensure_ascii=False))
    return 0
if __name__=='__main__':raise SystemExit(main())
