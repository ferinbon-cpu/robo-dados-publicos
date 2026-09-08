from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.analytics.current_observatory_answerability import (
    current_answerability_config,
)
from robo_dados_publicos.analytics.current_observatory_bundle import (
    build_current_products,
)
from robo_dados_publicos.productization.contextual_slot_binder import bind_context
from robo_dados_publicos.productization.document_event_context_execution import (
    build_extended_context_capability_matrix,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task212_mixed_context_planner.v1.json"


class Task212PlannerStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task212PlannerStop(code)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK212_MIXED_CONTEXT_PLANNER_V1", "TASK212_SCHEMA")
    _stop(obj.get("issue") == 668, "TASK212_ISSUE")
    _stop(
        obj.get("base_main_sha") == "29c482bf18a082295a5110376f10e424b8dff2f0",
        "TASK212_BASE",
    )
    _stop(
        obj.get("mode") == "T0_OFFLINE_MIXED_RECIPE_CONTEXT_PLANNING_ONLY",
        "TASK212_MODE",
    )
    _stop(
        set(obj["signal_states"])
        == {
            "LOCAL_EXECUTABLE",
            "METADATA_ONLY",
            "MISSING",
            "CONTEXT_INCOMPATIBLE",
        },
        "TASK212_SIGNAL_STATES",
    )
    _stop(len(obj["remaining_question_ids"]) == 18, "TASK212_REMAINING_COUNT")
    _stop(
        len(obj["baseline_ready_for_safe_executor_design"]) == 8,
        "TASK212_BASELINE_READY_COUNT",
    )
    _stop(
        len(obj["baseline_blocked_metadata_only"]) == 10,
        "TASK212_BASELINE_BLOCKED_COUNT",
    )
    _stop(
        set(obj["remaining_question_ids"])
        == set(obj["baseline_ready_for_safe_executor_design"])
        | set(obj["baseline_blocked_metadata_only"]),
        "TASK212_BASELINE_PARTITION",
    )
    _stop(
        obj["payload_truth"]["capability_metadata_authorizes_row_filtering"] is False,
        "TASK212_METADATA_FILTER_GUARD",
    )
    _stop(
        obj["join_safety"]["weak_join_can_create_identity"] is False,
        "TASK212_WEAK_JOIN_GUARD",
    )
    consumed = obj["context"]["recipe_consumed_facets"]
    _stop(
        consumed == {
            "FIN_Q3": ["FINANCIAMENTO_FUNDEB"],
            "INFRA_Q2": ["INFRAESTRUTURA"],
            "TEACH_Q2": ["DOCENTES"],
        },
        "TASK212_RECIPE_CONSUMED_FACETS",
    )
    _stop(
        obj["context"]["parallel_context_period_signals"]
        == {"EQUITY_Q1": ["TERRITORY_PROFILE"]},
        "TASK212_PARALLEL_CONTEXT_PERIOD_SIGNALS",
    )
    _stop(
        obj["context"]["unconsumed_requested_facets_are_context_incompatible"] is True,
        "TASK212_UNCONSUMED_FACET_GUARD",
    )
    bounds = obj["claim_boundaries"]
    _stop(bounds["planner_computes_numeric_answer"] is False, "TASK212_NUMERIC_GUARD")
    _stop(bounds["planner_promotes_execution_class"] is False, "TASK212_PROMOTION_GUARD")
    _stop(bounds["metadata_only_equals_local_payload"] is False, "TASK212_METADATA_LOCAL")
    _stop(
        bounds["municipal_numerator_may_be_divided_by_school_denominator"] is False,
        "TASK212_CROSS_GRAIN_RATIO",
    )
    _stop(bounds["partial_period_equals_annual_period"] is False, "TASK212_PARTIAL_ANNUAL")
    _stop(
        bounds["parallel_context_period_may_be_relabelled_as_requested_year"] is False,
        "TASK212_PARALLEL_PERIOD_RELABEL",
    )
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK212_REMOTE")
    return obj


def _question_index() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    cfg = current_answerability_config()
    by_id = {str(row["id"]): row for row in cfg["questions"]}
    _stop(len(by_id) == 38, "TASK212_QUESTION_COUNT")
    return cfg, by_id


def _baseline_context() -> dict[str, Any]:
    return {
        "schema": "TASK212_BASELINE_CONTEXT_V1",
        "state": "CONTEXT_BOUND",
        "selected_question_ids": [],
        "school": {
            "status": "NOT_REQUESTED",
            "origin": None,
            "personal_reference": False,
            "candidates": [],
        },
        "period": {"status": "NOT_REQUESTED", "mode": None},
        "policy_service_facets": [],
        "granularity": {"value": "MUNICIPALITY", "explicit": False},
    }


def _payload_state(product: Mapping[str, Any]) -> str:
    local_rows = len(product.get("rows", []))
    declared_rows = int(product.get("row_count") or 0)
    if local_rows > 0:
        return "LOCAL_ROWS_PRESENT"
    if declared_rows > 0:
        return "METADATA_ONLY"
    return "MISSING"


def product_payload_inventory(
    *,
    generated_at: str,
    software_version: str,
) -> list[dict[str, Any]]:
    products = build_current_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    rows = []
    for name in sorted(products):
        product = products[name]
        rows.append(
            {
                "product": name,
                "payload_state": _payload_state(product),
                "declared_row_count": int(product.get("row_count") or 0),
                "local_row_count": len(product.get("rows", [])),
                "snapshot_id": product.get("snapshot_id"),
                "content_sha256": product.get("content_sha256"),
                "capabilities": sorted(str(x) for x in product.get("capabilities", [])),
            }
        )
    return rows


def _values(value: Any) -> set[str]:
    if value in (None, ""):
        return set()
    if isinstance(value, (list, tuple, set)):
        return {str(x) for x in value if x not in (None, "")}
    return {str(value)}


def _row_criteria_match(
    row: Mapping[str, Any],
    criteria: Mapping[str, Any],
) -> bool:
    for key, allowed_raw in criteria.items():
        if not key.endswith("_any"):
            raise Task212PlannerStop(f"TASK212_UNSUPPORTED_ROW_CRITERION:{key}")
        field = key[:-4]
        if not (_values(row.get(field)) & _values(allowed_raw)):
            return False
    return True


def _period_year(value: Any) -> int | None:
    text = str(value or "").strip()
    if len(text) >= 4 and text[:4].isdigit():
        return int(text[:4])
    return None


def _period_granularity(value: Any) -> str:
    text = str(value or "").strip()
    if len(text) == 4 and text.isdigit():
        return "ANNUAL"
    if len(text) == 7 and text[:4].isdigit() and text[4] in "-:" and text[5:].isdigit():
        return "PARTIAL_OR_MONTH"
    if len(text) == 9 and text[:4].isdigit() and text[4] == "-" and text[5:].isdigit():
        return "MULTIYEAR_RANGE"
    if len(text) >= 10 and text[:4].isdigit():
        return "DATE_OR_PARTIAL"
    return "UNKNOWN"


def _requested_year(context: Mapping[str, Any]) -> int | None:
    period = context.get("period") or {}
    if period.get("status") == "RESOLVED" and period.get("mode") == "YEAR":
        return int(period["year"])
    return None


def _has_non_year_period(context: Mapping[str, Any]) -> bool:
    period = context.get("period") or {}
    return (
        period.get("status") == "RESOLVED"
        and period.get("mode") not in {None, "YEAR"}
    )


def _requested_school(context: Mapping[str, Any]) -> str | None:
    school = context.get("school") or {}
    if school.get("status") == "RESOLVED":
        return str(school["school_code"])
    return None


def _requested_facets(context: Mapping[str, Any]) -> list[str]:
    return [str(x) for x in (context.get("policy_service_facets") or [])]


def _metric_field(product_name: str) -> str:
    if product_name == "SCHOOL_INDICATOR_SERIES":
        return "indicator_id"
    if product_name == "FISCAL_SERIES":
        return "metric_id"
    raise Task212PlannerStop(f"TASK212_UNSUPPORTED_METRIC_PRODUCT:{product_name}")


def _metric_period_field(product_name: str) -> str:
    if product_name in {"SCHOOL_INDICATOR_SERIES", "FISCAL_SERIES"}:
        return "period"
    raise Task212PlannerStop(f"TASK212_UNSUPPORTED_METRIC_PERIOD:{product_name}")


def _context_incompatible_reason(
    *,
    question_id: str,
    product_name: str,
    signal: Mapping[str, Any],
    context: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> str | None:
    school_code = _requested_school(context)
    if school_code is not None:
        if product_name == "SCHOOL_INDICATOR_SERIES":
            required_scopes = set(str(x) for x in signal.get("scope_levels_required", []))
            if required_scopes and required_scopes != {"SCHOOL"}:
                return "REQUESTED_SCHOOL_CONFLICTS_WITH_RECIPE_REQUIRED_SCOPE"
        elif product_name == "TERRITORY_PROFILE":
            pass
        elif product_name in {"ACCOUNTING_LEDGER", "REVENUE_LEDGER"}:
            pass
        else:
            return f"{product_name}_HAS_NO_STRUCTURED_SCHOOL_GRAIN"

    if _has_non_year_period(context):
        return "TASK212_PLANNER_SUPPORTS_EXACT_YEAR_ONLY"

    requested_facets = set(_requested_facets(context))
    consumed_facets = set(
        str(x)
        for x in contract["context"]["recipe_consumed_facets"].get(question_id, [])
    )
    unconsumed_facets = sorted(requested_facets - consumed_facets)
    if unconsumed_facets:
        return (
            "TASK212_UNCONSUMED_CONTEXT_FACETS:"
            + ",".join(unconsumed_facets)
        )

    return None


def _filter_metric_rows(
    product_name: str,
    rows: list[dict[str, Any]],
    signal: Mapping[str, Any],
    context: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    metric_field = _metric_field(product_name)
    ids = [str(x) for x in signal.get("ids", [])]
    selected = [row for row in rows if str(row.get(metric_field) or "") in ids]

    school_code = _requested_school(context)
    if school_code is not None and product_name == "SCHOOL_INDICATOR_SERIES":
        selected = [
            row for row in selected
            if str(row.get("school_code") or "") == school_code
            or (
                str(row.get("scope_level") or "") == "SCHOOL"
                and str(row.get("scope_id") or "") == school_code
            )
        ]

    required_scopes = [str(x) for x in signal.get("scope_levels_required", [])]
    if required_scopes:
        selected = [
            row for row in selected
            if str(row.get("scope_level") or "") in set(required_scopes)
        ]

    year = _requested_year(context)
    if year is not None:
        period_field = _metric_period_field(product_name)
        selected = [
            row for row in selected
            if _period_year(row.get(period_field)) == year
        ]

    observed_ids = sorted({str(row.get(metric_field) or "") for row in selected})
    match = str(signal.get("match") or "ANY")
    if match == "ALL":
        satisfied = set(ids) <= set(observed_ids)
        missing_ids = sorted(set(ids) - set(observed_ids))
    elif match == "ANY":
        satisfied = bool(set(ids) & set(observed_ids))
        missing_ids = [] if satisfied else sorted(ids)
    else:
        raise Task212PlannerStop(f"TASK212_UNSUPPORTED_METRIC_MATCH:{match}")

    if required_scopes:
        observed_scopes = {str(row.get("scope_level") or "") for row in selected}
        missing_scopes = sorted(set(required_scopes) - observed_scopes)
        satisfied = satisfied and not missing_scopes
    else:
        missing_scopes = []

    period_field = _metric_period_field(product_name)
    observed_periods = sorted({str(row.get(period_field) or "") for row in selected})
    period_granularities = sorted({_period_granularity(x) for x in observed_periods})

    return selected, {
        "required_metric_ids": ids,
        "observed_metric_ids": observed_ids,
        "missing_metric_ids": missing_ids,
        "required_scope_levels": required_scopes,
        "missing_scope_levels": missing_scopes,
        "observed_periods": observed_periods,
        "observed_period_granularities": period_granularities,
        "recipe_signal_satisfied_in_context": satisfied,
    }


def _product_period_value(product_name: str, row: Mapping[str, Any]) -> Any:
    if product_name == "JOM_EVENT_INDEX":
        return row.get("publication_date")
    if product_name == "PLANNING_DOCUMENT_INDEX":
        return row.get("period")
    if product_name == "TERRITORY_PROFILE":
        return row.get("period")
    return None


def _filter_product_rows(
    question_id: str,
    product_name: str,
    product: Mapping[str, Any],
    signal: Mapping[str, Any],
    context: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [dict(row) for row in product.get("rows", [])]
    criteria = dict(signal.get("row_criteria") or {})
    if criteria:
        rows = [row for row in rows if _row_criteria_match(row, criteria)]

    family_roles = dict(signal.get("required_source_family_role_pairs") or {})
    if family_roles:
        rows = [
            row for row in rows
            if str(row.get("source_family") or "") in family_roles
            and str(row.get("evidence_role") or "")
            in set(family_roles[str(row.get("source_family") or "")])
        ]

    document_roles = dict(signal.get("required_document_role_pairs") or {})
    if document_roles:
        rows = [
            row for row in rows
            if str(row.get("document_type") or "") in document_roles
            and str(row.get("evidence_role") or "")
            in set(document_roles[str(row.get("document_type") or "")])
        ]

    school_code = _requested_school(context)
    if school_code is not None and product_name == "TERRITORY_PROFILE":
        rows = [
            row for row in rows
            if str(row.get("school_code") or "") == school_code
        ]

    year = _requested_year(context)
    parallel_period_products = set(
        str(x)
        for x in contract["context"]["parallel_context_period_signals"].get(
            question_id, []
        )
    )
    if (
        year is not None
        and product_name not in parallel_period_products
        and product_name in {
            "JOM_EVENT_INDEX",
            "PLANNING_DOCUMENT_INDEX",
            "TERRITORY_PROFILE",
        }
    ):
        rows = [
            row for row in rows
            if _period_year(_product_period_value(product_name, row)) == year
            or (
                product_name == "PLANNING_DOCUMENT_INDEX"
                and _planning_range_contains(row.get("period"), year)
            )
        ]

    required_caps = sorted(str(x) for x in signal.get("required_capabilities", []))
    observed_caps = sorted(str(x) for x in product.get("capabilities", []))
    missing_caps = sorted(set(required_caps) - set(observed_caps))

    required_document_types = sorted(document_roles)
    observed_document_types = sorted(
        {str(row.get("document_type") or "") for row in rows if row.get("document_type")}
    )
    missing_document_types = sorted(
        set(required_document_types) - set(observed_document_types)
    )

    satisfied = bool(rows) and not missing_caps and not missing_document_types
    return rows, {
        "required_capabilities": required_caps,
        "observed_capabilities": observed_caps,
        "missing_capabilities": missing_caps,
        "required_document_types": required_document_types,
        "observed_document_types": observed_document_types,
        "missing_document_types": missing_document_types,
        "observed_periods": sorted(
            {
                str(_product_period_value(product_name, row) or "")
                for row in rows
                if _product_period_value(product_name, row) not in (None, "")
            }
        ),
        "period_role": (
            "PARALLEL_CONTEXT_PERIOD"
            if product_name in parallel_period_products
            else "REQUEST_CONTEXT_PERIOD"
        ),
        "requested_year_relabelled": False,
        "recipe_signal_satisfied_in_context": satisfied,
    }


def _planning_range_contains(value: Any, year: int) -> bool:
    text = str(value or "").strip()
    if len(text) == 9 and text[:4].isdigit() and text[4] == "-" and text[5:].isdigit():
        return int(text[:4]) <= year <= int(text[5:])
    return False


def _signal_plan(
    *,
    question_id: str,
    signal_index: int,
    signal: Mapping[str, Any],
    product: Mapping[str, Any],
    context: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    product_name = str(signal["product"])
    payload = _payload_state(product)
    base = {
        "signal_index": signal_index,
        "kind": str(signal["kind"]),
        "product": product_name,
        "payload_state": payload,
        "declared_row_count": int(product.get("row_count") or 0),
        "local_row_count": len(product.get("rows", [])),
        "snapshot_id": product.get("snapshot_id"),
        "content_sha256": product.get("content_sha256"),
    }

    if payload == "METADATA_ONLY":
        return (
            {
                **base,
                "signal_state": "METADATA_ONLY",
                "reason": "DECLARED_ROWS_PRESENT_BUT_LOCAL_ROWS_ABSENT",
                "context_inventory": {
                    "required_capabilities": sorted(
                        str(x) for x in signal.get("required_capabilities", [])
                    ),
                    "metadata_capabilities": sorted(
                        str(x) for x in product.get("capabilities", [])
                    ),
                    "row_filtering_authorized": False,
                },
            },
            [],
        )
    if payload == "MISSING":
        return (
            {
                **base,
                "signal_state": "MISSING",
                "reason": "NO_DECLARED_OR_LOCAL_PRODUCT_ROWS",
                "context_inventory": {},
            },
            [],
        )

    incompatible = _context_incompatible_reason(
        question_id=question_id,
        product_name=product_name,
        signal=signal,
        context=context,
        contract=contract,
    )
    if incompatible is not None:
        return (
            {
                **base,
                "signal_state": "CONTEXT_INCOMPATIBLE",
                "reason": incompatible,
                "context_inventory": {},
            },
            [],
        )

    if signal["kind"] == "METRIC":
        selected, inventory = _filter_metric_rows(
            product_name,
            [dict(row) for row in product.get("rows", [])],
            signal,
            context,
        )
    elif signal["kind"] == "PRODUCT":
        selected, inventory = _filter_product_rows(
            question_id,
            product_name,
            product,
            signal,
            context,
            contract,
        )
    else:
        raise Task212PlannerStop(f"TASK212_UNKNOWN_SIGNAL_KIND:{signal['kind']}")

    if not inventory["recipe_signal_satisfied_in_context"]:
        return (
            {
                **base,
                "signal_state": "MISSING",
                "reason": "RECIPE_RELEVANT_LOCAL_EVIDENCE_MISSING_IN_REQUESTED_CONTEXT",
                "context_matching_row_count": len(selected),
                "context_inventory": inventory,
            },
            selected,
        )

    return (
        {
            **base,
            "signal_state": "LOCAL_EXECUTABLE",
            "reason": "RECIPE_RELEVANT_LOCAL_ROWS_PRESENT_IN_CONTEXT",
            "context_matching_row_count": len(selected),
            "context_inventory": inventory,
        },
        selected,
    )


def _annual_periods(rows: list[dict[str, Any]], field: str = "period") -> set[str]:
    return {
        str(row.get(field))
        for row in rows
        if _period_granularity(row.get(field)) == "ANNUAL"
    }


def _network_school_metric_rows(
    rows: list[dict[str, Any]],
    metric_id: str,
) -> list[dict[str, Any]]:
    return [
        row for row in rows
        if str(row.get("indicator_id") or "") == metric_id
        and str(row.get("scope_level") or "") == "NETWORK"
    ]


def _join_plan(
    question_id: str,
    signal_rows: list[list[dict[str, Any]]],
    signal_plans: list[dict[str, Any]],
    context: Mapping[str, Any],
) -> dict[str, Any]:
    base = {
        "identity_created": False,
        "weak_join_used": False,
        "exact_year_is_identity": False,
        "requested_school_code": _requested_school(context),
        "requested_year": _requested_year(context),
    }

    if question_id == "FIN_Q2":
        fiscal_rows = signal_rows[0]
        school_rows = _network_school_metric_rows(signal_rows[1], "BASIC_EDUCATION_ENROLLMENT")
        fiscal_annual = _annual_periods(fiscal_rows)
        school_annual = _annual_periods(school_rows)
        common = sorted(fiscal_annual & school_annual)
        requested_year = _requested_year(context)
        if _requested_school(context) is not None:
            status = "BLOCKED_CROSS_GRAIN"
        elif requested_year is not None and str(requested_year) not in common:
            status = "BLOCKED_NO_EXACT_ANNUAL_ALIGNMENT"
        elif not common:
            status = "BLOCKED_NO_EXACT_ANNUAL_ALIGNMENT"
        else:
            status = "SAFE_FOR_EXECUTOR_DESIGN"
        return {
            **base,
            "mode": "SAFE_RATIO_ALIGNMENT",
            "status": status,
            "common_exact_annual_periods": common,
            "numerator_scope": "MUNICIPAL_ENTITY",
            "denominator_scope": "NETWORK",
            "period_prefix_match_is_sufficient": False,
            "partial_period_may_equal_annual_period": False,
            "numeric_ratio_computed": False,
        }

    if question_id == "TEACH_Q2":
        return {
            **base,
            "mode": "PARALLEL_EVIDENCE_ONLY",
            "status": "SAFE_FOR_EXECUTOR_DESIGN",
            "row_level_join_allowed": False,
            "jom_personnel_event_equals_workforce_stock": False,
        }

    if question_id == "EQUITY_Q1":
        school_code = _requested_school(context)
        territory_rows = signal_rows[1]
        if school_code is not None:
            strong = any(str(row.get("school_code") or "") == school_code for row in territory_rows)
            status = "SAFE_FOR_EXECUTOR_DESIGN" if strong else "BLOCKED_NO_EXACT_SCHOOL_CODE_LINK"
        else:
            status = "SAFE_FOR_EXECUTOR_DESIGN"
        return {
            **base,
            "mode": "EXACT_SCHOOL_CODE_OR_PARALLEL_CONTEXT",
            "status": status,
            "exact_school_code_required_for_school_level_alignment": True,
            "sector_income_equals_student_household_income": False,
        }

    if question_id == "FIN_Q4":
        nominal = _annual_periods(signal_rows[0])
        real = _annual_periods(signal_rows[1])
        common = sorted(nominal & real)
        requested_year = _requested_year(context)
        if requested_year is not None and str(requested_year) not in common:
            status = "BLOCKED_NO_EXACT_ANNUAL_ALIGNMENT"
        elif not common:
            status = "BLOCKED_NO_EXACT_ANNUAL_ALIGNMENT"
        else:
            status = "SAFE_FOR_EXECUTOR_DESIGN"
        return {
            **base,
            "mode": "SAME_PRODUCT_SERIES_ALIGNMENT",
            "status": status,
            "common_exact_annual_periods": common,
            "exact_entity_and_period_required": True,
            "nominal_equals_real": False,
        }

    if len(signal_plans) <= 1:
        return {
            **base,
            "mode": "NO_JOIN_REQUIRED",
            "status": "SAFE_FOR_EXECUTOR_DESIGN",
        }

    return {
        **base,
        "mode": "NO_IDENTITY_JOIN_DEFINED",
        "status": "SAFE_FOR_EXECUTOR_DESIGN",
        "row_level_join_allowed": False,
    }


def _planning_state(
    signal_plans: list[dict[str, Any]],
    join_plan: Mapping[str, Any],
) -> tuple[str, list[str]]:
    states = [str(row["signal_state"]) for row in signal_plans]
    blockers = []
    for row in signal_plans:
        if row["signal_state"] != "LOCAL_EXECUTABLE":
            blockers.append(
                f"SIGNAL_{row['signal_index']}:{row['product']}:{row['signal_state']}:{row['reason']}"
            )

    if "CONTEXT_INCOMPATIBLE" in states:
        return "CONTEXT_INCOMPATIBLE", blockers
    if "METADATA_ONLY" in states:
        return "BLOCKED_METADATA_ONLY", blockers
    if "MISSING" in states:
        return "MISSING_LOCAL_EVIDENCE", blockers
    if str(join_plan.get("status") or "").startswith("BLOCKED_"):
        blockers.append(f"JOIN:{join_plan['status']}")
        return "CONTEXT_INCOMPATIBLE", blockers
    return "READY_FOR_SAFE_EXECUTOR_DESIGN", blockers


def plan_question(
    question_id: str,
    *,
    generated_at: str,
    software_version: str,
    context: Mapping[str, Any] | None = None,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    _stop(bool(generated_at), "TASK212_GENERATED_AT")
    _stop(bool(software_version), "TASK212_SOFTWARE_VERSION")
    context = deepcopy(context) if context is not None else _baseline_context()

    matrix = build_extended_context_capability_matrix()
    matrix_by_id = {row["question_id"]: row for row in matrix["questions"]}
    _stop(question_id in matrix_by_id, "TASK212_UNKNOWN_QUESTION")
    upstream_class = str(matrix_by_id[question_id]["execution_class"])
    if upstream_class != "NOT_YET_CONTEXT_EXECUTABLE":
        material = {
            "question_id": question_id,
            "planning_state": "UPSTREAM_CONTEXT_EXECUTOR_AVAILABLE",
            "upstream_execution_class": upstream_class,
            "context": context,
            "signals": [],
            "join_plan": {
                "mode": "UPSTREAM_OWNS_EXECUTION",
                "status": "DELEGATE_UPSTREAM",
                "identity_created": False,
                "weak_join_used": False,
            },
            "blockers": [],
            "numeric_answer_created": False,
            "execution_class_promoted": False,
        }
        return {
            "schema": "TASK212_MIXED_CONTEXT_PLAN_V1",
            **material,
            "plan_sha256": _sha(material),
            "remote_effects": deepcopy(contract["remote_effects"]),
        }

    _stop(
        question_id in set(contract["remaining_question_ids"]),
        "TASK212_REMAINING_SET_DRIFT",
    )
    cfg, by_id = _question_index()
    question = by_id[question_id]
    recipe = cfg["recipes"][question["recipe"]]
    products = build_current_products(
        generated_at=generated_at,
        software_version=software_version,
    )

    signal_plans = []
    signal_rows = []
    for index, signal in enumerate(recipe["signals"], start=1):
        product = products[str(signal["product"])]
        plan, selected = _signal_plan(
            question_id=question_id,
            signal_index=index,
            signal=signal,
            product=product,
            context=context,
            contract=contract,
        )
        signal_plans.append(plan)
        signal_rows.append(selected)

    join = _join_plan(question_id, signal_rows, signal_plans, context)
    state, blockers = _planning_state(signal_plans, join)

    material = {
        "question_id": question_id,
        "question": question["text"],
        "recipe": question["recipe"],
        "planning_state": state,
        "upstream_execution_class": "NOT_YET_CONTEXT_EXECUTABLE",
        "context": context,
        "signals": signal_plans,
        "join_plan": join,
        "blockers": blockers,
        "numeric_answer_created": False,
        "execution_class_promoted": False,
    }
    return {
        "schema": "TASK212_MIXED_CONTEXT_PLAN_V1",
        **material,
        "plan_sha256": _sha(material),
        "remote_effects": deepcopy(contract["remote_effects"]),
    }


def build_remaining_question_planning_matrix(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    rows = [
        plan_question(
            qid,
            generated_at=generated_at,
            software_version=software_version,
            context=_baseline_context(),
            contract_path=contract_path,
        )
        for qid in contract["remaining_question_ids"]
    ]
    counts = Counter(str(row["planning_state"]) for row in rows)
    ready = {
        row["question_id"]
        for row in rows
        if row["planning_state"] == "READY_FOR_SAFE_EXECUTOR_DESIGN"
    }
    blocked = {
        row["question_id"]
        for row in rows
        if row["planning_state"] == "BLOCKED_METADATA_ONLY"
    }
    _stop(
        ready == set(contract["baseline_ready_for_safe_executor_design"]),
        "TASK212_READY_PARTITION_DRIFT",
    )
    _stop(
        blocked == set(contract["baseline_blocked_metadata_only"]),
        "TASK212_BLOCKED_PARTITION_DRIFT",
    )
    _stop(len(rows) == 18, "TASK212_MATRIX_COUNT")
    material = {
        "question_ids": [row["question_id"] for row in rows],
        "planning_state_counts": dict(sorted(counts.items())),
        "rows": rows,
    }
    return {
        "schema": "TASK212_REMAINING_CONTEXT_PLANNING_MATRIX_V1",
        "question_count": 18,
        "planning_state_counts": dict(sorted(counts.items())),
        "questions": rows,
        "matrix_sha256": _sha(material),
        "execution_class_promoted": False,
        "numeric_answer_created": False,
        "remote_effects": deepcopy(contract["remote_effects"]),
    }


def plan_contextual_query(
    text: str,
    *,
    generated_at: str,
    software_version: str,
    reference_date: str | None = None,
    context_school_code: str | None = None,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    context = bind_context(
        text,
        reference_date=reference_date,
        context_school_code=context_school_code,
    )
    qids = list(context.get("selected_question_ids") or [])
    if context.get("state") != "CONTEXT_BOUND" or len(qids) != 1:
        material = {
            "input_text": text,
            "planning_state": "ROUTE_STOP_PROPAGATED",
            "context": context,
            "question_id": qids[0] if len(qids) == 1 else None,
            "signals": [],
            "join_plan": {
                "mode": "NOT_PLANNED",
                "status": "ROUTE_STOP_PROPAGATED",
                "identity_created": False,
                "weak_join_used": False,
            },
            "blockers": [f"CONTEXT_STATE:{context.get('state')}"],
            "numeric_answer_created": False,
            "execution_class_promoted": False,
        }
        return {
            "schema": "TASK212_MIXED_CONTEXT_PLAN_V1",
            **material,
            "plan_sha256": _sha(material),
            "remote_effects": deepcopy(contract["remote_effects"]),
        }

    result = plan_question(
        qids[0],
        generated_at=generated_at,
        software_version=software_version,
        context=context,
        contract_path=contract_path,
    )
    result["input_text"] = text
    return result


def validate_contract(
    *,
    generated_at: str,
    software_version: str,
    path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(path)
    inventory = product_payload_inventory(
        generated_at=generated_at,
        software_version=software_version,
    )
    by_name = {row["product"]: row for row in inventory}
    _stop(
        by_name["ACCOUNTING_LEDGER"]["payload_state"] == "METADATA_ONLY",
        "TASK212_ACCOUNTING_PAYLOAD_STATE",
    )
    _stop(
        by_name["REVENUE_LEDGER"]["payload_state"] == "METADATA_ONLY",
        "TASK212_REVENUE_PAYLOAD_STATE",
    )
    matrix = build_remaining_question_planning_matrix(
        generated_at=generated_at,
        software_version=software_version,
        contract_path=path,
    )
    _stop(
        matrix["planning_state_counts"]
        == {
            "BLOCKED_METADATA_ONLY": 10,
            "READY_FOR_SAFE_EXECUTOR_DESIGN": 8,
        },
        "TASK212_EXPECTED_BASELINE_COUNTS",
    )
    return {
        "schema": "TASK212_MIXED_CONTEXT_PLANNER_VALIDATION_V1",
        "status": "PASS",
        "remaining_question_count": 18,
        "baseline_ready_count": 8,
        "baseline_metadata_blocked_count": 10,
        "accounting_payload_state": by_name["ACCOUNTING_LEDGER"]["payload_state"],
        "revenue_payload_state": by_name["REVENUE_LEDGER"]["payload_state"],
        "matrix_sha256": matrix["matrix_sha256"],
        "network": False,
        "drive_read": False,
        "drive_write": False,
        "llm": False,
    }
