from __future__ import annotations
import json, re, ssl, urllib.request, urllib.error
from pathlib import Path

OUT=Path('probe-output/task199h_limeira_geo_public_probe.json')
SERVER='https://limeira.geopixel.com.br/geopixelcidades3_server'
LOGIN=SERVER+'/public/anonymousLogin'
GET_PROFILES=SERVER+'/authentication/getProfiles'
SET_PROFILE=SERVER+'/authentication/setCurrentProfile?profileId=2'
THEMES=SERVER+'/v2/profiles/2/themes'
BASE_LAYERS=SERVER+'/v2/profiles/2/base-layers'
UA='robo-dados-publicos/TASK199H bounded-public-theme-inventory'

SAFE=re.compile(r'(?:^id$|name|nome|title|titulo|theme|tema|layer|camada|type|tipo|url|service|servico|description|descricao|geometry|geometr|schema|table|tabela|field|campo|active|ativo|visible|visivel|public|default|order|ordem|group|grupo)',re.I)
BLOCK=re.compile(r'(?:token|authorization|password|secret|credential|email|login|cpf|user|usuario)',re.I)

def req(url,method='GET',token=None):
    headers={'User-Agent':UA,'Accept':'application/json,*/*;q=0.5'}; data=None
    if method=='POST': headers['Content-Type']='application/json'; data=b''
    if token: headers['Authorization']=token
    q=urllib.request.Request(url,headers=headers,data=data,method=method)
    try:
        with urllib.request.urlopen(q,timeout=40,context=ssl.create_default_context()) as r:
            b=r.read(12_000_001)[:12_000_000]
            return {'status':int(r.status),'final_url':r.geturl(),'content_type':r.headers.get('Content-Type'),'authorization':r.headers.get('Authorization'),'body':b}
    except urllib.error.HTTPError as e:
        try:b=e.read(2_000_000)
        except Exception:b=b''
        return {'status':int(e.code),'final_url':e.geturl(),'content_type':e.headers.get('Content-Type') if e.headers else None,'authorization':e.headers.get('Authorization') if e.headers else None,'body':b,'error':f'HTTPError:{e.code}'}
    except Exception as e:return {'status':None,'error':f'{type(e).__name__}:{e}','authorization':None,'body':b''}

def meta(r): return {k:v for k,v in r.items() if k not in ('authorization','body')}
def parse(r):
    try:return json.loads((r.get('body') or b'').decode('utf-8',errors='strict')),None
    except Exception as e:return None,f'{type(e).__name__}:{e}'

def sanitize(x,depth=0):
    if depth>5:return None
    if isinstance(x,dict):
        out={}
        for k,v in x.items():
            sk=str(k)
            if BLOCK.search(sk):continue
            if isinstance(v,(dict,list)):
                child=sanitize(v,depth+1)
                if child not in (None,{},[]): out[sk]=child
            elif SAFE.search(sk) and (isinstance(v,(str,int,float,bool)) or v is None):
                out[sk]=v
        return out
    if isinstance(x,list):
        return [y for y in (sanitize(v,depth+1) for v in x[:500]) if y not in (None,{},[])]
    return None

def items(x):
    if isinstance(x,list):return x
    if isinstance(x,dict):
        for k in ('themes','data','content','items','result'):
            if isinstance(x.get(k),list):return x[k]
    return []

def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    d={'schema':'TASK199H_PUBLIC_PROFILE_THEME_INVENTORY_V8','mode':'EPHEMERAL_BOUNDED_PUBLIC_ANONYMOUS_SESSION','credentials_supplied':False,'registration_attempted':False,'regular_login_attempted':False,'post_requests':1,'write_requests':0,'drive_writes':0,'tinyfish_used':False,'token_persisted':False,'token_logged':False,'profile':{'id':2,'profileName':'Público'},'steps':{},'status':'STOP_NOT_RUN'}
    login=req(LOGIN,'POST'); token=login.get('authorization'); d['steps']['anonymous_login']={**meta(login),'authorization_present':bool(token)}
    if not(token and login.get('status')==200): d['status']='STOP_ANONYMOUS_LOGIN_FAILED'; OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)); print(d['status']); return 0
    pr=req(GET_PROFILES,token=token); pobj,pe=parse(pr); d['steps']['get_profiles']={**meta(pr),'parse_error':pe,'profile_count':len(items(pobj)) if pe is None else None}
    if pe or pr.get('status')!=200 or not any(isinstance(x,dict) and x.get('id')==2 and x.get('profileName')=='Público' for x in items(pobj)):
        d['status']='STOP_PUBLIC_PROFILE_NOT_RECONFIRMED'; OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)); print(d['status']); return 0
    sp=req(SET_PROFILE,token=token); newtoken=sp.get('authorization') or token; d['steps']['set_current_profile']={**meta(sp),'authorization_refreshed':bool(sp.get('authorization'))}
    if sp.get('status')!=200: d['status']='STOP_SET_PUBLIC_PROFILE_FAILED'; OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)); print(d['status']); return 0
    for label,url in [('themes',THEMES),('base_layers',BASE_LAYERS)]:
        r=req(url,token=newtoken); obj,err=parse(r); seq=items(obj) if err is None else []
        d['steps'][label]={**meta(r),'parse_error':err,'item_count':len(seq),'items':sanitize(seq)}
    if d['steps']['themes'].get('status')==200 and d['steps']['themes'].get('parse_error') is None:
        d['status']='PASS_PUBLIC_PROFILE_THEME_INVENTORY'
        d['next_step']='identify official theme(s) relevant to schools, addresses, parcels or municipal cadastro; derive only literal read routes before querying features'
    else:
        d['status']='STOP_PUBLIC_THEME_INVENTORY_UNAVAILABLE'; d['next_step']='retain five HELD schools'
    OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':d['status'],'set_profile_status':sp.get('status'),'themes_status':d['steps']['themes'].get('status'),'theme_count':d['steps']['themes'].get('item_count'),'base_layer_count':d['steps']['base_layers'].get('item_count'),'out':str(OUT)},ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
