#!/usr/bin/env python3
"""Fail-closed current-state reconciliation gate for TASK 244."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_244_POST_TASK242_TASK243_ACQUISITION_READY_STATE_0.8.0.json"
READINESS = ROOT / "config/release_0_8_0_readiness.v4.json"
GOLD = ROOT / "config/siope_2025_gold_prerequisites.v4.json"
TASK242 = ROOT / "docs/evidence/TASK_242_SIOPE_HISTORICAL_FINANCIAL_SEMANTIC_VERSIONING_0.8.0.json"
TASK243 = ROOT / "docs/evidence/TASK_243_IBGE_POPULATION_DENOMINATOR_REBASE_0.8.0.json"

BASE = "094595b1ba8dd9d82596b918b621a2ae939aa204"
FIN = "BOUNDED_OFFICIAL_PUBLIC_CONTRACT_TEMPORAL_EVIDENCE_ACQUISITION_REQUIRES_EXPLICIT_AUTHORIZATION"
IBGE = "BOUNDED_OFFICIAL_IBGE_POPULATION_SOURCE_CONTRACT_AND_SERIES_ACQUISITION_REQUIRES_EXPLICIT_AUTHORIZATION"
PASS = "PASS_TASK244_ACQUISITION_READY_NO_GOLD"


def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def stop(condition, message):
    if not condition:
        raise ValueError(message)


def validate_objects(evidence, readiness, gold, task242, task243):
    stop(evidence.get("evidence_schema") == "TASK_244_POST_TASK242_TASK243_ACQUISITION_READY_STATE_V1", "evidence schema drift")
    stop(evidence.get("base_main_sha") == BASE, "TASK244 base drift")
    entry = evidence.get("entry_state", {})
    stop(entry.get("semantic_comparability") == "PARTIAL", "comparability promoted")
    stop(entry.get("financial_inputs") == "10_OF_10_PARTIAL", "financial inputs promoted")
    stop(entry.get("financial_metrics_1_to_6") == "6_OF_6_PARTIAL", "financial metrics promoted")
    stop(entry.get("per_capita_metrics_7_to_8") == "2_OF_2_NON_COMPARABLE_UNDER_NUM_POPU", "per-capita state drift")
    stop(entry.get("gold_2025") == "BLOCKED_NOT_CALCULATED", "Gold state drift")
    stop(entry.get("closed_annual_series") == "2016-2024", "closed series drift")
    stop(entry.get("release_0_8_0") == "CANDIDATE", "release promoted")

    routing = evidence.get("current_routing", {})
    stop(routing.get("financial_1_to_6", {}).get("gate") == FIN, "financial routing drift")
    stop(routing.get("per_capita_7_to_8", {}).get("gate") == IBGE, "IBGE routing drift")

    stop(readiness.get("schema") == "RELEASE_0_8_0_READINESS_V4", "readiness schema drift")
    stop(readiness.get("base_main_sha") == BASE, "readiness base drift")
    stop(readiness.get("semantic_comparability", {}).get("global_status") == "PARTIAL", "readiness comparability promoted")
    stop(readiness.get("next_evidence_gates", {}).get("FINANCIAL_1_TO_6") == FIN, "readiness financial route drift")
    stop(readiness.get("next_evidence_gates", {}).get("PER_CAPITA_7_TO_8") == IBGE, "readiness IBGE route drift")
    stop(readiness.get("release_0_8_0") == "CANDIDATE", "readiness release promoted")
    auth = readiness.get("authorization_state", {})
    stop(auth.get("user_authorized_big_jump_on_2026_09_14") is True, "bounded acquisition authorization missing")
    stop(auth.get("gold_calculation_authorized") is False, "Gold authorization leaked")
    stop(auth.get("series_inclusion_authorized") is False, "series inclusion authorization leaked")
    stop(auth.get("release_promotion_authorized") is False, "release promotion authorization leaked")

    stop(gold.get("schema") == "SIOPE_2025_GOLD_PREREQUISITES_V4", "Gold schema drift")
    stop(gold.get("base_main_sha") == BASE, "Gold base drift")
    stop(gold.get("prerequisites", {}).get("TASK242_HISTORICAL_FINANCIAL_AUDIT") == "COMPLETE_EVIDENCE_ACQUISITION_REQUIRED", "TASK242 completion drift")
    stop(gold.get("prerequisites", {}).get("TASK243_IBGE_DENOMINATOR_AUDIT") == "COMPLETE_SOURCE_CONTRACT_AND_SERIES_ACQUISITION_REQUIRED", "TASK243 completion drift")
    stop(gold.get("next_evidence_gates") == [FIN, IBGE], "Gold next-gate drift")
    stop(gold.get("gold_2025_calculated") is False, "Gold calculated prematurely")
    stop(gold.get("closed_annual_series") == "2016-2024", "Gold closed series drift")
    stop(gold.get("release_0_8_0") == "CANDIDATE", "Gold release promoted")

    stop(task242.get("offline_decision", {}).get("status") == "PARTIAL", "TASK242 historical evidence changed")
    stop(task242.get("next_gate") == FIN, "TASK242 next gate changed")
    stop(task243.get("decision", {}).get("status") == "PARTIAL", "TASK243 historical evidence changed")
    stop(task243.get("next_gate") == IBGE, "TASK243 next gate changed")

    guards = evidence.get("guards", {})
    stop(guards and all(value is False for value in guards.values()), "TASK244 guard violated")
    return PASS


def validate():
    return validate_objects(load(EVIDENCE), load(READINESS), load(GOLD), load(TASK242), load(TASK243))


if __name__ == "__main__":
    print(validate())
