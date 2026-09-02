"""Fail-closed validation for TASK 055A EITI terminology ontology."""
from __future__ import annotations

from typing import Any

TASK = "TASK_055A_F01_EITI_TERMINOLOGY_ONTOLOGY"
MODE = "T0_TERMINOLOGY_AND_NORMATIVE_ONTOLOGY_DESIGN"
BASE_SHA = "9394e7bc63c5c4128728f416e60d694c85c188db"
RESULT = "PASS_TASK055A_EITI_TERMINOLOGY_ONTOLOGY_READY_TASK056_REQUIRES_ONTOLOGY"
FAMILIES = (
    "A_CANONICAL_POLICY_IDENTIFIERS",
    "B_LOCAL_PLANNING_AND_NORMATIVE_ALIASES",
    "C_OPERATIONAL_OFFER_AND_JOURNEY_SIGNALS",
    "D_FINANCING_AND_INDUCTION_SIGNALS",
    "E_ACCOUNTING_AND_PLANNING_LINKAGE_KEYS",
)


class Task055AError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task055AError(code)


def validate_task055a_evidence(evidence: dict[str, Any], task055: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK055A_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK055A_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK055A_BASE_SHA_MISMATCH")
    _require(task055.get("task") == "TASK_055_F01_SELECTED_GRANULAR_SOURCE_BOUNDED_CONTENT_READ", "TASK055A_UPSTREAM_TASK_MISMATCH")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "TASK055A_OWNER_AUTH_MISSING")
    _require(auth.get("owner_message") == "Prossiga", "TASK055A_OWNER_MESSAGE_MISMATCH")
    _require(auth.get("authorization_consumed") is True, "TASK055A_AUTH_NOT_CONSUMED")
    _require(auth.get("future_blanket_authorizations_accepted") is False, "TASK055A_BLANKET_AUTH_FORBIDDEN")

    ontology = evidence.get("ontology") or {}
    for family in FAMILIES:
        values = ontology.get(family)
        _require(isinstance(values, list) and len(values) >= 5, f"TASK055A_FAMILY_{family}_MISSING_OR_TOO_SMALL")

    a = set(ontology["A_CANONICAL_POLICY_IDENTIFIERS"])
    _require("EITI" in a, "TASK055A_EITI_MISSING")
    _require("Programa Escola em Tempo Integral" in a, "TASK055A_PROGRAMA_ETI_FULL_NAME_MISSING")
    _require("Educacao Integral em Tempo Integral" in a, "TASK055A_EITI_FULL_NAME_MISSING")
    _require("Educacao em Tempo Integral" in a, "TASK055A_LOCAL_EDUCACAO_TEMPO_INTEGRAL_MISSING")

    b = set(ontology["B_LOCAL_PLANNING_AND_NORMATIVE_ALIASES"])
    _require("escolas com programas em tempo integral" in b, "TASK055A_PPA2018_ALIAS_MISSING")
    _require("indice de alunos em Educacao Integral" in b, "TASK055A_PPA2022_ALIAS_MISSING")
    _require("Meta 6" in b, "TASK055A_META6_MISSING")

    c = set(ontology["C_OPERATIONAL_OFFER_AND_JOURNEY_SIGNALS"])
    for term in ("jornada ampliada", "matriculas em tempo integral", "7 horas", "35 horas", "turno unico"):
        _require(term in c, f"TASK055A_OPERATIONAL_TERM_MISSING_{term}")

    d = set(ontology["D_FINANCING_AND_INDUCTION_SIGNALS"])
    for term in ("FUNDEB", "MDE", "fomento", "dotacao orcamentaria", "fonte de recursos"):
        _require(term in d, f"TASK055A_FINANCE_TERM_MISSING_{term}")

    e = set(ontology["E_ACCOUNTING_AND_PLANNING_LINKAGE_KEYS"])
    for term in ("programa", "acao", "subacao", "empenhado", "liquidado", "pago"):
        _require(term in e, f"TASK055A_ACCOUNTING_TERM_MISSING_{term}")

    rules = evidence.get("matching_rules") or {}
    _require(rules.get("no_semantic_overreach") is True, "TASK055A_SEMANTIC_OVERREACH_GUARD_MISSING")
    _require("POLICY_SIGNAL_PLUS" in rules.get("financial_identity_rule", ""), "TASK055A_FINANCIAL_IDENTITY_RULE_WEAK")
    _require("MUST_NOT" in rules.get("finance_signal_rule", ""), "TASK055A_FINANCE_FALSE_POSITIVE_GUARD_MISSING")
    _require("MUST_NOT" in rules.get("accounting_signal_rule", ""), "TASK055A_ACCOUNTING_FALSE_POSITIVE_GUARD_MISSING")

    reinterpretation = evidence.get("task055_reinterpretation") or {}
    _require(reinterpretation.get("structural_granularity_finding_remains_valid") is True, "TASK055A_TASK055_STRUCTURE_INVALIDATED")
    _require(reinterpretation.get("pre_055a_lexical_negative_search_is_exhaustive") is False, "TASK055A_LEXICAL_NEGATIVE_OVERCLAIM")
    _require(reinterpretation.get("future_tasks_must_use_ontology") is True, "TASK055A_FUTURE_ONTOLOGY_NOT_REQUIRED")

    gate = evidence.get("future_task056_contract") or {}
    _require(gate.get("ontology_required") is True, "TASK055A_TASK056_ONTOLOGY_NOT_REQUIRED")
    _require(gate.get("search_all_five_term_families") is True, "TASK055A_TASK056_FAMILY_COVERAGE_WEAK")
    _require(gate.get("fresh_owner_authorization_required_before_source_read") is True, "TASK055A_TASK056_AUTH_WEAKENED")

    effects = evidence.get("effects") or {}
    for key in ("f01_source_content_reads", "drive_write", "bronze", "silver", "gold", "serving", "publication"):
        _require(effects.get(key) == 0, f"TASK055A_EFFECT_{key.upper()}_NONZERO")

    promotion = evidence.get("promotion") or {}
    _require(promotion.get("terminology_ontology_ready") is True, "TASK055A_ONTOLOGY_NOT_READY")
    _require(promotion.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK055A_EITI_STATUS_CHANGED")
    _require(promotion.get("gold") is False, "TASK055A_GOLD_ENABLED")
    _require(evidence.get("result") == RESULT, "TASK055A_RESULT_MISMATCH")

    return {
        "status": RESULT,
        "family_count": len(FAMILIES),
        "ontology_required_for_task056": True,
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
    }
