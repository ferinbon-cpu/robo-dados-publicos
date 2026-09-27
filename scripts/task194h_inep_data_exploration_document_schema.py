from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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
DEFAULT_CONTRACT = ROOT / "config/task194h_inep_data_exploration_document_schema.v1.json"


class Task194HStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task194HStop(code)


def _load(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK194H_INEP_DATA_EXPLORATION_DOCUMENT_SCHEMA_V1", "TASK194H_SCHEMA")
    _stop(obj.get("mode") == "T1_BOUNDED_READ_ONLY_OFFICIAL_PUBLIC_PANEL_DOCUMENT_SCHEMA", "TASK194H_MODE")
    src=obj["source"]
    _stop(urllib.parse.urlparse(src["report_url"]).hostname == src["report_host"], "TASK194H_REPORT_HOST")
    _stop(src["max_http_requests"] == 2, "TASK194H_HTTP_BUDGET")
    _stop(src["querydata_calls"] == 0, "TASK194H_QUERYDATA")
    out=obj["output"]
    _stop(out["sanitized_json_only"] is True, "TASK194H_SANITIZED_ONLY")
    _stop(out["raw_models_persisted"] is False, "TASK194H_RAW_MODELS")
    _stop(out["raw_exploration_document_persisted"] is False, "TASK194H_RAW_DOCUMENT")
    _stop(out["querydata_calls"] == 0, "TASK194H_OUTPUT_QUERYDATA")
    _stop(out["class_count_materialized"] is False, "TASK194H_NO_MATERIALIZE")
    _stop(all(out[k] is False for k in ("drive_write","serving","publication","schedule","recurrence")), "TASK194H_EFFECTS")
    return obj


def exact_auth_comment(main_sha: str, contract_path: str | Path = DEFAULT_CONTRACT) -> str:
    obj=_load(contract_path)
    _stop(len(main_sha) == 40 and all(c in "0123456789abcdef" for c in main_sha.lower()), "TASK194H_AUTH_SHA")
    return (
        "TASK194H_EXPLORATION_DOCUMENT_AUTHORIZED "
        f"main={main_sha} issue={obj['authorization_issue']} max_http_requests=2 querydata=0"
    )


def _summary(value: Any) -> dict[str, Any]:
    if isinstance(value,dict):
        return {"type":"dict","size":len(value),"keys":sorted(str(k) for k in value.keys())[:100]}
    if isinstance(value,list):
        return {"type":"list","size":len(value)}
    if isinstance(value,str):
        return {"type":"str","chars":len(value),"sha256":hashlib.sha256(value.encode("utf-8")).hexdigest()}
    if value is None:
        return {"type":"null"}
    if isinstance(value,bool):
        return {"type":"bool"}
    if isinstance(value,(int,float)):
        return {"type":"number"}
    return {"type":type(value).__name__}


def _parse_json_string(value: str) -> Any | None:
    text=value.strip()
    if len(text) < 2 or text[0] not in "[{" or text[-1] not in "]}":
        return None
    try:
        return json.loads(text)
    except Exception:
        return None


def _extract_document(models: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    exploration=models.get("exploration") or {}
    content=exploration.get("explorationContent") or {}
    _stop(isinstance(content,dict), "TASK194H_EXPLORATION_CONTENT")
    _stop("explorationDocument" in content, "TASK194H_DOCUMENT_MISSING")
    raw=content["explorationDocument"]
    meta=_summary(raw)
    if isinstance(raw,str):
        parsed=_parse_json_string(raw)
        _stop(parsed is not None, "TASK194H_DOCUMENT_NOT_JSON")
        meta["parsed_from_json_string"]=True
        return parsed,meta
    _stop(isinstance(raw,(dict,list)), "TASK194H_DOCUMENT_TYPE")
    meta["parsed_from_json_string"]=False
    return raw,meta


def _safe_identifier(key: str, value: str) -> bool:
    k=key.casefold()
    return (
        k in {"objectname","visualtype","entity","property","measure","column","table","field","name"}
        and len(value) <= 180
        and "\n" not in value
        and "\r" not in value
    )


def inspect_document(document: Any, contract: dict[str, Any]) -> dict[str, Any]:
    interesting={str(x).casefold() for x in contract["interesting_keys"]}
    tokens=[str(x).casefold() for x in contract["allowed_text_tokens"]]
    limits=contract["limits"]
    max_paths=int(limits["max_paths"])
    max_identifiers=int(limits["max_identifiers"])
    max_texts=int(limits["max_matching_texts"])
    max_depth=int(limits["max_depth"])
    max_text_chars=int(limits["max_text_chars"])

    key_hist=Counter()
    type_hist=Counter()
    interesting_paths=[]
    identifiers=[]
    matching_texts=[]
    parsed_nested_json_count=0
    candidate_object_paths=set()

    def add_identifier(path: str, key: str, value: str) -> None:
        if len(identifiers) >= max_identifiers:
            return
        identifiers.append({"path":path,"key":key,"value":value})

    def add_matching(path: str, value: str) -> None:
        if len(matching_texts) >= max_texts:
            return
        normalized=value.casefold()
        matched=sorted({tok for tok in tokens if tok in normalized})
        if not matched:
            return
        text=value.strip().replace("\n"," ").replace("\r"," ")
        if len(text) > max_text_chars:
            text=text[:max_text_chars] + "…"
        matching_texts.append({"path":path,"matched_tokens":matched,"text":text})

    def walk(value: Any, path: str, depth: int, parent_key: str = "") -> None:
        nonlocal parsed_nested_json_count
        if depth > max_depth:
            return
        type_hist[type(value).__name__]+=1
        if isinstance(value,dict):
            object_name=value.get("objectName")
            has_queryish=any(str(k).casefold() in interesting for k in value)
            if isinstance(object_name,str) and has_queryish:
                candidate_object_paths.add(path)
            for key,child in value.items():
                key_s=str(key)
                key_norm=key_s.casefold()
                key_hist[key_s]+=1
                child_path=f"{path}.{key_s}" if path else key_s
                if key_norm in interesting and len(interesting_paths) < max_paths:
                    interesting_paths.append({
                        "path":child_path,
                        "key":key_s,
                        "value_summary":_summary(child),
                    })
                if isinstance(child,str):
                    if _safe_identifier(key_s,child):
                        add_identifier(child_path,key_s,child)
                    add_matching(child_path,child)
                    parsed=_parse_json_string(child)
                    if parsed is not None and key_norm in interesting:
                        parsed_nested_json_count += 1
                        walk(parsed,child_path+"<json>",depth+1,key_s)
                walk(child,child_path,depth+1,key_s)
        elif isinstance(value,list):
            for idx,child in enumerate(value):
                walk(child,f"{path}[{idx}]",depth+1,parent_key)
        elif isinstance(value,str):
            add_matching(path,value)

    walk(document,"document",0)

    return {
        "document_root":_summary(document),
        "interesting_path_count":len(interesting_paths),
        "interesting_paths":interesting_paths,
        "identifier_count":len(identifiers),
        "identifiers":identifiers,
        "matching_text_count":len(matching_texts),
        "matching_texts":matching_texts,
        "candidate_object_path_count":len(candidate_object_paths),
        "candidate_object_paths":sorted(candidate_object_paths)[:250],
        "parsed_nested_json_count":parsed_nested_json_count,
        "key_histogram_top":dict(key_hist.most_common(180)),
        "type_histogram":dict(type_hist.most_common()),
    }


def run(output_path: str | Path, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj=_load(contract_path)
    src=obj["source"]
    token=decode_report_token(src["report_url"])
    _stop(token["resource_key"] == src["expected_resource_key"], "TASK194H_RESOURCE_KEY")
    _stop(token["tenant_id"] == src["expected_tenant_id"], "TASK194H_TENANT")

    main_sha=str(os.environ.get("GITHUB_SHA") or "")
    checked=str(os.environ.get("TASK194H_CHECKED_OUT_SHA") or "")
    comment=str(os.environ.get("TASK194H_AUTH_COMMENT") or "")
    issue=str(os.environ.get("TASK194H_ISSUE_NUMBER") or "")
    _stop(main_sha == checked, "TASK194H_CHECKOUT")
    _stop(issue == str(obj["authorization_issue"]), "TASK194H_ISSUE")
    _stop(comment == exact_auth_comment(main_sha,contract_path), "TASK194H_AUTH_COMMENT")

    html_bytes,final_url=_get(src["report_url"])
    _stop(urllib.parse.urlparse(final_url).hostname == src["report_host"], "TASK194H_REPORT_FINAL_HOST")
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
    _stop(
        urllib.parse.urlparse(final_models_url).hostname == urllib.parse.urlparse(models_url).hostname,
        "TASK194H_MODELS_FINAL_HOST",
    )
    models=json.loads(models_bytes.decode("utf-8"))
    document,document_meta=_extract_document(models)
    inspected=inspect_document(document,obj)
    result={
        "schema":"TASK194H_INEP_DATA_EXPLORATION_DOCUMENT_SCHEMA_SANITIZED_V1",
        "status":"PASS",
        "exploration_document":document_meta,
        **inspected,
        "source":{
            "official_inep_page":src["official_inep_page"],
            "report_host":src["report_host"],
            "resource_key":boot["resource_key"],
            "tenant_id":boot["tenant_id"],
            "cluster_host":urllib.parse.urlparse(boot["cluster_api"]).hostname,
            "http_requests_used":2,
            "querydata_calls":0,
        },
        "authorization":{
            "issue":obj["authorization_issue"],
            "main_sha":main_sha,
            "exact_comment_verified":True,
        },
        "querydata_called":False,
        "class_count_materialized":False,
        "raw_models_persisted":False,
        "raw_exploration_document_persisted":False,
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
        "document_type":result["document_root"]["type"],
        "interesting_path_count":result["interesting_path_count"],
        "identifier_count":result["identifier_count"],
        "matching_text_count":result["matching_text_count"],
        "parsed_nested_json_count":result["parsed_nested_json_count"],
        "querydata_called":result["querydata_called"],
    },sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
