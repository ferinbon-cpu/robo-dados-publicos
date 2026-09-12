#!/usr/bin/env python3
"""Fail-closed T0 gate for TASK 242 historical financial semantic versioning."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_242_SIOPE_HISTORICAL_FINANCIAL_SEMANTIC_VERSIONING_0.8.0.json"
CONTRACT = ROOT / "config/siope_historical_financial_semantic_versioning.v1.json"
ACQUISITION = ROOT / "config/siope_historical_financial_semantic_acquisition_spec.v1.json"
TASK241 = ROOT / "docs/evidence/TASK_241_SIOPE_2016_2025_SEMANTIC_COMPARABILITY_0.8.0.json"
CONTINUITY = ROOT / "docs/evidence/TASK_010N_SIOPE_2016_2025_CONTRACT_CONTINUITY_AUDIT_0.8.0.json"
PROOF_STANDARD_DOC = ROOT / "docs/tasks/TASK_010N_R_SIOPE_PROOF_STANDARD_RECONCILIATION.md"
B2 = ROOT / "docs/evidence/TASK_195C_SIOPE_FUNCAO12_ALIAS_BRIDGE_0.8.0.json"

BASE = "620464182c911415f885fac64ce789e10c9e7c50"
DECISION = "STOP_HISTORICAL_FINANCIAL_SEMANTIC_PROMOTION_PRIMARY_TEMPORAL_PUBLIC_CONTRACT_EVIDENCE_REQUIRED"
NEXT = "BOUNDED_OFFICIAL_PUBLIC_CONTRACT_TEMPORAL_EVIDENCE_ACQUISITION_REQUIRES_EXPLICIT_AUTHORIZATION"
PASS = "PASS_TASK242_OFFLINE_PARTIAL_AND_BOUNDED_ACQUISITION_SPEC"
ALIASES = {
    "VAL_RECE_PREV_ATUA", "VAL_RECE_REAL", "VAL_DESP_DOTA_ATUA", "VAL_DESP_EMPE",
    "VAL_DESP_LIQU", "VAL_DESP_PAGA", "VL_DESP_DOTA_ATUA_EDU", "VL_DESP_EMPE_EDU",
    "VL_DESP_LIQU_EDU", "VL_DESP_PAGA_EDU",
}
METRICS = {
    "receita_realizada_sobre_previsao_atualizada_pct",
    "despesa_paga_sobre_dotacao_atualizada_pct",
    "despesa_educacao_paga_sobre_dotacao_atualizada_educacao_pct",
    "participacao_educacao_na_despesa_empenhada_pct",
    "participacao_educacao_na_despesa_liquidada_pct",
    "participacao_educacao_na_despesa_paga_pct",
}


def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def stop(condition, message):
    if not condition:
        raise ValueError(message)


def validate_objects(evidence, contract, acquisition, task241, continuity, proof_standard_text, b2):
    stop(
        (evidence.get("evidence_schema"), evidence.get("task"), evidence.get("issue"),
         evidence.get("base_main_sha"), evidence.get("tier")) ==
        ("TASK_242_SIOPE_HISTORICAL_FINANCIAL_SEMANTIC_VERSIONING_V1", "TASK_242", 812,
         BASE, "T0_OFFLINE_EXISTING_EVIDENCE_ONLY"),
        "TASK242 identity/base drift",
    )
    stop(task241.get("global_decision", {}).get("status") == "PARTIAL", "TASK241 dependency drift")
    stop(task241.get("financial_inputs_summary", {}).get("PARTIAL") == 10, "TASK241 financial input drift")
    stop(task241.get("financial_metrics_summary", {}).get("PARTIAL") == 6, "TASK241 metric drift")
    stop(continuity.get("result", {}).get("code") == "HISTORICAL_PROOF_STANDARD_INSUFFICIENT",
         "historical proof gap rewritten")
    stop(continuity.get("result", {}).get("positive_break_search") == "NO_POSITIVE_BREAK_EVIDENCE_FOUND",
         "positive-break search drift")
    stop("STANDARD_NOT_YET_DETERMINABLE" in proof_standard_text, "proof-standard reconciliation missing")
    stop("SOURCE_INTERNAL_IDENTITY" in proof_standard_text, "source/internal distinction missing")
    stop("não é o próximo passo automático" in proof_standard_text, "internal reverse-engineering guard missing")
    stop(b2.get("result", {}).get("B2_FINANCIAL_ALIAS_BRIDGE") == "PROVEN_10_OF_10_ALIAS_TO_CONCEPT",
         "current B2 drift")

    standard = evidence.get("proof_standard", {})
    stop(standard.get("preferred_standard") == "P1_UNIFORM_PUBLIC_CONTRACT_STANDARD_IF_TEMPORAL_APPLICABILITY_PROVEN",
         "public-contract proof standard drift")
    stop(standard.get("source_internal_identity_required_by_default") is False,
         "internal identity made mandatory without evidence")

    hist = evidence.get("repo_resident_evidence", {}).get("historical_contract", {})
    stop(hist.get("resource_all_years") == "Dados_Gerais_Siope", "historical resource drift")
    stop(hist.get("exact_fields_pinned_per_year") is False, "per-year exact fields fabricated")
    stop(hist.get("observed_types_versioned") is False, "versioned types fabricated")
    stop(hist.get("semantic_evidence") == "ARITHMETIC_FORMULA_AND_ALIAS_NAMES_ONLY", "historical semantic evidence drift")
    stop(hist.get("alias_identity") == "NO_EQUIVALENT_EXPLICIT_BRIDGE_VERSIONED", "historical alias identity drift")

    years = evidence.get("year_regime_matrix", [])
    stop([row.get("year") for row in years] == list(range(2016, 2025)), "year matrix drift")
    stop(years[0].get("period") == 1 and all(row.get("period") == 6 for row in years[1:]),
         "historical period boundary drift")
    stop(all(row.get("status") == "PARTIAL" for row in years), "historical year promoted without evidence")

    inputs = evidence.get("financial_inputs", [])
    stop(len(inputs) == 10 and {row.get("alias") for row in inputs} == ALIASES, "financial input set drift")
    stop(all(row.get("status") == "PARTIAL" for row in inputs), "financial input promoted without temporal proof")
    metrics = evidence.get("financial_metrics_1_to_6", [])
    stop(len(metrics) == 6 and {row.get("id") for row in metrics} == METRICS, "financial metric set drift")
    stop(all(row.get("status") == "PARTIAL" for row in metrics), "financial metric promoted without temporal proof")

    decision = evidence.get("offline_decision", {})
    stop(decision.get("status") == "PARTIAL" and decision.get("code") == DECISION, "TASK242 decision drift")
    stop(decision.get("financial_inputs_proven_comparable") == 0 and decision.get("financial_inputs_partial") == 10,
         "TASK242 input summary drift")
    stop(decision.get("financial_metrics_proven_comparable") == 0 and decision.get("financial_metrics_partial") == 6,
         "TASK242 metric summary drift")
    stop(decision.get("source_internal_identity_required") is False, "internal identity incorrectly required")
    stop(decision.get("remote_acquisition_required_for_next_evidence") is True, "next evidence requirement drift")
    stop(decision.get("remote_acquisition_authorized") is False, "remote acquisition authorized")
    stop(decision.get("gold_2025_authorized") is False, "Gold authorized")

    missing = evidence.get("missing_evidence_class", {})
    stop(missing.get("name") == "OFFICIAL_PUBLIC_CONTRACT_TEMPORAL_ALIAS_TO_CONCEPT_EVIDENCE_2016_2024",
         "missing evidence class drift")
    stop(len(missing.get("acceptable_routes", [])) == 3, "acceptable evidence routes drift")
    stop(evidence.get("next_gate") == NEXT, "next gate drift")

    stop(contract.get("schema") == "SIOPE_HISTORICAL_FINANCIAL_SEMANTIC_VERSIONING_V1", "contract schema drift")
    stop(contract.get("base_main_sha") == BASE, "contract base drift")
    stop(contract.get("financial_inputs", {}).get("partial") == 10, "contract input count drift")
    stop(contract.get("financial_metrics_1_to_6", {}).get("partial") == 6, "contract metric count drift")
    stop(contract.get("offline_result") == DECISION, "contract decision drift")
    stop(contract.get("remote_acquisition_authorized") is False, "contract remote acquisition authorized")
    stop(contract.get("gold_2025_authorized") is False, "contract Gold authorized")
    stop(contract.get("next_gate") == NEXT, "contract next gate drift")

    stop(acquisition.get("schema") == "SIOPE_HISTORICAL_FINANCIAL_SEMANTIC_ACQUISITION_SPEC_V1",
         "acquisition spec schema drift")
    stop(acquisition.get("design_only") is True, "acquisition spec no longer design-only")
    stop(acquisition.get("execution_authorized") is False and acquisition.get("remote_collection_authorized") is False,
         "acquisition execution authorized")
    stop(acquisition.get("years") == list(range(2016, 2025)), "acquisition years drift")
    stop(set(acquisition.get("aliases", [])) == ALIASES, "acquisition aliases drift")
    stop(len(acquisition.get("acceptable_proof_routes", [])) == 3, "acquisition proof routes drift")
    stop(acquisition.get("escalation", {}).get("source_internal_identity") == "NOT_REQUIRED_BY_DEFAULT",
         "acquisition internal identity policy drift")

    guards = evidence.get("guards", {})
    stop(guards and all(value is False for value in guards.values()), "TASK242 guard violated")
    return PASS


def validate():
    return validate_objects(
        load(EVIDENCE), load(CONTRACT), load(ACQUISITION), load(TASK241), load(CONTINUITY),
        PROOF_STANDARD_DOC.read_text(encoding="utf-8"), load(B2),
    )


if __name__ == "__main__":
    print(validate())
