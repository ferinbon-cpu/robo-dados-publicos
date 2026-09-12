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
    "NOM_PAST", "TIP_PASTA", "COD_PAST", "COD_EXIB", "COD_EXIB_FORMATADO", "COD_FONTE",
    "NOM_ITEM", "IDN_CLAS", "NOM_COLU", "NUM_NIVE", "NUM_ORDE", "VAL_DECL",
]


def get(url: str, limit: int):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TASK195C-readonly-odata-probe", "Accept": "application/json, application/xml;q=0.9, */*;q=0.1"})
    with urllib.request.urlopen(req, timeout=90) as r:
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
    # Replicate byte-for-byte the filter syntax preserved by TASK195 from the successful
    # owner-mediated official URL: TIPO='Municipal' AND COD_MUNI=352690, with %09 whitespace.
    filt = "TIPO%09eq%09%27Municipal%27%09and%09COD_MUNI%09eq%09352690"
    return (
        f"{BASE}/{signature}?@Ano_Consulta=2025&@Num_Peri=6&@Sig_UF=%27SP%27"
        f"&$format=json&$filter={filt}"
    )


def main():
    result = {
        "schema": "TASK195C_SIOPE_DA_OFFICIAL_ODATA_PROBE_V3",
        "mode": "READ_ONLY_GET_OFFICIAL_FNDE_NO_AUTH_NO_RETRY",
        "target": "Replicate TASK195 proven Despesas_Siope Limeira 2025/P6 transport; inspect DA locally",
        "transport": "EXACT_TASK195_PROVEN_FILTER_TIPO_MUNICIPAL_AND_COD_MUNI_WITH_PERCENT09",
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
    nextlink = "@odata.nextLink" in payload
    all_sanitized = [{k: row.get(k) for k in SAFE_FIELDS if k in row} for row in rows]
    da_rows = [row for row in all_sanitized if row.get("IDN_CLAS") == "DA"]
    result["query"] = {
        "url": url,
        **{k: v for k, v in data.items() if k != "data"},
        "row_count": len(rows),
        "nextlink_present": nextlink,
        "da_row_count": len(da_rows),
        "da_rows": da_rows,
        "class_counts": {},
    }
    for row in all_sanitized:
        cls = row.get("IDN_CLAS")
        result["query"]["class_counts"][str(cls)] = result["query"]["class_counts"].get(str(cls), 0) + 1
    if nextlink:
        result["classification"] = "PARTIAL_RESPONSE_NEXTLINK_PRESENT_NO_ABSENCE_CLAIM"
    elif da_rows:
        result["classification"] = "COMPLETE_MUNICIPAL_RESPONSE_DA_ROWS_LOCATED"
    else:
        result["classification"] = "COMPLETE_MUNICIPAL_RESPONSE_NO_DA_ROWS_LOCATED"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "metadata_sha256": result["metadata"]["sha256"],
        "query_status": result["query"]["status"],
        "query_sha256": result["query"]["sha256"],
        "row_count": result["query"]["row_count"],
        "nextlink_present": result["query"]["nextlink_present"],
        "class_counts": result["query"]["class_counts"],
        "da_row_count": result["query"]["da_row_count"],
        "da_rows": da_rows,
        "classification": result["classification"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
