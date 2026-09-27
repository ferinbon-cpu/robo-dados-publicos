from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task172_observatory_fiscal_machine_readable_batch.v1.json"


class Task172Stop(RuntimeError):
    pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class _HrefParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value)


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task172Stop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK172_OBSERVATORY_FISCAL_MACHINE_READABLE_BATCH_V1", "TASK172_SCHEMA")
    _stop(obj.get("task") == "TASK_172_BOUNDED_OBSERVATORY_FISCAL_MACHINE_READABLE_ACQUISITION", "TASK172_TASK")
    policy = obj["network_policy"]
    _stop(policy["method"] == "GET", "TASK172_METHOD")
    _stop(policy["retry"] == 0, "TASK172_RETRY")
    _stop(policy["follow_redirects"] is False, "TASK172_REDIRECT")
    _stop(policy["max_requests"] == 13, "TASK172_REQUEST_BUDGET")
    _stop(obj["remote_effects"]["source_writes"] is False, "TASK172_SOURCE_WRITE")
    _stop(obj["remote_effects"]["drive_write"] is False, "TASK172_DRIVE_WRITE")
    _stop(obj["remote_effects"]["serving"] is False and obj["remote_effects"]["publication"] is False, "TASK172_PUBLICATION")
    return obj


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    sources = obj["sources"]
    _stop(len(sources) == 12, "TASK172_SOURCE_COUNT")
    ids = [x["id"] for x in sources]
    _stop(len(ids) == len(set(ids)), "TASK172_DUPLICATE_SOURCE")
    hosts = set(obj["network_policy"]["allowed_hosts"])
    for source in sources:
        parsed = urllib.parse.urlparse(source["url"])
        _stop(parsed.scheme == "https", "TASK172_HTTPS_ONLY")
        _stop(parsed.hostname in hosts, "TASK172_HOST_NOT_ALLOWED")
    expected_prefixes = {
        "SICONFI_": 4,
        "FNDE_FUNDEB_": 4,
        "TCESP_": 3,
        "TDA_": 1,
    }
    for prefix, count in expected_prefixes.items():
        _stop(sum(x.startswith(prefix) for x in ids) == count, f"TASK172_SOURCE_GROUP_{prefix}")
    _stop(obj["adjudication"]["transport_failure"] == "SOURCE_TRANSPORT_UNAVAILABLE_NOT_NO_DATA", "TASK172_TRANSPORT_SEMANTICS")
    _stop(obj["adjudication"]["payment_promotion"] is False, "TASK172_PAYMENT_PROMOTION")
    return {
        "schema": "TASK172_CONTRACT_VALIDATION_RESULT_V1",
        "status": "PASS",
        "source_count": len(sources),
        "max_requests": obj["network_policy"]["max_requests"],
        "hosts": sorted(hosts),
        "live_authorized": obj["remote_effects"]["source_gets_authorized_within_contract"],
    }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _decode_text(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    return data.decode("latin-1", errors="replace")


def _safe_scalar(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    text = str(value)
    return text[:1000]


def _select_json_fields(row: dict[str, Any]) -> dict[str, Any]:
    safe_exact = {
        "exercicio", "an_exercicio", "periodo", "nr_periodo", "instituicao", "cod_ibge",
        "id_ente", "ente", "uf", "no_anexo", "anexo", "co_esfera", "co_poder",
        "coluna", "cod_conta", "conta", "rotulo", "label", "valor",
    }
    selected: dict[str, Any] = {}
    for key, value in row.items():
        low = key.lower()
        if low in safe_exact or low.startswith("vl_") or "valor" in low:
            selected[key] = _safe_scalar(value)
    if not selected:
        for key in list(row)[:12]:
            selected[key] = _safe_scalar(row[key])
    return selected


def summarize_json(data: bytes) -> dict[str, Any]:
    obj = json.loads(_decode_text(data))
    if isinstance(obj, dict):
        top_keys = sorted(obj.keys())[:100]
        records = obj.get("items")
        if not isinstance(records, list):
            records = obj.get("value")
        if not isinstance(records, list):
            records = []
    elif isinstance(obj, list):
        top_keys = []
        records = obj
    else:
        raise Task172Stop("TASK172_JSON_SHAPE")
    dict_rows = [x for x in records if isinstance(x, dict)]
    schema_keys = sorted({k for row in dict_rows[:100] for k in row})[:200]
    selected = [_select_json_fields(row) for row in dict_rows[:50]]
    return {
        "schema_keys": schema_keys or top_keys,
        "record_count": len(records),
        "limeira_selected_rows": selected,
    }


def _csv_delimiter(text: str) -> str:
    sample = "\n".join(text.splitlines()[:30])
    scores = {d: sample.count(d) for d in (";", ",", "\t")}
    return max(scores, key=scores.get)


def summarize_csv(data: bytes, selectors: list[str] | None = None, *, all_rows_scoped: bool = False) -> dict[str, Any]:
    text = _decode_text(data)
    delim = _csv_delimiter(text)
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    nonempty = [row for row in rows if any(str(x).strip() for x in row)]
    selectors_u = [x.upper() for x in (selectors or [])]
    matches: list[tuple[int, list[str]]] = []
    for idx, row in enumerate(nonempty):
        joined = " | ".join(row).upper()
        if all_rows_scoped or any(token in joined for token in selectors_u):
            matches.append((idx, row))
    if all_rows_scoped:
        matches = matches[:20]
    else:
        matches = matches[:20]
    header: list[str] = []
    if matches:
        first_idx, first_row = matches[0]
        width = len(first_row)
        candidates = [r for r in nonempty[:first_idx] if len(r) == width]
        preferred = [
            r for r in candidates
            if any(re.search(r"(?i)UF|ENTE|MUNIC|COD|IBGE|EMPENHO|FORNECEDOR|VALOR|RECEITA|DESPESA", cell or "") for cell in r)
        ]
        if preferred:
            header = preferred[-1]
        elif candidates:
            header = candidates[-1]
    selected_rows: list[Any] = []
    for _, row in matches:
        clipped = [str(x)[:1000] for x in row[:100]]
        if header and len(header) == len(row):
            selected_rows.append({str(k)[:200]: v for k, v in zip(header, clipped)})
        else:
            selected_rows.append(clipped)
    return {
        "csv_headers": [str(x)[:200] for x in header[:100]],
        "record_count": max(0, len(nonempty) - (1 if header else 0)),
        "limeira_selected_rows": selected_rows,
    }


def summarize_zip(data: bytes) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        infos = zf.infolist()
        _stop(len(infos) <= 50, "TASK172_ZIP_MEMBER_COUNT")
        total_uncompressed = sum(i.file_size for i in infos)
        _stop(total_uncompressed <= 100_000_000, "TASK172_ZIP_EXPANSION")
        names: list[str] = []
        csv_summaries: list[dict[str, Any]] = []
        for info in infos:
            name = info.filename
            _stop(not info.flag_bits & 0x1, "TASK172_ZIP_ENCRYPTED")
            p = Path(name)
            _stop(not p.is_absolute() and ".." not in p.parts, "TASK172_ZIP_PATH")
            if info.is_dir():
                continue
            names.append(name[:500])
            if name.lower().endswith((".csv", ".txt")) and len(csv_summaries) < 5:
                member = zf.read(info)
                csv_summaries.append({"member": name[:500], **summarize_csv(member, all_rows_scoped=True)})
        record_count = sum(x.get("record_count", 0) for x in csv_summaries)
        headers = [x.get("csv_headers", []) for x in csv_summaries]
        selected: list[Any] = []
        for summary in csv_summaries:
            for row in summary.get("limeira_selected_rows", []):
                if len(selected) >= 30:
                    break
                selected.append({"member": summary["member"], "row": row})
        return {
            "zip_member_names": names,
            "csv_headers": headers,
            "record_count": record_count,
            "limeira_selected_rows": selected,
        }


def declared_machine_routes(html: bytes, base_url: str, contract: dict[str, Any]) -> list[str]:
    parser = _HrefParser()
    parser.feed(_decode_text(html))
    allowed_hosts = set(contract["network_policy"]["allowed_hosts"])
    source_cfg = next(x for x in contract["sources"] if x["id"] == "TDA_LIMEIRA_DECLARED_ROUTE_DISCOVERY")
    markers = [x.lower() for x in source_cfg["allowed_declared_markers"]]
    exts = tuple(x.lower() for x in source_cfg["allowed_declared_extensions"])
    found: list[str] = []
    for href in parser.hrefs:
        absolute = urllib.parse.urljoin(base_url, href)
        parsed = urllib.parse.urlparse(absolute)
        low = absolute.lower()
        explicit = parsed.path.lower().endswith(exts) or any(marker in low for marker in markers)
        if parsed.scheme == "https" and parsed.hostname in allowed_hosts and explicit:
            if absolute not in found:
                found.append(absolute)
    return found[:20]


class LiveTransport:
    def __init__(self, contract: dict[str, Any]):
        self.contract = contract
        self.requests = 0
        self.opener = urllib.request.build_opener(_NoRedirect())

    def get(self, url: str, *, accept: str = "*/*") -> dict[str, Any]:
        self.requests += 1
        _stop(self.requests <= self.contract["network_policy"]["max_requests"], "TASK172_REQUEST_BUDGET_EXCEEDED")
        parsed = urllib.parse.urlparse(url)
        _stop(parsed.scheme == "https", "TASK172_LIVE_HTTPS")
        _stop(parsed.hostname in set(self.contract["network_policy"]["allowed_hosts"]), "TASK172_LIVE_HOST")
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "ROBO_DADOS_PUBLICOS_TASK172/0.8.0", "Accept": accept})
        limit = int(self.contract["network_policy"]["max_response_bytes"])
        try:
            with self.opener.open(req, timeout=30) as response:
                status = int(response.status)
                content_type = str(response.headers.get("Content-Type") or "")
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > limit:
                    raise Task172Stop("TASK172_RESPONSE_TOO_LARGE")
                body = response.read(limit + 1)
                _stop(len(body) <= limit, "TASK172_RESPONSE_TOO_LARGE")
                return {
                    "ok": 200 <= status < 300,
                    "http_status": status,
                    "content_type": content_type,
                    "headers": dict(response.headers.items()),
                    "body": body,
                }
        except urllib.error.HTTPError as exc:
            return {
                "ok": False,
                "http_status": int(exc.code),
                "content_type": str(exc.headers.get("Content-Type") or "") if exc.headers else "",
                "headers": dict(exc.headers.items()) if exc.headers else {},
                "body": b"",
                "error": f"HTTP_{exc.code}",
            }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return {
                "ok": False,
                "http_status": None,
                "content_type": "",
                "headers": {},
                "body": b"",
                "error": f"TRANSPORT_{type(exc).__name__}",
            }


def _base_result(source: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    body = response.get("body") or b""
    result = {
        "source_id": source["id"],
        "status": "PASS_MACHINE_READABLE" if response["ok"] else (
            "SOURCE_TRANSPORT_UNAVAILABLE_NOT_NO_DATA" if response.get("http_status") is None else "SOURCE_HTTP_UNAVAILABLE_NOT_NO_DATA"
        ),
        "http_status": response.get("http_status"),
        "content_type": response.get("content_type"),
        "bytes": len(body),
        "sha256": _sha256(body) if body else None,
    }
    return result


def run_live(contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(contract_path)
    _stop(
        contract["remote_effects"]["source_gets_authorized_within_contract"] is True,
        "TASK172_LIVE_NOT_AUTHORIZED",
    )
    transport = LiveTransport(contract)
    results: list[dict[str, Any]] = []
    tda_declared: list[str] = []
    for source in contract["sources"]:
        fmt = source["format"]
        accept = "application/json" if fmt == "JSON" else ("text/csv,*/*" if fmt == "CSV" else "*/*")
        response = transport.get(source["url"], accept=accept)
        result = _base_result(source, response)
        body = response.get("body") or b""
        if response["ok"]:
            try:
                if fmt == "JSON":
                    result.update(summarize_json(body))
                    if result.get("record_count") == 0:
                        result["status"] = "EMPTY_WITHIN_EXACT_QUERY_NOT_GLOBAL_ABSENCE"
                elif fmt == "CSV":
                    selectors = source.get("selector", {}).get("contains_any", [])
                    result.update(summarize_csv(body, selectors))
                elif fmt == "ZIP":
                    result.update(summarize_zip(body))
                elif fmt == "HTML_DISCOVERY":
                    routes = declared_machine_routes(body, source["url"], contract)
                    result["declared_machine_routes"] = routes
                    tda_declared = routes
                    result["status"] = "PASS_DECLARED_MACHINE_ROUTE_DISCOVERED" if routes else "STOP_NO_DECLARED_MACHINE_READABLE_ROUTE"
            except (ValueError, json.JSONDecodeError, csv.Error, zipfile.BadZipFile, Task172Stop) as exc:
                result["status"] = f"STOP_PARSE_OR_SCHEMA_{type(exc).__name__}"
        else:
            location = str((response.get("headers") or {}).get("Location") or "")
            if fmt == "HTML_DISCOVERY" and response.get("http_status") in {301, 302, 303, 307, 308}:
                if re.search(r"(?i)login|logout|session|acesso", location):
                    result["status"] = "SOURCE_ACCESS_SURFACE_BLOCKED"
                result["declared_machine_routes"] = []
                if location:
                    result["redirect_location"] = location[:1000]
        result.pop("body", None)
        results.append(result)

    if tda_declared and transport.requests < contract["network_policy"]["max_requests"]:
        follow_url = tda_declared[0]
        follow = transport.get(follow_url)
        synthetic = {
            "id": "TDA_LIMEIRA_DECLARED_ROUTE_FOLLOWUP",
            "format": "DECLARED_MACHINE_ROUTE",
        }
        follow_result = _base_result(synthetic, follow)
        follow_result["declared_url"] = follow_url
        body = follow.get("body") or b""
        ctype = (follow.get("content_type") or "").lower()
        if follow["ok"] and body:
            try:
                if "json" in ctype or follow_url.lower().endswith(".json"):
                    follow_result.update(summarize_json(body))
                elif "csv" in ctype or follow_url.lower().endswith((".csv", ".txt")):
                    follow_result.update(summarize_csv(body, ["LIMEIRA", "3526902"]))
                elif follow_url.lower().endswith(".zip") or "zip" in ctype:
                    follow_result.update(summarize_zip(body))
                else:
                    follow_result["status"] = "STOP_DECLARED_ROUTE_UNSUPPORTED_CONTENT"
            except Exception as exc:
                follow_result["status"] = f"STOP_PARSE_OR_SCHEMA_{type(exc).__name__}"
        results.append(follow_result)

    core = {
        "schema": "TASK172_SANITIZED_RESULT_V1",
        "task": contract["task"],
        "jurisdiction": contract["jurisdiction"],
        "request_count": transport.requests,
        "request_budget": contract["network_policy"]["max_requests"],
        "raw_payload_persisted": False,
        "policy_identity_promoted": False,
        "financial_identity_promoted": False,
        "payment_promoted": False,
        "results": results,
    }
    core["result_sha256"] = hashlib.sha256(
        json.dumps(core, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return core


if __name__ == "__main__":
    print(json.dumps(run_live(), ensure_ascii=False, indent=2, sort_keys=True))
