#!/usr/bin/env python3
"""Fail-closed T0 gate for TASK 241 semantic comparability 2016-2025."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_241_SIOPE_2016_2025_SEMANTIC_COMPARABILITY_0.8.0.json"
CONTRACT = ROOT / "config/siope_2025_semantic_comparability.v1.json"
GOLD_V3 = ROOT / "config/siope_2025_gold_prerequisites.v3.json"
READINESS_V3 = ROOT / "config/release_0_8_0_readiness.v3.json"
GOLD_V2 = ROOT / "config/siope_2025_gold_prerequisites.v2.json"
READINESS_V2 = ROOT / "config/release_0_8_0_readiness.v2.json"
CONTINUITY = ROOT / "docs/evidence/TASK_010N_SIOPE_2016_2025_CONTRACT_CONTINUITY_AUDIT_0.8.0.json"
REGIMES = ROOT / "config/siope_historical_regimes.v1.json"
HISTORICAL_MATRIX = ROOT / "config/siope_historical_evidence_matrix.v1.json"
B1 = ROOT / "docs/evidence/TASK_010N_R_E_M6_SIOPE_NUM_POPU_FNDE_DISPOSITION_0.8.0.json"
B2 = ROOT / "docs/evidence/TASK_195C_SIOPE_FUNCAO12_ALIAS_BRIDGE_0.8.0.json"
B3 = ROOT / "docs/evidence/TASK_240_SIOPE_2025_EFFECTIVE_ANNUAL_DECLARATION_0.8.0.json"

BASE = "2d898e99bd8681ec6f020430bead20df7ac3d370"
B1_STATE = "RESOLVED_BY_EXCLUSION_FROM_ANALYTICAL_POPULATION_SEMANTICS"
B2_STATE = "PROVEN_10_OF_10_ALIAS_TO_CONCEPT"
B3_STATE = "PROVEN_DYNAMIC_EFFECTIVE_SELECTION_RULE_WITH_PINNED_LIMEIRA_RECEIPT"
DECISION = "PARTIAL_FINANCIAL_CONTINUITY_HISTORICAL_VERSIONING_GAP_PER_CAPITA_REQUIRES_IBGE_REBASE"
PASS = "PASS_TASK241_PARTIAL_COMPARABILITY_FAIL_CLOSED"

FINANCIAL_ALIASES = {
    "VAL_RECE_PREV_ATUA", "VAL_RECE_REAL", "VAL_DESP_DOTA_ATUA", "VAL_DESP_EMPE",
    "VAL_DESP_LIQU", "VAL_DESP_PAGA", "VL_DESP_DOTA_ATUA_EDU", "VL_DESP_EMPE_EDU",
    "VL_DESP_LIQU_EDU", "VL_DESP_PAGA_EDU",
}
FINANCIAL_METRICS = {
    "receita_realizada_sobre_previsao_atualizada_pct": {"VAL_RECE_REAL", "VAL_RECE_PREV_ATUA"},
    "despesa_paga_sobre_dotacao_atualizada_pct": {"VAL_DESP_PAGA", "VAL_DESP_DOTA_ATUA"},
    "despesa_educacao_paga_sobre_dotacao_atualizada_educacao_pct": {"VL_DESP_PAGA_EDU", "VL_DESP_DOTA_ATUA_EDU"},
    "participacao_educacao_na_despesa_empenhada_pct": {"VL_DESP_EMPE_EDU", "VAL_DESP_EMPE"},
    "participacao_educacao_na_despesa_liquidada_pct": {"VL_DESP_LIQU_EDU", "VAL_DESP_LIQU"},
    "participacao_educacao_na_despesa_paga_pct": {"VL_DESP_PAGA_EDU", "VAL_DESP_PAGA"},
}
PER_CAPITA = {"despesa_total_paga_por_habitante", "despesa_educacao_paga_por_habitante"}


def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def stop(condition, message):
    if not condition:
        raise ValueError(message)


def validate_objects(evidence, contract, gold_v3, readiness_v3, gold_v2, readiness_v2,
                     continuity, regimes, historical_matrix, b1, b2, b3):
    stop(
        (evidence.get("evidence_schema"), evidence.get("task"), evidence.get("issue"),
         evidence.get("canonical_date"), evidence.get("base_main_sha"), evidence.get("tier")) ==
        ("TASK_241_SIOPE_2016_2025_SEMANTIC_COMPARABILITY_V1", "TASK_241", 809,
         "2026-09-12", BASE, "T0_OFFLINE_EXISTING_EVIDENCE_ONLY"),
        "TASK241 identity/base drift",
    )

    entry = evidence.get("entry_state", {})
    stop(entry.get("B1_NUM_POPU") == B1_STATE, "B1 entry drift")
    stop(entry.get("B2_FINANCIAL_ALIAS_BRIDGE") == B2_STATE, "B2 entry drift")
    stop(entry.get("B3_EFFECTIVE_ANNUAL_DECLARATION") == B3_STATE, "B3 entry drift")
    stop(entry.get("effective_receipt_at_pinned_observation") == "428477-6", "effective receipt drift")
    stop(entry.get("gold_2025") == "BLOCKED_NOT_CALCULATED", "Gold entry drift")
    stop(entry.get("closed_annual_series") == "2016-2024", "closed series entry drift")
    stop(entry.get("release_0_8_0") == "CANDIDATE", "release entry drift")

    stop(continuity.get("result", {}).get("class") == "B", "historical proof-gap class rewritten")
    stop(continuity.get("result", {}).get("code") == "HISTORICAL_PROOF_STANDARD_INSUFFICIENT",
         "historical proof-gap code rewritten")
    stop(continuity.get("result", {}).get("positive_break_search") == "NO_POSITIVE_BREAK_EVIDENCE_FOUND",
         "positive-break search drift")
    stop(continuity.get("result", {}).get("proof_standard") == "2025_STRICTER_THAN_HISTORICAL",
         "historical proof-standard drift")

    rows = {row.get("years"): row for row in historical_matrix.get("rows", [])}
    stop(rows.get("2016", {}).get("surface") == "Dados_Gerais_Siope", "2016 surface drift")
    stop(rows.get("2017-2024", {}).get("surface") == "Dados_Gerais_Siope", "2017-2024 surface drift")
    stop(rows.get("2017-2024", {}).get("annual_period") == "P6_PROVEN", "2017-2024 annual period drift")

    regime_rows = {item.get("id"): item for item in regimes.get("regimes", [])}
    stop(regime_rows.get("PROVEN_ANNUAL_2016", {}).get("period", {}).get("value") == 1,
         "2016 period boundary drift")
    stop(regime_rows.get("PROVEN_BIMONTHLY_2017_2024", {}).get("period", {}).get("value") == 6,
         "2017-2024 period boundary drift")

    stop(b1.get("release_gate_effect", {}).get("B1_new_state") == B1_STATE, "B1 source drift")
    stop(b1.get("source_statements", {}).get("recommended_treatment_of_num_popu_for_population_analysis") == "DISREGARD",
         "NUM_POPU disposition drift")
    stop(b1.get("guards", {}).get("num_popu_used_as_population_denominator") is False,
         "NUM_POPU denominator guard drift")
    stop(b2.get("result", {}).get("B2_FINANCIAL_ALIAS_BRIDGE") == B2_STATE, "B2 source drift")
    stop(b3.get("b3_decision", {}).get("new_state") == B3_STATE, "B3 source drift")

    financial_inputs = evidence.get("financial_inputs", [])
    stop(len(financial_inputs) == 10, "financial input count drift")
    stop({row.get("alias") for row in financial_inputs} == FINANCIAL_ALIASES, "financial alias set drift")
    stop(all(row.get("status") == "PARTIAL" for row in financial_inputs),
         "financial input promoted or downgraded without evidence")
    summary = evidence.get("financial_inputs_summary", {})
    stop(summary.get("PROVEN_COMPARABLE") == 0 and summary.get("PARTIAL") == 10,
         "financial input summary drift")

    metrics = evidence.get("financial_gold_metrics_1_to_6", [])
    stop(len(metrics) == 6, "financial metric count drift")
    observed = {row.get("id"): set(row.get("inputs", [])) for row in metrics}
    stop(observed == FINANCIAL_METRICS, "financial metric input mapping drift")
    stop(all(row.get("status") == "PARTIAL" for row in metrics),
         "financial metric promoted without historical bridge")
    metric_summary = evidence.get("financial_metrics_summary", {})
    stop(metric_summary.get("PROVEN_COMPARABLE") == 0 and metric_summary.get("PARTIAL") == 6,
         "financial metric summary drift")

    per_capita = evidence.get("per_capita_gold_metrics_7_to_8", [])
    stop(len(per_capita) == 2 and {row.get("id") for row in per_capita} == PER_CAPITA,
         "per-capita metric set drift")
    stop(all(row.get("status") == "NON_COMPARABLE" for row in per_capita),
         "per-capita metric incorrectly promoted")
    stop(all(row.get("historical_denominator") == "NUM_POPU" for row in per_capita),
         "per-capita historical denominator drift")
    stop(all(row.get("required_route") == "IBGE_HOMOGENEOUS_DENOMINATOR_REBASE_2016_2025" for row in per_capita),
         "per-capita rebase route drift")
    pc_summary = evidence.get("per_capita_summary", {})
    stop(pc_summary.get("NON_COMPARABLE") == 2, "per-capita summary drift")
    stop(pc_summary.get("num_popu_2025_use_forbidden") is True, "NUM_POPU 2025 guard lost")
    stop(pc_summary.get("historical_num_popu_compatibility_inferred") is False,
         "historical denominator compatibility inferred")
    stop(pc_summary.get("historical_gold_rewrite_authorized") is False,
         "historical Gold rewrite authorized")

    decision = evidence.get("global_decision", {})
    stop(decision.get("status") == "PARTIAL" and decision.get("code") == DECISION,
         "TASK241 global decision drift")
    stop(decision.get("financial_1_to_6_gold_authorized") is False, "financial Gold prematurely authorized")
    stop(decision.get("per_capita_7_to_8_gold_authorized") is False, "per-capita Gold prematurely authorized")
    stop(decision.get("full_8_of_8_comparability") is False, "8/8 comparability fabricated")
    stop(decision.get("gold_2025_authorized") is False, "Gold 2025 authorized")
    stop(decision.get("series_2016_2025_authorized") is False, "2025 series inclusion authorized")
    stop(decision.get("release_promotion_authorized") is False, "release promotion authorized")

    stop(contract.get("schema") == "SIOPE_2025_SEMANTIC_COMPARABILITY_V1", "comparability contract schema drift")
    stop(contract.get("base_main_sha") == BASE, "comparability contract base drift")
    stop(contract.get("global_status") == "PARTIAL" and contract.get("decision") == DECISION,
         "comparability contract decision drift")
    stop(contract.get("financial_inputs_10_of_10", {}).get("partial") == 10,
         "comparability contract input summary drift")
    stop(contract.get("financial_gold_metrics_1_to_6", {}).get("partial") == 6,
         "comparability contract metric summary drift")
    stop(contract.get("per_capita_gold_metrics_7_to_8", {}).get("non_comparable") == 2,
         "comparability contract per-capita summary drift")
    stop(contract.get("gold_2025_authorized") is False, "comparability contract authorized Gold")

    stop(gold_v3.get("schema") == "SIOPE_2025_GOLD_PREREQUISITES_V3", "Gold v3 schema drift")
    stop(gold_v3.get("prerequisites", {}).get("SEMANTIC_COMPARABILITY") ==
         "PARTIAL_TASK241_HISTORICAL_FINANCIAL_VERSIONING_GAP_AND_IBGE_REBASE_REQUIRED",
         "Gold v3 comparability drift")
    stop(gold_v3.get("gold_2025_calculated") is False and gold_v3.get("gold_2025_authorized") is False,
         "Gold v3 incorrectly opened")
    stop(gold_v3.get("closed_annual_series") == "2016-2024", "Gold v3 closed series drift")
    stop(gold_v3.get("effects", {}).get("gold_arithmetic") == 0, "Gold arithmetic occurred")

    stop(readiness_v3.get("schema") == "RELEASE_0_8_0_READINESS_V3", "readiness v3 schema drift")
    stop(readiness_v3.get("semantic_comparability", {}).get("global_status") == "PARTIAL",
         "readiness v3 comparability drift")
    open_gates = readiness_v3.get("open_gates", {})
    stop(open_gates.get("HISTORICAL_FINANCIAL_SEMANTIC_VERSIONING") == "OPEN",
         "historical financial gate not open")
    stop(open_gates.get("IBGE_PER_CAPITA_REBASE") == "OPEN", "IBGE rebase gate not open")
    stop(readiness_v3.get("release_0_8_0") == "CANDIDATE", "release incorrectly promoted")

    # v2 artifacts remain historical snapshots of the pre-TASK241 current state.
    stop(gold_v2.get("schema") == "SIOPE_2025_GOLD_PREREQUISITES_V2", "historical Gold v2 rewritten")
    stop(gold_v2.get("prerequisites", {}).get("SEMANTIC_COMPARABILITY") == "UNKNOWN_REQUIRES_TASK241",
         "historical Gold v2 comparability rewritten")
    stop(readiness_v2.get("schema") == "RELEASE_0_8_0_READINESS_V2", "historical readiness v2 rewritten")
    stop(readiness_v2.get("open_gates", {}).get("SEMANTIC_COMPARABILITY") == "UNKNOWN_REQUIRES_TASK241",
         "historical readiness v2 comparability rewritten")

    guards = evidence.get("guards", {})
    stop(guards and all(value is False for value in guards.values()), "TASK241 guard violated")
    stop(evidence.get("next_gates") == [
        "HISTORICAL_FINANCIAL_SEMANTIC_VERSIONED_BRIDGE_2016_2024",
        "IBGE_POPULATION_DENOMINATOR_REBASE_CONTRACT_2016_2025",
    ], "next-gate routing drift")
    return PASS


def validate():
    return validate_objects(
        load(EVIDENCE), load(CONTRACT), load(GOLD_V3), load(READINESS_V3),
        load(GOLD_V2), load(READINESS_V2), load(CONTINUITY), load(REGIMES),
        load(HISTORICAL_MATRIX), load(B1), load(B2), load(B3),
    )


if __name__ == "__main__":
    print(validate())
