from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import os
import re
import unicodedata
import urllib.parse
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.task194b_inep_data_metadata_probe import (
    _get,
    bootstrap_metadata,
    decode_report_token,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "config/task194f_inep_data_embedded_visual_probe.v1.json"


class Task194FStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task194FStop(code)


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip().casefold()


def _load(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK194F_INEP_DATA_EMBEDDED_VISUAL_PROBE_V1", "TASK194F_SCHEMA")
    _stop(obj.get("mode") == "T1_BOUNDED_READ_ONLY_OFFICIAL_PUBLIC_PANEL_EMBEDDED_DATA", "TASK194F_MODE")
    src=obj["source"]
    _stop(urllib.parse.urlparse(src["report_url"]).hostname == src["report_host"], "TASK194F_HOST")
    _stop(src["max_http_requests"] == 2, "TASK194F_HTTP_BUDGET")
    _stop(src["querydata_calls"] == 0, "TASK194F_QUERYDATA")
    out=obj["output"]
    _stop(out["class_count_materialized"] is False, "TASK194F_NO_MATERIALIZE")
    _stop(out["raw_models_persisted"] is False and out["raw_embedded_binary_persisted"] is False, "TASK194F_RAW")
    _stop(out["unrelated_municipality_rows_persisted"] is False, "TASK194F_UNRELATED_ROWS")
    _stop(all(out[k] is False for k in ("drive_write","serving","publication","schedule","recurrence")), "TASK194F_EFFECTS")
    return obj


def exact_auth_comment(main_sha: str, contract_path: str | Path = DEFAULT_CONTRACT) -> str:
    obj=_load(contract_path)
    _stop(len(main_sha) == 40 and all(c in "0123456789abcdef" for c in main_sha.lower()), "TASK194F_AUTH_SHA")
    return (
        "TASK194F_INEP_DATA_EMBEDDED_AUTHORIZED "
        f"main={main_sha} issue={obj['authorization_issue']} max_http_requests=2 querydata=0"
    )


def _decode_embedded(value: str) -> tuple[dict[str, Any] | None, bytes]:
    raw=base64.b64decode(value)
    if raw.startswith(bytes((0x1F,0x8B))):
        raw=gzip.decompress(raw)
    try:
        return json.loads(raw.decode("utf-8")), raw
    except Exception:
        return None, raw


def _matched_literals(
    obj: Any,
    tokens: list[str],
    *,
    max_items: int,
    max_chars: int,
) -> list[str]:
    normalized=[_norm(t) for t in tokens]
    found=[]
    seen=set()

    def walk(value: Any) -> None:
        if len(found) >= max_items:
            return
        if isinstance(value, str):
            if len(value) > max_chars:
                return
            n=_norm(value)
            if any(t and t in n for t in normalized):
                if value not in seen:
                    seen.add(value)
                    found.append(value)
            return
        if isinstance(value, dict):
            for v in value.values():
                walk(v)
                if len(found) >= max_items:
                    break
            return
        if isinstance(value, list):
            for v in value:
                walk(v)
                if len(found) >= max_items:
                    break

    walk(obj)
    return found


def _descriptor_select(payload: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        items=payload["data"]["descriptor"]["Select"]
    except Exception:
        return []
    result=[]
    for item in items[:80]:
        row={}
        if isinstance(item,dict):
            if "Kind" in item:
                row["kind"]=item["Kind"]
            if "Value" in item and isinstance(item["Value"],str):
                row["value"]=item["Value"][:240]
            try:
                source=item["GroupKeys"][0]["Source"]
                if isinstance(source,dict):
                    if "Property" in source:
                        row["property"]=source["Property"]
                    if "Entity" in source:
                        row["entity"]=source["Entity"]
            except Exception:
                pass
        if row:
            result.append(row)
    return result


def _config_summary(raw: Any, tokens: list[str]) -> dict[str, Any] | None:
    if not raw:
        return None
    if isinstance(raw,str):
        text=raw
        try:
            obj=json.loads(raw)
        except Exception:
            obj={}
    else:
        obj=raw if isinstance(raw,dict) else {}
        text=json.dumps(raw,ensure_ascii=False,sort_keys=True)
    matches=sorted({t for t in tokens if _norm(t) in _norm(text)})
    if not matches:
        return None
    single=obj.get("singleVisual") if isinstance(obj,dict) else {}
    return {
        "sha256":hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "chars":len(text),
        "name":str(obj.get("name") or "")[:120] if isinstance(obj,dict) else "",
        "visual_type":str((single or {}).get("visualType") or "")[:120] if isinstance(single,dict) else "",
        "matched_tokens":matches,
        "top_level_keys":sorted(obj.keys())[:40] if isinstance(obj,dict) else [],
    }


def sanitize_models(models: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    exploration=models.get("exploration") or {}
    sections=exploration.get("sections") or []
    _stop(bool(sections), "TASK194F_SECTIONS")
    tokens=contract["target_tokens"]
    limits=contract["limits"]
    key_hist=Counter()
    section_summaries=[]
    candidates=[]
    embedded_count=0
    config_count=0
    query_count=0

    for section in sections:
        name=str(section.get("displayName") or section.get("name") or "")
        containers=section.get("visualContainers") or []
        section_keys=Counter()
        section_embedded=0
        section_config=0
        section_query=0
        for idx,c in enumerate(containers):
            if not isinstance(c,dict):
                continue
            for k in c:
                key_hist[k]+=1
                section_keys[k]+=1
            if c.get("config") is not None:
                config_count+=1
                section_config+=1
            if c.get("query") is not None:
                query_count+=1
                section_query+=1
            if c.get("dataBinaryBase64Encoded"):
                embedded_count+=1
                section_embedded+=1

            cfg=_config_summary(c.get("config"), tokens)
            payload_match=None
            embedded=c.get("dataBinaryBase64Encoded")
            if embedded:
                payload,raw=_decode_embedded(str(embedded))
                if payload is not None:
                    literals=_matched_literals(
                        payload,
                        tokens,
                        max_items=int(limits["max_matched_literals_per_payload"]),
                        max_chars=int(limits["max_literal_chars"]),
                    )
                    payload_text=_norm(json.dumps(payload,ensure_ascii=False,sort_keys=True))
                    matched_tokens=sorted({t for t in tokens if _norm(t) in payload_text})
                    if matched_tokens or literals:
                        payload_match={
                            "sha256":hashlib.sha256(raw).hexdigest(),
                            "decoded_bytes":len(raw),
                            "matched_tokens":matched_tokens,
                            "matched_literals":literals,
                            "descriptor_select":_descriptor_select(payload),
                        }

            if (cfg or payload_match) and len(candidates) < int(limits["max_candidate_visuals"]):
                candidates.append({
                    "section":name,
                    "container_index":idx,
                    "container_keys":sorted(c.keys())[:50],
                    "config_match":cfg,
                    "embedded_match":payload_match,
                })

        section_summaries.append({
            "section":name,
            "visual_count":len(containers),
            "container_key_counts":dict(sorted(section_keys.items())),
            "config_count":section_config,
            "query_count":section_query,
            "embedded_count":section_embedded,
        })

    model_rows=models.get("models") or []
    return {
        "schema":"TASK194F_INEP_DATA_EMBEDDED_VISUAL_SANITIZED_V1",
        "status":"PASS",
        "model":{
            "id":str((model_rows[0] if model_rows else {}).get("id") or ""),
            "db_name":str((model_rows[0] if model_rows else {}).get("dbName") or ""),
        },
        "section_count":len(sections),
        "visual_count":sum(x["visual_count"] for x in section_summaries),
        "config_count":config_count,
        "query_count":query_count,
        "embedded_payload_count":embedded_count,
        "container_key_counts":dict(sorted(key_hist.items())),
        "sections":section_summaries,
        "candidate_count":len(candidates),
        "candidates":candidates,
        "querydata_called":False,
        "class_count_materialized":False,
        "raw_models_persisted":False,
        "raw_embedded_binary_persisted":False,
        "unrelated_municipality_rows_persisted":False,
    }


def run(output_path: str | Path, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj=_load(contract_path)
    src=obj["source"]
    token=decode_report_token(src["report_url"])
    _stop(token["resource_key"] == src["expected_resource_key"], "TASK194F_RESOURCE_KEY")
    _stop(token["tenant_id"] == src["expected_tenant_id"], "TASK194F_TENANT")

    main_sha=str(os.environ.get("GITHUB_SHA") or "")
    checked=str(os.environ.get("TASK194F_CHECKED_OUT_SHA") or "")
    comment=str(os.environ.get("TASK194F_AUTH_COMMENT") or "")
    issue=str(os.environ.get("TASK194F_ISSUE_NUMBER") or "")
    _stop(main_sha == checked, "TASK194F_CHECKOUT")
    _stop(issue == str(obj["authorization_issue"]), "TASK194F_ISSUE")
    _stop(comment == exact_auth_comment(main_sha,contract_path), "TASK194F_AUTH_COMMENT")

    html_bytes,final_url=_get(src["report_url"])
    _stop(urllib.parse.urlparse(final_url).hostname == src["report_host"], "TASK194F_REPORT_HOST")
    boot=bootstrap_metadata(
        html_bytes.decode("utf-8",errors="replace"),
        src["expected_resource_key"],
        src["expected_tenant_id"],
    )
    models_url=(
        boot["cluster_api"] + "/public/reports/" + boot["resource_key"]
        + "/modelsAndExploration?preferReadOnlySession=true"
    )
    models_bytes,final_models_url=_get(
        models_url,
        headers={
            "ActivityId":boot["activity_id"],
            "RequestId":boot["request_id"],
            "X-PowerBI-ResourceKey":boot["resource_key"],
            "Origin":"https://app.powerbi.com",
            "Referer":"https://app.powerbi.com/",
        },
    )
    _stop(urllib.parse.urlparse(final_models_url).hostname == urllib.parse.urlparse(models_url).hostname, "TASK194F_MODELS_HOST")
    models=json.loads(models_bytes.decode("utf-8"))
    result=sanitize_models(models,obj)
    result["source"]={
        "official_inep_page":src["official_inep_page"],
        "report_host":src["report_host"],
        "resource_key":boot["resource_key"],
        "tenant_id":boot["tenant_id"],
        "cluster_host":urllib.parse.urlparse(boot["cluster_api"]).hostname,
        "http_requests_used":2,
        "querydata_calls":0,
    }
    result["authorization"]={
        "issue":obj["authorization_issue"],
        "main_sha":main_sha,
        "exact_comment_verified":True,
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
        "visual_count":result["visual_count"],
        "embedded_payload_count":result["embedded_payload_count"],
        "candidate_count":result["candidate_count"],
        "querydata_called":result["querydata_called"],
    },sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
