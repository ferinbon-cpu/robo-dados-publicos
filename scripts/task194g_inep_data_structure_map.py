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
DEFAULT_CONTRACT = ROOT / "config/task194g_inep_data_structure_map.v1.json"


class Task194GStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task194GStop(code)


def _load(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK194G_INEP_DATA_STRUCTURE_MAP_V1", "TASK194G_SCHEMA")
    _stop(obj.get("mode") == "T1_BOUNDED_READ_ONLY_OFFICIAL_PUBLIC_PANEL_STRUCTURE", "TASK194G_MODE")
    src=obj["source"]
    _stop(urllib.parse.urlparse(src["report_url"]).hostname == src["report_host"], "TASK194G_REPORT_HOST")
    _stop(src["max_http_requests"] == 2, "TASK194G_HTTP_BUDGET")
    _stop(src["querydata_calls"] == 0, "TASK194G_QUERYDATA")
    out=obj["output"]
    _stop(out["raw_models_persisted"] is False, "TASK194G_RAW_MODELS")
    _stop(out["querydata_calls"] == 0, "TASK194G_OUTPUT_QUERYDATA")
    _stop(out["class_count_materialized"] is False, "TASK194G_NO_MATERIALIZE")
    _stop(all(out[k] is False for k in ("drive_write","serving","publication","schedule","recurrence")), "TASK194G_EFFECTS")
    return obj


def exact_auth_comment(main_sha: str, contract_path: str | Path = DEFAULT_CONTRACT) -> str:
    obj=_load(contract_path)
    _stop(len(main_sha) == 40 and all(c in "0123456789abcdef" for c in main_sha.lower()), "TASK194G_AUTH_SHA")
    return (
        "TASK194G_INEP_DATA_STRUCTURE_AUTHORIZED "
        f"main={main_sha} issue={obj['authorization_issue']} max_http_requests=2 querydata=0"
    )


def _summary(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {"type":"dict","size":len(value),"keys":sorted(str(k) for k in value.keys())[:80]}
    if isinstance(value, list):
        return {"type":"list","size":len(value)}
    if isinstance(value, str):
        return {
            "type":"str",
            "chars":len(value),
            "sha256":hashlib.sha256(value.encode("utf-8")).hexdigest(),
        }
    if value is None:
        return {"type":"null"}
    if isinstance(value, bool):
        return {"type":"bool"}
    if isinstance(value, (int,float)):
        return {"type":"number"}
    return {"type":type(value).__name__}


def _join(path: str, part: str) -> str:
    return part if not path else path + "." + part


def _extract_objectnames(models: dict[str, Any]) -> set[str]:
    names=set()
    exploration=models.get("exploration") or {}
    for section in exploration.get("sections") or []:
        for container in section.get("visualContainers") or []:
            if isinstance(container,dict):
                value=container.get("objectName")
                if isinstance(value,str) and value:
                    names.add(value)
    return names


def structural_map(models: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    tokens=[str(x).casefold() for x in contract["interesting_key_tokens"]]
    limits=contract["limits"]
    max_paths=int(limits["max_interesting_paths"])
    max_cross=int(limits["max_objectname_crossrefs"])
    max_depth=int(limits["max_depth"])
    objectnames=_extract_objectnames(models)

    interesting=[]
    crossrefs=[]
    key_hist=Counter()
    type_hist=Counter()
    branch_summaries={}

    for key,value in models.items():
        branch_summaries[str(key)] = _summary(value)

    primary_objectname_paths=set()

    exploration=models.get("exploration") or {}
    for si,section in enumerate(exploration.get("sections") or []):
        for vi,container in enumerate(section.get("visualContainers") or []):
            if isinstance(container,dict) and isinstance(container.get("objectName"),str):
                primary_objectname_paths.add(
                    f"exploration.sections[{si}].visualContainers[{vi}].objectName"
                )

    def walk(value: Any, path: str, depth: int) -> None:
        if depth > max_depth:
            return
        type_hist[type(value).__name__]+=1
        if isinstance(value,dict):
            for key,child in value.items():
                key_s=str(key)
                key_hist[key_s]+=1
                child_path=_join(path,key_s)
                key_norm=key_s.casefold()
                if any(tok in key_norm for tok in tokens) and len(interesting) < max_paths:
                    interesting.append({
                        "path":child_path,
                        "key":key_s,
                        "value_summary":_summary(child),
                    })
                if key_s in objectnames and len(crossrefs) < max_cross:
                    crossrefs.append({
                        "kind":"dict_key_equals_objectName",
                        "objectName":key_s,
                        "path":child_path,
                        "value_summary":_summary(child),
                    })
                if isinstance(child,str) and child in objectnames and len(crossrefs) < max_cross:
                    if child_path not in primary_objectname_paths:
                        crossrefs.append({
                            "kind":"string_value_equals_objectName",
                            "objectName":child,
                            "path":child_path,
                        })
                walk(child,child_path,depth+1)
        elif isinstance(value,list):
            for idx,child in enumerate(value):
                walk(child,f"{path}[{idx}]",depth+1)

    walk(models,"",0)

    cross_objectnames=sorted({x["objectName"] for x in crossrefs})
    exploration_summary=_summary(models.get("exploration"))
    model_rows=models.get("models") or []
    first_model_summary=_summary(model_rows[0]) if model_rows else {"type":"missing"}
    report_summary=_summary((models.get("exploration") or {}).get("report"))
    sections=(models.get("exploration") or {}).get("sections") or []
    first_section_summary=_summary(sections[0]) if sections else {"type":"missing"}

    return {
        "schema":"TASK194G_INEP_DATA_STRUCTURE_MAP_SANITIZED_V1",
        "status":"PASS",
        "top_level":branch_summaries,
        "structural_summaries":{
            "exploration":exploration_summary,
            "first_model":first_model_summary,
            "report":report_summary,
            "first_section":first_section_summary,
        },
        "objectnames":{
            "visual_container_unique_count":len(objectnames),
            "crossreferenced_unique_count":len(cross_objectnames),
            "crossreferenced_sample":cross_objectnames[:100],
            "crossref_count":len(crossrefs),
            "crossrefs":crossrefs,
        },
        "interesting_path_count":len(interesting),
        "interesting_paths":interesting,
        "key_histogram_top":dict(key_hist.most_common(120)),
        "type_histogram":dict(type_hist.most_common()),
        "querydata_called":False,
        "class_count_materialized":False,
        "raw_models_persisted":False,
    }


def run(output_path: str | Path, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj=_load(contract_path)
    src=obj["source"]
    token=decode_report_token(src["report_url"])
    _stop(token["resource_key"] == src["expected_resource_key"], "TASK194G_RESOURCE_KEY")
    _stop(token["tenant_id"] == src["expected_tenant_id"], "TASK194G_TENANT")

    main_sha=str(os.environ.get("GITHUB_SHA") or "")
    checked=str(os.environ.get("TASK194G_CHECKED_OUT_SHA") or "")
    comment=str(os.environ.get("TASK194G_AUTH_COMMENT") or "")
    issue=str(os.environ.get("TASK194G_ISSUE_NUMBER") or "")
    _stop(main_sha == checked, "TASK194G_CHECKOUT")
    _stop(issue == str(obj["authorization_issue"]), "TASK194G_ISSUE")
    _stop(comment == exact_auth_comment(main_sha,contract_path), "TASK194G_AUTH_COMMENT")

    html_bytes,final_url=_get(src["report_url"])
    _stop(urllib.parse.urlparse(final_url).hostname == src["report_host"], "TASK194G_REPORT_FINAL_HOST")
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
        "TASK194G_MODELS_FINAL_HOST",
    )
    models=json.loads(models_bytes.decode("utf-8"))
    result=structural_map(models,obj)
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
        "interesting_path_count":result["interesting_path_count"],
        "objectname_crossref_count":result["objectnames"]["crossref_count"],
        "crossreferenced_unique_count":result["objectnames"]["crossreferenced_unique_count"],
        "querydata_called":result["querydata_called"],
    },sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
