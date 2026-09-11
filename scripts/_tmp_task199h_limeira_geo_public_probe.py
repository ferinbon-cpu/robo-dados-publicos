from __future__ import annotations
import hashlib,json,re,ssl,urllib.request,urllib.error
from pathlib import Path
OUT=Path('probe-output/task199h_limeira_geo_public_probe.json')
CONFIG='https://limeira.geopixel.com.br/geopixelcidades3/configurations.json'
BUNDLE='https://limeira.geopixel.com.br/geopixelcidades3/assets/index-Dp9ZDG-S.js'
UA='robo-dados-publicos/TASK199H read-only declared-config-audit'
ANCHORS=['AuthenticationRoute','publicAuthentication','PUBLIC_AUTH','SET_CURRENT_PROFILE','GET_USER_PROFILES','PROFILES_PATH','/authentication','/profiles','getProfileThemes','getProfileBaseLayerThemes','serverPath']

def get(url,accept='*/*'):
 q=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':accept},method='GET')
 try:
  with urllib.request.urlopen(q,timeout=45,context=ssl.create_default_context()) as r:
   b=r.read(16_000_001)[:16_000_000]
   return {'status':int(r.status),'final_url':r.geturl(),'content_type':r.headers.get('Content-Type'),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()},b
 except urllib.error.HTTPError as e:
  b=e.read(1_000_000)
  return {'status':int(e.code),'final_url':e.geturl(),'content_type':e.headers.get('Content-Type') if e.headers else None,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'error':f'HTTPError:{e.code}'},b
 except Exception as e:return {'status':None,'error':f'{type(e).__name__}:{e}'},b''

def ctx(s,n,maxn=30):
 out=[]; p=0
 while len(out)<maxn:
  i=s.find(n,p)
  if i<0:break
  out.append(re.sub(r'\s+',' ',s[max(0,i-1800):min(len(s),i+len(n)+3200)]));p=i+len(n)
 return out

def main():
 OUT.parent.mkdir(parents=True,exist_ok=True)
 cm,cb=get(CONFIG,'application/json,*/*;q=0.5'); cs=cb.decode('utf-8',errors='replace')
 config_payload=None
 try:
  x=json.loads(cs)
  if isinstance(x,dict):
   config_payload={'type':'object','keys':sorted(map(str,x.keys())),'serverPath':x.get('serverPath'),'sanitized':{k:v for k,v in x.items() if not re.search(r'(?:secret|password|token|key)',str(k),re.I)}}
  else:config_payload={'type':type(x).__name__,'repr_prefix':repr(x)[:5000]}
 except Exception as e:config_payload={'parse_error':f'{type(e).__name__}:{e}','text_prefix':cs[:3000]}
 bm,bb=get(BUNDLE,'application/javascript,*/*;q=0.5'); s=bb.decode('utf-8',errors='replace')
 route_strings=[]
 for q in re.findall(r'[\"\']([^\"\'\n\r]{2,300})[\"\']',s):
  if re.search(r'(?:authentication|profiles?|publicAuth|themes/getThemeByProfile|serverPath)',q,re.I) and q not in route_strings:route_strings.append(q)
  if len(route_strings)>=1000:break
 d={'schema':'TASK199H_DECLARED_CONFIG_AND_PUBLIC_ROUTE_TRACE_V6','mode':'EPHEMERAL_READ_ONLY_DECLARED_RESOURCES','auth_attempted':False,'registration_attempted':False,'post_requests':0,'write_requests':0,'tinyfish_used':False,'configuration_url':CONFIG,'configuration_response':cm,'configuration_payload':config_payload,'bundle_response':bm,'anchors':{a:ctx(s,a) for a in ANCHORS},'route_strings':route_strings,'status':'PASS_DECLARED_CONFIGURATION_READ' if cm.get('status')==200 and isinstance(config_payload,dict) and not config_payload.get('parse_error') else 'STOP_CONFIGURATION_UNAVAILABLE','absence_inference_allowed':False,'next_step':'derive exact anonymous/public GET sequence from code and serverPath before execution'}
 OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':d['status'],'config_status':cm.get('status'),'serverPath':(config_payload or {}).get('serverPath'),'route_strings':len(route_strings),'out':str(OUT)},ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())