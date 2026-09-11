from __future__ import annotations
import json,re,ssl,urllib.parse,urllib.request,urllib.error
from pathlib import Path
OUT=Path('probe-output/task199h_limeira_geo_public_probe.json')
SERVER='https://limeira.geopixel.com.br/geopixelcidades3_server'
LOGIN=SERVER+'/public/anonymousLogin'
SET_PROFILE=SERVER+'/authentication/setCurrentProfile?profileId=2'
RUNTIME_THEMES=SERVER+'/themes/getThemeByProfile?profileId=2'
UA='robo-dados-publicos/TASK199H public-runtime-theme-audit'
TARGET=re.compile(r'(?:educa|escola|creche|emei|emeief|ceief|centro infantil|endereco|endere[cç]o|imovel|im[oó]vel|lote|quadra|cadastro|predial|logradouro|equipamento|municipal|pr[oó]prio)',re.I)
SAFE=re.compile(r'(?:^id$|name|nome|title|titulo|theme|tema|layer|camada|type|tipo|url|service|servico|description|descricao|geometry|geometr|schema|table|tabela|field|campo|active|ativo|visible|visivel|public|default|order|ordem|group|grupo|permission|search|query|feature|source)',re.I)
BLOCK=re.compile(r'(?:token|authorization|password|secret|credential|email|login|cpf|user|usuario)',re.I)

def req(url,method='GET',token=None):
 h={'User-Agent':UA,'Accept':'application/json,*/*;q=0.5'}; data=None
 if method=='POST':h['Content-Type']='application/json';data=b''
 if token:h['Authorization']=token
 q=urllib.request.Request(url,headers=h,data=data,method=method)
 try:
  with urllib.request.urlopen(q,timeout=40,context=ssl.create_default_context()) as r:
   b=r.read(20_000_001)[:20_000_000]
   return {'status':int(r.status),'final_url':r.geturl(),'content_type':r.headers.get('Content-Type'),'authorization':r.headers.get('Authorization'),'body':b}
 except urllib.error.HTTPError as e:
  try:b=e.read(2_000_000)
  except Exception:b=b''
  return {'status':int(e.code),'final_url':e.geturl(),'content_type':e.headers.get('Content-Type') if e.headers else None,'authorization':e.headers.get('Authorization') if e.headers else None,'body':b,'error':f'HTTPError:{e.code}'}
 except Exception as e:return {'status':None,'error':f'{type(e).__name__}:{e}','authorization':None,'body':b''}

def meta(r):return {k:v for k,v in r.items() if k not in ('authorization','body')}
def parse(r):
 try:return json.loads((r.get('body') or b'').decode('utf-8',errors='strict')),None
 except Exception as e:return None,f'{type(e).__name__}:{e}'
def sanitize(v,depth=0):
 if depth>6:return None
 if isinstance(v,dict):
  o={}
  for k,x in v.items():
   sk=str(k)
   if BLOCK.search(sk):continue
   if isinstance(x,(dict,list)):
    y=sanitize(x,depth+1)
    if y not in (None,{},[]):o[sk]=y
   elif SAFE.search(sk) and (isinstance(x,(str,int,float,bool)) or x is None):o[sk]=x
  return o
 if isinstance(v,list):return [x for x in (sanitize(a,depth+1) for a in v[:1000]) if x not in (None,{},[])]
 return None
def seq(x):
 if isinstance(x,list):return x
 if isinstance(x,dict):
  for k in ('themes','data','content','items','result'):
   if isinstance(x.get(k),list):return x[k]
 return []
def searchable_text(x):
 try:return json.dumps(x,ensure_ascii=False)
 except:return str(x)

def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 d={'schema':'TASK199H_PUBLIC_RUNTIME_THEME_INVENTORY_V9','mode':'EPHEMERAL_BOUNDED_PUBLIC_ANONYMOUS_SESSION','credentials_supplied':False,'registration_attempted':False,'regular_login_attempted':False,'post_requests':1,'write_requests':0,'drive_writes':0,'tinyfish_used':False,'token_persisted':False,'token_logged':False,'profile':{'id':2,'profileName':'Público'},'steps':{},'status':'STOP_NOT_RUN'}
 lg=req(LOGIN,'POST');tok=lg.get('authorization');d['steps']['anonymous_login']={**meta(lg),'authorization_present':bool(tok)}
 if lg.get('status')!=200 or not tok:d['status']='STOP_ANONYMOUS_LOGIN_FAILED';OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2));print(d['status']);return 0
 sp=req(SET_PROFILE,token=tok);tok2=sp.get('authorization') or tok;d['steps']['set_current_profile']={**meta(sp),'authorization_refreshed':bool(sp.get('authorization'))}
 if sp.get('status')!=200:d['status']='STOP_SET_PUBLIC_PROFILE_FAILED';OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2));print(d['status']);return 0
 rt=req(RUNTIME_THEMES,token=tok2);obj,err=parse(rt);items=seq(obj) if err is None else [];san=sanitize(items) or []
 hits=[]
 for i,x in enumerate(san):
  if TARGET.search(searchable_text(x)):hits.append({'index':i,'theme':x})
 d['steps']['runtime_themes']={**meta(rt),'parse_error':err,'payload_type':type(obj).__name__ if obj is not None else None,'theme_count':len(items),'sanitized_theme_count':len(san),'target_hit_count':len(hits),'target_hits':hits[:200],'all_themes':san[:500]}
 if rt.get('status')==200 and err is None:
  d['status']='PASS_PUBLIC_RUNTIME_THEME_INVENTORY';d['next_step']='select exact official theme(s) relevant to five held schools and derive literal read-only feature/query contract from frontend before querying records'
 else:d['status']='STOP_RUNTIME_THEME_INVENTORY_UNAVAILABLE';d['next_step']='retain five HELD schools'
 OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':d['status'],'runtime_status':rt.get('status'),'theme_count':len(items),'target_hits':len(hits),'out':str(OUT)},ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())