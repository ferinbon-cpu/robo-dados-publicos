from __future__ import annotations
import hashlib,json,re,ssl,urllib.request
from pathlib import Path
OUT=Path('probe-output/task199h_limeira_geo_public_probe.json')
URL='https://limeira.geopixel.com.br/geopixelcidades3/assets/index-Dp9ZDG-S.js'
UA='robo-dados-publicos/TASK199H read-only feature-query-contract-trace'
ANCHORS=['getCountRowsTheme','getFeatureDescription','getFeatureDescriptionByProfileId','attributeAlias','searchText','defaultSearch','searchable','quickSearch','QuickSearch','getFeatures','featureCollection','filter:tt,extent','themeId:j,attributeAlias','featureId','CQL_FILTER','getThemeProperty']

def get():
 q=urllib.request.Request(URL,headers={'User-Agent':UA,'Accept':'application/javascript,*/*;q=0.5'},method='GET')
 with urllib.request.urlopen(q,timeout=45,context=ssl.create_default_context()) as r:
  b=r.read(16_000_001)[:16_000_000]
  return {'status':int(r.status),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()},b.decode('utf-8',errors='replace')
def contexts(s,n,maxn=80):
 out=[];p=0
 while len(out)<maxn:
  i=s.find(n,p)
  if i<0:break
  out.append(re.sub(r'\s+',' ',s[max(0,i-2500):min(len(s),i+len(n)+5000)]));p=i+len(n)
 return out

def main():
 OUT.parent.mkdir(parents=True,exist_ok=True);meta,s=get()
 quoted=[]
 for x in re.findall(r'[\"\']([^\"\'\n\r]{2,400})[\"\']',s):
  if re.search(r'(?:feature|theme|search|filter|attribute|query|count|extent|table|data)',x,re.I) and (x.startswith('/') or 'search' in x.lower() or 'feature' in x.lower() or 'theme' in x.lower()) and x not in quoted:quoted.append(x)
  if len(quoted)>=1500:break
 d={'schema':'TASK199H_FEATURE_QUERY_STATIC_CONTRACT_V10','mode':'EPHEMERAL_READ_ONLY_DECLARED_JS_ONLY','source':URL,'source_response':meta,'auth_attempted':False,'registration_attempted':False,'post_requests':0,'write_requests':0,'tinyfish_used':False,'anchors':{a:contexts(s,a) for a in ANCHORS},'route_strings':quoted,'status':'PASS_FEATURE_QUERY_STATIC_TRACE','absence_inference_allowed':False,'next_step':'execute only literal read route proven for theme 1234 and searchable Nome attribute'}
 OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':d['status'],'routes':len(quoted),'out':str(OUT)}));return 0
if __name__=='__main__':raise SystemExit(main())