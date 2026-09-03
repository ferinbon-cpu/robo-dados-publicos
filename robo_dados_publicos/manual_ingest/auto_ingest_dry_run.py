from __future__ import annotations
from .drive_ingestion_controller import classify_metadata
from .source_family_maturity import execution_maturity
from .ingestion_execution_policy import decide_execution
from .folder_authorization import authorize_record


def plan_record(record, controller, maturity_registry, execution_policy, authorization_manifest=None):
    routing = classify_metadata(record, controller)
    base={"file_id":routing.file_id,"title":routing.title,"family":routing.family,"route":routing.route,"routing_reasons":list(routing.reasons)}
    if routing.route == "QUARANTINE": return {**base,"plan_state":"QUARANTINE"}
    if routing.route == "REVIEW": return {**base,"plan_state":"REVIEW"}
    maturity=execution_maturity(routing.family,maturity_registry)
    if maturity != "EXECUTION_READY_BOUNDED": return {**base,"maturity":maturity,"plan_state":"BLOCKED_MATURITY"}
    enriched=dict(record)
    auth_reasons=[]
    if authorization_manifest is not None:
        auth=authorize_record(record,routing.family,authorization_manifest)
        enriched["folder_scope_authorized"]=auth.allowed
        auth_reasons=list(auth.reasons)
    else:
        enriched["folder_scope_authorized"]=bool(record.get("folder_scope_authorized"))
    enriched["unresolved_duplicate_signal"]=bool(record.get("unresolved_duplicate_signal"))
    execution=decide_execution(enriched,routing.route,routing.family,execution_policy)
    result={**base,"maturity":maturity,"plan_state":"ELIGIBLE" if execution.allowed else "BLOCKED_POLICY","execution_reasons":list(execution.reasons)}
    if authorization_manifest is not None: result["authorization_reasons"]=auth_reasons
    return result


def summarize_plan(items):
    out={"ELIGIBLE":0,"REVIEW":0,"QUARANTINE":0,"BLOCKED_MATURITY":0,"BLOCKED_POLICY":0}
    for item in items: out[item["plan_state"]]+=1
    return out
