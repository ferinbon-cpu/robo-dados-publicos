from __future__ import annotations

from collections import Counter
from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.analytics.current_observatory_bundle import build_current_products
from robo_dados_publicos.analytics.current_territory import (
    coverage_context, coverage_fact, coverage_caution, income_missingness_facts,
)
from robo_dados_publicos.productization.context_aware_execution import (
    _base_filter_accounting,
    _finalize,
    _row_ref,
    _unsupported,
    render_contextual_answer_markdown,
)
from robo_dados_publicos.productization.contextual_slot_binder import bind_context
from robo_dados_publicos.productization.document_event_context_execution import (
    execute_contextual_query_v3,
)
from robo_dados_publicos.productization.mixed_context_planner import plan_question


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task213_safe_local_mixed_execution.v1.json"
TASK209_CONTRACT = ROOT / "config/task209_context_aware_execution.v1.json"


class Task213ExecutionStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task213ExecutionStop(code)


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
    _stop(obj.get("schema") == "TASK213_SAFE_LOCAL_MIXED_EXECUTION_V1", "TASK213_SCHEMA")
    _stop(obj.get("issue") == 670, "TASK213_ISSUE")
    _stop(
        obj.get("base_main_sha") == "4ffc4eb24aefe9ca1887a400313825e406922f00",
        "TASK213_BASE",
    )
    _stop(
        obj.get("mode") == "T0_OFFLINE_SAFE_LOCAL_MIXED_RECIPE_EXECUTION",
        "TASK213_MODE",
    )
    _stop(
        set(obj["promoted_questions"])
        == {
            "CTRL_Q1",
            "CTRL_Q3",
            "EQUITY_Q1",
            "FIN_Q2",
            "FIN_Q4",
            "TEACH_Q2",
            "TERR_Q1",
            "TERR_Q2",
        },
        "TASK213_PROMOTED_SET",
    )
    _stop(
        set(obj["metadata_blocked_questions"])
        == {
            "ACC_Q1",
            "ACC_Q2",
            "ACC_Q3",
            "CTRL_Q2",
            "FIN_Q3",
            "INFRA_Q2",
            "PLAN_Q3",
            "PROC_Q1",
            "PROC_Q2",
            "PROC_Q3",
        },
        "TASK213_BLOCKED_SET",
    )
    _stop(
        not (set(obj["promoted_questions"]) & set(obj["metadata_blocked_questions"])),
        "TASK213_SET_OVERLAP",
    )
    _stop(obj["planner_gate"]["required_state"] == "READY_FOR_SAFE_EXECUTOR_DESIGN", "TASK213_PLANNER_STATE")
    _stop(obj["planner_gate"]["bypass_allowed"] is False, "TASK213_PLANNER_BYPASS")
    _stop(obj["planner_gate"]["numeric_answer_without_planner_approval"] is False, "TASK213_PLANNER_NUMERIC")
    _stop(obj["fin_q2"]["exact_annual_period_required"] is True, "TASK213_FINQ2_ANNUAL")
    _stop(obj["fin_q2"]["school_context_supported"] is False, "TASK213_FINQ2_SCHOOL")
    _stop(obj["teach_q2"]["bond_counts_additive"] is False, "TASK213_BONDS")
    _stop(obj["teach_q2"]["jom_mode"] == "PARALLEL_EVIDENCE_ONLY", "TASK213_TEACH_JOM")
    _stop(
        obj["equity_q1"]["held"] == 5
        and obj["equity_q1"]["strong_links"] == 64
        and obj["equity_q1"]["active_school_denominator"] == 69,
        "TASK213_EQUITY_COVERAGE",
    )
    _stop(
        obj["equity_q1"]["no_period_resolution"]
        == "LATEST_EXACT_ROW_PER_REQUIRED_METRIC_WITH_NATIVE_PERIOD",
        "TASK213_EQUITY_PERIOD_RESOLUTION",
    )
    _stop(
        obj["equity_q1"]["explicit_year_requires_all_required_metrics_in_exact_year"] is True,
        "TASK213_EQUITY_EXACT_YEAR",
    )
    _stop(
        obj["equity_q1"]["nearest_period_substitution"] is False,
        "TASK213_EQUITY_NO_NEAREST",
    )
    _stop(
        set(obj["equity_q1"]["held_codes"])
        == {"35208437", "35286229", "35004773", "35099569", "35241885"},
        "TASK213_EQUITY_HELD",
    )
    _stop(
        set(obj["control"]["metadata_only_products"])
        == {"ACCOUNTING_LEDGER", "REVENUE_LEDGER"},
        "TASK213_CONTROL_METADATA",
    )
    bounds = obj["claim_boundaries"]
    for key in (
        "mixed_executor_replaces_upstream_20",
        "metadata_blocked_10_promoted",
        "weak_join_can_create_identity",
        "partial_period_equals_annual_period",
        "municipal_numerator_may_use_school_denominator",
        "bond_categories_additive",
        "jom_event_equals_workforce_stock",
        "sector_income_equals_student_household_income",
        "territory_period_may_be_relabelled_to_school_metric_period",
        "catalog_readiness_equals_local_payload",
        "caller_generated_at_equals_source_update_time",
        "equity_metric_periods_may_be_collapsed_to_single_year",
    ):
        _stop(bounds[key] is False, f"TASK213_BOUNDARY_{key}")
    _stop(bounds["task213_executes_only_planner_approved_context"] is True, "TASK213_PLANNER_BOUNDARY")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK213_REMOTE")
    return obj


def _task209_contract() -> dict[str, Any]:
    obj = json.loads(TASK209_CONTRACT.read_text(encoding="utf-8"))
    _stop(obj.get("output_schema") == "OBSERVATORY_CONTEXTUAL_ANSWER_V1", "TASK213_OUTPUT_SCHEMA")
    return obj


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    return {
        "schema": "TASK213_SAFE_LOCAL_MIXED_EXECUTION_VALIDATION_V1",
        "status": "PASS",
        "promoted_question_count": len(obj["promoted_questions"]),
        "metadata_blocked_question_count": len(obj["metadata_blocked_questions"]),
        "planner_gate": obj["planner_gate"]["required_state"],
        "network": False,
        "drive_read": False,
        "drive_write": False,
        "llm": False,
    }


def _period_year(context: Mapping[str, Any]) -> str | None:
    period = context["period"]
    if period.get("status") != "RESOLVED":
        return None
    if period.get("mode") != "YEAR":
        return ""
    return str(period["year"])


def _mark_applied(filters: dict[str, Any], *names: str) -> None:
    for name in names:
        if filters[name]["status"] == "PENDING":
            filters[name]["status"] = "APPLIED"


def _product_provenance(product_name: str, product: Mapping[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        "product": product_name,
        "snapshot_id": product.get("snapshot_id"),
        "content_sha256": product.get("content_sha256"),
        "declared_row_count": product.get("row_count"),
        "local_row_count": len(product.get("rows", [])),
        **extra,
    }


def _planner_blocked(
    *,
    text: str,
    context: Mapping[str, Any],
    question_id: str,
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    contract = _task209_contract()
    filters = _base_filter_accounting(context)
    state = str(plan["planning_state"])
    answer_state = (
        "UNSUPPORTED_CONTEXT_COMBINATION"
        if state == "CONTEXT_INCOMPATIBLE"
        else "EXPLICIT_CONTEXT_GAP"
    )
    for row in filters.values():
        if row["status"] == "PENDING":
            row["status"] = "BLOCKED_BY_TASK212_PLANNER"
    signal_summary = [
        {
            "signal_index": row.get("signal_index"),
            "product": row.get("product"),
            "signal_state": row.get("signal_state"),
            "reason": row.get("reason"),
        }
        for row in plan.get("signals", [])
    ]
    return _finalize(
        state=answer_state,
        text=text,
        context=context,
        question_id=question_id,
        filter_accounting=filters,
        facts=[
            {
                "kind": "TASK212_EXECUTION_BLOCKER",
                "planner_state": state,
                "signals": signal_summary,
                "text": (
                    "A TASK212 não autorizou execução local para o contexto exato solicitado; "
                    "nenhum filtro, período ou granularidade foi descartado."
                ),
            }
        ],
        time_reference=[],
        provenance=[
            {
                "product": "TASK212_MIXED_CONTEXT_PLANNER",
                "plan_sha256": plan.get("plan_sha256"),
                "planning_state": state,
                "blockers": list(plan.get("blockers") or []),
                "numeric_answer_created_by_planner": False,
            }
        ],
        cautions=[
            "TASK212_PLANNER_GATE_ENFORCED",
            "REQUESTED_CONTEXT_WAS_NOT_DROPPED",
            "NO_NEAREST_PERIOD_SUBSTITUTION",
        ],
        gap_scope="TASK212_EXACT_CONTEXT_EXECUTION_GATE",
        contract=contract,
    )


def _annual_rows(
    product: Mapping[str, Any],
    *,
    id_field: str,
    metric_id: str,
) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in product.get("rows", [])
        if str(row.get(id_field) or "") == metric_id
        and len(str(row.get("period") or "")) == 4
        and str(row.get("period") or "").isdigit()
    ]
    rows.sort(key=lambda row: (str(row.get("period")), _canonical_json(row)))
    return rows


def _unique_by_period(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["period"]), []).append(row)
    return {
        period: items[0]
        for period, items in grouped.items()
        if len(items) == 1
    }


def _execute_fin_q2(
    *,
    text: str,
    context: Mapping[str, Any],
    products: Mapping[str, Mapping[str, Any]],
    plan: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    out = _task209_contract()
    filters = _base_filter_accounting(context)
    if context["school"].get("status") == "RESOLVED":
        return _unsupported(
            text,
            context,
            "FIN_Q2",
            filters,
            "FIN_Q2 usa numerador municipal e denominador da rede; matrícula de uma escola não pode ser usada nesse quociente.",
            out,
        )
    year = _period_year(context)
    if year == "":
        return _unsupported(
            text,
            context,
            "FIN_Q2",
            filters,
            "FIN_Q2 aceita somente período anual exato; período parcial/mensal não é anualizado.",
            out,
        )
    fiscal = products["FISCAL_SERIES"]
    school = products["SCHOOL_INDICATOR_SERIES"]
    numerators = _unique_by_period(
        _annual_rows(fiscal, id_field="metric_id", metric_id="EDUCATION_EXPENDITURE")
    )
    denominator_rows = [
        row
        for row in _annual_rows(
            school,
            id_field="indicator_id",
            metric_id="BASIC_EDUCATION_ENROLLMENT",
        )
        if str(row.get("scope_level") or "") == contract["fin_q2"]["denominator_scope_level"]
        and str(row.get("network") or "") == contract["fin_q2"]["denominator_network"]
    ]
    denominators = _unique_by_period(denominator_rows)
    common = sorted(set(numerators) & set(denominators))
    selected = year or (common[-1] if common else None)
    if selected is None or selected not in common:
        return _planner_blocked(
            text=text,
            context=context,
            question_id="FIN_Q2",
            plan=plan,
        )
    numerator = numerators[selected]
    denominator = denominators[selected]
    denominator_value = Decimal(str(denominator["value"]))
    _stop(denominator_value > 0, "TASK213_FINQ2_DENOMINATOR")
    numerator_value = Decimal(str(numerator["value"]))
    ratio = (numerator_value / denominator_value).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    if filters["PERIOD"]["status"] == "PENDING":
        filters["PERIOD"]["status"] = "APPLIED"
    filters["GRANULARITY"]["status"] = "APPLIED"
    facts = [
        {
            "kind": "SPENDING_PER_STUDENT_NUMERATOR",
            "metric_id": "EDUCATION_EXPENDITURE",
            "period": selected,
            "value_brl": str(numerator_value.quantize(Decimal("0.01"))),
            "stage_semantic": numerator.get("stage_semantic"),
            "scope": "MUNICIPAL_ENTITY",
            "text": (
                f"Numerador {selected}: despesa anual de Educação = R$ "
                f"{numerator_value.quantize(Decimal('0.01'))}."
            ),
        },
        {
            "kind": "SPENDING_PER_STUDENT_DENOMINATOR",
            "metric_id": "BASIC_EDUCATION_ENROLLMENT",
            "period": selected,
            "value": int(denominator_value),
            "scope": "MUNICIPAL_NETWORK",
            "text": f"Denominador {selected}: {int(denominator_value)} matrículas da rede municipal.",
        },
        {
            "kind": "SPENDING_PER_ENROLLMENT_DERIVED",
            "period": selected,
            "value_brl_per_enrollment": str(ratio),
            "unit": "BRL_PER_ENROLLMENT",
            "formula": "EDUCATION_EXPENDITURE / BASIC_EDUCATION_ENROLLMENT",
            "rounding": "DECIMAL_HALF_UP_2",
            "same_annual_period_verified": True,
            "individual_student_cost_claim": False,
            "text": f"Despesa anual empenhada por matrícula em {selected}: R$ {ratio}.",
        },
    ]
    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id="FIN_Q2",
        filter_accounting=filters,
        facts=facts,
        time_reference=[selected],
        comparisons=[],
        provenance=[
            _row_ref("FISCAL_SERIES", numerator),
            _row_ref("SCHOOL_INDICATOR_SERIES", denominator),
            {
                "product": "TASK212_MIXED_CONTEXT_PLANNER",
                "plan_sha256": plan.get("plan_sha256"),
                "join_mode": plan.get("join_plan", {}).get("mode"),
                "planner_state": plan.get("planning_state"),
            },
        ],
        cautions=[
            "PER_ENROLLMENT_NE_INDIVIDUAL_STUDENT_COST",
            "ANNUAL_COMMITTED_EXPENDITURE_NE_INTERIM_LIQUIDATED_EXPENDITURE",
            "MUNICIPAL_EXPENDITURE_NE_SCHOOL_LEVEL_EXPENDITURE",
            "NOMINAL_NE_REAL",
            "TASK212_JOIN_PLAN_ENFORCED",
        ],
        contract=out,
    )


def _pct_change(first: Decimal, last: Decimal) -> Decimal:
    _stop(first != 0, "TASK213_TREND_ZERO_BASE")
    return ((last / first - Decimal("1")) * Decimal("100")).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _execute_fin_q4(
    *,
    text: str,
    context: Mapping[str, Any],
    products: Mapping[str, Mapping[str, Any]],
    plan: Mapping[str, Any],
) -> dict[str, Any]:
    out = _task209_contract()
    filters = _base_filter_accounting(context)
    year = _period_year(context)
    if year == "":
        return _unsupported(
            text,
            context,
            "FIN_Q4",
            filters,
            "FIN_Q4 usa somente períodos anuais exatos; nenhum período parcial foi convertido em ano.",
            out,
        )
    fiscal = products["FISCAL_SERIES"]
    nominal = _unique_by_period(
        _annual_rows(fiscal, id_field="metric_id", metric_id="EDUCATION_EXPENDITURE")
    )
    real = _unique_by_period(
        _annual_rows(fiscal, id_field="metric_id", metric_id="REAL_EDUCATION_EXPENDITURE")
    )
    common = sorted(set(nominal) & set(real))
    if year is not None:
        if year not in common:
            return _planner_blocked(
                text=text,
                context=context,
                question_id="FIN_Q4",
                plan=plan,
            )
        periods = [year]
    else:
        periods = common
        if len(periods) < 2:
            return _planner_blocked(
                text=text,
                context=context,
                question_id="FIN_Q4",
                plan=plan,
            )
    facts: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    for period in periods:
        nrow = nominal[period]
        rrow = real[period]
        n = Decimal(str(nrow["value"])).quantize(Decimal("0.01"))
        r = Decimal(str(rrow["value"])).quantize(Decimal("0.01"))
        facts.append(
            {
                "kind": "NOMINAL_REAL_ANNUAL_PAIR",
                "period": period,
                "nominal_brl": str(n),
                "real_brl_dec_2025_equivalent": str(r),
                "real_unit": rrow.get("unit"),
                "same_entity_period_alignment": True,
                "text": f"{period}: nominal R$ {n}; real a preços de dez/2025 R$ {r}.",
            }
        )
        provenance.extend([
            _row_ref("FISCAL_SERIES", nrow),
            _row_ref("FISCAL_SERIES", rrow),
        ])
    comparisons: list[str] = []
    cautions = [
        "NOMINAL_NE_REAL",
        "IPCA_DEFLATED_SERIES_NE_MONTHLY_WEIGHTED_FLOW",
        "NO_2026_ANNUALIZATION",
        "TASK212_JOIN_PLAN_ENFORCED",
    ]
    if len(periods) >= 2:
        first = periods[0]
        last = periods[-1]
        nominal_change = _pct_change(
            Decimal(str(nominal[first]["value"])),
            Decimal(str(nominal[last]["value"])),
        )
        real_change = _pct_change(
            Decimal(str(real[first]["value"])),
            Decimal(str(real[last]["value"])),
        )
        comparisons.append(
            f"{first}→{last}: nominal {nominal_change}%; real {real_change}%."
        )
        facts.append(
            {
                "kind": "NOMINAL_REAL_FIRST_TO_LAST_TREND",
                "first_period": first,
                "last_period": last,
                "nominal_change_pct": str(nominal_change),
                "real_change_pct": str(real_change),
                "rounding": "DECIMAL_HALF_UP_2",
                "text": comparisons[-1],
            }
        )
    else:
        cautions.append("SINGLE_YEAR_SNAPSHOT_NE_MULTIYEAR_TREND")
    if filters["PERIOD"]["status"] == "PENDING":
        filters["PERIOD"]["status"] = "APPLIED"
    filters["GRANULARITY"]["status"] = "APPLIED"
    provenance.append(
        {
            "product": "TASK212_MIXED_CONTEXT_PLANNER",
            "plan_sha256": plan.get("plan_sha256"),
            "join_mode": plan.get("join_plan", {}).get("mode"),
        }
    )
    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id="FIN_Q4",
        filter_accounting=filters,
        facts=facts,
        time_reference=periods,
        comparisons=comparisons,
        provenance=provenance,
        cautions=cautions,
        contract=out,
    )


def _event_year(row: Mapping[str, Any]) -> str:
    return str(row.get("publication_date") or "")[:4]


def _execute_teach_q2(
    *,
    text: str,
    context: Mapping[str, Any],
    products: Mapping[str, Mapping[str, Any]],
    plan: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    out = _task209_contract()
    filters = _base_filter_accounting(context)
    if context["school"].get("status") == "RESOLVED":
        return _unsupported(
            text,
            context,
            "TEACH_Q2",
            filters,
            "TEACH_Q2 materializa estoque/vínculos apenas no escopo da rede municipal; não há total de quadro por escola nessa receita.",
            out,
        )
    year = _period_year(context)
    if year == "":
        return _unsupported(
            text,
            context,
            "TEACH_Q2",
            filters,
            "TEACH_Q2 não converte mês ou período parcial em estoque anual.",
            out,
        )
    selected_year = year or contract["teach_q2"]["stock_period"]
    if selected_year != contract["teach_q2"]["stock_period"]:
        return _planner_blocked(
            text=text,
            context=context,
            question_id="TEACH_Q2",
            plan=plan,
        )
    school = products["SCHOOL_INDICATOR_SERIES"]
    base_rows = [
        dict(row)
        for row in school.get("rows", [])
        if str(row.get("scope_level") or "") == "NETWORK"
        and str(row.get("network") or "") == "MUNICIPAL"
        and str(row.get("period") or "") == selected_year
    ]
    staff = [row for row in base_rows if row.get("indicator_id") == "STAFF_COUNT"]
    bonds = [row for row in base_rows if row.get("indicator_id") == "EMPLOYMENT_BOND"]
    _stop(len(staff) == 1, "TASK213_TEACH_STAFF_ROW")
    _stop(len(bonds) == 1, "TASK213_TEACH_BOND_ROW")
    bond_counts = dict(bonds[0].get("bond_counts") or {})
    _stop(len(bond_counts) == 4, "TASK213_TEACH_BOND_COUNTS")
    facts: list[dict[str, Any]] = [
        {
            "kind": "WORKFORCE_STOCK",
            "period": selected_year,
            "metric_id": "STAFF_COUNT",
            "value": staff[0]["value"],
            "unit": staff[0].get("unit"),
            "scope": "MUNICIPAL_NETWORK",
            "semantic": "DOCENTES_UNICOS_EM_EFETIVA_REGENCIA",
            "all_education_workers_claim": False,
            "text": (
                f"Censo Escolar {selected_year}: {staff[0]['value']} docentes únicos em efetiva regência "
                "na dependência municipal; isso não é o total de trabalhadores da Educação."
            ),
        },
        {
            "kind": "EMPLOYMENT_BOND_COUNTS",
            "period": selected_year,
            "metric_id": "EMPLOYMENT_BOND",
            "bond_counts": bond_counts,
            "category_count": bonds[0].get("value"),
            "categories_additive": False,
            "text": (
                "Vínculos docentes: concursado/efetivo/estável="
                f"{bond_counts.get('CONCURSADO_EFETIVO_ESTAVEL')}; temporário="
                f"{bond_counts.get('CONTRATO_TEMPORARIO')}; terceirizado="
                f"{bond_counts.get('CONTRATO_TERCEIRIZADO')}; CLT="
                f"{bond_counts.get('CONTRATO_CLT')}. As categorias não são aditivas."
            ),
        },
    ]
    jom = products["JOM_EVENT_INDEX"]
    events = [
        dict(row)
        for row in jom.get("rows", [])
        if _event_year(row) == selected_year
        and "PERSONNEL" in set(str(x) for x in row.get("evidence_layers") or [])
        and "EDUCATION" in set(str(x) for x in row.get("policy_domains") or [])
    ]
    events.sort(key=lambda row: (str(row.get("publication_date") or ""), str(row.get("event_id") or "")))
    sample = events[:6]
    facts.append(
        {
            "kind": "JOM_PERSONNEL_PARALLEL_EVIDENCE",
            "period": selected_year,
            "matched_event_count": len(events),
            "displayed_event_count": len(sample),
            "row_level_join_to_workforce_stock": False,
            "text": (
                f"Jornal Oficial {selected_year}: {len(events)} eventos estruturados de pessoal/educação "
                "no corpus materializado; eles são evidência paralela e não foram ligados a indivíduos do estoque."
            ),
        }
    )
    for row in sample:
        facts.append(
            {
                "kind": "JOM_PERSONNEL_EVENT_SAMPLE",
                "event_id": row.get("event_id"),
                "publication_date": row.get("publication_date"),
                "event_type": row.get("event_type"),
                "text": str(row.get("object_text") or ""),
            }
        )
    _mark_applied(filters, "PERIOD", "GRANULARITY")
    facets = set(str(x) for x in context.get("policy_service_facets") or [])
    if facets:
        if not facets <= {"DOCENTES"}:
            return _unsupported(
                text,
                context,
                "TEACH_Q2",
                filters,
                "TEACH_Q2 consome apenas a faceta DOCENTES nesta execução.",
                out,
            )
        filters["POLICY_SERVICE_FACETS"]["status"] = "APPLIED_BY_RECIPE_SCOPE"
    provenance = [
        _row_ref("SCHOOL_INDICATOR_SERIES", staff[0]),
        _row_ref("SCHOOL_INDICATOR_SERIES", bonds[0]),
        _product_provenance(
            "JOM_EVENT_INDEX",
            jom,
            matched_personnel_education_event_count=len(events),
            displayed_event_count=len(sample),
            row_level_join_to_workforce_stock=False,
        ),
        *[_row_ref("JOM_EVENT_INDEX", row) for row in sample],
        {
            "product": "TASK212_MIXED_CONTEXT_PLANNER",
            "plan_sha256": plan.get("plan_sha256"),
            "join_mode": "PARALLEL_EVIDENCE_ONLY",
        },
    ]
    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id="TEACH_Q2",
        filter_accounting=filters,
        facts=facts,
        time_reference=[selected_year],
        comparisons=[],
        provenance=provenance,
        cautions=[
            "DOCENTES_NE_ALL_EDUCATION_WORKERS",
            "BOND_COUNTS_NON_ADDITIVE",
            "SAME_DOCENTE_MAY_APPEAR_IN_MULTIPLE_BOND_CATEGORIES",
            "JOM_PERSONNEL_EVENT_NE_WORKFORCE_STOCK",
            "NO_PERSON_LEVEL_JOIN",
            "2025_INEP_NE_2026_SME_OPERATIONAL_SNAPSHOT",
            "CURRENT_MATERIALIZED_JOM_CORPUS_NE_COMPLETE_YEAR",
        ],
        contract=out,
    )


def _metric_rows_for_scope(
    product: Mapping[str, Any],
    *,
    metric_ids: set[str],
    school_code: str | None,
) -> list[dict[str, Any]]:
    rows = []
    for raw in product.get("rows", []):
        row = dict(raw)
        if str(row.get("indicator_id") or "") not in metric_ids:
            continue
        level = str(row.get("scope_level") or "")
        if school_code is not None:
            if level != "SCHOOL" or str(row.get("scope_id") or "") != school_code:
                continue
        else:
            if level != "NETWORK":
                continue
            if str(row.get("network") or "") not in {"", "MUNICIPAL"}:
                continue
        if len(str(row.get("period") or "")) != 4 or not str(row.get("period") or "").isdigit():
            continue
        rows.append(row)
    return rows


def _select_required_metric_rows(
    rows: list[dict[str, Any]],
    metric_ids: set[str],
    requested_year: str | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    by_metric: dict[str, list[dict[str, Any]]] = {
        metric_id: [] for metric_id in metric_ids
    }
    for row in rows:
        metric_id = str(row.get("indicator_id") or "")
        if metric_id in by_metric:
            by_metric[metric_id].append(row)

    selected: list[dict[str, Any]] = []
    for metric_id in sorted(metric_ids):
        candidates = by_metric[metric_id]
        if requested_year is not None:
            candidates = [
                row for row in candidates
                if str(row.get("period") or "") == requested_year
            ]
        if not candidates:
            return [], []
        candidates.sort(key=lambda row: (str(row.get("period") or ""), _canonical_json(row)))
        if requested_year is None:
            latest_period = str(candidates[-1].get("period") or "")
            candidates = [
                row for row in candidates
                if str(row.get("period") or "") == latest_period
            ]
        if len(candidates) != 1:
            return [], []
        selected.append(candidates[0])
    periods = sorted({str(row.get("period") or "") for row in selected})
    return selected, periods


def _territory_school_rows(
    product: Mapping[str, Any],
    school_code: str,
) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in product.get("rows", [])
        if str(row.get("geo_level") or "") == "SCHOOL_LOCATION_CENSUS_SECTOR"
        and str(row.get("school_code") or "") == school_code
        and str(row.get("period") or "") == "2022"
    ]
    rows.sort(key=lambda row: (str(row.get("metric_id") or ""), _canonical_json(row)))
    return rows


def _territory_municipal_rows(product: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in product.get("rows", [])
        if str(row.get("geo_level") or "") == "MUNICIPAL"
        and str(row.get("geo_id") or "") == "3526902"
        and str(row.get("period") or "") == "2022"
    ]
    rows.sort(key=lambda row: str(row.get("metric_id") or ""))
    return rows


def _territory_fact(row: Mapping[str, Any], *, period_role: str) -> dict[str, Any]:
    return {
        "kind": "TERRITORY_METRIC",
        "geo_level": row.get("geo_level"),
        "geo_id": row.get("geo_id"),
        "school_code": row.get("school_code"),
        "school_name": row.get("school_name"),
        "sector_id": row.get("sector_id"),
        "period": row.get("period"),
        "period_role": period_role,
        "metric_id": row.get("metric_id"),
        "metric_name": row.get("metric_name"),
        "value": row.get("value"),
        "unit": row.get("unit"),
        "text": (
            f"{row.get('metric_name')}: {row.get('value')} {row.get('unit')} "
            f"| período territorial={row.get('period')}."
        ),
    }


def _execute_equity_q1(
    *,
    text: str,
    context: Mapping[str, Any],
    products: Mapping[str, Mapping[str, Any]],
    plan: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    out = _task209_contract()
    filters = _base_filter_accounting(context)
    year = _period_year(context)
    if year == "":
        return _unsupported(
            text,
            context,
            "EQUITY_Q1",
            filters,
            "EQUITY_Q1 usa ano exato para indicadores escolares; o contexto territorial mantém seu próprio período 2022.",
            out,
        )
    school_info = context["school"]
    school_code = (
        str(school_info["school_code"])
        if school_info.get("status") == "RESOLVED"
        else None
    )
    metric_ids = set(contract["equity_q1"]["required_school_metrics"])
    school_product = products["SCHOOL_INDICATOR_SERIES"]
    metric_rows = _metric_rows_for_scope(
        school_product,
        metric_ids=metric_ids,
        school_code=school_code,
    )
    selected_metrics, metric_periods = _select_required_metric_rows(
        metric_rows,
        metric_ids,
        year,
    )
    if not selected_metrics:
        return _planner_blocked(
            text=text,
            context=context,
            question_id="EQUITY_Q1",
            plan=plan,
        )
    facts: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    for row in selected_metrics:
        facts.append(
            {
                "kind": "EQUITY_SCHOOL_OR_NETWORK_METRIC",
                "metric_id": row.get("indicator_id"),
                "metric_name": row.get("indicator_name"),
                "period": row.get("period"),
                "period_role": "SCHOOL_OR_NETWORK_INDICATOR_PERIOD",
                "scope_level": row.get("scope_level"),
                "scope_id": row.get("scope_id"),
                "value": row.get("value"),
                "unit": row.get("unit"),
                "text": (
                    f"{row.get('indicator_name')}: {row.get('value')} {row.get('unit')} "
                    f"| período={row.get('period')}."
                ),
            }
        )
        provenance.append(_row_ref("SCHOOL_INDICATOR_SERIES", row))

    territory = products["TERRITORY_PROFILE"]
    coverage = coverage_context(territory)
    held = set(contract["equity_q1"]["held_codes"])
    if school_code is not None:
        territory_rows = _territory_school_rows(territory, school_code)
        if territory_rows:
            for row in territory_rows:
                facts.append(_territory_fact(row, period_role="PARALLEL_TERRITORIAL_CONTEXT_PERIOD"))
                provenance.append(_row_ref("TERRITORY_PROFILE", row))
            territory_status = "EXACT_SCHOOL_CODE_LINK"
        elif school_code in held:
            facts.append(
                {
                    "kind": "EXPLICIT_TERRITORY_MISSINGNESS",
                    "school_code": school_code,
                    "school_name": school_info.get("school_name"),
                    "status": "HELD_NO_STRONG_SCHOOL_TO_SECTOR_LINK",
                    "weak_substitution_performed": False,
                    "network_coverage": f"{coverage['strong_links']}_OF_{coverage['denominator']}_STRONG_LINKS",
                    "text": (
                        f"A escola está entre as {coverage['held']} unidades mantidas como missingness territorial explícita: "
                        "nenhum setor foi atribuído por aproximação fraca."
                    ),
                }
            )
            territory_status = "EXPLICIT_HELD_MISSINGNESS"
        else:
            return _planner_blocked(
                text=text,
                context=context,
                question_id="EQUITY_Q1",
                plan=plan,
            )
    else:
        territory_rows = _territory_municipal_rows(territory)
        _stop(bool(territory_rows), "TASK213_EQUITY_MUNICIPAL_TERRITORY")
        for row in territory_rows:
            facts.append(_territory_fact(row, period_role="PARALLEL_TERRITORIAL_CONTEXT_PERIOD"))
            provenance.append(_row_ref("TERRITORY_PROFILE", row))
        facts.append(coverage_fact(territory))
        territory_status = "MUNICIPAL_CONTEXT_PLUS_EXPLICIT_COVERAGE"

    facts.extend(income_missingness_facts(territory, school_code))

    _mark_applied(filters, "SCHOOL", "PERIOD", "GRANULARITY")
    provenance.extend([
        _product_provenance(
            "TERRITORY_PROFILE",
            territory,
            equity_territory_status=territory_status,
            territory_period="2022",
        ),
        {
            "product": "TASK212_MIXED_CONTEXT_PLANNER",
            "plan_sha256": plan.get("plan_sha256"),
            "join_mode": "EXACT_SCHOOL_CODE_OR_PARALLEL_CONTEXT",
            "territory_period_relabelled": False,
        },
    ])
    cautions = [
        "SECTOR_INCOME_NE_STUDENT_HOUSEHOLD_INCOME",
        "SCHOOL_LOCATION_SECTOR_NE_STUDENT_CATCHMENT",
        "TERRITORY_2022_NE_SCHOOL_INDICATOR_PERIOD",
        "EQUITY_CONTEXT_NE_CAUSAL_EXPLANATION",
        coverage_caution(coverage),
    ]
    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id="EQUITY_Q1",
        filter_accounting=filters,
        facts=facts,
        time_reference=sorted(set([*metric_periods, "2022"])),
        comparisons=[],
        provenance=provenance,
        cautions=cautions,
        contract=out,
    )


def _execute_territory(
    *,
    text: str,
    context: Mapping[str, Any],
    products: Mapping[str, Mapping[str, Any]],
    plan: Mapping[str, Any],
    question_id: str,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    out = _task209_contract()
    filters = _base_filter_accounting(context)
    year = _period_year(context)
    if year == "":
        return _unsupported(
            text,
            context,
            question_id,
            filters,
            "O produto territorial possui período estruturado 2022; períodos mensais/parciais não são coeridos.",
            out,
        )
    if year is not None and year != contract["territory"]["period"]:
        return _planner_blocked(
            text=text,
            context=context,
            question_id=question_id,
            plan=plan,
        )
    territory = products["TERRITORY_PROFILE"]
    school = context["school"]
    school_code = (
        str(school["school_code"])
        if school.get("status") == "RESOLVED"
        else None
    )
    if school_code is not None:
        rows = _territory_school_rows(territory, school_code)
        if not rows:
            return _planner_blocked(
                text=text,
                context=context,
                question_id=question_id,
                plan=plan,
            )
        scope = "SCHOOL_LOCATION_CENSUS_SECTOR"
    else:
        rows = _territory_municipal_rows(territory)
        _stop(bool(rows), "TASK213_TERR_MUNICIPAL_ROWS")
        scope = "MUNICIPAL"
    facts = [_territory_fact(row, period_role="TERRITORY_OBSERVATION_PERIOD") for row in rows]
    provenance = [_row_ref("TERRITORY_PROFILE", row) for row in rows]
    comparisons: list[str] = []
    if question_id == "TERR_Q2":
        if school_code is not None:
            percentile = [
                row
                for row in rows
                if row.get("metric_id") == "SECTOR_RESPONSIBLE_INCOME_MEAN_PERCENTILE"
            ]
            if percentile:
                p = percentile[0]
                comparisons.append(
                    "Comparação suportada: percentil setorial não ponderado de V06004 em Limeira = "
                    f"{p.get('value')} ({p.get('unit')}); isso compara setores, não famílias de alunos."
                )
                facts.append(
                    {
                        "kind": "SUPPORTED_TERRITORIAL_COMPARISON",
                        "metric_id": p.get("metric_id"),
                        "period": "2022",
                        "value": p.get("value"),
                        "unit": p.get("unit"),
                        "comparison_population": "LIMEIRA_CENSUS_SECTORS_WITH_PUBLISHED_V06004",
                        "student_household_claim": False,
                        "text": comparisons[-1],
                    }
                )
        else:
            distribution_ids = [
                "SECTOR_RESPONSIBLE_INCOME_MEAN_MIN",
                "SECTOR_RESPONSIBLE_INCOME_MEAN_Q1",
                "SECTOR_RESPONSIBLE_INCOME_MEAN_MEDIAN",
                "SECTOR_RESPONSIBLE_INCOME_MEAN_Q3",
                "SECTOR_RESPONSIBLE_INCOME_MEAN_MAX",
            ]
            dist = {
                row["metric_id"]: row
                for row in rows
                if row.get("metric_id") in distribution_ids
            }
            if set(dist) == set(distribution_ids):
                values = {
                    key: dist[key]["value"]
                    for key in distribution_ids
                }
                facts.append(
                    {
                        "kind": "SUPPORTED_SECTOR_INCOME_DISTRIBUTION",
                        "period": "2022",
                        "metric_semantic": "V06004_UNWEIGHTED_SECTOR_DISTRIBUTION",
                        "values": values,
                        "unit": "BRL_NOMINAL_MONTHLY",
                        "weighted": False,
                        "text": "Comparação municipal suportada: distribuição não ponderada do rendimento médio dos responsáveis entre setores com V06004 publicado.",
                    }
                )
                comparisons.append(
                    "Comparações quantitativas são válidas entre setores no mesmo V06004/2022; não constituem ranking de alunos ou bairros sem identidade estruturada."
                )
    if school_code is None:
        facts.append(coverage_fact(territory))
    facts.extend(income_missingness_facts(territory, school_code))
    _mark_applied(filters, "SCHOOL", "PERIOD", "GRANULARITY")
    provenance.extend([
        _product_provenance(
            "TERRITORY_PROFILE",
            territory,
            selected_scope=scope,
            selected_row_count=len(rows),
            selected_period="2022",
        ),
        {
            "product": "TASK212_MIXED_CONTEXT_PLANNER",
            "plan_sha256": plan.get("plan_sha256"),
        },
    ])
    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id=question_id,
        filter_accounting=filters,
        facts=facts,
        time_reference=["2022"],
        comparisons=comparisons,
        provenance=provenance,
        cautions=[
            "SECTOR_INCOME_NE_STUDENT_HOUSEHOLD_INCOME",
            "SCHOOL_LOCATION_SECTOR_NE_STUDENT_CATCHMENT",
            "SECTOR_COMPARISON_NE_CAUSAL_EXPLANATION",
            coverage_caution(coverage_context(territory)),
            "NO_WEAK_GEOGRAPHIC_SUBSTITUTION",
        ],
        contract=out,
    )


def _control_context_supported(
    text: str,
    context: Mapping[str, Any],
    question_id: str,
) -> dict[str, Any] | None:
    out = _task209_contract()
    filters = _base_filter_accounting(context)
    if (
        context["school"].get("status") == "RESOLVED"
        or context["period"].get("status") == "RESOLVED"
        or bool(context.get("policy_service_facets"))
    ):
        return _unsupported(
            text,
            context,
            question_id,
            filters,
            "CTRL_Q1/CTRL_Q3 inventariam força e payload dos produtos atuais; escola, período ou faceta não são filtros estruturados deste inventário.",
            out,
        )
    return None


def _payload_state(product: Mapping[str, Any]) -> str:
    local = len(product.get("rows", []))
    declared = int(product.get("row_count") or 0)
    if local:
        return "LOCAL_ROWS_PRESENT"
    if declared:
        return "METADATA_ONLY_REMOTE_SNAPSHOT"
    return "EMPTY_PRODUCT"


def _strength(product_name: str, product: Mapping[str, Any]) -> tuple[str, dict[str, int]]:
    if product_name == "QUERY_PRODUCT_CATALOG":
        return "LOCAL_DERIVED_CATALOG", {}
    state = _payload_state(product)
    if state == "METADATA_ONLY_REMOTE_SNAPSHOT":
        return "METADATA_ONLY_REMOTE_SNAPSHOT", {}
    counts = Counter(
        str(row.get("quality_status") or "UNSPECIFIED")
        for row in product.get("rows", [])
    )
    if counts and set(counts) == {"VALIDATED"}:
        return "LOCAL_VALIDATED_ROWS", dict(sorted(counts.items()))
    return "LOCAL_READY_WITH_CAUTION_ROWS", dict(sorted(counts.items()))


def _execute_control(
    *,
    text: str,
    context: Mapping[str, Any],
    products: Mapping[str, Mapping[str, Any]],
    plan: Mapping[str, Any],
    question_id: str,
) -> dict[str, Any]:
    unsupported = _control_context_supported(text, context, question_id)
    if unsupported is not None:
        return unsupported
    out = _task209_contract()
    filters = _base_filter_accounting(context)
    filters["GRANULARITY"]["status"] = "APPLIED"
    catalog = products["QUERY_PRODUCT_CATALOG"]
    catalog_rows = {
        str(row.get("product_name")): dict(row)
        for row in catalog.get("rows", [])
    }
    facts: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    for name in sorted(products):
        product = products[name]
        local_count = len(product.get("rows", []))
        declared = int(product.get("row_count") or 0)
        payload_state = _payload_state(product)
        catalog_row = catalog_rows.get(name)
        if question_id == "CTRL_Q1":
            facts.append(
                {
                    "kind": "PRODUCT_PAYLOAD_STATUS",
                    "product": name,
                    "declared_row_count": declared,
                    "local_row_count": local_count,
                    "payload_state": payload_state,
                    "catalog_readiness": (
                        catalog_row.get("readiness") if catalog_row else "SELF_DERIVED_CATALOG"
                    ),
                    "catalog_readiness_overrides_payload_truth": False,
                    "generated_at": product.get("generated_at"),
                    "generated_at_proves_source_freshness": False,
                    "text": (
                        f"{name}: declaradas={declared}; locais={local_count}; "
                        f"payload={payload_state}; readiness do catálogo="
                        f"{catalog_row.get('readiness') if catalog_row else 'SELF'}."
                    ),
                }
            )
        else:
            strength, quality_counts = _strength(name, product)
            facts.append(
                {
                    "kind": "PRODUCT_EVIDENCE_STRENGTH",
                    "product": name,
                    "strength": strength,
                    "declared_row_count": declared,
                    "local_row_count": local_count,
                    "quality_status_counts": quality_counts,
                    "numeric_truth_from_metadata_only_allowed": False,
                    "catalog_readiness_equals_source_truth_strength": False,
                    "text": (
                        f"{name}: força={strength}; linhas locais={local_count}; "
                        f"linhas declaradas={declared}."
                    ),
                }
            )
        provenance.append(_product_provenance(name, product))
    provenance.extend([
        _product_provenance("QUERY_PRODUCT_CATALOG", catalog),
        {
            "product": "TASK212_MIXED_CONTEXT_PLANNER",
            "plan_sha256": plan.get("plan_sha256"),
        },
    ])
    cautions = [
        "CATALOG_READINESS_NE_LOCAL_PAYLOAD_TRUTH",
        "GENERATED_AT_NE_SOURCE_UPDATE_TIME",
        "DERIVED_QUERY_CACHE_NE_SOURCE_OF_TRUTH",
        "METADATA_ONLY_NE_NUMERIC_EVIDENCE",
    ]
    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id=question_id,
        filter_accounting=filters,
        facts=facts,
        time_reference=[],
        comparisons=[],
        provenance=provenance,
        cautions=cautions,
        contract=out,
    )


def execute_contextual_query_v4(
    text: str,
    *,
    generated_at: str,
    software_version: str,
    reference_date: str | None = None,
    context_school_code: str | None = None,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    validate_contract(contract_path)
    _stop(bool(generated_at), "TASK213_GENERATED_AT")
    _stop(bool(software_version), "TASK213_SOFTWARE_VERSION")

    context = bind_context(
        text,
        reference_date=reference_date,
        context_school_code=context_school_code,
    )
    if context.get("state") != "CONTEXT_BOUND":
        return execute_contextual_query_v3(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )
    qids = list(context.get("selected_question_ids") or [])
    if len(qids) != 1:
        return execute_contextual_query_v3(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )
    qid = qids[0]
    if qid not in set(contract["promoted_questions"]):
        return execute_contextual_query_v3(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )

    plan = plan_question(
        qid,
        generated_at=generated_at,
        software_version=software_version,
        context=context,
    )
    if plan["planning_state"] != contract["planner_gate"]["required_state"]:
        return _planner_blocked(
            text=text,
            context=context,
            question_id=qid,
            plan=plan,
        )

    products = build_current_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    if qid == "FIN_Q2":
        return _execute_fin_q2(
            text=text,
            context=context,
            products=products,
            plan=plan,
            contract=contract,
        )
    if qid == "FIN_Q4":
        return _execute_fin_q4(
            text=text,
            context=context,
            products=products,
            plan=plan,
        )
    if qid == "TEACH_Q2":
        return _execute_teach_q2(
            text=text,
            context=context,
            products=products,
            plan=plan,
            contract=contract,
        )
    if qid == "EQUITY_Q1":
        return _execute_equity_q1(
            text=text,
            context=context,
            products=products,
            plan=plan,
            contract=contract,
        )
    if qid in {"TERR_Q1", "TERR_Q2"}:
        return _execute_territory(
            text=text,
            context=context,
            products=products,
            plan=plan,
            question_id=qid,
            contract=contract,
        )
    if qid in {"CTRL_Q1", "CTRL_Q3"}:
        return _execute_control(
            text=text,
            context=context,
            products=products,
            plan=plan,
            question_id=qid,
        )
    raise Task213ExecutionStop(f"TASK213_UNREACHABLE_PROMOTED:{qid}")


def render_contextual_answer_v4(answer: Mapping[str, Any]) -> dict[str, Any]:
    return render_contextual_answer_markdown(answer)
