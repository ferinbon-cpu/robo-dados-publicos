from __future__ import annotations
import base64, binascii, json, re, ssl, struct, urllib.parse, urllib.request, urllib.error
from pathlib import Path
OUT=Path('probe-output/task199h_limeira_geo_public_probe.json')
SERVER='https://limeira.geopixel.com.br/geopixelcidades3_server'
LOGIN=SERVER+'/public/anonymousLogin'
SET_PROFILE=SERVER+'/authentication/setCurrentProfile?profileId=2'
SRID=SERVER+'/data/srid?themeId=1234'
QUICK=SERVER+'/data/quickSearch'
UA='robo-dados-publicos/TASK199H five-held-school-public-layer-probe'
SCHOOLS=[
 ('35208437','EMEIEF Ismael Pereira Lago, Pastor','Ismael Pereira Lago'),
 ('35286229','EMEIEF Maurício Sebastião Ferreira, Padre','Maurício Sebastião Ferreira'),
 ('35004773','EMEIEF Raquel Aparecida Gonçalves Franceschi, Profa.','Raquel Aparecida Gonçalves Franceschi'),
 ('35099569','CI Neusa Francisco Correa da Silva','Neusa Francisco Correa da Silva'),
 ('35241885','EMEI Theresa Veronesi D Andrea','Theresa Veronesi D Andrea'),
]

def req(url,method='GET',token=None):
 h={'User-Agent':UA,'Accept':'application/json,*/*;q=0.5'}; data=None
 if method=='POST':h['Content-Type']='application/json';data=b''
 if token:h['Authorization']=token
 q=urllib.request.Request(url,headers=h,data=data,method=method)
 try:
  with urllib.request.urlopen(q,timeout=40,context=ssl.create_default_context()) as r:
   b=r.read(10_000_001)[:10_000_000]
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

def decode_point_wkb(v):
 if not isinstance(v,str) or not v:return None
 candidates=[]
 try:candidates.append(bytes.fromhex(v))
 except Exception:pass
 try:candidates.append(base64.b64decode(v,validate=True))
 except Exception:pass
 for b in candidates:
  try:
   if len(b)<21:continue
   endian='<' if b[0]==1 else '>' if b[0]==0 else None
   if not endian:continue
   typ=struct.unpack(endian+'I',b[1:5])[0]
   base=typ & 0xFF
   # Standard POINT WKB; do not attempt EWKB/SRID reinterpretation beyond base type.
   if base!=1 and typ!=1:continue
   x,y=struct.unpack(endian+'dd',b[5:21])
   return {'geometry_type':'POINT','x':x,'y':y,'encoded_length':len(v)}
  except Exception:continue
 return {'geometry_type':'UNDECODED','encoded_length':len(v),'prefix':v[:24]}

def sanitize_fc(obj):
 if not isinstance(obj,dict):return {'payload_type':type(obj).__name__}
 desc=obj.get('description') if isinstance(obj.get('description'),dict) else {}
 attrs=[]
 for a in desc.get('attributes') or []:
  if isinstance(a,dict):attrs.append({k:a.get(k) for k in ('name','alias','type','attributeType','isPrimaryKey') if k in a})
 spat=[]
 for a in desc.get('spatialAttributes') or []:
  if isinstance(a,dict):spat.append({k:a.get(k) for k in ('name','alias','type','attributeType','srid','geometryType') if k in a})
 feats=[]
 for f in (obj.get('features') or [])[:20]:
  if not isinstance(f,dict):continue
  geoms=f.get('geometriesWKB') or f.get('geometries') or []
  if not isinstance(geoms,list):geoms=[geoms]
  feats.append({'values':f.get('values') if isinstance(f.get('values'),list) else None,'geometry_count':len(geoms),'geometry_points':[decode_point_wkb(g) for g in geoms[:4]]})
 return {'attributes':attrs,'spatial_attributes':spat,'feature_count':len(obj.get('features') or []),'features':feats}

def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 d={'schema':'TASK199H_FIVE_HELD_SCHOOL_PUBLIC_LAYER_PROBE_V11','mode':'EPHEMERAL_BOUNDED_PUBLIC_ANONYMOUS_SESSION','theme':{'id':1234,'name':'Escola Municipal','layer':'limeira:escola_municipal_limeira'},'credentials_supplied':False,'registration_attempted':False,'regular_login_attempted':False,'post_requests':1,'write_requests':0,'drive_writes':0,'tinyfish_used':False,'token_persisted':False,'token_logged':False,'queries':[],'status':'STOP_NOT_RUN'}
 lg=req(LOGIN,'POST');tok=lg.get('authorization');d['anonymous_login']={**meta(lg),'authorization_present':bool(tok)}
 if lg.get('status')!=200 or not tok:d['status']='STOP_ANONYMOUS_LOGIN_FAILED';OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2));print(d['status']);return 0
 sp=req(SET_PROFILE,token=tok);tok2=sp.get('authorization') or tok;d['set_current_profile']={**meta(sp),'authorization_refreshed':bool(sp.get('authorization'))}
 if sp.get('status')!=200:d['status']='STOP_SET_PUBLIC_PROFILE_FAILED';OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2));print(d['status']);return 0
 sr=req(SRID,token=tok2);srobj,srerr=parse(sr);d['srid']={**meta(sr),'parse_error':srerr,'value':srobj if isinstance(srobj,(str,int,float)) else None}
 for code,school,value in SCHOOLS:
  url=QUICK+'?'+urllib.parse.urlencode({'themeId':1234,'value':value,'queryExpiredData':'false'})
  r=req(url,token=tok2);obj,err=parse(r)
  d['queries'].append({'codigo_inep':code,'school':school,'query_value':value,'response':{**meta(r),'parse_error':err},'feature_collection':sanitize_fc(obj) if err is None else None})
 ok=[q for q in d['queries'] if q['response'].get('status')==200 and q.get('feature_collection') is not None]
 d['status']='PASS_FIVE_HELD_PUBLIC_LAYER_QUERIES' if len(ok)==5 else 'STOP_PARTIAL_HELD_PUBLIC_LAYER_QUERIES'
 d['next_step']='reconcile returned official point coordinates against school identities and 2022 census-sector geometry; promote only exact/strong matches' if ok else 'retain unresolved schools whose official query failed or remained ambiguous'
 OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':d['status'],'srid':d['srid'].get('value'),'query_statuses':[q['response'].get('status') for q in d['queries']],'feature_counts':[q.get('feature_collection',{}).get('feature_count') if q.get('feature_collection') else None for q in d['queries']],'out':str(OUT)},ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())