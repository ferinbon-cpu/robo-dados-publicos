from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any

from robo_dados_publicos.router.rules import route_query as legacy_route_query


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROUTER = ROOT / "config/observatory_unified_query_router.v1.json"
DEFAULT_ONTOLOGY = ROOT / "config/observatory_question_ontology.v1.json"
DEFAULT_MATURITY = ROOT / "config/source_family_maturity_registry.v1.json"
DEFAULT_SOURCE_ROLES = ROOT / "config/source_role_evidence_semantics.v1.json"
DEFAULT_BUDGET_MAP = ROOT / "config/budget_fiscal_source_acquisition_map.v1.json"


class Task175Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task175Stop(code)


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _upper_ascii(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.upper().split())


def load_contracts(
    router_path: str | Path = DEFAULT_ROUTER,
    ontology_path: str | Path = DEFAULT_ONTOLOGY,
    maturity_path: str | Path = DEFAULT_MATURITY,
    source_roles_path: str | Path = DEFAULT_SOURCE_ROLES,
    budget_map_path: str | Path = DEFAULT_BUDGET_MAP,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    router = _load(router_path)
    ontology = _load(ontology_path)
    maturity = _load(maturity_path)
    source_roles = _load(source_roles_path)
    budget_map = _load(budget_map_path)
    return router, ontology, maturity, source_roles, budget_map


def validate_contracts(
    router_path: str | Path = DEFAULT_ROUTER,
    ontology_path: str | Path = DEFAULT_ONTOLOGY,
    maturity_path: str | Path = DEFAULT_MATURITY,
    source_roles_path: str | Path = DEFAULT_SOURCE_ROLES,
    budget_map_path: str | Path = DEFAULT_BUDGET_MAP,
) -> dict[str, Any]:
    router, ontology, maturity, source_roles, budget_map = load_contracts(
        router_path, ontology_path, maturity_path, source_roles_path, budget_map_path
    )
    _stop(router.get("schema") == "UNIFIED_OBSERVATORY_QUERY_ROUTER_V1", "TASK175_ROUTER_SCHEMA")
    _stop(router.get("mode") == "T0_OFFLINE_QUERY_PLANNING", "TASK175_ROUTER_MODE")
    _stop(ontology.get("schema") == "LIMEIRA_OBSERVATORY_QUESTION_ONTOLOGY_V1", "TASK175_ONTOLOGY_SCHEMA")
    _stop(maturity.get("version") == 1 and isinstance(maturity.get("families"), dict), "TASK175_MATURITY_SCHEMA")
    _stop(source_roles.get("schema") == "SOURCE_ROLE_EVIDENCE_SEMANTICS_V1", "TASK175_SOURCE_ROLE_SCHEMA")
    _stop(budget_map.get("schema") == "LIMEIRA_BUDGET_FISCAL_SOURCE_ACQUISITION_MAP_V1", "TASK175_BUDGET_MAP_SCHEMA")

    ontology_ids = {row["id"] for row in ontology["domains"]}
    route_ids = set(router["domain_routes"])
    _stop(len(ontology_ids) == 15, "TASK175_DOMAIN_COUNT")
    _stop(ontology_ids == route_ids, "TASK175_DOMAIN_ROUTE_COVERAGE")
    _stop(
        router["answer_contract"] == ontology["answer_contract"]["required_parts_when_available"],
        "TASK175_ANSWER_CONTRACT",
    )
    _stop(
        set(router["route_modes"]) == {"NUMERIC", "DOCUMENT", "HYBRID"},
        "TASK175_ROUTE_MODES",
    )
    _stop(
        "SOURCE_ROLE_LIMITS_WHAT_A_DOCUMENT_CAN_DIRECTLY_PROVE" in source_roles["invariants"],
        "TASK175_SOURCE_ROLE_GUARD",
    )
    _stop(
        "STATISTICAL_OBSERVATION_IS_NOT_CAUSAL_EFFECT" in source_roles["invariants"],
        "TASK175_CAUSAL_GUARD",
    )
    effects = router.get("remote_effects") or {}
    _stop(effects and all(value is False for value in effects.values()), "TASK175_REMOTE_EFFECT")
    return {
        "schema": "TASK175_ROUTER_VALIDATION_RESULT_V1",
        "status": "PASS",
        "domain_count": len(ontology_ids),
        "scenario_count": len(router["scenario_expansions"]),
        "network": False,
        "drive_write": False,
        "serving": False,
        "publication": False,
    }


def _readiness(
    source: str,
    router: dict[str, Any],
    maturity: dict[str, Any],
) -> dict[str, Any]:
    family = (maturity.get("families") or {}).get(source)
    family_level = family.get("level") if isinstance(family, dict) else "UNREGISTERED_REVIEW"
    family_score = router["maturity_scores"].get(family_level, 1)
    override = (router.get("exact_capability_overrides") or {}).get(source)
    if override:
        score = max(family_score, int(override["score"]))
        status = override["status"]
        scope_note = (
            "EXACT_CAPABILITY_PROVEN_BUT_FAMILY_NOT_GLOBALLY_PROMOTED"
            if family_level not in {"EXECUTION_READY_BOUNDED"} and score >= 3
            else "CAPABILITY_ALIGNED_WITH_FAMILY_MATURITY"
        )
    else:
        score = family_score
        status = family_level
        scope_note = "FAMILY_LEVEL_ONLY"
    return {
        "family_maturity": family_level,
        "readiness_status": status,
        "readiness_score": score,
        "readiness_scope_note": scope_note,
        "evidence_ref": override.get("evidence") if override else None,
    }


def _ordered_unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


def _matching_scenarios(question_text: str, router: dict[str, Any]) -> list[dict[str, Any]]:
    q = _upper_ascii(question_text)
    matches = []
    for scenario in router["scenario_expansions"]:
        observed = [marker for marker in scenario["markers"] if _upper_ascii(marker) in q]
        if observed:
            matches.append({**scenario, "matched_markers": observed})
    return matches


def _coverage_state(mode: str, source_plans: list[dict[str, Any]]) -> str:
    numeric_ready = any(
        p["source_mode"] in {"NUMERIC", "BOTH"} and p["readiness_score"] >= 3
        for p in source_plans
    )
    document_ready = any(
        p["source_mode"] in {"DOCUMENT", "BOTH"} and p["readiness_score"] >= 3
        for p in source_plans
    )
    any_supervised_or_ready = any(p["readiness_score"] >= 2 for p in source_plans)

    if mode == "NUMERIC" and numeric_ready:
        return "READY_CORE"
    if mode == "DOCUMENT" and document_ready:
        return "READY_CORE"
    if mode == "HYBRID" and numeric_ready and document_ready:
        return "READY_CORE"
    if any_supervised_or_ready:
        return "PARTIAL"
    return "BLOCKED_OR_UNREGISTERED"


def route_observatory_question(
    domain_id: str,
    *,
    question_text: str = "",
    timeframe: str | None = None,
    school_or_unit: str | None = None,
    policy_or_service: str | None = None,
    desired_granularity: str | None = None,
    router_path: str | Path = DEFAULT_ROUTER,
    ontology_path: str | Path = DEFAULT_ONTOLOGY,
    maturity_path: str | Path = DEFAULT_MATURITY,
    source_roles_path: str | Path = DEFAULT_SOURCE_ROLES,
    budget_map_path: str | Path = DEFAULT_BUDGET_MAP,
) -> dict[str, Any]:
    router, ontology, maturity, source_roles, budget_map = load_contracts(
        router_path, ontology_path, maturity_path, source_roles_path, budget_map_path
    )
    validate_contracts(router_path, ontology_path, maturity_path, source_roles_path, budget_map_path)

    ontology_by_id = {row["id"]: row for row in ontology["domains"]}
    _stop(domain_id in ontology_by_id, "TASK175_UNKNOWN_DOMAIN")
    domain = ontology_by_id[domain_id]
    route = router["domain_routes"][domain_id]

    scenarios = _matching_scenarios(question_text, router)
    mode = route["mode"]
    supplemental: list[str] = []
    join_rules: list[str] = []
    for scenario in scenarios:
        supplemental.extend(scenario["add_sources"])
        if scenario["mode"] == "HYBRID":
            mode = "HYBRID"
        join_rules.append(scenario["required_join_rule"])

    source_order = _ordered_unique(
        list(route["primary"]) + supplemental + list(route["fallback"])
    )
    primary_set = set(route["primary"])
    supplemental_set = set(supplemental)
    fallback_set = set(route["fallback"])

    source_plans = []
    for source in source_order:
        if source in primary_set:
            route_role = "PRIMARY"
        elif source in supplemental_set:
            route_role = "SCENARIO_SUPPLEMENTAL"
        elif source in fallback_set:
            route_role = "FALLBACK"
        else:
            route_role = "SUPPLEMENTAL"
        readiness = _readiness(source, router, maturity)
        source_plans.append(
            {
                "source_family": source,
                "route_role": route_role,
                "source_mode": router["source_modes"].get(source, "UNKNOWN"),
                **readiness,
            }
        )

    numeric_candidates = [
        p for p in source_plans
        if p["source_mode"] in {"NUMERIC", "BOTH"} and p["readiness_score"] >= 2
    ]
    document_candidates = [
        p for p in source_plans
        if p["source_mode"] in {"DOCUMENT", "BOTH"} and p["readiness_score"] >= 2
    ]
    query_ready_numeric = [
        p["source_family"] for p in numeric_candidates if p["readiness_score"] >= 3
    ]
    query_ready_document = [
        p["source_family"] for p in document_candidates if p["readiness_score"] >= 3
    ]

    gaps = []
    for plan in source_plans:
        if plan["readiness_score"] == 0:
            gaps.append(
                {
                    "source_family": plan["source_family"],
                    "gap": "BLOCKED_PENDING_CONTRACT",
                    "effect": "DO_NOT_INVENT_ANSWER_FROM_THIS_SOURCE",
                }
            )
        elif plan["readiness_score"] == 1:
            gaps.append(
                {
                    "source_family": plan["source_family"],
                    "gap": "UNREGISTERED_OR_UNPROVEN_QUERY_CONTRACT",
                    "effect": "REVIEW_OR_SOURCE_CONTRACT_REQUIRED",
                }
            )
        elif plan["readiness_score"] == 2:
            gaps.append(
                {
                    "source_family": plan["source_family"],
                    "gap": "SUPERVISED_OR_ROUTING_ONLY_NOT_GENERIC_QUERY_READY",
                    "effect": "USE_ONLY_WITH_EXPLICIT_CUSTODY_ADAPTER_OR_REVIEW",
                }
            )

    route_context = {
        "timeframe": timeframe,
        "school_or_unit": school_or_unit,
        "policy_or_service": policy_or_service,
        "desired_granularity": desired_granularity,
    }
    route_context = {k: v for k, v in route_context.items() if v is not None}

    return {
        "schema": "UNIFIED_OBSERVATORY_QUERY_PLAN_V1",
        "domain_id": domain_id,
        "domain_questions": domain["questions"],
        "metric_classes": domain["metrics"],
        "required_evidence_role": domain["evidence_role"],
        "route_mode": mode,
        "legacy_text_route_hint": legacy_route_query(question_text) if question_text else None,
        "question_text_is_truth_source": False,
        "context": route_context,
        "matched_scenarios": [
            {"id": s["id"], "matched_markers": s["matched_markers"]}
            for s in scenarios
        ],
        "source_plan": source_plans,
        "deterministic_number_candidates": [p["source_family"] for p in numeric_candidates],
        "query_ready_numeric_sources": query_ready_numeric,
        "document_explanation_candidates": [p["source_family"] for p in document_candidates],
        "query_ready_document_sources": query_ready_document,
        "joins": {
            "strong_allowed": router["join_strengths"]["STRONG"],
            "contextual_only": router["join_strengths"]["CONTEXTUAL"],
            "weak_corroborators_only": router["join_strengths"]["WEAK"],
            "scenario_join_rules": _ordered_unique(join_rules),
            "weak_can_create_identity": False,
        },
        "coverage_status": _coverage_state(mode, source_plans),
        "evidence_gaps": gaps,
        "answer_contract": router["answer_contract"],
        "guards": {
            "llm_final_numeric_truth": False,
            "source_role_limits_proof": True,
            "jom_publication_proves_accounting_execution": False,
            "semantic_similarity_creates_identity": False,
            "statistical_association_proves_causality": False,
            "ranking_without_context_requires_caution": True,
        },
    }


def coverage_summary(
    *,
    router_path: str | Path = DEFAULT_ROUTER,
    ontology_path: str | Path = DEFAULT_ONTOLOGY,
    maturity_path: str | Path = DEFAULT_MATURITY,
    source_roles_path: str | Path = DEFAULT_SOURCE_ROLES,
    budget_map_path: str | Path = DEFAULT_BUDGET_MAP,
) -> dict[str, Any]:
    _, ontology, _, _, _ = load_contracts(
        router_path, ontology_path, maturity_path, source_roles_path, budget_map_path
    )
    rows = [
        route_observatory_question(
            domain["id"],
            router_path=router_path,
            ontology_path=ontology_path,
            maturity_path=maturity_path,
            source_roles_path=source_roles_path,
            budget_map_path=budget_map_path,
        )
        for domain in ontology["domains"]
    ]
    counts = {"READY_CORE": 0, "PARTIAL": 0, "BLOCKED_OR_UNREGISTERED": 0}
    for row in rows:
        counts[row["coverage_status"]] += 1
    return {
        "schema": "UNIFIED_OBSERVATORY_COVERAGE_SUMMARY_V1",
        "domain_count": len(rows),
        "counts": counts,
        "domains": [
            {
                "domain_id": row["domain_id"],
                "route_mode": row["route_mode"],
                "coverage_status": row["coverage_status"],
                "query_ready_numeric_sources": row["query_ready_numeric_sources"],
                "query_ready_document_sources": row["query_ready_document_sources"],
                "gap_count": len(row["evidence_gaps"]),
            }
            for row in rows
        ],
        "all_domains_have_explicit_plan": len(rows) == 15,
        "network": False,
        "drive_write": False,
    }


if __name__ == "__main__":
    print(json.dumps(coverage_summary(), ensure_ascii=False, indent=2, sort_keys=True))
