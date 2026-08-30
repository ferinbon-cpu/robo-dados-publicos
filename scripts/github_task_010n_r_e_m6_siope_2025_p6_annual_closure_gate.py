#!/usr/bin/env python3
"""Fail-closed offline B3 closure/finality gate for TASK 010N-R-E-M6."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_010N_R_E_M6_SIOPE_2025_P6_ANNUAL_CLOSURE_FINALITY_0.8.0.json"
DECISION = "KEEP_ANNUAL_CLOSURE_UNKNOWN_EFFECTIVE_STATUS_RULE_MISSING"
FIELDS = ["DAT_DECL", "IDN_DECL_RETI", "DS_JUST_RETIFICACAO", "NUM_RECI", "NUM_SOLI", "TIPO", "IDN_TIPO_DECL", "DS_NOTA_RODAPE_RREO", "DS_NOTA_RODAPE_FUNDEB", "IDN_POSS_CERT_TC", "IDN_POSS_DECI_JUDI"]
STATE = {"release_0_7_0": "ACTIVE", "release_0_8_0": "CANDIDATE", "year_2025": "PROVEN_STRUCTURAL_RECENT", "S1_NUM_POPU": "NOT_PROVEN", "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN", "financial_aliases_proven_exact_operational": "9/10", "annual_closure_status": "UNKNOWN", "semantic_comparability_status": "UNKNOWN", "closed_annual_series": "2016-2024", "gold_2025": "UNKNOWN/BLOCKED", "year_2026": "UNPROVEN_CURRENT_YEAR"}


def validate(data):
    identity = (data.get("evidence_schema"), data.get("task"), data.get("base_main_sha"), data.get("tier"))
    if identity != ("TASK_010N_R_E_M6_SIOPE_2025_P6_ANNUAL_CLOSURE_FINALITY_V1", "TASK_010N-R-E-M6", "bef759cd11f364519f84c822522cac1d028ca604", "T0_OFFLINE_REVIEW_WITH_BOUNDED_PUBLIC_DOCUMENTARY_DISCOVERY"):
        raise ValueError("identity, base, or tier drifted")
    if data.get("scope") != {"year": 2025, "period": 6, "municipality": "Limeira", "municipality_code": 352690, "uf": "SP", "resource": "Dados_Gerais_Siope"}:
        raise ValueError("year, P6, or Limeira identity drifted")
    model = data.get("closure_proof_model", {})
    required = {"ANNUAL_CONSOLIDATION", "VALID_ANNUAL_SUBMISSION", "CURRENTLY_EFFECTIVE_DECLARATION", "RECTIFICATION_POSSIBLE", "RECTIFICATION_PENDING", "SUPERSEDED_DECLARATION", "SOURCE_FINAL_LOCKED_STATE", "REPOSITORY_CLOSED_SERIES_ELIGIBILITY"}
    if set(model) != required or not model["ANNUAL_CONSOLIDATION"].startswith("PROVEN:") or not model["CURRENTLY_EFFECTIVE_DECLARATION"].startswith("NOT_PROVEN:") or not model["RECTIFICATION_POSSIBLE"].startswith("PROVEN:"):
        raise ValueError("closure model missing or annual consolidation used as finality")
    history = data.get("historical_reconciliation", {})
    if history.get("classification") != "F_REPOSITORY_CONVENTION_WITHOUT_EXPLICIT_SOURCE_FINALITY_PROOF" or not all(k in history for k in ("2016", "2017_2020", "2021_2024", "2025", "policy")):
        raise ValueError("historical proof standard unreconciled")
    rows = data.get("candidate_field_inventory", [])
    if [r.get("field") for r in rows] != FIELDS or any(set(r) != {"field", "structural_presence", "observed_value", "official_definition", "original_vs_rectifying", "currently_effective", "proof_kind"} for r in rows):
        raise ValueError("status field missing or inventory drifted")
    if any(not r["structural_presence"] or r["observed_value"] is not None or r["official_definition"] is not None or r["currently_effective"] != "NOT_PROVEN" for r in rows):
        raise ValueError("status value drift or undocumented status interpretation")
    sources = data.get("official_documentary_sources", [])
    if len(sources) != 3 or any(r.get("authority") != "FNDE" or not r.get("url", "").startswith("https://") or not r.get("supports") or not r.get("does_not_support") for r in sources):
        raise ValueError("missing source rule provenance")
    if data.get("decision") != DECISION:
        raise ValueError("B3 decision drifted")
    observation = data.get("current_observation", {})
    if observation.get("performed") is not False or not observation.get("reason") or not observation.get("required_after_rule_is_pinned"):
        raise ValueError("unauthorized or incomplete current observation")
    expected_result = {"annual_closure_status": "UNKNOWN", "immutable_finality": "NOT_PROVEN_NOT_REQUIRED_FOR_MODEL_BUT_EFFECTIVE_STATUS_RULE_MISSING", "semantic_comparability_status": "UNKNOWN", "closed_series_2025_eligibility": "BLOCKED_BY_B3_AND_S1_S2_SEMANTIC_COMPARABILITY", "closed_annual_series": "2016-2024", "gold_2025": "UNKNOWN/BLOCKED"}
    if data.get("resulting_state") != expected_result or data.get("canonical_state") != STATE:
        raise ValueError("forbidden semantic, series, Gold, release, or 2026 promotion")
    guards = {"annual_consolidation_alone_used_as_finality": False, "field_semantics_inferred": False, "rectification_possible_treated_as_automatic_ineffectiveness": False, "future_immutability_assumed": False, "remote_writes": 0, "publication": False, "gold_computation": False}
    if data.get("guards") != guards:
        raise ValueError("fail-closed guard drifted")
    return DECISION


def main():
    print(validate(json.loads(EVIDENCE.read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
