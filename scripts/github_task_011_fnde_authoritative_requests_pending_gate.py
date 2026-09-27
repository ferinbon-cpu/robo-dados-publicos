#!/usr/bin/env python3
"""Validate the pending FNDE requests without treating submission as proof."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_011_FNDE_AUTHORITATIVE_REQUESTS_PENDING_0.8.0.json"
DECISION = "KEEP_B1_B2_B3_PENDING_NO_PROMOTION"
MAPPING = [
    ("B3_EFFECTIVE_DECLARATION", "23546.111502/2026-41", "NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING"),
    ("B1_NUM_POPU", "23546.111503/2026-95", "NOT_PROVEN_DEFINITION_SOURCE_VINTAGE_MISSING"),
    ("B2_DOTACAO_EDU", "23546.111504/2026-30", "NOT_PROVEN_DOTACAO_EDU_SOURCE_DEFINED_BRIDGE_MISSING"),
]
TARGET_PROPOSITIONS = {
    "B3_EFFECTIVE_DECLARATION": [
        "later retifying declaration/receipt supersession rule",
        "currently valid/current/effective declaration selection rule",
        "whether Recibos de Transmissão can show a superseded receipt",
        "exact official documentation or system rule",
    ],
    "B1_NUM_POPU": [
        "exact NUM_POPU semantic definition",
        "authoritative source and whether it is IBGE",
        "exact reference date/year/version and census/estimate rule",
        "official dictionary/layout/import/backend rule",
    ],
    "B2_DOTACAO_EDU": [
        "exact VL_DESP_DOTA_ATUA_EDU definition and accounting source",
        "aggregation formula and included/excluded categories",
        "relation to RREO/MDE updated appropriation",
        "treatment of 3.2.00.00.00 and 3.2.91.00.00",
        "official SQL/view/backend/layout/dictionary/report rule",
    ],
}
CANONICAL = {"release_0_7_0": "ACTIVE", "release_0_8_0": "CANDIDATE", "year_2025": "PROVEN_STRUCTURAL_RECENT", "S1_NUM_POPU": "NOT_PROVEN", "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN", "financial_aliases_proven_exact_operational": "9/10", "annual_closure_status": "UNKNOWN", "VALID_ANNUAL_SUBMISSION": "PROVEN", "CURRENTLY_EFFECTIVE_DECLARATION": "NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING", "semantic_comparability_status": "UNKNOWN", "closed_annual_series": "2016-2024", "gold_2025": "UNKNOWN/BLOCKED", "year_2026": "UNPROVEN_CURRENT_YEAR"}


def validate(data):
    if (data.get("schema"), data.get("task"), data.get("tier"), data.get("request_date"), data.get("authority"), data.get("deadline"), data.get("decision")) != ("TASK_011_FNDE_AUTHORITATIVE_REQUESTS_PENDING_V1", "TASK_011", "T0_OFFLINE", "2026-08-30", "FNDE", "2026-09-21", DECISION):
        raise ValueError("request identity, authority, date, deadline, or decision drift")
    requests = data.get("requests", [])
    if [(r.get("blocker_id"), r.get("protocol"), r.get("current_blocker_state")) for r in requests] != MAPPING:
        raise ValueError("protocol or blocker mapping drift")
    for request in requests:
        if request.get("target_propositions") != TARGET_PROPOSITIONS[request["blocker_id"]]:
            raise ValueError("exact ordered target propositions drift")
        if (request.get("response_status"), request.get("promotion_effect"), request.get("source_class")) != ("PENDING", "NONE_WHILE_PENDING", "AUTHORITATIVE_INFORMATION_REQUEST_PENDING"):
            raise ValueError("pending request falsely received or promoted")
    if data.get("canonical_state") != CANONICAL:
        raise ValueError("canonical B1/B2/B3, Gold, series, release, or 2026 promotion")
    return DECISION


def main():
    print(validate(json.loads(EVIDENCE.read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
