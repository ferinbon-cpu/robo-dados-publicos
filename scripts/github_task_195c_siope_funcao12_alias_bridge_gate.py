from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/task195c_siope_funcao12_alias_bridge.v1.json"
EVIDENCE = ROOT / "docs/evidence/TASK_195C_SIOPE_FUNCAO12_ALIAS_BRIDGE_0.8.0.json"

EXPECTED_BASE = "dc7dbc94979bdad2b02eebd449a801cdcebe5f67"
EXPECTED_TARGET = "VL_DESP_DOTA_ATUA_EDU"
EXPECTED_VALUE = "520399255.47"
EXPECTED_RREO = "520398255.47"
EXPECTED_VARIANCE = "1000.00"
EXPECTED_B2 = "PROVEN_10_OF_10_ALIAS_TO_CONCEPT"
EXPECTED_B3 = "NOT_PROVEN_EFFECTIVE_SELECTION_RULE_MISSING"
EXPECTED_DECISION = "PROVE_B2_10_OF_10_ALIAS_TO_CONCEPT_PRESERVE_B3_AND_GOLD_BLOCK"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(config: dict, evidence: dict) -> None:
    if config.get("schema") != "TASK195C_SIOPE_FUNCAO12_ALIAS_BRIDGE_V1":
        raise ValueError("TASK195C config schema drift")
    if config.get("base_main_sha") != EXPECTED_BASE:
        raise ValueError("TASK195C canonical base drift")
    scope = config.get("scope", {})
    if (scope.get("year"), scope.get("period"), scope.get("municipality_code")) != (2025, 6, 352690):
        raise ValueError("TASK195C identity drift")
    if scope.get("target_alias") != EXPECTED_TARGET:
        raise ValueError("TASK195C target alias drift")

    dictionary = config.get("official_documentary_chain", {}).get("dictionary_2019", {})
    fields = dictionary.get("fields", [])
    mapping = {row.get("current_alias"): row for row in fields}
    if len(mapping) != 10:
        raise ValueError("TASK195C must pin exactly ten financial alias mappings")
    target = mapping.get(EXPECTED_TARGET, {})
    if target.get("historical_field") != "VL_DOTACAO_ATUALIZADA_EDUCACAO":
        raise ValueError("TASK195C historical education-dotacao field drift")
    if target.get("meaning") != "Valor de despesa dotada atualizada com educação":
        raise ValueError("TASK195C historical concept drift")

    tutorial = config.get("official_documentary_chain", {}).get("tutorial_2024", {})
    if tutorial.get("dados_gerais_tabs_observed") != [
        "Receita total do Município",
        "Despesa total do Município",
        "Despesa com Educação (Função 12)",
    ]:
        raise ValueError("TASK195C official Dados Gerais tab boundary drift")
    if tutorial.get("mde_is_separate_guide") is not True or tutorial.get("demonstrativo_is_separate_screen") is not True:
        raise ValueError("TASK195C MDE/Demonstrativo separation lost")

    metadata = config.get("official_documentary_chain", {}).get("metadata_2025", {})
    if metadata.get("education_root") != {"name": "Despesas com Educação", "COD_PAST": 27}:
        raise ValueError("TASK195C current education-root identity drift")
    if metadata.get("standard_stages") != {
        "DA": "Dotação Atualizada",
        "DE": "Desp. Empenhadas",
        "DL": "Desp. Liquidadas",
        "DP": "Desp. Pagas",
    }:
        raise ValueError("TASK195C current financial-stage labels drift")
    if metadata.get("mde_separate_structure") is not True:
        raise ValueError("TASK195C must preserve EDU != MDE")

    op = config.get("operational_evidence", {})
    if (op.get("target_alias_observed_value"), op.get("rreo_anexo_8_line_33_da"), op.get("rreo_variance")) != (
        EXPECTED_VALUE,
        EXPECTED_RREO,
        EXPECTED_VARIANCE,
    ):
        raise ValueError("TASK195C pinned values drift")
    siblings = op.get("three_education_execution_siblings", [])
    if len(siblings) != 3 or any(x.get("status") != "PROVEN_EXACT_OPERATIONAL" for x in siblings):
        raise ValueError("TASK195C education sibling proof drift")

    semantic = config.get("semantic_decision", {})
    if semantic.get(EXPECTED_TARGET) != "PROVEN_ALIAS_TO_EDUCATION_EXPENSE_UPDATED_BUDGET_CONCEPT":
        raise ValueError("TASK195C target semantic state not proven")
    if semantic.get("education_scope") != "DESPESA_COM_EDUCACAO_FUNCAO_12":
        raise ValueError("TASK195C education scope drift")
    if semantic.get("B2_FINANCIAL_ALIAS_BRIDGE") != EXPECTED_B2:
        raise ValueError("TASK195C B2 must be exactly 10/10 alias-to-concept")
    if semantic.get("rreo_line_33_identity_required") is not False:
        raise ValueError("TASK195C must not require RREO line 33 identity")
    if semantic.get("backend_account_inclusion_formula") != "NOT_PROVEN_NOT_REQUIRED_FOR_ALIAS_TO_CONCEPT_IDENTITY":
        raise ValueError("TASK195C must not fabricate backend formula")
    if semantic.get("source_defined_1000_inclusion_rule") != "NOT_CLAIMED":
        raise ValueError("TASK195C must not promote the R$1000 candidate into a rule")
    if semantic.get("EDU_equals_MDE") is not False:
        raise ValueError("TASK195C must preserve EDU != MDE")

    probe = config.get("bounded_remote_probe", {})
    if probe.get("form_submission_performed") is not False or probe.get("captcha_bypass_attempted") is not False:
        raise ValueError("TASK195C CAPTCHA/form boundary violated")
    if probe.get("tinyfish_used") is not False:
        raise ValueError("TASK195C should not claim TinyFish use")
    attempts = probe.get("odata_da_runs", [])
    if len(attempts) != 3 or any(x.get("semantic_result") is not False for x in attempts):
        raise ValueError("TASK195C timeout attempts cannot become semantic evidence")
    if probe.get("timeout_is_not_zero_rows") is not True:
        raise ValueError("TASK195C transport timeout guard lost")

    release = config.get("release_effect", {})
    if release.get("B1_NUM_POPU") != "RESOLVED_BY_EXCLUSION_FROM_ANALYTICAL_POPULATION_SEMANTICS":
        raise ValueError("TASK195C must preserve authoritative B1 disposition")
    if release.get("B2_FINANCIAL_ALIAS_BRIDGE") != EXPECTED_B2:
        raise ValueError("TASK195C B2 release effect drift")
    if release.get("B3_EFFECTIVE_ANNUAL_DECLARATION") != EXPECTED_B3:
        raise ValueError("TASK195C must not promote B3")
    if release.get("gold_2025_calculated") is not False or release.get("release_0_8_0") != "CANDIDATE":
        raise ValueError("TASK195C must not calculate Gold or promote release")
    if release.get("closed_annual_series") != "2016-2024":
        raise ValueError("TASK195C must not widen closed annual series")

    required_guards = {
        "DADOS_GERAIS_FUNCAO12_NE_RREO_LINE33_IDENTITY",
        "EDU_NE_MDE",
        "ALIAS_CONCEPT_PROOF_NE_BACKEND_AGGREGATION_FORMULA",
        "THOUSAND_REAL_VARIANCE_NE_INCLUSION_RULE_PROOF",
        "TRANSPORT_TIMEOUT_NE_ZERO_ROWS",
        "CAPTCHA_NOT_BYPASSED",
        "B3_UNCHANGED",
        "NO_GOLD_2025_CALCULATION",
        "NO_RELEASE_PROMOTION",
    }
    if not required_guards.issubset(set(config.get("guards", []))):
        raise ValueError("TASK195C required fail-closed guards missing")
    if config.get("decision") != EXPECTED_DECISION:
        raise ValueError("TASK195C decision drift")

    if evidence.get("evidence_schema") != "TASK195C_SIOPE_FUNCAO12_ALIAS_BRIDGE_EVIDENCE_V1":
        raise ValueError("TASK195C evidence schema drift")
    result = evidence.get("result", {})
    if result.get(EXPECTED_TARGET) != "PROVEN_ALIAS_TO_EDUCATION_EXPENSE_UPDATED_BUDGET_CONCEPT":
        raise ValueError("TASK195C evidence target state drift")
    if result.get("B2_FINANCIAL_ALIAS_BRIDGE") != EXPECTED_B2:
        raise ValueError("TASK195C evidence B2 drift")
    if result.get("backend_aggregation_formula") != "NOT_PROVEN":
        raise ValueError("TASK195C evidence must preserve formula unknown")
    if result.get("1000_account_inclusion_rule") != "NOT_PROVEN_AND_NOT_ASSERTED":
        raise ValueError("TASK195C evidence must preserve R$1000 rule unknown")
    if result.get("B3_EFFECTIVE_ANNUAL_DECLARATION") != EXPECTED_B3:
        raise ValueError("TASK195C evidence must preserve B3")
    if result.get("gold_2025") != "BLOCKED_NOT_CALCULATED":
        raise ValueError("TASK195C evidence must keep Gold blocked")


def main() -> int:
    validate(load(CONFIG), load(EVIDENCE))
    print("PASS_TASK195C_SIOPE_FUNCAO12_ALIAS_BRIDGE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
