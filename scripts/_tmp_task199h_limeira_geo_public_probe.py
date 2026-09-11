from __future__ import annotations
import base64,json,math,ssl,struct,urllib.parse,urllib.request,urllib.error
from pathlib import Path
OUT=Path('probe-output/task199h_limeira_geo_public_probe.json')
SERVER='https://limeira.geopixel.com.br/geopixelcidades3_server'
LOGIN=SERVER+'/public/anonymousLogin'; SET_PROFILE=SERVER+'/authentication/setCurrentProfile?profileId=2'; QUICK=SERVER+'/data/quickSearch'
UA='robo-dados-publicos/TASK199H official-school-point-recovery'
QUERIES={
 '35208437':['Ismael Pereira Lago'],
 '35286229':['Maurício Sebastião Ferreira'],
 '35004773':['Raquel','Franceschi','Gonçalves Franceschi'],
 '35099569':['Neusa Francisco Correa da Silva'],
 '35241885':['Theresa','Veronesi','D Andrea','Theresa Veronesi'],
}
NAMES={
 '35208437':'EMEIEF Ismael Pereira Lago, Pastor','35286229':'EMEIEF Maurício Sebastião Ferreira, Padre','35004773':'EMEIEF Raquel Aparecida Gonçalves Franceschi, Profa.','35099569':'CI Neusa Francisco Correa da Silva','35241885':'EMEI Theresa Veronesi D Andrea'}

def req(url,method='GET',token=None):
 h={'User-Agent':UA,'Accept':'application/json,*/*;q=0.5'};data=None
 if method=='POST':h['Content-Type']='application/json';data=b''
 if token:h['Authorization']=token
 q=urllib.request.Request(url,headers=h,data=data,method=method)
 try:
  with urllib.request.urlopen(q,timeout=40,context=ssl.create_default_context()) as r:
   b=r.read(10_000_001)[:10_000_000];return {'status':int(r.status),'authorization':r.headers.get('Authorization'),'body':b}
 except urllib.error.HTTPError as e:
  try:b=e.read(2_000_000)
  except Exception:b=b''
  return {'status':int(e.code),'authorization':e.headers.get('Authorization') if e.headers else None,'body':b,'error':f'HTTPError:{e.code}'}
 except Exception as e:return {'status':None,'authorization':None,'body':b'','error':f'{type(e).__name__}:{e}'}
def parse(r):
 try:return json.loads((r.get('body') or b'').decode('utf-8')),None
 except Exception as e:return None,f'{type(e).__name__}:{e}'

def ewkb_read(buf,off=0):
 if off+5>len(buf):raise ValueError('short geometry')
 endian='<' if buf[off]==1 else '>'; off+=1
 typ=struct.unpack_from(endian+'I',buf,off)[0];off+=4
 has_z=bool(typ&0x80000000);has_m=bool(typ&0x40000000);has_srid=bool(typ&0x20000000);base=typ&0xFF
 srid=None
 if has_srid:srid=struct.unpack_from(endian+'I',buf,off)[0];off+=4
 dims=2+int(has_z)+int(has_m)
 if base==1:
  vals=struct.unpack_from(endian+('d'*dims),buf,off);off+=8*dims
  return {'type':'POINT','srid':srid,'x':vals[0],'y':vals[1]},off
 if base==4:
  n=struct.unpack_from(endian+'I',buf,off)[0];off+=4;pts=[]
  for _ in range(n):
   g,off=ewkb_read(buf,off);pts.append(g)
  return {'type':'MULTIPOINT','srid':srid,'points':pts},off
 return {'type':f'UNSUPPORTED_{base}','srid':srid},off

def decode(v):
 if not isinstance(v,str):return None
 try:b=bytes.fromhex(v)
 except Exception:
  try:b=base64.b64decode(v,validate=True)
  except Exception:return {'error':'encoding_unknown'}
 try:g,_=ewkb_read(b)
 except Exception as e:return {'error':f'{type(e).__name__}:{e}','encoded_length':len(v)}
 pts=g.get('points') if g.get('type')=='MULTIPOINT' else [g] if g.get('type')=='POINT' else []
 out=[]
 for p in pts:
  x,y=p.get('x'),p.get('y');sr=p.get('srid') or g.get('srid')
  row={'x':x,'y':y,'srid':sr}
  if sr==3857 and isinstance(x,(int,float)) and isinstance(y,(int,float)):
   R=6378137.0;row['lon']=x/R*180/math.pi;row['lat']=(2*math.atan(math.exp(y/R))-math.pi/2)*180/math.pi
  out.append(row)
 return {'type':g.get('type'),'srid':g.get('srid'),'points':out}

def clean_fc(obj):
 if not isinstance(obj,dict):return {'feature_count':0}
 desc=obj.get('description') if isinstance(obj.get('description'),dict) else {}
 attrs=[{'name':a.get('name'),'alias':a.get('alias'),'isPrimaryKey':a.get('isPrimaryKey')} for a in (desc.get('attributes') or []) if isinstance(a,dict)]
 feats=[]
 for f in (obj.get('features') or [])[:20]:
  if not isinstance(f,dict):continue
  gs=f.get('geometriesWKB') or []
  feats.append({'values':f.get('values'),'geometries':[decode(x) for x in gs[:4]]})
 return {'attributes':attrs,'feature_count':len(obj.get('features') or []),'features':feats}

def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 d={'schema':'TASK199H_OFFICIAL_SCHOOL_POINT_RECOVERY_V12','mode':'EPHEMERAL_BOUNDED_PUBLIC_ANONYMOUS_SESSION','theme':{'id':1234,'name':'Escola Municipal','srid':3857},'credentials_supplied':False,'registration_attempted':False,'regular_login_attempted':False,'post_requests':1,'write_requests':0,'drive_writes':0,'tinyfish_used':False,'token_persisted':False,'token_logged':False,'schools':[],'status':'STOP_NOT_RUN'}
 lg=req(LOGIN,'POST');tok=lg.get('authorization')
 if lg.get('status')!=200 or not tok:d['status']='STOP_ANONYMOUS_LOGIN_FAILED';OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2));print(d['status']);return 0
 sp=req(SET_PROFILE,token=tok);tok2=sp.get('authorization') or tok
 if sp.get('status')!=200:d['status']='STOP_SET_PUBLIC_PROFILE_FAILED';OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2));print(d['status']);return 0
 for code,variants in QUERIES.items():
  row={'codigo_inep':code,'school':NAMES[code],'attempts':[],'selected':None}
  for value in variants:
   url=QUICK+'?'+urllib.parse.urlencode({'themeId':1234,'value':value,'queryExpiredData':'false'})
   r=req(url,token=tok2);obj,err=parse(r);fc=clean_fc(obj) if err is None else None
   att={'query_value':value,'status':r.get('status'),'parse_error':err,'feature_collection':fc}
   row['attempts'].append(att)
   if r.get('status')==200 and fc and fc.get('feature_count')==1:
    row['selected']=att;break
  d['schools'].append(row)
 selected=sum(1 for r in d['schools'] if r['selected'])
 d['status']='PASS_ALL_FIVE_OFFICIAL_SCHOOL_POINTS' if selected==5 else 'PASS_PARTIAL_OFFICIAL_SCHOOL_POINTS'
 d['selected_count']=selected
 d['next_step']='reconcile each selected municipal point to 2022 census sector using official geometry/CNEFE spatial evidence; no promotion for unresolved identity or geometry'
 OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':d['status'],'selected_count':selected,'selected_queries':{r['codigo_inep']:(r['selected'] or {}).get('query_value') for r in d['schools']},'out':str(OUT)},ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())