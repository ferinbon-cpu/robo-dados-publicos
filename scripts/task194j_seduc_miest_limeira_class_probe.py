from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "config/task194j_seduc_miest_limeira_class_probe.v1.json"


class Task194JStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task194JStop(code)


def _load(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK194J_SEDUC_MIEST_LIMEIRA_CLASS_PROBE_V1", "TASK194J_SCHEMA")
    _stop(obj.get("mode") == "T1_BOUNDED_READ_ONLY_OFFICIAL_SEDUC_MIEST_SCHEMA", "TASK194J_MODE")
    src=obj["source"]
    parsed=urllib.parse.urlparse(src["csv_url"])
    _stop(parsed.scheme == "https", "TASK194J_SCHEME")
    _stop(parsed.hostname == src["allowed_host"], "TASK194J_HOST")
    _stop(src["max_http_requests"] == 1, "TASK194J_HTTP_BUDGET")
    out=obj["output"]
    _stop(out["sanitized_json_only"] is True, "TASK194J_SANITIZED")
    _stop(out["raw_csv_persisted"] is False, "TASK194J_RAW")
    _stop(out["class_count_materialized"] is False, "TASK194J_NO_MATERIALIZE")
    _stop(all(out[k] is False for k in ("drive_write","serving","publication","schedule","recurrence")), "TASK194J_EFFECTS")
    return obj


def exact_auth_comment(main_sha: str, contract_path: str | Path = DEFAULT_CONTRACT) -> str:
    obj=_load(contract_path)
    _stop(len(main_sha) == 40 and all(c in "0123456789abcdef" for c in main_sha.lower()), "TASK194J_AUTH_SHA")
    return (
        "TASK194J_SEDUC_MIEST_AUTHORIZED "
        f"main={main_sha} issue={obj['authorization_issue']} max_http_requests=1 materialize=0"
    )


def _normalize(value: str) -> str:
    text=unicodedata.normalize("NFKD",str(value))
    text="".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+"," ",text).strip().upper()


def _get(url: str, allowed_host: str) -> tuple[bytes,str]:
    request=urllib.request.Request(
        url,
        headers={
            "User-Agent":"robo-dados-publicos-task194j/0.8.0",
            "Accept":"text/csv,text/plain;q=0.9,*/*;q=0.1",
        },
        method="GET",
    )
    with urllib.request.urlopen(request,timeout=120) as response:
        final=response.geturl()
        _stop(urllib.parse.urlparse(final).hostname == allowed_host, "TASK194J_FINAL_HOST")
        return response.read(),final


def _decode(raw: bytes) -> tuple[str,str]:
    for enc in ("utf-8-sig","utf-8","cp1252","latin-1"):
        try:
            return raw.decode(enc),enc
        except UnicodeDecodeError:
            continue
    raise Task194JStop("TASK194J_ENCODING")


def _delimiter(text: str) -> str:
    sample="\n".join(text.splitlines()[:12])
    try:
        dialect=csv.Sniffer().sniff(sample,delimiters=";,|\t")
        return dialect.delimiter
    except csv.Error:
        counts={d:sample.count(d) for d in (";",",","|","\t")}
        return max(counts,key=counts.get)


def _number(value: str) -> float | None:
    text=str(value).strip()
    if not text:
        return None
    text=text.replace("\u00a0","").replace(" ","")
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})*,\d+",text):
        text=text.replace(".","").replace(",",".")
    elif re.fullmatch(r"-?\d+,\d+",text):
        text=text.replace(",",".")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+",text):
        text=text.replace(".","")
    try:
        return float(text)
    except ValueError:
        return None


def inspect_csv(raw: bytes, contract: dict[str,Any]) -> dict[str,Any]:
    text,encoding=_decode(raw)
    delim=_delimiter(text)
    reader=csv.DictReader(io.StringIO(text),delimiter=delim)
    _stop(reader.fieldnames is not None, "TASK194J_HEADER")
    fields=[str(x or "").strip() for x in reader.fieldnames]
    _stop(len(fields) >= 2, "TASK194J_FIELD_COUNT")

    normalized={f:_normalize(f) for f in fields}
    municipality_tokens=[_normalize(x) for x in contract["target"]["municipality_tokens"]]
    interesting_tokens=[_normalize(x) for x in contract["target"]["interesting_header_tokens"]]
    municipality_fields=[
        f for f in fields
        if any(tok in normalized[f] for tok in municipality_tokens)
    ]
    interesting_fields=[
        f for f in fields
        if any(tok in normalized[f] for tok in interesting_tokens)
    ]

    target=_normalize(contract["target"]["municipality_name"])
    rows=0
    limeira=[]
    for row in reader:
        rows += 1
        matched=False
        for f in municipality_fields:
            if _normalize(row.get(f,"")) == target:
                matched=True
                break
        if not matched and not municipality_fields:
            matched=any(_normalize(v) == target for v in row.values())
        if matched:
            limeira.append({f:str(row.get(f,"")).strip() for f in fields})

    _stop(rows > 0, "TASK194J_EMPTY")
    _stop(len(limeira) > 0, "TASK194J_LIMEIRA_NOT_FOUND")

    limits=contract["limits"]
    distinct={}
    for f in interesting_fields:
        values=sorted({_normalize(r.get(f,"")) for r in limeira if str(r.get(f,"")).strip()})
        if 0 < len(values) <= int(limits["max_distinct_values_per_field"]):
            distinct[f]=values

    numeric_fields=[]
    numeric_sums={}
    numeric_nonnull={}
    for f in interesting_fields:
        nums=[_number(r.get(f,"")) for r in limeira]
        usable=[x for x in nums if x is not None]
        if not usable:
            continue
        numeric_fields.append(f)
        numeric_sums[f]=round(sum(usable),6)
        numeric_nonnull[f]=len(usable)
        if len(numeric_fields) >= int(limits["max_numeric_summary_fields"]):
            break

    network_candidates=[
        f for f in fields
        if any(tok in normalized[f] for tok in ("REDE","DEPEND","ADMINISTR"))
    ]
    grouped={}
    for nf in network_candidates[:8]:
        groups=defaultdict(list)
        for r in limeira:
            key=_normalize(r.get(nf,"")) or "<EMPTY>"
            groups[key].append(r)
        group_out={}
        for key,grows in sorted(groups.items()):
            sums={}
            for f in numeric_fields:
                head=normalized[f]
                if not any(tok in head for tok in ("CLAS","TURM","MATR")):
                    continue
                vals=[_number(r.get(f,"")) for r in grows]
                usable=[x for x in vals if x is not None]
                if usable:
                    sums[f]=round(sum(usable),6)
            group_out[key]={"row_count":len(grows),"numeric_sums":sums}
        grouped[nf]=group_out

    return {
        "encoding":encoding,
        "delimiter":delim,
        "row_count":rows,
        "field_count":len(fields),
        "fields":fields,
        "municipality_candidate_fields":municipality_fields,
        "interesting_fields":interesting_fields,
        "limeira_row_count":len(limeira),
        "limeira_distinct_values":distinct,
        "limeira_numeric_fields":numeric_fields,
        "limeira_numeric_sums":numeric_sums,
        "limeira_numeric_nonnull":numeric_nonnull,
        "limeira_grouped_by_network_candidates":grouped,
    }


def run(output_path: str | Path, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str,Any]:
    obj=_load(contract_path)
    src=obj["source"]
    main_sha=str(os.environ.get("GITHUB_SHA") or "")
    checked=str(os.environ.get("TASK194J_CHECKED_OUT_SHA") or "")
    comment=str(os.environ.get("TASK194J_AUTH_COMMENT") or "")
    issue=str(os.environ.get("TASK194J_ISSUE_NUMBER") or "")
    _stop(main_sha == checked, "TASK194J_CHECKOUT")
    _stop(issue == str(obj["authorization_issue"]), "TASK194J_ISSUE")
    _stop(comment == exact_auth_comment(main_sha,contract_path), "TASK194J_AUTH_COMMENT")

    raw,final=_get(src["csv_url"],src["allowed_host"])
    sha=hashlib.sha256(raw).hexdigest()
    inspected=inspect_csv(raw,obj)
    result={
        "schema":"TASK194J_SEDUC_MIEST_LIMEIRA_CLASS_PROBE_SANITIZED_V1",
        "status":"PASS",
        "source":{
            "catalog_url":src["catalog_url"],
            "csv_url":src["csv_url"],
            "final_host":urllib.parse.urlparse(final).hostname,
            "period":src["period"],
            "bytes":len(raw),
            "sha256":sha,
            "http_requests_used":1,
        },
        **inspected,
        "authorization":{
            "issue":obj["authorization_issue"],
            "main_sha":main_sha,
            "exact_comment_verified":True,
        },
        "class_count_materialized":False,
        "raw_csv_persisted":False,
        "drive_write":False,
        "serving":False,
        "publication":False,
        "schedule":False,
        "recurrence":False,
    }
    path=Path(output_path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    p.add_argument("--contract",default=str(DEFAULT_CONTRACT))
    a=p.parse_args()
    result=run(a.output,a.contract)
    print(json.dumps({
        "status":result["status"],
        "row_count":result["row_count"],
        "field_count":result["field_count"],
        "limeira_row_count":result["limeira_row_count"],
        "municipality_candidate_fields":result["municipality_candidate_fields"],
        "network_group_fields":sorted(result["limeira_grouped_by_network_candidates"]),
        "class_count_materialized":result["class_count_materialized"],
    },sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
