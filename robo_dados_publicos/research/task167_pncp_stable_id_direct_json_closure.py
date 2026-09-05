from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
E=ROOT/"docs/evidence/TASK_167_PNCP_STABLE_ID_DIRECT_JSON_TRAVERSAL_0.8.0.json"


def _r(cond: bool, code: str) -> None:
    if not cond:
        raise AssertionError(code)


def validate() -> dict:
    e=json.loads(E.read_text(encoding="utf-8"))
    _r(e["issue"]==546,"TASK167_ISSUE")
    _r(e["authorization"]["scope"]=="PNCP_LIVE_READ_DISCOVERY_ONLY","TASK167_AUTH")
    integ=e["integration_family_attempt"]
    _r(integ["requests"]==10 and integ["http_503_count"]==10,"TASK167_503")
    _r(integ["no_absence_conclusion_allowed"] is True,"TASK167_NO_ABSENCE")

    pub=e["public_consulta_specific_detail"]
    _r(pub["result"]=="SUCCESS_JSON_2_OF_2","TASK167_PUBLIC_DETAIL")
    records={x["id"]:x for x in pub["records"]}
    s=records["SCHOOL_PASS"]
    c=records["I00084"]
    _r(s["numeroControlePNCP"]=="45132495000140-1-000368/2026","TASK167_SCHOOL_ID")
    _r(s["processo"]=="I00055" and s["http_status"]==200,"TASK167_SCHOOL_KEYS")
    _r(s["amparoLegal"]=="Lei 14.133/2021, Art. 74, I","TASK167_SCHOOL_LEGAL")
    _r(s["fontesOrcamentarias_count"]==0,"TASK167_SCHOOL_BUDGET_EMPTY")
    _r(c["numeroControlePNCP"]=="45132495000140-1-000593/2026","TASK167_COURSE_ID")
    _r(c["processo"]=="I00084" and c["http_status"]==200,"TASK167_COURSE_KEYS")
    _r(c["amparoLegal"]=="Lei 14.133/2021, Art. 74, III, f","TASK167_COURSE_LEGAL")
    _r(c["fontesOrcamentarias_count"]==0,"TASK167_COURSE_BUDGET_EMPTY")

    pc=e["public_contracts_attempt"]
    _r(pc["monthly_timeouts"]==4 and pc["target_date_timeouts"]==2,"TASK167_CONTRACT_TIMEOUTS")
    _r(pc["contract_match_observed"] is False,"TASK167_NO_CONTRACT_OBS")
    _r(pc["contract_absence_proven"] is False,"TASK167_NO_CONTRACT_ABSENCE")
    _r(pc["supplier_identity_proven"] is False,"TASK167_NO_SUPPLIER")
    _r(pc["payment_identity_proven"] is False,"TASK167_NO_PAYMENT")

    ep=e["epistemic_closure"]
    _r(ep["purchase_identity_school_pass"]=="PROVEN_OFFICIAL_PUBLIC_JSON","TASK167_EP_SCHOOL")
    _r(ep["purchase_identity_i00084"]=="PROVEN_OFFICIAL_PUBLIC_JSON","TASK167_EP_COURSE")
    _r(ep["contract_identity"]=="NOT_PROVEN_ENDPOINT_UNAVAILABLE","TASK167_EP_CONTRACT")
    _r(ep["payment_identity"]=="NOT_PROVEN","TASK167_EP_PAYMENT")

    routing=e["routing_lesson"]
    _r(routing["integration_http_503_is_not_resource_absence"] is True,"TASK167_ROUTE_503")
    _r(routing["public_contract_timeout_is_not_contract_absence"] is True,"TASK167_ROUTE_TIMEOUT")
    _r(routing["reverse_engineering_required_now"] is False,"TASK167_NO_REVERSE")

    return {
        "task":e["task"],
        "school_pass_id":s["numeroControlePNCP"],
        "course_id":c["numeroControlePNCP"],
        "public_detail_successes":2,
        "integration_503_requests":10,
        "public_contract_timeout_requests":6,
        "contract_identity_proven":False,
        "status":"VALID"
    }


if __name__=="__main__":
    print(json.dumps(validate(),ensure_ascii=False,sort_keys=True))
