from __future__ import annotations
import argparse,json,os,urllib.parse
from pathlib import Path
from typing import Any
from scripts.task194b_inep_data_metadata_probe import _get,bootstrap_metadata,decode_report_token

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"config/task194h_inep_resource_index.v1.json"
class Task194HStop(RuntimeError): pass
def _stop(c,code):
    if not c: raise Task194HStop(code)
def _load(path=DEFAULT_CONTRACT):
    o=json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(o.get("schema")=="TASK194H_INEP_RESOURCE_INDEX_V1","TASK194H_SCHEMA")
    _stop(o["source"]["max_http_requests"]==2 and o["source"]["blob_gets"]==0 and o["source"]["querydata_calls"]==0,"TASK194H_BUDGET")
    return o
def exact_auth_comment(sha,contract_path=DEFAULT_CONTRACT):
    o=_load(contract_path); _stop(len(sha)==40,"TASK194H_SHA")
    return f"TASK194H_INEP_RESOURCE_INDEX_AUTHORIZED main={sha} issue={o['authorization_issue']} max_http_requests=2 blob_gets=0 querydata=0"

def _scalar(v):
    return isinstance(v,(str,int,float,bool)) or v is None

def resource_index(models:dict[str,Any],contract:dict[str,Any])->dict[str,Any]:
    allowed=set(contract["allowed_scalar_keys"])
    records=[]; branch_summaries=[]
    target_branch_names={"resourcePackages","pbixResources","pods"}
    def walk(v,path="",inside=False):
        if isinstance(v,dict):
            for k,child in v.items():
                p=f"{path}.{k}" if path else str(k)
                now=inside or k in target_branch_names
                if k in target_branch_names:
                    branch_summaries.append({"path":p,"type":type(child).__name__,"size":len(child) if isinstance(child,(dict,list,str)) else None})
                if now and isinstance(child,dict):
                    rec={}
                    for ak,av in child.items():
                        if ak in allowed and _scalar(av):
                            rec[ak]=av
                    if rec and ("path" in rec or "resourcePackageItemBlobInfoId" in rec or "resourcePackageId" in rec):
                        rec["object_path"]=p
                        records.append(rec)
                walk(child,p,now)
        elif isinstance(v,list):
            for i,child in enumerate(v): walk(child,f"{path}[{i}]",inside)
    walk(models)
    # de-duplicate deterministically
    uniq=[]; seen=set()
    for r in records:
        key=json.dumps(r,sort_keys=True,ensure_ascii=False)
        if key not in seen: seen.add(key); uniq.append(r)
    return {
      "schema":"TASK194H_INEP_RESOURCE_INDEX_SANITIZED_V1","status":"PASS",
      "branch_summaries":branch_summaries,
      "resource_record_count":len(uniq),"resource_records":uniq,
      "blob_id_count":len({str(r.get("resourcePackageItemBlobInfoId")) for r in uniq if r.get("resourcePackageItemBlobInfoId") is not None}),
      "paths":[str(r["path"]) for r in uniq if r.get("path") is not None],
      "blob_gets":0,"querydata_called":False,"class_count_materialized":False,"raw_models_persisted":False,"blob_content_persisted":False
    }

def run(output_path,contract_path=DEFAULT_CONTRACT):
    o=_load(contract_path); s=o["source"]; token=decode_report_token(s["report_url"])
    _stop(token["resource_key"]==s["expected_resource_key"],"TASK194H_RK"); _stop(token["tenant_id"]==s["expected_tenant_id"],"TASK194H_TENANT")
    sha=os.environ.get("GITHUB_SHA",""); _stop(os.environ.get("TASK194H_CHECKED_OUT_SHA","")==sha,"TASK194H_CHECKOUT")
    _stop(os.environ.get("TASK194H_ISSUE_NUMBER","")==str(o["authorization_issue"]),"TASK194H_ISSUE")
    _stop(os.environ.get("TASK194H_AUTH_COMMENT","")==exact_auth_comment(sha,contract_path),"TASK194H_AUTH")
    html,final=_get(s["report_url"]); _stop(urllib.parse.urlparse(final).hostname==s["report_host"],"TASK194H_HOST")
    boot=bootstrap_metadata(html.decode("utf-8",errors="replace"),s["expected_resource_key"],s["expected_tenant_id"])
    url=boot["cluster_api"]+"/public/reports/"+boot["resource_key"]+"/modelsAndExploration?preferReadOnlySession=true"
    body,final2=_get(url,headers={"ActivityId":boot["activity_id"],"RequestId":boot["request_id"],"X-PowerBI-ResourceKey":boot["resource_key"],"Origin":"https://app.powerbi.com","Referer":"https://app.powerbi.com/"})
    _stop(urllib.parse.urlparse(final2).hostname==urllib.parse.urlparse(url).hostname,"TASK194H_MODELS_HOST")
    result=resource_index(json.loads(body.decode("utf-8")),o)
    result["source"]={"resource_key":boot["resource_key"],"cluster_host":urllib.parse.urlparse(boot["cluster_api"]).hostname,"http_requests_used":2,"blob_gets":0,"querydata_calls":0}
    result["authorization"]={"issue":o["authorization_issue"],"main_sha":sha,"exact_comment_verified":True}
    p=Path(output_path); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return result
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); ap.add_argument("--contract",default=str(DEFAULT_CONTRACT)); a=ap.parse_args()
    r=run(a.output,a.contract); print(json.dumps({"status":r["status"],"resource_record_count":r["resource_record_count"],"blob_id_count":r["blob_id_count"],"blob_gets":0,"querydata":0},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
