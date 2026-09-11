from __future__ import annotations
import json, ssl, urllib.request, urllib.error
from pathlib import Path

OUT=Path('probe-output/task199h_limeira_geo_public_probe.json')
SERVER='https://limeira.geopixel.com.br/geopixelcidades3_server'
LOGIN=SERVER+'/public/anonymousLogin'
PROFILES=SERVER+'/authentication/getProfiles'
UA='robo-dados-publicos/TASK199H one-shot anonymous-public-profile-audit'

SAFE_KEY_WORDS=('id','name','nome','profile','perfil','label','description','descricao','application','path','public','default','active','ativo')
BLOCK_KEY_WORDS=('token','authorization','password','secret','email','login','cpf','user','usuario')

def request(url, method='GET', token=None):
    headers={'User-Agent':UA,'Accept':'application/json,*/*;q=0.5'}
    data=None
    if method=='POST':
        headers['Content-Type']='application/json'
        data=b''
    if token:
        headers['Authorization']=token
    req=urllib.request.Request(url,headers=headers,data=data,method=method)
    try:
        with urllib.request.urlopen(req,timeout=35,context=ssl.create_default_context()) as r:
            body=r.read(4_000_001)[:4_000_000]
            return {'status':int(r.status),'final_url':r.geturl(),'content_type':r.headers.get('Content-Type'),'authorization':r.headers.get('Authorization'),'body':body}
    except urllib.error.HTTPError as e:
        try: body=e.read(1_000_000)
        except Exception: body=b''
        return {'status':int(e.code),'final_url':e.geturl(),'content_type':e.headers.get('Content-Type') if e.headers else None,'authorization':e.headers.get('Authorization') if e.headers else None,'body':body,'error':f'HTTPError:{e.code}'}
    except Exception as e:
        return {'status':None,'error':f'{type(e).__name__}:{e}','authorization':None,'body':b''}

def summarize(r):
    return {k:v for k,v in r.items() if k not in ('authorization','body')}

def safe_scalar(k,v):
    lk=str(k).lower()
    if any(w in lk for w in BLOCK_KEY_WORDS): return None
    if not any(w in lk for w in SAFE_KEY_WORDS): return None
    if isinstance(v,(str,int,float,bool)) or v is None: return v
    return None

def sanitize_profile(obj):
    if not isinstance(obj,dict): return None
    out={}
    for k,v in obj.items():
        sv=safe_scalar(k,v)
        if sv is not None or (v is None and any(w in str(k).lower() for w in SAFE_KEY_WORDS)):
            out[str(k)]=sv
    return out

def extract_profiles(payload):
    if isinstance(payload,list): return [x for x in (sanitize_profile(o) for o in payload) if x]
    if isinstance(payload,dict):
        for key in ('profiles','data','content','items','result'):
            val=payload.get(key)
            if isinstance(val,list): return [x for x in (sanitize_profile(o) for o in val) if x]
        one=sanitize_profile(payload)
        return [one] if one else []
    return []

def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={
      'schema':'TASK199H_ANONYMOUS_PUBLIC_PROFILE_PROBE_V7',
      'mode':'EPHEMERAL_ONE_SHOT_PUBLIC_ANONYMOUS_SESSION',
      'server':SERVER,
      'contract_source':'DECLARED_CONFIGURATIONS_JSON_PLUS_STATIC_FRONTEND_CODE',
      'auth_kind':'PRODUCT_BUILTIN_ANONYMOUS_PUBLIC_ACCESS',
      'credentials_supplied':False,
      'registration_attempted':False,
      'regular_login_attempted':False,
      'post_requests_planned':1,
      'write_requests':0,
      'drive_writes':0,
      'tinyfish_used':False,
      'token_persisted':False,
      'token_logged':False,
      'anonymous_login':{},
      'profile_inventory':{},
      'status':'STOP_NOT_RUN'
    }

    login=request(LOGIN,'POST')
    token=login.get('authorization')
    result['anonymous_login']={**summarize(login),'authorization_present':bool(token)}
    if not (login.get('status') and 200 <= login['status'] < 300 and token):
        result['status']='STOP_ANONYMOUS_LOGIN_NOT_ESTABLISHED'
        result['next_step']='retain five HELD schools; do not infer data absence'
        OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'status':result['status'],'login_status':login.get('status'),'authorization_present':bool(token),'out':str(OUT)}))
        return 0

    prof=request(PROFILES,'GET',token=token)
    raw=prof.get('body') or b''
    parsed=None; parse_error=None
    try: parsed=json.loads(raw.decode('utf-8',errors='strict'))
    except Exception as e: parse_error=f'{type(e).__name__}:{e}'
    profiles=extract_profiles(parsed) if parse_error is None else []
    result['profile_inventory']={
      **summarize(prof),
      'json_parse_error':parse_error,
      'payload_type':type(parsed).__name__ if parsed is not None else None,
      'profile_count':len(profiles),
      'profiles':profiles[:50]
    }
    if prof.get('status') and 200 <= prof['status'] < 300 and parse_error is None:
        result['status']='PASS_ANONYMOUS_PUBLIC_PROFILE_INVENTORY'
        result['next_step']='identify the intended public GeoPortal profile from returned public profile metadata; do not select profile until unambiguous'
    else:
        result['status']='STOP_PROFILE_INVENTORY_UNAVAILABLE'
        result['next_step']='retain five HELD schools; do not infer data absence'
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':result['status'],'login_status':login.get('status'),'authorization_present':bool(token),'profiles_status':prof.get('status'),'profile_count':len(profiles),'out':str(OUT)},ensure_ascii=False))
    return 0

if __name__=='__main__': raise SystemExit(main())
