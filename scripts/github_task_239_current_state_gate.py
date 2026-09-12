#!/usr/bin/env python3
"""Fail-closed T0 gate for TASK 239 current-state reconciliation."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "docs/evidence/TASK_239_CURRENT_0_8_0_STATE_0.8.0.json"
TERRITORY = ROOT / "docs/evidence/TASK_199H_FULL_NETWORK_OFFICIAL_POINT_IN_POLYGON_0.8.0.json"
B1 = ROOT / "docs/evidence/TASK_010N_R_E_M6_SIOPE_NUM_POPU_FNDE_DISPOSITION_0.8.0.json"
B2 = ROOT / "docs/evidence/TASK_195C_SIOPE_FUNCAO12_ALIAS_BRIDGE_0.8.0.json"
B3 = ROOT / "docs/evidence/TASK_240_SIOPE_2025_EFFECTIVE_ANNUAL_DECLARATION_0.8.0.json"
READINESS_V2 = ROOT / "config/release_0_8_0_readiness.v2.json"
GOLD_V2 = ROOT / "config/siope_2025_gold_prerequisites.v2.json"
READINESS_V1 = ROOT / "config/release_0_8_0_readiness.v1.json"
GOLD_V1 = ROOT / "config/siope_2025_gold_prerequisites.v1.json"
TASK011 = ROOT / "docs/evidence/TASK_011_FNDE_AUTHORITATIVE_REQUESTS_PENDING_0.8.0.json"
README = ROOT / "README.md"
STATUS = ROOT / "STATUS_0.8.0.md"

BASE = "07952f63c6ec86a5dd9ce316cc2516c8e4225580"
B1_STATE = "RESOLVED_BY_EXCLUSION_FROM_ANALYTICAL_POPULATION_SEMANTICS"
B2_STATE = "PROVEN_10_OF_10_ALIAS_TO_CONCEPT"
B3_STATE = "PROVEN_DYNAMIC_EFFECTIVE_SELECTION_RULE_WITH_PINNED_LIMEIRA_RECEIPT"
DECISION = "RECONCILE_CURRENT_STATE_B1_B2_B3_RESOLVED_COMPARABILITY_NEXT"
PASS = "PASS_TASK239_CURRENT_STATE_RECONCILED"


def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def stop(condition, message):
    if not condition:
        raise ValueError(message)


def validate_objects(state, territory, b1, b2, b3, readiness_v2, gold_v2,
                     readiness_v1, gold_v1, task011, readme, status):
    stop(
        (state.get("schema"), state.get("task"), state.get("issue"),
         state.get("canonical_date"), state.get("base_main_sha"), state.get("tier"),
         state.get("decision")) ==
        ("TASK_239_CURRENT_0_8_0_STATE_V1", "TASK_239", 805, "2026-09-12", BASE,
         "T0_OFFLINE_CURRENT_STATE_RECONCILIATION", DECISION),
        "TASK239 identity/base/decision drift",
    )

    geo = state.get("territory", {})
    stop(geo.get("territory_profile_rows") == 284, "territory rows drift")
    stop(geo.get("strong_school_links") == 69 and geo.get("network_schools") == 69,
         "full-network geography drift")
    stop(geo.get("held_geography") == 0, "held geography reintroduced")
    stop(geo.get("schools_with_numeric_income_context") == 68, "numeric income coverage drift")
    stop(geo.get("schools_with_explicit_sector_income_missingness") == 1,
         "explicit income missingness drift")
    stop(geo.get("explicit_missingness_school_code") == "35286229", "missingness school drift")
    stop(geo.get("explicit_missingness_status") == "SOURCE_EXPLICIT_X", "X status drift")
    stop(geo.get("source_x_is_zero") is False, "source X cannot equal zero")
    stop(geo.get("contextual_answerability") == "38/38", "answerability drift")

    after = territory.get("after", {})
    stop(territory.get("status") == "PASS_FULL_NETWORK_69_OF_69_WITH_EXPLICIT_INCOME_MISSINGNESS",
         "TASK199H status drift")
    stop(after.get("strong_school_links") == 69 and after.get("held") == 0,
         "TASK199H geography drift")
    stop(after.get("territory_profile_rows") == 284, "TASK199H rows drift")
    stop(after.get("schools_with_numeric_income_context") == 68, "TASK199H income drift")
    stop(territory.get("income_missingness", {}).get("codigo_inep") == "35286229",
         "TASK199H missingness identity drift")
    stop(territory.get("income_missingness", {}).get("rule") == "X_NE_ZERO_AND_NO_NUMERIC_INCOME_ROWS_MATERIALIZED",
         "TASK199H X rule drift")
    stop(territory.get("answerability", {}).get("question_coverage_after") == "38_OF_38_COMPLETE",
         "TASK199H answerability drift")

    siope = state.get("siope_2025", {})
    stop(siope.get("B1_NUM_POPU") == B1_STATE, "B1 current state drift")
    stop(siope.get("B2_FINANCIAL_ALIAS_BRIDGE") == B2_STATE, "B2 current state drift")
    stop(siope.get("B3_EFFECTIVE_ANNUAL_DECLARATION") == B3_STATE, "B3 current state drift")
    stop(siope.get("VALID_ANNUAL_SUBMISSION") == "PROVEN", "annual submission drift")
    stop(siope.get("currently_effective_receipt_at_pinned_observation") == "428477-6",
         "effective receipt drift")
    stop(siope.get("pinned_observation_date") == "2026-08-30", "observation date drift")
    stop(siope.get("future_successful_rectification_requires_refresh") is True,
         "dynamic B3 refresh guard lost")
    stop(siope.get("immutable_finality_asserted") is False, "immutable finality invented")
    stop(siope.get("semantic_comparability_2016_2025") == "UNKNOWN_REQUIRES_TASK241",
         "comparability inferred")
    stop(siope.get("gold_2025") == "BLOCKED_NOT_CALCULATED", "Gold promotion drift")
    stop(siope.get("closed_annual_series") == "2016-2024", "closed series drift")
    stop(siope.get("release_0_8_0") == "CANDIDATE", "release promotion drift")

    stop(b1.get("release_gate_effect", {}).get("B1_new_state") == B1_STATE,
         "authoritative B1 disposition drift")
    stop(b1.get("source_statements", {}).get("recommended_treatment_of_num_popu_for_population_analysis") == "DISREGARD",
         "NUM_POPU exclusion drift")
    stop(b1.get("guards", {}).get("num_popu_used_as_population_denominator") is False,
         "NUM_POPU denominator guard lost")

    b2_result = b2.get("result", {})
    stop(b2_result.get("B2_FINANCIAL_ALIAS_BRIDGE") == B2_STATE, "authoritative B2 drift")
    stop(b2_result.get("backend_aggregation_formula") == "NOT_PROVEN", "backend formula invented")
    stop(b2_result.get("1000_account_inclusion_rule") == "NOT_PROVEN_AND_NOT_ASSERTED",
         "1000 account rule invented")

    b3_decision = b3.get("b3_decision", {})
    stop(b3_decision.get("new_state") == B3_STATE and b3_decision.get("blocker_removed") is True,
         "authoritative B3 drift")
    stop(b3.get("pinned_limeira_receipt_evidence", {}).get("receipt_number") == "428477-6",
         "pinned receipt source drift")
    stop(b3.get("deterministic_application", {}).get("immutable_finality") == "NOT_ASSERTED_AND_NOT_REQUIRED",
         "B3 temporal boundary lost")

    stop(readiness_v2.get("schema") == "RELEASE_0_8_0_READINESS_V2", "readiness v2 schema drift")
    stop(readiness_v2.get("base_main_sha") == BASE, "readiness v2 base drift")
    rp = readiness_v2.get("resolved_predecessors", {})
    stop(rp == {"B1_NUM_POPU": B1_STATE, "B2_FINANCIAL_ALIAS_BRIDGE": B2_STATE,
                "B3_EFFECTIVE_DECLARATION": B3_STATE}, "readiness v2 predecessors drift")
    stop(readiness_v2.get("open_gates", {}).get("SEMANTIC_COMPARABILITY") == "UNKNOWN_REQUIRES_TASK241",
         "readiness comparability drift")
    stop(readiness_v2.get("release_0_8_0") == "CANDIDATE", "readiness release drift")

    stop(gold_v2.get("schema") == "SIOPE_2025_GOLD_PREREQUISITES_V2", "gold v2 schema drift")
    gp = gold_v2.get("prerequisites", {})
    stop(gp.get("B1_NUM_POPU") == B1_STATE and gp.get("B2_FINANCIAL_ALIAS_BRIDGE") == B2_STATE
         and gp.get("B3_EFFECTIVE_ANNUAL_DECLARATION") == B3_STATE, "gold v2 predecessors drift")
    stop(gp.get("SEMANTIC_COMPARABILITY") == "UNKNOWN_REQUIRES_TASK241", "gold comparability drift")
    stop(gold_v2.get("metric_scope", {}).get("per_capita_metrics_7_to_8") ==
         "BLOCKED_NUM_POPU_EXCLUDED_IBGE_REBASE_ROUTE_REQUIRED", "per-capita route drift")
    stop(gold_v2.get("gold_2025_calculated") is False, "Gold was calculated")
    stop(gold_v2.get("effects", {}).get("gold_arithmetic") == 0, "Gold arithmetic occurred")

    # Historical snapshots are immutable evidence of their own earlier state.
    old_r = readiness_v1.get("blockers", {})
    stop(old_r.get("B1_NUM_POPU") == "WAITING_FNDE_LAI_23546_111503_2026_95",
         "historical readiness v1 rewritten")
    stop(old_r.get("B3_EFFECTIVE_DECLARATION") == "WAITING_FNDE_LAI_23546_111502_2026_41",
         "historical B3 readiness rewritten")
    stop(gold_v1.get("prerequisites", {}).get("B2_FINANCIAL_ALIAS_BRIDGE") ==
         "NOT_PROVEN_DOTACAO_EDU_SOURCE_DEFINED_BRIDGE_MISSING", "historical gold v1 rewritten")
    stop(task011.get("decision") == "KEEP_B1_B2_B3_PENDING_NO_PROMOTION", "historical TASK011 rewritten")
    stop(all(item.get("response_status") == "PENDING" for item in task011.get("requests", [])),
         "historical TASK011 response state rewritten")

    required_readme = [B1_STATE, B2_STATE, B3_STATE, "TASK 241", "69/69"]
    stop(all(text in readme for text in required_readme), "README current-state markers missing")
    forbidden_readme = ["**Próximo gate:** respostas oficiais FNDE", "Nove dos dez aliases financeiros",
                        "As três respostas oficiais estão pendentes"]
    stop(not any(text in readme for text in forbidden_readme), "README still advertises stale current state")

    required_status = [B1_STATE, B2_STATE, B3_STATE, "TASK 241",
                       "Gold 2025 permanece bloqueado e não calculado", "69/69", "68/69"]
    stop(all(text in status for text in required_status), "STATUS current-state markers missing")
    forbidden_status = ["Aguarda resposta\nFNDE do protocolo", "Nove de dez\naliases estão provados",
                        "Enquanto pendentes, têm efeito de promoção `NONE`"]
    stop(not any(text in status for text in forbidden_status), "STATUS still advertises stale pending state")

    guards = state.get("guards", {})
    stop(all(value is False for value in guards.values()), "TASK239 fail-closed guard promoted")
    next_gate = state.get("next_gate", {})
    stop(next_gate == {"task": "TASK_241", "issue": 809, "purpose": "SEMANTIC_COMPARABILITY_2016_2025"},
         "next gate drift")
    return PASS


def validate():
    return validate_objects(
        load(STATE), load(TERRITORY), load(B1), load(B2), load(B3), load(READINESS_V2), load(GOLD_V2),
        load(READINESS_V1), load(GOLD_V1), load(TASK011), README.read_text(encoding="utf-8"),
        STATUS.read_text(encoding="utf-8"),
    )


if __name__ == "__main__":
    print(validate())
