from __future__ import annotations

import hashlib
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://www.fnde.gov.br/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata"
META = BASE + "/$metadata"
OUT = Path("tmp/task195c_siope_da_probe.json")
MAX_META = 1_000_000
MAX_DATA = 4_000_000
EXPECTED_PARAMS = [("Ano_Consulta", "Edm.Int32"), ("Num_Peri", "Edm.Int32"), ("Sig_UF", "Edm.String")]
SAFE_FIELDS = [
    "TIPO", "NUM_ANO", "NUM_PERI", "COD_UF", "SIG_UF", "COD_MUNI", "NOM_MUNI",
    "NOM_PAST", "TIP_PASTA", "COD_EXIB", "COD_EXIB_FORMATADO", "COD_FONTE",
    "NOM_ITEM", "IDN_CLAS", "NOM_COLU", "NUM_NIVE", "NUM_ORDE", "VAL_DECL",
]


def get(url: str, limit: int):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TASK195C-readonly-odata-probe", "Accept": "application/json, application/xml;q=0.9, */*;q=0.1"})
    with urllib.request.urlopen(req, timeout=45) as r:
        final = r.geturl()
        if urllib.parse.urlparse(final).hostname != "www.fnde.gov.br":
            raise RuntimeError(f"unexpected redirect host: {final}")
        b = r.read(limit + 1)
        if len(b) > limit:
            raise RuntimeError(f"response exceeds {limit} bytes")
        return {
            "status": getattr(r, "status", None),
            "final_url": final,
            "content_type": r.headers.get("Content-Type"),
            "bytes": len(b),
            "sha256": hashlib.sha256(b).hexdigest(),
            "data": b,
        }


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
    # Preserve %20 whitespace because prior official handoff proved '+' breaks this OData parser.
    filt = "COD_MUNI%20eq%20352690%20and%20IDN_CLAS%20eq%20%27DA%27"
    return (
        f"{BASE}/{signature}?@Ano_Consulta=2025&@Num_Peri=6&@Sig_UF=%27SP%27"
        f"&$filter={filt}&$format=json"
    )


def main():
    result = {
        "schema": "TASK195C_SIOPE_DA_OFFICIAL_ODATA_PROBE_V1",
        "mode": "READ_ONLY_GET_OFFICIAL_FNDE_NO_AUTH_NO_RETRY",
        "target": "Despesas_Siope Limeira 2025/P6 IDN_CLAS=DA",
        "guards": {
            "get_requests_max": 2,
            "post_requests": 0,
            "auth": 0,
            "retries": 0,
            "drive_writes": 0,
            "tinyfish": 0,
            "gold_promotion": 0,
        },
    }
    meta = get(META, MAX_META)
    result["metadata"] = {k: v for k, v in meta.items() if k != "data"}
    result["metadata"]["despesas_siope_parameters"] = discover_function(meta["data"])

    url = build_url()
    data = get(url, MAX_DATA)
    payload = json.loads(data["data"].decode("utf-8"))
    rows = payload.get("value")
    if not isinstance(rows, list):
        raise RuntimeError("official OData response missing value list")
    sanitized = []
    for row in rows:
        sanitized.append({k: row.get(k) for k in SAFE_FIELDS if k in row})
    result["query"] = {
        "url": url,
        **{k: v for k, v in data.items() if k != "data"},
        "row_count": len(rows),
        "nextlink_present": "@odata.nextLink" in payload,
        "rows": sanitized,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "metadata_sha256": result["metadata"]["sha256"],
        "query_status": result["query"]["status"],
        "query_sha256": result["query"]["sha256"],
        "row_count": result["query"]["row_count"],
        "nextlink_present": result["query"]["nextlink_present"],
        "rows": sanitized,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
