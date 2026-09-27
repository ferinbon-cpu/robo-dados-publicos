from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
E=ROOT/"docs/evidence/TASK_166_PNCP_MODALITY9_DIRECT_JSON_SWEEP_0.8.0.json"


def _r(cond: bool, code: str) -> None:
    if not cond:
        raise AssertionError(code)


def validate() -> dict:
    e=json.loads(E.read_text(encoding="utf-8"))
    _r(e["issue"]==544,"TASK166_ISSUE")
    _r(e["authorization"]["scope"]=="PNCP_LIVE_READ_DISCOVERY_ONLY","TASK166_AUTH")
    p=e["partitioned_exhaustive_result"]
    _r(p["status"]=="EXHAUSTIVE_COMPLETE","TASK166_STATUS")
    _r(p["exhaustive_within_exact_overall_scope"] is True,"TASK166_EXHAUSTIVE")
    _r(p["total_records"]==96,"TASK166_TOTAL")
    _r(p["explicit_eiti_match_count"]==0,"TASK166_EITI")
    _r(len(p["intervals"])==11,"TASK166_INTERVALS")
    _r(sum(x["records"] for x in p["intervals"])==96,"TASK166_INTERVAL_SUM")
    _r(all(x["pages"]==1 for x in p["intervals"]),"TASK166_PAGES")

    targets={x["target"]:x for x in e["targeted_direct_json_success"]["resolved_targets"]}
    school=targets["AQUISICAO DE PASSE ESCOLAR"]
    course=targets["CURSO DE CAPACITACAO"]
    _r(school["numeroControlePNCP"]=="45132495000140-1-000368/2026","TASK166_SCHOOL_ID")
    _r(school["processo"]=="I00055" and school["sequencialCompra"]==368,"TASK166_SCHOOL_KEYS")
    _r(course["numeroControlePNCP"]=="45132495000140-1-000593/2026","TASK166_I00084_ID")
    _r(course["processo"]=="I00084" and course["sequencialCompra"]==593,"TASK166_I00084_KEYS")

    c=e["cumulative_complete_modalities"]
    _r(c=={"6":181,"8":434,"9":96,"12":5,"total_records_screened":716,"explicit_eiti_matches":0},"TASK166_CUMULATIVE")
    _r(e["scoped_conclusion"]["global_pncp_no_match"] is False,"TASK166_NO_GLOBAL")
    _r(e["scoped_conclusion"]["eiti_financial_identity_proven"] is False,"TASK166_NO_FIN_ID")

    false_pos=e["semantic_adjudication"]["keyword_false_positives"]
    _r(len(false_pos)==2 and all("ESCOLA DE SAMBA" in x["objetoCompra"] for x in false_pos),"TASK166_SAMBA_GUARD")

    return {
        "task":e["task"],
        "modality":9,
        "records":96,
        "explicit_eiti_matches":0,
        "school_pass_id":school["numeroControlePNCP"],
        "i00084_id":course["numeroControlePNCP"],
        "cumulative_records":716,
        "status":"VALID"
    }


if __name__=="__main__":
    print(json.dumps(validate(),ensure_ascii=False,sort_keys=True))
