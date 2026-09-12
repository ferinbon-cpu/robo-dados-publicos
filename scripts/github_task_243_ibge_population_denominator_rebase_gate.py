#!/usr/bin/env python3
"""Fail-closed T0 gate for TASK 243 IBGE population denominator rebase design."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/TASK_243_IBGE_POPULATION_DENOMINATOR_REBASE_0.8.0.json"
CONTRACT = ROOT / "config/ibge_population_denominator_rebase.v1.json"
DISCOVERY = ROOT / "config/ibge_population_source_contract_discovery_spec.v1.json"
TASK241 = ROOT / "docs/evidence/TASK_241_SIOPE_2016_2025_SEMANTIC_COMPARABILITY_0.8.0.json"
B1 = ROOT / "docs/evidence/TASK_010N_R_E_M6_SIOPE_NUM_POPU_FNDE_DISPOSITION_0.8.0.json"
TERRITORY = ROOT / "config/ibge_limeira_territorial_foundation.v1.json"
GOLD_SCOPE = ROOT / "docs/references/M7_SIOPE_LIMEIRA_GOLD_ARITHMETIC_SCOPE_0.8.0.md"

BASE = "620464182c911415f885fac64ce789e10c9e7c50"
DECISION = "STOP_IBGE_REBASE_SOURCE_CONTRACT_NOT_PINNED"
NEXT = "BOUNDED_OFFICIAL_IBGE_POPULATION_SOURCE_CONTRACT_AND_SERIES_ACQUISITION_REQUIRES_EXPLICIT_AUTHORIZATION"
PASS = "PASS_TASK243_SOURCE_CONTRACT_NOT_PINNED_FAIL_CLOSED"
YEARS = list(range(2016, 2026))
METRICS = {"despesa_total_paga_por_habitante", "despesa_educacao_paga_por_habitante"}


def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream)


def stop(condition, message):
    if not condition:
        raise ValueError(message)


def validate_objects(evidence, contract, discovery, task241, b1, territory, gold_scope_text):
    stop(
        (evidence.get("evidence_schema"), evidence.get("task"), evidence.get("issue"),
         evidence.get("base_main_sha"), evidence.get("tier")) ==
        ("TASK_243_IBGE_POPULATION_DENOMINATOR_REBASE_V1", "TASK_243", 813,
         BASE, "T0_OFFLINE_EXISTING_EVIDENCE_ONLY"),
        "TASK243 identity/base drift",
    )
    scope = evidence.get("scope", {})
    stop(scope.get("municipality") == "Limeira" and scope.get("uf") == "SP", "municipality drift")
    stop(scope.get("ibge_code_7") == "3526902" and scope.get("siope_municipality_code") == 352690,
         "municipality code drift")
    stop(scope.get("years") == YEARS, "year scope drift")
    stop(set(scope.get("target_metrics", [])) == METRICS, "target metric drift")

    entry = evidence.get("entry_state", {})
    stop(entry.get("task241_per_capita_status") == "NON_COMPARABLE", "TASK241 per-capita state drift")
    stop(entry.get("num_popu_2025") == "FORBIDDEN_FOR_ANALYTICAL_POPULATION_USE", "NUM_POPU entry drift")
    stop(entry.get("historical_num_popu_compatibility") == "NOT_PROVEN", "historical NUM_POPU drift")
    stop(entry.get("historical_gold_rewrite_authorized") is False, "historical Gold rewrite authorized")
    stop(entry.get("gold_2025") == "BLOCKED_NOT_CALCULATED", "Gold entry drift")
    stop(entry.get("closed_annual_series") == "2016-2024", "closed series entry drift")

    task_pc = task241.get("per_capita_summary", {})
    stop(task_pc.get("NON_COMPARABLE") == 2, "TASK241 per-capita count drift")
    stop(task_pc.get("num_popu_2025_use_forbidden") is True, "TASK241 NUM_POPU guard drift")
    stop(task_pc.get("historical_num_popu_compatibility_inferred") is False,
         "TASK241 historical NUM_POPU inference drift")
    stop(task_pc.get("historical_gold_rewrite_authorized") is False, "TASK241 historical rewrite drift")

    stop(b1.get("source_statements", {}).get("recommended_population_source") == "OFFICIAL_IBGE_BASES_DIRECTLY",
         "FNDE population route drift")
    stop(b1.get("source_statements", {}).get("recommended_treatment_of_num_popu_for_population_analysis") == "DISREGARD",
         "FNDE NUM_POPU disposition drift")
    stop(b1.get("guards", {}).get("num_popu_used_as_population_denominator") is False,
         "B1 NUM_POPU denominator guard drift")

    terr_scope = territory.get("scope", {})
    stop(terr_scope.get("municipality") == "Limeira" and terr_scope.get("uf") == "SP" and
         terr_scope.get("ibge_code_7") == "3526902", "IBGE territorial identity drift")
    city = next((row for row in territory.get("official_source_registry", []) if row.get("id") == "IBGE_CIDADES_LIMEIRA"), None)
    stop(city is not None, "IBGE Cidades source missing")
    observed = city.get("observed_values", {})
    stop(observed.get("population_census_2022") == 291869, "2022 census observation drift")
    stop(observed.get("population_estimate_2025") == 301292, "2025 estimate observation drift")
    stop(city.get("status") == "OFFICIAL_WEB_OBSERVED_RAW_BYTES_NOT_CAPTURED", "IBGE Cidades custody drift")

    repo_ibge = evidence.get("repo_resident_ibge_evidence", {})
    terr_ev = repo_ibge.get("territorial_foundation", {})
    stop(terr_ev.get("annual_population_series_2016_2025_materialized") is False,
         "annual population series fabricated")
    stop(terr_ev.get("denominator_product_contract_materialized") is False,
         "denominator contract fabricated")
    fnde = repo_ibge.get("fnde_num_popu_disposition", {})
    stop(fnde.get("specific_ibge_product_selected_by_fnde") is False, "IBGE product selection fabricated")
    stop(fnde.get("specific_reference_rule_selected_by_fnde") is False, "reference rule fabricated")

    discovery_result = evidence.get("offline_discovery_result", {})
    stop(discovery_result.get("status") == "SOURCE_CONTRACT_NOT_PINNED", "offline discovery state drift")
    stop(discovery_result.get("annual_population_values_2016_2025_materialized") == 0,
         "annual population values fabricated")
    stop(discovery_result.get("single_year_population_observations_available") == [2022, 2025],
         "single-year observations drift")
    stop(discovery_result.get("single_year_observations_sufficient_for_rebase") is False,
         "single-year observations incorrectly sufficient")
    for key in ("sidra_assumed", "census_assumed_for_all_years", "annual_estimates_assumed"):
        stop(discovery_result.get(key) is False, f"source product assumption violated: {key}")
    stop(discovery_result.get("remote_acquisition_required_for_next_evidence") is True,
         "next evidence acquisition requirement drift")
    stop(discovery_result.get("remote_acquisition_authorized") is False, "remote acquisition authorized")
    stop(discovery_result.get("rebased_per_capita_calculation_authorized") is False, "rebase calculation authorized")

    required = evidence.get("required_source_contract", {})
    stop(required.get("authority") == "IBGE", "required authority drift")
    stop(required.get("product_name") == "NOT_PINNED" and required.get("population_concept") == "NOT_PINNED",
         "unproven source product/concept pinned")
    stop(required.get("unit") == "persons" and required.get("geographic_grain") == "municipality",
         "required population unit/grain drift")
    stop(required.get("required_years") == YEARS, "required year coverage drift")
    stop(required.get("revision_policy_required") is True and required.get("method_change_policy_required") is True,
         "version/method policy requirement lost")
    stop(required.get("no_silent_interpolation") is True and required.get("no_silent_imputation") is True,
         "imputation guard lost")

    rebased = evidence.get("rebased_series_contract", {})
    stop(rebased.get("identity") == "SIOPE_PER_CAPITA_IBGE_REBASED_2016_2025", "rebased identity drift")
    stop(rebased.get("role") == "NEW_COMPARABLE_DERIVED_SERIES_NOT_HISTORICAL_GOLD_REWRITE",
         "rebased series role drift")
    stop(rebased.get("population_denominator") == "OFFICIAL_IBGE_CONTRACT_PENDING",
         "population denominator prematurely pinned")
    stop(rebased.get("historical_gold_original_preserved") is True and
         rebased.get("historical_gold_mutation_authorized") is False and
         rebased.get("calculation_authorized") is False,
         "historical/rebase authorization drift")

    decision = evidence.get("decision", {})
    stop(decision.get("status") == "PARTIAL" and decision.get("code") == DECISION, "TASK243 decision drift")
    stop(decision.get("metrics_7_to_8_current_contract") == "NON_COMPARABLE", "per-capita decision drift")
    stop(decision.get("source_contract_discovery_complete_offline") is True, "offline discovery completion drift")
    stop(decision.get("population_series_acquisition_needed") is True, "population acquisition need drift")
    stop(decision.get("population_series_acquisition_authorized") is False, "population acquisition authorized")
    stop(decision.get("rebased_series_authorized") is False, "rebased series authorized")
    stop(decision.get("gold_2025_authorized") is False, "Gold authorized")
    stop(decision.get("series_2016_2025_authorized") is False, "series inclusion authorized")
    stop(decision.get("release_promotion_authorized") is False, "release promotion authorized")
    stop(evidence.get("next_gate") == NEXT, "next gate drift")

    stop(contract.get("schema") == "IBGE_POPULATION_DENOMINATOR_REBASE_V1", "contract schema drift")
    stop(contract.get("base_main_sha") == BASE, "contract base drift")
    stop(contract.get("source_contract_status") == "SOURCE_CONTRACT_NOT_PINNED", "contract source state drift")
    stop(contract.get("annual_population_series_materialized") is False, "contract annual series fabricated")
    stop(contract.get("historical_num_popu_compatible") == "NOT_PROVEN", "contract NUM_POPU drift")
    stop(contract.get("num_popu_2025_allowed") is False, "contract allows NUM_POPU")
    stop(contract.get("rebased_series_calculation_authorized") is False, "contract authorizes rebase")
    stop(contract.get("historical_gold_rewrite_authorized") is False, "contract authorizes history rewrite")
    stop(contract.get("remote_acquisition_authorized") is False, "contract authorizes remote acquisition")
    stop(contract.get("decision") == DECISION and contract.get("next_gate") == NEXT, "contract decision routing drift")

    stop(discovery.get("schema") == "IBGE_POPULATION_SOURCE_CONTRACT_DISCOVERY_SPEC_V1", "discovery schema drift")
    stop(discovery.get("design_only") is True, "discovery spec no longer design-only")
    stop(discovery.get("execution_authorized") is False and discovery.get("remote_collection_authorized") is False,
         "discovery execution authorized")
    stop(discovery.get("target_years") == YEARS, "discovery years drift")
    policy = discovery.get("candidate_product_policy", {})
    stop(policy.get("preselected_product") is None, "IBGE product preselected")
    for key in ("sidra_assumed", "ibge_cidades_assumed", "annual_estimates_assumed", "census_assumed_for_non_census_years"):
        stop(policy.get(key) is False, f"candidate product assumption violated: {key}")
    stop(discovery.get("result_identity") == "SIOPE_PER_CAPITA_IBGE_REBASED_2016_2025", "discovery output identity drift")
    preservation = discovery.get("historical_preservation", {})
    stop(preservation.get("historical_gold_original_mutable") is False and
         preservation.get("rebased_series_is_separate_product") is True,
         "historical preservation drift")

    stop("NUM_POPU" in gold_scope_text and "por habitante" in gold_scope_text,
         "historical Gold denominator evidence missing")
    guards = evidence.get("guards", {})
    stop(guards and all(value is False for value in guards.values()), "TASK243 guard violated")
    return PASS


def validate():
    return validate_objects(
        load(EVIDENCE), load(CONTRACT), load(DISCOVERY), load(TASK241), load(B1), load(TERRITORY),
        GOLD_SCOPE.read_text(encoding="utf-8"),
    )


if __name__ == "__main__":
    print(validate())
