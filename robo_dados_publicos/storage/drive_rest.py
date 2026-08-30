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
SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"

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

    def import_formats(self):
        """Return Drive's live import-format matrix.

        Google documents this matrix as dynamic. The product-publication gate
        therefore proves the requested import conversion before any write.
        """
        fields=quote("importFormats")
        with self._request(f"{DRIVE_API}/about?fields={fields}") as resp:
            data=json.loads(resp.read().decode("utf-8"))
        formats=data.get("importFormats") or {}
        if not isinstance(formats,dict):
            raise RuntimeError("STOP_DRIVE_IMPORT_FORMATS_INVALID")
        return formats

    def get(self,file_id,destination):
        dest=Path(destination); dest.parent.mkdir(parents=True,exist_ok=True)
        h=hashlib.sha256(); total=0
        with self._request(f"{DRIVE_API}/files/{quote(file_id)}?alt=media") as resp, dest.open("wb") as f:
            while True:
                block=resp.read(1024*1024)
                if not block: break
                f.write(block); h.update(block); total += len(block)
        return {"file_id":file_id,"path":str(dest),"bytes":total,"sha256":h.hexdigest()}

    def export(self,file_id,destination,mime_type):
        """Export one Google Workspace file through Drive's read-only export API."""
        if not str(mime_type).strip():
            raise ValueError("EXPORT_MIME_TYPE_REQUIRED")
        dest=Path(destination); dest.parent.mkdir(parents=True,exist_ok=True)
        h=hashlib.sha256(); total=0
        params=urlencode({"mimeType":mime_type})
        url=f"{DRIVE_API}/files/{quote(file_id)}/export?{params}"
        with self._request(url) as resp, dest.open("wb") as f:
            while True:
                block=resp.read(1024*1024)
                if not block: break
                f.write(block); h.update(block); total += len(block)
        return {"file_id":file_id,"path":str(dest),"bytes":total,"sha256":h.hexdigest(),"mime_type":mime_type}

    def _multipart_create(self,local_path,remote_name,parent_id,mime_type,metadata_mime_type=None):
        p=Path(local_path)
        boundary="===============%s==" % uuid.uuid4().hex
        meta={"name":remote_name}
        if parent_id: meta["parents"]=[parent_id]
        if metadata_mime_type: meta["mimeType"]=metadata_mime_type
        metadata=json.dumps(meta,ensure_ascii=False).encode("utf-8")
        content=p.read_bytes()
        body=(
            f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n".encode()+metadata+
            f"\r\n--{boundary}\r\nContent-Type: {mime_type}\r\n\r\n".encode()+content+
            f"\r\n--{boundary}--\r\n".encode()
        )
        headers={"Content-Type":f"multipart/related; boundary={boundary}"}
        fields="id,name,mimeType,size,parents,md5Checksum"
        with self._request(f"{DRIVE_UPLOAD}/files?uploadType=multipart&fields={fields}",method="POST",data=body,headers=headers,timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def put(self,local_path,remote_name,parent_id=None,mime_type="application/octet-stream"):
        return self._multipart_create(local_path,remote_name,parent_id,mime_type)

    def put_converted(self,local_path,remote_name,parent_id,source_mime_type,target_mime_type):
        """Create a Google Workspace file by importing local media.

        Existing files are never updated by this method. Callers are expected
        to validate the provider's live importFormats matrix first.
        """
        if not parent_id:
            raise ValueError("PARENT_ID_REQUIRED_FOR_CONVERSION")
        if not source_mime_type or not target_mime_type:
            raise ValueError("SOURCE_AND_TARGET_MIME_REQUIRED")
        return self._multipart_create(
            local_path,
            remote_name,
            parent_id,
            source_mime_type,
            metadata_mime_type=target_mime_type,
        )

    def create_google_sheet(self,remote_name,parent_id):
        """Create an empty Sheet without importing locale-sensitive CSV media."""
        if not parent_id:
            raise ValueError("PARENT_ID_REQUIRED_FOR_SHEET")
        metadata=json.dumps({
            "name":remote_name,
            "parents":[parent_id],
            "mimeType":"application/vnd.google-apps.spreadsheet",
        },ensure_ascii=False).encode("utf-8")
        headers={"Content-Type":"application/json; charset=UTF-8"}
        fields="id,name,mimeType,parents"
        with self._request(f"{DRIVE_API}/files?fields={fields}",method="POST",data=metadata,headers=headers) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def sheets_values_update_raw(self,spreadsheet_id,range_a1,values):
        """Write an explicit matrix with RAW semantics through Sheets API."""
        params=urlencode({"valueInputOption":"RAW","includeValuesInResponse":"false"})
        payload=json.dumps({"range":range_a1,"majorDimension":"ROWS","values":values},ensure_ascii=False).encode("utf-8")
        headers={"Content-Type":"application/json; charset=UTF-8"}
        url=f"{SHEETS_API}/{quote(spreadsheet_id)}/values/{quote(range_a1,safe='')}?{params}"
        with self._request(url,method="PUT",data=payload,headers=headers) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def sheets_values_get(self,spreadsheet_id,range_a1):
        """Read unformatted values for exact semantic verification."""
        params=urlencode({"majorDimension":"ROWS","valueRenderOption":"UNFORMATTED_VALUE","dateTimeRenderOption":"FORMATTED_STRING"})
        url=f"{SHEETS_API}/{quote(spreadsheet_id)}/values/{quote(range_a1,safe='')}?{params}"
        with self._request(url) as resp:
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
