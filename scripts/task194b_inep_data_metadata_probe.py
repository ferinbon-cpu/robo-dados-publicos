from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "config/task194b_inep_data_metadata_probe.v1.json"


class Task194BStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task194BStop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK194B_INEP_DATA_METADATA_PROBE_V1", "TASK194B_SCHEMA")
    _stop(obj.get("mode") == "T1_BOUNDED_READ_ONLY_OFFICIAL_PUBLIC_PANEL_METADATA", "TASK194B_MODE")
    source = obj["source"]
    _stop(urllib.parse.urlparse(source["report_url"]).hostname == source["report_host"], "TASK194B_REPORT_HOST")
    _stop(source["max_http_requests"] == 2, "TASK194B_REQUEST_BUDGET")
    out = obj["output"]
    _stop(out["querydata_calls"] == 0, "TASK194B_QUERYDATA")
    _stop(out["raw_html_persisted"] is False and out["raw_models_persisted"] is False, "TASK194B_RAW_PERSISTENCE")
    _stop(all(out[k] is False for k in ("drive_write","serving","publication","schedule","recurrence")), "TASK194B_REMOTE_EFFECT")
    return obj


def decode_report_token(report_url: str) -> dict[str, str]:
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(report_url).query)
    token = qs.get("r", [""])[0]
    _stop(bool(token), "TASK194B_REPORT_TOKEN")
    padding = "=" * (-len(token) % 4)
    try:
        obj = json.loads(base64.urlsafe_b64decode(token + padding).decode("utf-8"))
    except Exception as exc:
        raise Task194BStop("TASK194B_REPORT_TOKEN_DECODE") from exc
    _stop(set(obj) >= {"k","t"}, "TASK194B_REPORT_TOKEN_FIELDS")
    return {"resource_key": str(obj["k"]), "tenant_id": str(obj["t"])}


def exact_auth_comment(main_sha: str, contract_path: str | Path = DEFAULT_CONTRACT) -> str:
    obj = load_contract(contract_path)
    _stop(len(main_sha) == 40 and all(c in "0123456789abcdef" for c in main_sha.lower()), "TASK194B_AUTH_SHA")
    return (
        "TASK194B_INEP_DATA_METADATA_AUTHORIZED "
        f"main={main_sha} issue={obj['authorization_issue']} max_http_requests=2 querydata=0"
    )


def _get(url: str, headers: dict[str, str] | None = None) -> tuple[bytes, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent":"robo-dados-publicos-task194b/0.8.0",
            "Accept":"application/json,text/html;q=0.9,*/*;q=0.1",
            **(headers or {}),
        },
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read(), response.geturl()


def _extract(pattern: str, text: str, code: str) -> str:
    match = re.search(pattern, text, flags=re.I | re.S)
    _stop(match is not None, code)
    return match.group(1)


def bootstrap_metadata(html: str, expected_resource_key: str, expected_tenant_id: str) -> dict[str, str]:
    # Current Publish-to-Web HTML exposes these values as JS variables.
    resource_key = _extract(r"var\s+resourceKey\s*=\s*'([^']+)'", html, "TASK194B_HTML_RESOURCE_KEY")
    tenant_id = _extract(r"var\s+tenantId\s*=\s*'([^']+)'", html, "TASK194B_HTML_TENANT")
    cluster = _extract(r"var\s+resolvedClusterUri\s*=\s*'([^']+)'", html, "TASK194B_HTML_CLUSTER")
    activity = _extract(r"var\s+telemetrySessionId\s*=\s*'([^']+)'", html, "TASK194B_HTML_ACTIVITY")
    request_id = _extract(
        r"function\s+getModelsAndExploration\(\).*?var\s+requestId\s*=\s*'([^']+)'",
        html,
        "TASK194B_HTML_REQUEST",
    )
    _stop(resource_key == expected_resource_key, "TASK194B_RESOURCE_KEY_DRIFT")
    _stop(tenant_id == expected_tenant_id, "TASK194B_TENANT_DRIFT")
    cluster_api = cluster.replace("-redirect.", "-api.")
    _stop(cluster_api.startswith("https://") and ".analysis.windows.net" in cluster_api, "TASK194B_CLUSTER")
    return {
        "resource_key":resource_key,
        "tenant_id":tenant_id,
        "cluster_api":cluster_api.rstrip("/"),
        "activity_id":activity,
        "request_id":request_id,
    }


def _literal_title(config: dict[str, Any]) -> str:
    try:
        return str(
            config["singleVisual"]["vcObjects"]["title"][0]["properties"]["text"]["expr"]["Literal"]["Value"]
        ).strip("'")
    except Exception:
        return ""


def sanitize_models(models: dict[str, Any], keywords: list[str]) -> dict[str, Any]:
    model_rows = models.get("models") or []
    _stop(bool(model_rows), "TASK194B_MODELS_EMPTY")
    exploration = models.get("exploration") or {}
    sections = exploration.get("sections") or []
    _stop(bool(sections), "TASK194B_SECTIONS_EMPTY")
    keys = [k.casefold() for k in keywords]
    section_out=[]
    match_out=[]
    visual_count=0
    for section in sections:
        section_name=str(section.get("displayName") or section.get("name") or "")
        containers=section.get("visualContainers") or []
        section_out.append({
            "name":str(section.get("name") or ""),
            "display_name":section_name,
            "visual_count":len(containers),
        })
        for c in containers:
            visual_count += 1
            config_raw=c.get("config") or "{}"
            query_raw=c.get("query") or ""
            try:
                config=json.loads(config_raw) if isinstance(config_raw,str) else dict(config_raw)
            except Exception:
                config={}
            visual_type=str((config.get("singleVisual") or {}).get("visualType") or "")
            title=_literal_title(config)
            haystack=(section_name+" "+title+" "+visual_type+" "+str(config_raw)+" "+str(query_raw)).casefold()
            matched=sorted({k for k in keys if k in haystack})
            if matched:
                # Query metadata is retained only for keyword-matched visuals and is still metadata, not result data.
                query_obj=None
                if query_raw:
                    try:
                        query_obj=json.loads(query_raw) if isinstance(query_raw,str) else query_raw
                    except Exception:
                        query_obj={"unparsed_length":len(str(query_raw))}
                match_out.append({
                    "section":section_name,
                    "visual_type":visual_type,
                    "title":title,
                    "matched_keywords":matched,
                    "query":query_obj,
                })
    report=exploration.get("report") or {}
    return {
        "schema":"TASK194B_INEP_DATA_SANITIZED_METADATA_V1",
        "status":"PASS",
        "model":{
            "id":str(model_rows[0].get("id") or ""),
            "db_name":str(model_rows[0].get("dbName") or ""),
        },
        "report":{
            "object_id":str(report.get("objectId") or ""),
            "name":str(report.get("name") or ""),
        },
        "section_count":len(sections),
        "visual_count":visual_count,
        "sections":section_out,
        "keyword_visual_count":len(match_out),
        "keyword_visuals":match_out,
        "querydata_called":False,
        "raw_payload_persisted":False,
    }


def run(output_path: str | Path, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj=load_contract(contract_path)
    source=obj["source"]
    token=decode_report_token(source["report_url"])
    _stop(token["resource_key"] == source["expected_resource_key"], "TASK194B_TOKEN_RESOURCE_KEY")
    _stop(token["tenant_id"] == source["expected_tenant_id"], "TASK194B_TOKEN_TENANT")

    main_sha=str(os.environ.get("GITHUB_SHA") or "")
    checked=str(os.environ.get("TASK194B_CHECKED_OUT_SHA") or "")
    comment=str(os.environ.get("TASK194B_AUTH_COMMENT") or "")
    issue=str(os.environ.get("TASK194B_ISSUE_NUMBER") or "")
    _stop(main_sha == checked, "TASK194B_CHECKOUT_SHA")
    _stop(issue == str(obj["authorization_issue"]), "TASK194B_ISSUE")
    _stop(comment == exact_auth_comment(main_sha, contract_path), "TASK194B_AUTH_COMMENT")

    html_bytes, final_url=_get(source["report_url"])
    _stop(urllib.parse.urlparse(final_url).hostname == source["report_host"], "TASK194B_FINAL_REPORT_HOST")
    html=html_bytes.decode("utf-8",errors="replace")
    boot=bootstrap_metadata(html, source["expected_resource_key"], source["expected_tenant_id"])
    models_url=(
        boot["cluster_api"] + "/public/reports/" + boot["resource_key"]
        + "/modelsAndExploration?preferReadOnlySession=true"
    )
    models_bytes, final_models_url=_get(
        models_url,
        headers={
            "ActivityId":boot["activity_id"],
            "RequestId":boot["request_id"],
            "X-PowerBI-ResourceKey":boot["resource_key"],
            "Origin":"https://app.powerbi.com",
            "Referer":"https://app.powerbi.com/",
        },
    )
    _stop(urllib.parse.urlparse(final_models_url).hostname == urllib.parse.urlparse(models_url).hostname, "TASK194B_MODELS_REDIRECT")
    models=json.loads(models_bytes.decode("utf-8"))
    result=sanitize_models(models, obj["keyword_scan"])
    result["source"]={
        "official_inep_page":source["official_inep_page"],
        "report_host":source["report_host"],
        "resource_key":boot["resource_key"],
        "tenant_id":boot["tenant_id"],
        "cluster_host":urllib.parse.urlparse(boot["cluster_api"]).hostname,
        "http_requests_used":2,
    }
    result["authorization"]={"issue":obj["authorization_issue"],"main_sha":main_sha,"exact_comment_verified":True}
    path=Path(output_path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True)
    parser.add_argument("--contract",default=str(DEFAULT_CONTRACT))
    args=parser.parse_args()
    result=run(args.output,args.contract)
    print(json.dumps({
        "status":result["status"],
        "section_count":result["section_count"],
        "visual_count":result["visual_count"],
        "keyword_visual_count":result["keyword_visual_count"],
        "querydata_called":result["querydata_called"],
    },sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
