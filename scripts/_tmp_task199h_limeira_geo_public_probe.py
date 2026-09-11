from __future__ import annotations

import hashlib
import html.parser
import http.cookiejar
import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path("probe-output/task199h_limeira_geo_public_probe.json")
UA = "robo-dados-publicos/TASK199H read-only public-geoportal-audit"
MAX_BODY = 16_000_000
ALLOWED_HOSTS = {"limeira.geoportal.geopixel.com.br", "limeira.geopixel.com.br"}
NEW_ROOT = "https://limeira.geoportal.geopixel.com.br/"
NEW_PAGES = "https://limeira.geoportal.geopixel.com.br/api/pages"
OLD_ROOT = "https://limeira.geopixel.com.br/geopixelcidades3/"
RELEVANT_CHUNK = re.compile(r"(?:api|map|layer|theme|search|address|property|parcel|feature|geo|query|identify|localiz|endereco|imovel|cadastro)", re.I)
JS_REF_RE = re.compile(r"[\"'](\./[^\"']+?\.js)[\"']")
PATH_RE = re.compile(r"[\"']((?:/api|/rest|/geoserver|/ows|/wms|/wfs)/[^\"']*)[\"']", re.I)
ABS_RE = re.compile(r"https://(?:limeira\.geoportal\.geopixel\.com\.br|limeira\.geopixel\.com\.br)/[^\"'\\\s]+", re.I)
NETWORK_RE = re.compile(r"(?:axios|fetch\s*\(|\.get\s*\(|\.post\s*\(|baseURL|withCredentials|wms|wfs|geoserver|feature|layer|theme|address|endereco|imovel|parcel|identify)", re.I)

class AssetParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.scripts=[]; self.links=[]
    def handle_starttag(self, tag, attrs):
        d=dict(attrs)
        if tag.lower()=="script" and d.get("src"): self.scripts.append(d["src"])
        if tag.lower()=="link" and d.get("href"): self.links.append(d["href"])


def cookie_names(headers) -> list[str]:
    out=[]
    if not headers: return out
    for raw in headers.get_all("Set-Cookie") or []:
        name=raw.split("=",1)[0].strip()
        if name and name not in out: out.append(name)
    return out


def make_opener():
    jar=http.cookiejar.CookieJar()
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    return opener, jar


def fetch(opener, url: str, limit: int=MAX_BODY) -> dict:
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"text/html,application/json,text/javascript,application/javascript,*/*;q=0.5"}, method="GET")
    row={"requested_url":url}
    try:
        with opener.open(req, timeout=40) as resp:
            body=resp.read(limit+1); truncated=len(body)>limit; body=body[:limit]
            row.update(status=int(resp.status), final_url=resp.geturl(), content_type=resp.headers.get("Content-Type"), content_length_header=resp.headers.get("Content-Length"), bytes_captured=len(body), truncated=truncated, sha256_captured=hashlib.sha256(body).hexdigest(), set_cookie_names=cookie_names(resp.headers), body=body)
    except urllib.error.HTTPError as exc:
        try: body=exc.read(limit+1)
        except Exception: body=b""
        body=body[:limit]
        row.update(status=int(exc.code), final_url=exc.geturl(), content_type=exc.headers.get("Content-Type") if exc.headers else None, bytes_captured=len(body), truncated=False, sha256_captured=hashlib.sha256(body).hexdigest(), set_cookie_names=cookie_names(exc.headers), error=f"HTTPError:{exc.code}", body=body)
    except Exception as exc:
        row.update(status=None,error=f"{type(exc).__name__}:{exc}",body=b"")
    return row


def text(body: bytes)->str: return body.decode("utf-8",errors="replace")
def summary(row: dict)->dict: return {k:v for k,v in row.items() if k!="body"}

def safe_url(base: str, raw: str):
    u=urllib.parse.urljoin(base,raw)
    p=urllib.parse.urlparse(u)
    if p.scheme!="https" or p.hostname not in ALLOWED_HOSTS or p.username or p.password: return None
    return urllib.parse.urlunparse((p.scheme,p.netloc,p.path,"",p.query,""))

def snippets(s: str, limit=80):
    out=[]
    for m in NETWORK_RE.finditer(s):
        a=max(0,m.start()-220); b=min(len(s),m.end()+500)
        z=re.sub(r"\s+"," ",s[a:b])
        if z not in out: out.append(z)
        if len(out)>=limit: break
    return out

def payload_shape(row: dict):
    b=row.get("body") or b""; s=text(b)
    if not b: return None
    if "json" not in (row.get("content_type") or "").lower() and not s.lstrip().startswith(("{","[")): return {"text_prefix":s[:1200]}
    try: x=json.loads(s)
    except Exception as e: return {"json_parse_error":f"{type(e).__name__}:{e}","text_prefix":s[:1200]}
    if isinstance(x,dict): return {"type":"object","keys":sorted(map(str,x.keys()))[:200],"repr_prefix":json.dumps(x,ensure_ascii=False)[:6000]}
    if isinstance(x,list): return {"type":"array","length":len(x),"repr_prefix":json.dumps(x[:8],ensure_ascii=False)[:6000]}
    return {"type":type(x).__name__,"repr_prefix":repr(x)[:2000]}


def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    result={"schema":"TASK199H_LIMEIRA_GEO_PUBLIC_PROBE_V2","mode":"EPHEMERAL_READ_ONLY_GITHUB_ACTIONS","auth_attempted":False,"registration_attempted":False,"post_requests":0,"write_requests":0,"tinyfish_used":False,"session_probe":{},"roots":[],"declared_assets":[],"relevant_lazy_chunks":[],"chunk_findings":[],"candidate_literal_get_paths":[],"candidate_get_responses":[]}

    # New GeoPortal: preserve a public anonymous cookie/session from root into /api/pages.
    op_new, jar_new=make_opener()
    root_new=fetch(op_new,NEW_ROOT); pages=fetch(op_new,NEW_PAGES,4_000_000)
    result["session_probe"]={"root":summary(root_new),"cookie_names_after_root":sorted({c.name for c in jar_new}),"pages":summary(pages),"pages_payload":payload_shape(pages)}

    # Old viewer root and all scripts directly declared by HTML.
    op_old, jar_old=make_opener(); old=fetch(op_old,OLD_ROOT)
    result["roots"]=[summary(root_new),summary(old)]
    declared=[]
    for base,row in [(NEW_ROOT,root_new),(OLD_ROOT,old)]:
        if row.get("status")!=200: continue
        p=AssetParser(); p.feed(text(row.get("body") or b""))
        urls=[]
        for raw in p.scripts:
            u=safe_url(base,raw)
            if u and u not in urls: urls.append(u)
        result["declared_assets"].append({"source":base,"scripts":p.scripts,"resolved":urls})
        declared.extend(urls)

    # Read declared bundles, then discover lazy JS chunk names literally listed by those bundles.
    lazy=[]; asset_rows=[]
    for u in dict.fromkeys(declared):
        r=fetch(op_new if urllib.parse.urlparse(u).hostname=="limeira.geoportal.geopixel.com.br" else op_old,u)
        asset_rows.append((u,r))
        s=text(r.get("body") or b"")
        for rel in JS_REF_RE.findall(s):
            if not RELEVANT_CHUNK.search(rel): continue
            x=safe_url(u,rel)
            if x and x not in lazy: lazy.append(x)
        # Main bundles themselves may carry network contracts.
        result["chunk_findings"].append({**summary(r),"network_snippets":snippets(s,35),"literal_paths":sorted(set(PATH_RE.findall(s)))[:200],"absolute_urls":sorted(set(ABS_RE.findall(s)))[:100]})

    result["relevant_lazy_chunks"]=lazy[:120]
    literal_candidates=set()
    # Fetch only semantically named lazy chunks declared by the public main bundles.
    for u in lazy[:120]:
        r=fetch(op_old if urllib.parse.urlparse(u).hostname=="limeira.geopixel.com.br" else op_new,u,8_000_000)
        s=text(r.get("body") or b"")
        paths=sorted(set(PATH_RE.findall(s)))
        absurls=sorted(set(ABS_RE.findall(s)))
        result["chunk_findings"].append({**summary(r),"network_snippets":snippets(s,40),"literal_paths":paths[:200],"absolute_urls":absurls[:100]})
        for raw in paths:
            x=safe_url(u,raw)
            if x: literal_candidates.add(x)
        for x in absurls:
            y=safe_url(u,x)
            if y: literal_candidates.add(y)

    # Also include the known public /api/pages route; GET only, no guessed parameterized actions.
    literal_candidates.add(NEW_PAGES)
    result["candidate_literal_get_paths"]=sorted(literal_candidates)
    for u in sorted(literal_candidates)[:80]:
        # Avoid obvious mutation/auth paths even under GET probing.
        if re.search(r"(?:login|logout|auth|register|signup|delete|remove|update|create|save|insert|edit)",u,re.I): continue
        op=op_new if urllib.parse.urlparse(u).hostname=="limeira.geoportal.geopixel.com.br" else op_old
        r=fetch(op,u,3_000_000)
        result["candidate_get_responses"].append({**summary(r),"payload":payload_shape(r)})

    good=[r for r in result["candidate_get_responses"] if isinstance(r.get("status"),int) and 200<=r["status"]<300]
    result["status"]="PASS_PUBLIC_DATA_ENDPOINT_FOUND" if good else "STOP_NO_USABLE_PUBLIC_DATA_ENDPOINT_FOUND"
    result["absence_inference_allowed"]=False
    result["next_step"]="inspect successful public payloads for official point/parcel/layer evidence" if good else "retain five HELD schools; inspect contract snippets before any further probe"
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"status":result["status"],"good_endpoints":len(good),"lazy_chunks":len(lazy),"out":str(OUT)},ensure_ascii=False))
    return 0

if __name__=="__main__": raise SystemExit(main())
