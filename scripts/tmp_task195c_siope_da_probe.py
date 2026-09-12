from __future__ import annotations

import hashlib
import json
import socket
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata"
META = BASE + "/$metadata"
OUT = Path("tmp/task195c_siope_da_probe.json")
MAX_META = 1_000_000
MAX_DATA = 1_000_000
READ_CHUNK = 64 * 1024
TOP = 200
DATA_ATTEMPTS_MAX = 3
EXPECTED_PARAMS = [("Ano_Consulta", "Edm.Int32"), ("Num_Peri", "Edm.Int32"), ("Sig_UF", "Edm.String")]
SAFE_FIELDS = [
    "TIPO", "NUM_ANO", "NUM_PERI", "COD_UF", "SIG_UF", "COD_MUNI", "NOM_MUNI",
    "NOM_PAST", "TIP_PASTA", "COD_PAST", "COD_EXIB", "COD_EXIB_FORMATADO", "COD_FONTE",
    "NOM_ITEM", "IDN_CLAS", "NOM_COLU", "NUM_NIVE", "NUM_ORDE", "VAL_DECL",
]


def _read_bounded(response, limit: int) -> bytes:
    parts: list[bytes] = []
    total = 0
    while True:
        chunk = response.read(READ_CHUNK)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise RuntimeError(f"response exceeds {limit} bytes")
        parts.append(chunk)
    return b"".join(parts)


def get(url: str, limit: int, *, attempts_max: int = 1):
    last_error: Exception | None = None
    attempt_log = []
    for attempt in range(1, attempts_max + 1):
        started = time.monotonic()
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 TASK195C-readonly-odata-probe",
                    "Accept": "application/json, application/xml;q=0.9, */*;q=0.1",
                },
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                final = r.geturl()
                if urllib.parse.urlparse(final).hostname != "www.fnde.gov.br":
                    raise RuntimeError(f"unexpected redirect host: {final}")
                b = _read_bounded(r, limit)
                attempt_log.append({
                    "attempt": attempt,
                    "status": getattr(r, "status", None),
                    "elapsed_s": round(time.monotonic() - started, 3),
                    "bytes": len(b),
                })
                return {
                    "status": getattr(r, "status", None),
                    "final_url": final,
                    "content_type": r.headers.get("Content-Type"),
                    "bytes": len(b),
                    "sha256": hashlib.sha256(b).hexdigest(),
                    "attempts": attempt_log,
                    "data": b,
                }
        except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
            last_error = exc
            attempt_log.append({
                "attempt": attempt,
                "error": f"{type(exc).__name__}: {exc}",
                "elapsed_s": round(time.monotonic() - started, 3),
            })
            if attempt < attempts_max:
                time.sleep(attempt)
                continue
            break
    assert last_error is not None
    raise last_error


def discover_function(meta: bytes):
    root = ET.fromstring(meta)
    matches = []
    for fn in root.iter():
        if fn.tag.endswith("Function") and fn.attrib.get("Name") == "Despesas_Siope":
            params = []
            for child in fn:
                if child.tag.endswith("Parameter"):
                    params.append((child.attrib.get("Name"), child.attrib.get("Type")))
            matches.append(params)
    if not matches:
        raise RuntimeError("Despesas_Siope function not found in official EDMX")
    exact = [m for m in matches if m == EXPECTED_PARAMS]
    if len(exact) != 1:
        raise RuntimeError(f"unexpected Despesas_Siope parameter contract: {matches}")
    return exact[0]


def build_url():
    signature = "Despesas_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)"
    # Preserve the exact TASK195-proven municipal filter syntax, then narrow server-side
    # to DA so the probe does not download the full municipal payload just to inspect one class.
    filt = (
        "TIPO%09eq%09%27Municipal%27"
        "%09and%09COD_MUNI%09eq%09352690"
        "%09and%09IDN_CLAS%09eq%09%27DA%27"
    )
    select = ",".join(SAFE_FIELDS)
    return (
        f"{BASE}/{signature}?@Ano_Consulta=2025&@Num_Peri=6&@Sig_UF=%27SP%27"
        f"&$format=json&$filter={filt}&$select={select}&$top={TOP}"
    )


def main():
    result = {
        "schema": "TASK195C_SIOPE_DA_OFFICIAL_ODATA_PROBE_V4",
        "mode": "READ_ONLY_GET_OFFICIAL_FNDE_BOUNDED_SERVER_SIDE_DA_FILTER",
        "target": "Limeira municipal SIOPE 2025/P6; inspect IDN_CLAS=DA without downloading the full municipal payload",
        "transport": "TASK195_PROVEN_MUNICIPAL_FILTER_PLUS_SERVER_SIDE_DA_SELECT_TOP",
        "guards": {
            "get_requests_max": 1 + DATA_ATTEMPTS_MAX,
            "post_requests": 0,
            "auth": 0,
            "captcha_bypass": 0,
            "data_attempts_max": DATA_ATTEMPTS_MAX,
            "max_data_bytes": MAX_DATA,
            "top": TOP,
            "drive_writes": 0,
            "tinyfish": 0,
            "gold_promotion": 0,
            "absence_claim_if_top_reached": False,
            "absence_claim_if_nextlink_present": False,
        },
    }

    meta = get(META, MAX_META)
    result["metadata"] = {k: v for k, v in meta.items() if k != "data"}
    result["metadata"]["despesas_siope_parameters"] = discover_function(meta["data"])

    url = build_url()
    data = get(url, MAX_DATA, attempts_max=DATA_ATTEMPTS_MAX)
    payload = json.loads(data["data"].decode("utf-8"))
    rows = payload.get("value")
    if not isinstance(rows, list):
        raise RuntimeError("official OData response missing value list")

    nextlink = "@odata.nextLink" in payload
    sanitized = [{k: row.get(k) for k in SAFE_FIELDS if k in row} for row in rows]
    non_da = [row for row in sanitized if row.get("IDN_CLAS") != "DA"]

    result["query"] = {
        "url": url,
        **{k: v for k, v in data.items() if k != "data"},
        "row_count": len(rows),
        "nextlink_present": nextlink,
        "top_reached": len(rows) >= TOP,
        "non_da_row_count": len(non_da),
        "rows": sanitized,
    }

    if non_da:
        result["classification"] = "FILTER_CONTRACT_VIOLATION_NON_DA_ROWS_RETURNED"
    elif nextlink:
        result["classification"] = "PARTIAL_FILTERED_RESPONSE_NEXTLINK_PRESENT_NO_ABSENCE_CLAIM"
    elif len(rows) >= TOP:
        result["classification"] = "BOUNDED_TOP_REACHED_INDETERMINATE_NO_ABSENCE_CLAIM"
    elif rows:
        result["classification"] = "COMPLETE_FILTERED_RESPONSE_DA_ROWS_LOCATED"
    else:
        result["classification"] = "COMPLETE_FILTERED_RESPONSE_NO_DA_ROWS_LOCATED"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "metadata_sha256": result["metadata"]["sha256"],
        "query_status": result["query"]["status"],
        "query_sha256": result["query"]["sha256"],
        "query_bytes": result["query"]["bytes"],
        "attempts": result["query"]["attempts"],
        "row_count": result["query"]["row_count"],
        "nextlink_present": result["query"]["nextlink_present"],
        "top_reached": result["query"]["top_reached"],
        "non_da_row_count": result["query"]["non_da_row_count"],
        "rows": result["query"]["rows"],
        "classification": result["classification"],
        "output": str(OUT),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
