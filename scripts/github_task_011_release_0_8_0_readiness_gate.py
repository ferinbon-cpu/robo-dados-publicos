#!/usr/bin/env python3
"""Fail-closed, evaluation-only readiness gate for release 0.8.0."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/release_0_8_0_readiness.v1.json"
DECISION = "KEEP_0_8_0_CANDIDATE_BLOCKERS_REMAIN"
READY = "READY_0_8_0_FOR_EXPLICIT_PROMOTION"
CURRENT = {"B1_NUM_POPU": "WAITING_FNDE_LAI_23546_111503_2026_95", "B2_DOTACAO_EDU": "WAITING_FNDE_LAI_23546_111504_2026_30", "B3_EFFECTIVE_DECLARATION": "WAITING_FNDE_LAI_23546_111502_2026_41", "SEMANTIC_COMPARABILITY": "UNKNOWN", "B4_GOLD_2025": "BLOCKED_BY_B1_B2_B3_AND_SEMANTIC_COMPARABILITY", "B5_SERIES_2016_2025": "BLOCKED_BY_B4"}


def validate(data):
    if (data.get("schema"), data.get("tier"), data.get("decision")) != ("RELEASE_0_8_0_READINESS_V1", "T0_OFFLINE", DECISION):
        raise ValueError("readiness identity or decision drift")
    required = {key: "PROVEN" for key in CURRENT}
    if data.get("permitted_proven_state") != required:
        raise ValueError("permitted predecessor state drift")
    blockers = data.get("blockers", {})
    if set(blockers) != set(CURRENT) or any(blockers[key] not in (CURRENT[key], required[key]) for key in CURRENT):
        raise ValueError("blocker identity, protocol mapping, or state vocabulary drift")
    if data.get("RELEASE_0_8_0") != "CANDIDATE":
        raise ValueError("release promoted while blockers remain")
    if data.get("readiness_effect") != "EVALUATION_ONLY_NO_PUBLICATION_DEPLOYMENT_SCHEDULE_OR_RECURRENCE":
        raise ValueError("readiness acquired an operational effect")
    unmet = [key for key in CURRENT if blockers[key] != required[key]]
    return {"decision": DECISION if unmet else READY, "unmet": unmet, "release": "0.8.0 CANDIDATE", "operational_effect": "NONE_EVALUATION_ONLY"}


def main():
    print(json.dumps(validate(json.loads(CONFIG.read_text(encoding="utf-8"))), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
