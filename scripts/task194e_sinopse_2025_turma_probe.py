from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "config/task194e_sinopse_2025_turma_recovery.v1.json"
NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


class Task194EStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task194EStop(code)


def _norm(text: Any) -> str:
    raw = str(text or "")
    raw = unicodedata.normalize("NFKD", raw)
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", raw).strip().casefold()


def _load(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK194E_SINOPSE_2025_TURMA_RECOVERY_V1", "TASK194E_SCHEMA")
    _stop(obj.get("mode") == "T1_BOUNDED_READ_ONLY_OFFICIAL_SINOPSE_AGGREGATE_PROBE", "TASK194E_MODE")
    src = obj["source"]
    _stop(urllib.parse.urlparse(src["url"]).hostname == src["allowed_host"], "TASK194E_HOST")
    _stop(src["max_http_attempts"] == 3, "TASK194E_ATTEMPTS")
    out = obj["output"]
    _stop(out["class_count_materialized"] is False, "TASK194E_NO_MATERIALIZE")
    _stop(out["raw_zip_persisted"] is False and out["raw_workbook_persisted"] is False, "TASK194E_RAW_PERSIST")
    _stop(all(out[k] is False for k in ("drive_write","serving","publication","schedule","recurrence")), "TASK194E_EFFECTS")
    return obj


def exact_auth_comment(main_sha: str, contract_path: str | Path = DEFAULT_CONTRACT) -> str:
    obj = _load(contract_path)
    _stop(len(main_sha) == 40 and all(c in "0123456789abcdef" for c in main_sha.lower()), "TASK194E_AUTH_SHA")
    return (
        "TASK194E_SINOPSE_2025_TURMAS_AUTHORIZED "
        f"main={main_sha} issue={obj['authorization_issue']} max_http_attempts=3 raw_persist=0"
    )


class _SameHostRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, host: str):
        super().__init__()
        self.host = host

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlparse(newurl).hostname != self.host:
            raise Task194EStop("TASK194E_CROSS_HOST_REDIRECT")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _download(url: str, dest: Path, *, host: str, attempts: int) -> dict[str, Any]:
    opener = urllib.request.build_opener(_SameHostRedirect(host))
    errors: list[str] = []
    for attempt in range(1, attempts + 1):
        try:
            dest.unlink(missing_ok=True)
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "robo-dados-publicos-task194e/0.8.0",
                    "Accept": "application/zip,application/octet-stream;q=0.9,*/*;q=0.1",
                    "Accept-Encoding": "identity",
                },
                method="GET",
            )
            sha = hashlib.sha256()
            size = 0
            with opener.open(req, timeout=180) as response, dest.open("wb") as out:
                _stop(urllib.parse.urlparse(response.geturl()).hostname == host, "TASK194E_FINAL_HOST")
                while True:
                    chunk = response.read(2 * 1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    sha.update(chunk)
                    size += len(chunk)
            _stop(size > 0, "TASK194E_EMPTY_PACKAGE")
            return {"attempts_used": attempt, "sha256": sha.hexdigest(), "bytes": size}
        except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError, Task194EStop) as exc:
            dest.unlink(missing_ok=True)
            errors.append(type(exc).__name__)
            if isinstance(exc, Task194EStop) and str(exc) in {"TASK194E_CROSS_HOST_REDIRECT", "TASK194E_FINAL_HOST"}:
                raise
            if attempt < attempts:
                time.sleep(attempt * 2)
    raise Task194EStop("TASK194E_DOWNLOAD_FAILED:" + ",".join(errors))


def _shared_strings(xlsx: zipfile.ZipFile) -> list[str]:
    name = "xl/sharedStrings.xml"
    if name not in xlsx.namelist():
        return []
    root = ET.fromstring(xlsx.read(name))
    out=[]
    for si in root.findall("main:si", NS):
        texts=[t.text or "" for t in si.findall(".//main:t", NS)]
        out.append("".join(texts))
    return out


def _sheet_map(xlsx: zipfile.ZipFile) -> list[tuple[str, str]]:
    wb = ET.fromstring(xlsx.read("xl/workbook.xml"))
    rels = ET.fromstring(xlsx.read("xl/_rels/workbook.xml.rels"))
    target_by_id={}
    for rel in rels.findall("pkgrel:Relationship", NS):
        target_by_id[rel.attrib["Id"]] = rel.attrib["Target"]
    result=[]
    for sheet in wb.findall("main:sheets/main:sheet", NS):
        rid = sheet.attrib.get("{%s}id" % NS["rel"])
        target = target_by_id.get(rid, "")
        if not target.startswith("/"):
            target = "xl/" + target.lstrip("./")
        else:
            target = target.lstrip("/")
        result.append((sheet.attrib.get("name",""), target))
    return result


def _cell_value(cell: ET.Element, shared: list[str]) -> str:
    ctype = cell.attrib.get("t")
    if ctype == "inlineStr":
        return "".join((t.text or "") for t in cell.findall(".//main:t", NS))
    v = cell.find("main:v", NS)
    if v is None:
        return ""
    text = v.text or ""
    if ctype == "s":
        try:
            return shared[int(text)]
        except (ValueError, IndexError):
            return ""
    if ctype == "b":
        return "TRUE" if text == "1" else "FALSE"
    return text


def _row_cells(row: ET.Element, shared: list[str]) -> list[dict[str, str]]:
    out=[]
    for cell in row.findall("main:c", NS):
        value=_cell_value(cell, shared)
        if value != "":
            out.append({"ref":cell.attrib.get("r",""),"value":value})
    return out


def scan_workbook(xlsx_bytes: bytes, workbook_name: str, target: dict[str, Any]) -> list[dict[str, Any]]:
    candidates=[]
    with tempfile.NamedTemporaryFile(suffix=".xlsx") as tf:
        tf.write(xlsx_bytes)
        tf.flush()
        with zipfile.ZipFile(tf.name, "r") as xlsx:
            shared=_shared_strings(xlsx)
            for sheet_name, sheet_path in _sheet_map(xlsx):
                if sheet_path not in xlsx.namelist():
                    continue
                root=ET.fromstring(xlsx.read(sheet_path))
                keyword_rows=[]
                limeira_rows=[]
                keyword_hits=set()
                for row in root.findall(".//main:sheetData/main:row", NS):
                    cells=_row_cells(row, shared)
                    if not cells:
                        continue
                    text=" | ".join(c["value"] for c in cells)
                    norm=_norm(text)
                    row_num=int(row.attrib.get("r","0") or 0)
                    for key in target["keywords"]:
                        if _norm(key) in norm:
                            keyword_hits.add(_norm(key))
                    if any(_norm(key) in norm for key in target["keywords"]):
                        if len(keyword_rows) < 25:
                            keyword_rows.append({"row":row_num,"cells":cells[:40]})
                    if _norm(target["municipality_name"]) in norm:
                        limeira_rows.append({"row":row_num,"cells":cells[:60]})
                if limeira_rows and {"turma","dependencia administrativa","municipal"}.issubset(keyword_hits):
                    candidates.append({
                        "workbook":workbook_name,
                        "sheet":sheet_name,
                        "keyword_hits":sorted(keyword_hits),
                        "keyword_rows":keyword_rows,
                        "limeira_rows":limeira_rows,
                    })
    return candidates


def derive_candidates(package_path: str | Path, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj=_load(contract_path)
    package_path=Path(package_path)
    _stop(package_path.is_file(), "TASK194E_PACKAGE_MISSING")
    workbooks=[]
    candidates=[]
    with zipfile.ZipFile(package_path, "r") as outer:
        names=[n for n in outer.namelist() if not n.endswith("/")]
        xlsx_names=[n for n in names if n.casefold().endswith(".xlsx")]
        _stop(bool(xlsx_names), "TASK194E_NO_XLSX")
        for name in xlsx_names:
            data=outer.read(name)
            workbooks.append({
                "basename":Path(name).name,
                "sha256":hashlib.sha256(data).hexdigest(),
                "bytes":len(data),
            })
            candidates.extend(scan_workbook(data, Path(name).name, obj["target"]))
    return {
        "schema":"TASK194E_SINOPSE_2025_SANITIZED_CANDIDATES_V1",
        "status":"PASS" if candidates else "NO_MATCH",
        "target":{
            "year":obj["target"]["year"],
            "municipality_name":obj["target"]["municipality_name"],
            "municipality_code":obj["target"]["municipality_code"],
        },
        "workbooks":workbooks,
        "candidate_count":len(candidates),
        "candidates":candidates,
        "guards":{
            "class_count_materialized":False,
            "raw_zip_persisted":False,
            "raw_workbook_persisted":False,
            "unrelated_municipality_rows_persisted":False,
            "drive_write":False,
            "serving":False,
            "publication":False,
            "schedule":False,
            "recurrence":False,
        },
    }


def run_live(output_path: str | Path, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj=_load(contract_path)
    main_sha=str(os.environ.get("GITHUB_SHA") or "")
    checked=str(os.environ.get("TASK194E_CHECKED_OUT_SHA") or "")
    comment=str(os.environ.get("TASK194E_AUTH_COMMENT") or "")
    issue=str(os.environ.get("TASK194E_ISSUE_NUMBER") or "")
    _stop(main_sha == checked, "TASK194E_CHECKOUT")
    _stop(issue == str(obj["authorization_issue"]), "TASK194E_ISSUE")
    _stop(comment == exact_auth_comment(main_sha, contract_path), "TASK194E_AUTH_COMMENT")

    output=Path(output_path)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="task194e-") as td:
        package=Path(td)/"sinopse_2025.zip"
        dl=_download(
            obj["source"]["url"],
            package,
            host=obj["source"]["allowed_host"],
            attempts=obj["source"]["max_http_attempts"],
        )
        result=derive_candidates(package, contract_path)
        result["source"]={
            "official_page":obj["source"]["official_page"],
            "url":obj["source"]["url"],
            "package_sha256":dl["sha256"],
            "package_bytes":dl["bytes"],
            "http_attempts_used":dl["attempts_used"],
        }
        result["authorization"]={
            "issue":obj["authorization_issue"],
            "main_sha":main_sha,
            "exact_comment_verified":True,
        }
        output.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    p.add_argument("--contract",default=str(DEFAULT_CONTRACT))
    a=p.parse_args()
    result=run_live(a.output,a.contract)
    print(json.dumps({
        "status":result["status"],
        "candidate_count":result["candidate_count"],
        "workbook_count":len(result["workbooks"]),
        "class_count_materialized":result["guards"]["class_count_materialized"],
    },sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
