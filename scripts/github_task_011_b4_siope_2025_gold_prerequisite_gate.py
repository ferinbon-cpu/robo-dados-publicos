#!/usr/bin/env python3
"""Offline prerequisite check only; this module contains no Gold arithmetic."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/siope_2025_gold_prerequisites.v1.json"
DECISION = "STOP_GOLD_2025_PREREQUISITES_NOT_PROVEN"
KEYS = ["B1_NUM_POPU", "B2_FINANCIAL_ALIAS_BRIDGE", "B3_EFFECTIVE_ANNUAL_DECLARATION", "SEMANTIC_COMPARABILITY"]


def validate(data):
    if (data.get("schema"), data.get("tier"), data.get("decision")) != ("SIOPE_2025_GOLD_PREREQUISITES_V1", "T0_OFFLINE", DECISION):
        raise ValueError("B4 identity or decision drift")
    if data.get("scope") != {"year": 2025, "period": 6, "period_label": "Annual", "uf": "SP", "municipality": "Limeira", "municipality_code": 352690}:
        raise ValueError("B4 scope drift")
    required = {key: "PROVEN" for key in KEYS}
    if data.get("required_state") != required:
        raise ValueError("B4 required state drift")
    state = data.get("prerequisites", {})
    unmet = [key for key in KEYS if state.get(key) != required[key]]
    if not unmet:
        raise ValueError("current TASK 011 must remain stopped")
    context = data.get("context_only", {})
    if context != {"year_2025": "PROVEN_STRUCTURAL_RECENT", "VALID_ANNUAL_SUBMISSION": "PROVEN", "financial_aliases_proven_exact_operational": "9/10", "VL_DESP_DOTA_ATUA_EDU": "PARTIAL_CURRENT_EXACT_1000_VARIANCE_NO_SOURCE_DEFINED_INCLUSION_RULE"}:
        raise ValueError("structural, submission, or 9/10 shortcut attempted")
    if data.get("gold_2025_calculated") is not False or data.get("effects") != {"network_calls": 0, "drive_calls": 0, "writes": 0, "gold_arithmetic": 0}:
        raise ValueError("forbidden B4 effect")
    return {"decision": DECISION, "unmet": unmet, "gold_2025_calculated": False}


def main():
    print(json.dumps(validate(json.loads(CONFIG.read_text(encoding="utf-8"))), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
