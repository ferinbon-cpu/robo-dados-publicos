from __future__ import annotations
import hashlib,json,re,ssl,urllib.request,urllib.error
from pathlib import Path
OUT=Path('probe-output/task199h_limeira_geo_public_probe.json')
URL='https://limeira.geopixel.com.br/geopixelcidades3/assets/index-Dp9ZDG-S.js'
UA='robo-dados-publicos/TASK199H read-only static-js-contract-isolation'
ANCHORS=['geopixelClient','baseURL','/button/findByThemeId','/themes/getThemeByProfile','/themes/getAllThemeConfiguration','/themes/getExtent','/themes/getDescriptionByThemeId/','window.location','location.origin','geopixelcidades3','/rest/','rest/json','axios.create','create({baseURL']

def fetch():
    q=urllib.request.Request(URL,headers={'User-Agent':UA,'Accept':'application/javascript,text/javascript,*/*;q=0.5'},method='GET')
    try:
        with urllib.request.urlopen(q,timeout=45,context=ssl.create_default_context()) as r:
            b=r.read(16_000_001); tr=len(b)>16_000_000; b=b[:16_000_000]
            return {'status':int(r.status),'bytes':len(b),'truncated':tr,'sha256':hashlib.sha256(b).hexdigest(),'body':b}
    except Exception as e:return {'status':None,'error':f'{type(e).__name__}:{e}','body':b''}

def contexts(s,needle,maxn=20):
    out=[]; start=0
    while len(out)<maxn:
        i=s.find(needle,start)
        if i<0:break
        z=re.sub(r'\s+',' ',s[max(0,i-1200):min(len(s),i+len(needle)+2200)])
        out.append(z); start=i+len(needle)
    return out

def main():
    OUT.parent.mkdir(parents=True,exist_ok=True); r=fetch(); s=(r.pop('body')).decode('utf-8',errors='replace')
    absolute=sorted(set(re.findall(r'https?://[^\"\'\\\s`]+',s)))
    quoted=[]
    for x in re.findall(r'[\"\']([^\"\'\n\r]{2,320})[\"\']',s):
        if re.search(r'(?:/themes|/theme|/button|/rest|/api|wms|wfs|geoserver|baseURL|geopixel)',x,re.I) and x not in quoted:quoted.append(x)
        if len(quoted)>=800:break
    data={'schema':'TASK199H_GEOPIXELCLIENT_STATIC_CONTRACT_V4','mode':'EPHEMERAL_READ_ONLY_DECLARED_JS_ONLY','auth_attempted':False,'registration_attempted':False,'post_requests':0,'write_requests':0,'tinyfish_used':False,'source':URL,'source_response':r,'anchors':{},'absolute_urls':absolute[:500],'relevant_quoted_strings':quoted,'status':'PASS_STATIC_CLIENT_CONTRACT_CAPTURE','absence_inference_allowed':False}
    for a in ANCHORS:data['anchors'][a]=contexts(s,a)
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':data['status'],'source_status':r.get('status'),'source_bytes':r.get('bytes'),'absolute_urls':len(absolute),'quoted':len(quoted),'out':str(OUT)},ensure_ascii=False))
    return 0
if __name__=='__main__':raise SystemExit(main())
