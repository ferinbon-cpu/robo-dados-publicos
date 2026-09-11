from __future__ import annotations
import hashlib,json,re,ssl,urllib.request
from pathlib import Path
OUT=Path('probe-output/task199h_limeira_geo_public_probe.json')
URL='https://limeira.geopixel.com.br/geopixelcidades3/assets/index-Dp9ZDG-S.js'
UA='robo-dados-publicos/TASK199H read-only configuration-contract-isolation'
ANCHORS=['ConfigurationReader','readStringConfiguration','serverPath','getServerProxyUrl','serverProxy','configuration.json','config.json','runtime-config','environment','AUTHENTICATION_PUBLIC_KEY','ConfigurationParameter','readConfiguration','retrievePublicKey']

def get():
 q=urllib.request.Request(URL,headers={'User-Agent':UA,'Accept':'application/javascript,*/*;q=0.5'},method='GET')
 with urllib.request.urlopen(q,timeout=45,context=ssl.create_default_context()) as r:
  b=r.read(16_000_001)[:16_000_000]
  return {'status':int(r.status),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()},b.decode('utf-8',errors='replace')

def ctx(s,n,maxn=50):
 out=[]; p=0
 while len(out)<maxn:
  i=s.find(n,p)
  if i<0:break
  out.append(re.sub(r'\s+',' ',s[max(0,i-1800):min(len(s),i+len(n)+3200)])); p=i+len(n)
 return out

def main():
 OUT.parent.mkdir(parents=True,exist_ok=True); meta,s=get()
 strings=[]
 for x in re.findall(r'[\"\']([^\"\'\n\r]{2,500})[\"\']',s):
  if re.search(r'(?:serverPath|configuration|config(?:uration)?\.json|proxy|public.?key|environment|geopixelcidades3|\.json$)',x,re.I) and x not in strings:strings.append(x)
  if len(strings)>=1000:break
 d={'schema':'TASK199H_SERVERPATH_STATIC_CONFIG_TRACE_V5','mode':'EPHEMERAL_READ_ONLY_DECLARED_JS_ONLY','auth_attempted':False,'registration_attempted':False,'post_requests':0,'write_requests':0,'tinyfish_used':False,'source':URL,'source_response':meta,'anchors':{a:ctx(s,a) for a in ANCHORS},'relevant_strings':strings,'status':'PASS_SERVERPATH_CONFIG_TRACE_COMPLETE','absence_inference_allowed':False,'next_step':'derive exact configuration resource from literal code before any GET'}
 OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps({'status':d['status'],'strings':len(strings),'out':str(OUT)})); return 0
if __name__=='__main__':raise SystemExit(main())