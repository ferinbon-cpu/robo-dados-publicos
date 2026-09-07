from __future__ import annotations

import argparse
import json
import os
import urllib.parse
from pathlib import Path
from typing import Any

from scripts.task194b_inep_data_metadata_probe import (
    _get,
    bootstrap_metadata,
    decode_report_token,
)
from scripts.task194h_inep_data_exploration_document_schema import _extract_document

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "config/task194i_inep_data_turmas_visual_locator.v1.json"


class Task194IStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task194IStop(code)


def _load(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj=json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK194I_INEP_DATA_TURMAS_VISUAL_LOCATOR_V1", "TASK194I_SCHEMA")
    _stop(obj.get("mode") == "T1_BOUNDED_READ_ONLY_OFFICIAL_PUBLIC_PANEL_TURMAS_SCHEMA", "TASK194I_MODE")
    src=obj["source"]
    _stop(urllib.parse.urlparse(src["report_url"]).hostname == src["report_host"], "TASK194I_REPORT_HOST")
    _stop(src["max_http_requests"] == 2, "TASK194I_HTTP_BUDGET")
    _stop(src["querydata_calls"] == 0, "TASK194I_QUERYDATA")
    out=obj["output"]
    _stop(out["raw_models_persisted"] is False, "TASK194I_RAW_MODELS")
    _stop(out["raw_exploration_document_persisted"] is False, "TASK194I_RAW_DOCUMENT")
    _stop(out["querydata_calls"] == 0, "TASK194I_OUTPUT_QUERYDATA")
    _stop(out["class_count_materialized"] is False, "TASK194I_NO_MATERIALIZE")
    _stop(all(out[k] is False for k in ("drive_write","serving","publication","schedule","recurrence")), "TASK194I_EFFECTS")
    return obj


def exact_auth_comment(main_sha: str, contract_path: str | Path = DEFAULT_CONTRACT) -> str:
    obj=_load(contract_path)
    _stop(len(main_sha) == 40 and all(c in "0123456789abcdef" for c in main_sha.lower()), "TASK194I_AUTH_SHA")
    return (
        "TASK194I_TURMAS_VISUAL_AUTHORIZED "
        f"main={main_sha} issue={obj['authorization_issue']} max_http_requests=2 querydata=0"
    )


def _walk_strings(value: Any, path: str):
    if isinstance(value,dict):
        for key,child in value.items():
            child_path=f"{path}.{key}" if path else str(key)
            if isinstance(child,str):
                yield child_path,str(key),child
            yield from _walk_strings(child,child_path)
    elif isinstance(value,list):
        for idx,child in enumerate(value):
            yield from _walk_strings(child,f"{path}[{idx}]")


def _short(value: str, limit: int) -> str:
    text=value.strip().replace("\n"," ").replace("\r"," ")
    return text if len(text) <= limit else text[:limit] + "…"


def locate_turmas_visuals(document: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    pages=(document.get("pages") or {}).get("pages") or []
    _stop(isinstance(pages,list), "TASK194I_PAGES")
    token=str(contract["match_token"]).casefold()
    identifier_keys={str(x).casefold() for x in contract["identifier_keys"]}
    context_tokens=[str(x).casefold() for x in contract["allowed_context_tokens"]]
    limits=contract["limits"]

    results=[]
    for pi,page in enumerate(pages):
        if not isinstance(page,dict):
            continue
        visuals=page.get("visualContainers") or []
        if not isinstance(visuals,list):
            continue
        page_name=str(page.get("name") or page.get("objectName") or "")
        page_display=str(page.get("displayName") or "")
        for vi,visual in enumerate(visuals):
            if not isinstance(visual,dict):
                continue
            strings=list(_walk_strings(visual,"visual"))
            matches=[
                {"path":p,"text":_short(v,int(limits["max_text_chars"]))}
                for p,k,v in strings
                if token in v.casefold()
            ]
            if not matches:
                continue

            ids=[]
            seen=set()
            for p,k,v in strings:
                key_norm=k.casefold()
                if key_norm not in identifier_keys:
                    continue
                if len(v) > int(limits["max_text_chars"]) or "\n" in v or "\r" in v:
                    continue
                tup=(p,k,v)
                if tup in seen:
                    continue
                seen.add(tup)
                ids.append({"path":p,"key":k,"value":v})
                if len(ids) >= int(limits["max_identifiers_per_visual"]):
                    break

            context=[]
            for p,k,v in strings:
                low=v.casefold()
                matched=sorted({t for t in context_tokens if t in low})
                if not matched:
                    continue
                context.append({
                    "path":p,
                    "matched_tokens":matched,
                    "text":_short(v,int(limits["max_text_chars"])),
                })
                if len(context) >= int(limits["max_matches_per_visual"]):
                    break

            content=visual.get("content") or {}
            visual_def=content.get("visual") if isinstance(content,dict) else {}
            if not isinstance(visual_def,dict):
                visual_def={}
            visual_type=str(visual_def.get("visualType") or "")
            object_name=str(visual.get("objectName") or visual_def.get("objectName") or "")

            query_ids=[x for x in ids if ".query." in x["path"] or ".queryState." in x["path"]]
            filter_ids=[x for x in ids if "filter" in x["path"].casefold()]
            score=sum(
                1 for x in ids
                if token in x["value"].casefold()
                or x["value"].upper().startswith("QT_TUR")
                or "TURMA" in x["value"].upper()
            )
            title_match=any("title" in x["path"].casefold() for x in matches)

            results.append({
                "page_index":pi,
                "page_name":page_name,
                "page_display_name":page_display,
                "visual_index":vi,
                "object_name":object_name,
                "visual_type":visual_type,
                "match_count":len(matches),
                "matches":matches[:int(limits["max_matches_per_visual"])],
                "identifier_count":len(ids),
                "identifiers":ids,
                "query_identifiers":query_ids,
                "filter_identifiers":filter_ids,
                "turma_field_score":score,
                "title_match":title_match,
            })
            if len(results) >= int(limits["max_visuals"]):
                break
        if len(results) >= int(limits["max_visuals"]):
            break

    _stop(bool(results), "TASK194I_NO_TURM_VISUAL")
    ranked=sorted(
        results,
        key=lambda x:(x["turma_field_score"], int(x["title_match"]), x["match_count"]),
        reverse=True,
    )
    return {
        "page_count":len(pages),
        "matched_visual_count":len(results),
        "matched_visuals":results,
        "ranked_candidates":ranked[:30],
    }


def run(output_path: str | Path, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj=_load(contract_path)
    src=obj["source"]
    token=decode_report_token(src["report_url"])
    _stop(token["resource_key"] == src["expected_resource_key"], "TASK194I_RESOURCE_KEY")
    _stop(token["tenant_id"] == src["expected_tenant_id"], "TASK194I_TENANT")

    main_sha=str(os.environ.get("GITHUB_SHA") or "")
    checked=str(os.environ.get("TASK194I_CHECKED_OUT_SHA") or "")
    comment=str(os.environ.get("TASK194I_AUTH_COMMENT") or "")
    issue=str(os.environ.get("TASK194I_ISSUE_NUMBER") or "")
    _stop(main_sha == checked, "TASK194I_CHECKOUT")
    _stop(issue == str(obj["authorization_issue"]), "TASK194I_ISSUE")
    _stop(comment == exact_auth_comment(main_sha,contract_path), "TASK194I_AUTH_COMMENT")

    html_bytes,final_url=_get(src["report_url"])
    _stop(urllib.parse.urlparse(final_url).hostname == src["report_host"], "TASK194I_REPORT_FINAL_HOST")
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
        "TASK194I_MODELS_FINAL_HOST",
    )
    models=json.loads(models_bytes.decode("utf-8"))
    document,document_meta=_extract_document(models)
    _stop(isinstance(document,dict), "TASK194I_DOCUMENT_ROOT")
    located=locate_turmas_visuals(document,obj)
    result={
        "schema":"TASK194I_INEP_DATA_TURMAS_VISUAL_LOCATOR_SANITIZED_V1",
        "status":"PASS",
        "exploration_document_sha256":document_meta.get("sha256"),
        **located,
        "source":{
            "official_inep_page":src["official_inep_page"],
            "report_host":src["report_host"],
            "resource_key":boot["resource_key"],
            "tenant_id":boot["tenant_id"],
            "cluster_host":urllib.parse.urlparse(boot["cluster_api"]).hostname,
            "model_id":str((models.get("models") or [{}])[0].get("id") or ""),
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
    top=result["ranked_candidates"][0]
    print(json.dumps({
        "status":result["status"],
        "matched_visual_count":result["matched_visual_count"],
        "top_page_index":top["page_index"],
        "top_visual_index":top["visual_index"],
        "top_turma_field_score":top["turma_field_score"],
        "top_visual_type":top["visual_type"],
        "querydata_called":result["querydata_called"],
    },sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
