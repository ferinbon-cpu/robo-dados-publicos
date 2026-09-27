from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import hashlib, os, tempfile

@dataclass(frozen=True)
class FetchResult:
    status: str
    http_status: int
    url: str
    path: str | None = None
    sha256: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    content_type: str | None = None
    bytes_written: int = 0

class HttpSourceConnector:
    def __init__(self, user_agent="ROBO_DADOS_PUBLICOS/0.2"):
        self.user_agent = user_agent

    def download(self, url, destination, etag=None, last_modified=None, timeout=60):
        headers={"User-Agent":self.user_agent}
        if etag: headers["If-None-Match"] = etag
        if last_modified: headers["If-Modified-Since"] = last_modified
        req=Request(url, headers=headers, method="GET")
        dest=Path(destination)
        dest.parent.mkdir(parents=True,exist_ok=True)
        try:
            resp=urlopen(req, timeout=timeout)
        except HTTPError as e:
            if e.code == 304:
                return FetchResult("NOT_MODIFIED",304,url,etag=etag,last_modified=last_modified)
            raise
        with resp:
            status=getattr(resp,"status",200) or 200
            new_etag=resp.headers.get("ETag")
            new_lm=resp.headers.get("Last-Modified")
            ctype=resp.headers.get("Content-Type")
            h=hashlib.sha256(); total=0
            fd,tmp=tempfile.mkstemp(prefix=dest.name+".",suffix=".part",dir=str(dest.parent))
            try:
                with os.fdopen(fd,"wb") as f:
                    while True:
                        block=resp.read(1024*1024)
                        if not block: break
                        f.write(block); h.update(block); total += len(block)
                os.replace(tmp,dest)
            except Exception:
                try: os.unlink(tmp)
                except FileNotFoundError: pass
                raise
        return FetchResult("DOWNLOADED",status,url,str(dest),h.hexdigest(),new_etag,new_lm,ctype,total)
