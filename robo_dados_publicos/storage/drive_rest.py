"""Google Drive REST client without third-party packages.

Secrets are never stored in source code. Use environment variables:
GOOGLE_DRIVE_CLIENT_ID, GOOGLE_DRIVE_CLIENT_SECRET, GOOGLE_DRIVE_REFRESH_TOKEN.

This module is designed for an external Python runtime. It is separate from the
ChatGPT Drive connector used during development.
"""
from dataclasses import dataclass
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode, quote
from urllib.error import HTTPError
import json, os, time, hashlib, uuid, subprocess

TOKEN_URL = "https://oauth2.googleapis.com/token"
DRIVE_API = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD = "https://www.googleapis.com/upload/drive/v3"

@dataclass(frozen=True)
class OAuthCredentials:
    client_id: str
    client_secret: str
    refresh_token: str

    @classmethod
    def from_env(cls):
        vals={
            "client_id":os.getenv("GOOGLE_DRIVE_CLIENT_ID","").strip(),
            "client_secret":os.getenv("GOOGLE_DRIVE_CLIENT_SECRET","").strip(),
            "refresh_token":os.getenv("GOOGLE_DRIVE_REFRESH_TOKEN","").strip(),
        }
        missing=[k for k,v in vals.items() if not v]
        if missing:
            raise RuntimeError("credenciais OAuth ausentes: " + ", ".join(missing))
        return cls(**vals)

class TokenProvider:
    def __init__(self, credentials: OAuthCredentials, opener=urlopen):
        self.credentials=credentials; self.opener=opener
        self._token=None; self._expires_at=0.0

    def access_token(self):
        if self._token and time.time() < self._expires_at - 60:
            return self._token
        body=urlencode({
            "client_id":self.credentials.client_id,
            "client_secret":self.credentials.client_secret,
            "refresh_token":self.credentials.refresh_token,
            "grant_type":"refresh_token",
        }).encode()
        req=Request(TOKEN_URL,data=body,headers={"Content-Type":"application/x-www-form-urlencoded"},method="POST")
        try:
            with self.opener(req,timeout=30) as resp:
                data=json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            # Expose only Google's public OAuth error code/description. Never
            # include the request body or any credential value in CI logs.
            try:
                payload=json.loads(exc.read().decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                payload={}
            error=str(payload.get("error") or "oauth_http_error")
            description=str(payload.get("error_description") or "")
            detail=f": {description}" if description else ""
            raise RuntimeError(f"Google OAuth token exchange failed ({error}){detail}") from exc
        self._token=data["access_token"]
        self._expires_at=time.time()+int(data.get("expires_in",3600))
        return self._token



class EnvironmentAccessTokenProvider:
    """Short-lived bearer token supplied by the execution environment.

    Useful for controlled bridges where a scheduler provides a fresh user OAuth
    token at runtime. The token is never written to disk by this provider.
    """
    def __init__(self, env_var="GOOGLE_DRIVE_ACCESS_TOKEN"):
        self.env_var=env_var

    def access_token(self):
        token=os.getenv(self.env_var, "").strip()
        if not token:
            raise RuntimeError(f"access token ausente em {self.env_var}")
        return token


class GcloudTokenProvider:
    """Access token provider for Google Cloud Shell / gcloud-authenticated runtimes.

    Uses the active account from `gcloud auth print-access-token`. This lets the
    robot run online without storing OAuth client secrets or refresh tokens in
    the project directory.
    """
    def __init__(self, runner=subprocess.run, cache_seconds=240):
        self.runner=runner
        self.cache_seconds=cache_seconds
        self._token=None
        self._expires_at=0.0

    def access_token(self):
        if self._token and time.time() < self._expires_at:
            return self._token
        cp=self.runner(
            ["gcloud","auth","print-access-token"],
            capture_output=True,text=True,check=True,
        )
        token=cp.stdout.strip()
        if not token:
            raise RuntimeError("gcloud não retornou access token")
        self._token=token
        self._expires_at=time.time()+self.cache_seconds
        return token

class DriveRESTClient:
    def __init__(self, token_provider: TokenProvider, opener=urlopen):
        self.tokens=token_provider; self.opener=opener

    def _request(self,url,method="GET",data=None,headers=None,timeout=60):
        hdr={"Authorization":f"Bearer {self.tokens.access_token()}"}
        hdr.update(headers or {})
        req=Request(url,data=data,headers=hdr,method=method)
        return self.opener(req,timeout=timeout)

    def list_children(self,parent_id):
        q=f"'{parent_id}' in parents and trashed = false"
        params=urlencode({"q":q,"pageSize":"1000","fields":"files(id,name,mimeType,size,modifiedTime,md5Checksum,parents),nextPageToken"})
        out=[]; token=None
        while True:
            url=f"{DRIVE_API}/files?{params}" + ("&pageToken="+quote(token) if token else "")
            with self._request(url) as resp: data=json.loads(resp.read().decode())
            out.extend(data.get("files",[])); token=data.get("nextPageToken")
            if not token: return out

    def find_by_name(self,parent_id,name):
        return [x for x in self.list_children(parent_id) if x.get("name")==name]

    def get(self,file_id,destination):
        dest=Path(destination); dest.parent.mkdir(parents=True,exist_ok=True)
        h=hashlib.sha256(); total=0
        with self._request(f"{DRIVE_API}/files/{quote(file_id)}?alt=media") as resp, dest.open("wb") as f:
            while True:
                block=resp.read(1024*1024)
                if not block: break
                f.write(block); h.update(block); total += len(block)
        return {"file_id":file_id,"path":str(dest),"bytes":total,"sha256":h.hexdigest()}

    def put(self,local_path,remote_name,parent_id=None,mime_type="application/octet-stream"):
        p=Path(local_path)
        boundary="===============%s==" % uuid.uuid4().hex
        meta={"name":remote_name}
        if parent_id: meta["parents"]=[parent_id]
        metadata=json.dumps(meta,ensure_ascii=False).encode("utf-8")
        content=p.read_bytes()
        body=(
            f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode()+metadata+
            f"\r\n--{boundary}\r\nContent-Type: {mime_type}\r\n\r\n".encode()+content+
            f"\r\n--{boundary}--\r\n".encode()
        )
        headers={"Content-Type":f"multipart/related; boundary={boundary}"}
        with self._request(f"{DRIVE_UPLOAD}/files?uploadType=multipart&fields=id,name,mimeType,size,parents",method="POST",data=body,headers=headers,timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def metadata(self,file_id):
        fields="id,name,mimeType,size,modifiedTime,md5Checksum,parents,trashed"
        with self._request(f"{DRIVE_API}/files/{quote(file_id)}?fields={quote(fields)}") as resp:
            return json.loads(resp.read().decode("utf-8"))

    def delete(self,file_id):
        with self._request(f"{DRIVE_API}/files/{quote(file_id)}",method="DELETE") as resp:
            resp.read()
        return {"file_id":file_id,"deleted":True}

    def replace_content(self,file_id,local_path,mime_type="application/octet-stream"):
        data=Path(local_path).read_bytes()
        headers={"Content-Type":mime_type}
        with self._request(f"{DRIVE_UPLOAD}/files/{quote(file_id)}?uploadType=media&fields=id,name,mimeType,size,parents",method="PATCH",data=data,headers=headers,timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
