from __future__ import annotations

from decimal import Decimal
import json
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.productization.context_aware_execution import (
    _base_filter_accounting,
    _finalize,
    _unsupported,
    render_contextual_answer_markdown,
)
from robo_dados_publicos.productization.contextual_slot_binder import bind_context
from robo_dados_publicos.productization.safe_local_mixed_execution import (
    execute_contextual_query_v4,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task214_custody_ledger_projections.v1.json"
TASK209_CONTRACT = ROOT / "config/task209_context_aware_execution.v1.json"
FIXTURE_DIR = ROOT / "docs/evidence/fixtures/task214"


class Task214ExecutionStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task214ExecutionStop(code)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _task209_contract() -> dict[str, Any]:
    obj = _load_json(TASK209_CONTRACT)
    _stop(obj.get("output_schema") == "OBSERVATORY_CONTEXTUAL_ANSWER_V1", "TASK214_OUTPUT_SCHEMA")
    return obj


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = _load_json(Path(path))
    _stop(obj.get("schema") == "TASK214_CUSTODY_LEDGER_PROJECTIONS_V1", "TASK214_SCHEMA")
    _stop(obj.get("issue") == 672, "TASK214_ISSUE")
    _stop(
        obj.get("base_main_sha") == "e7df99d92e9b177bf6fc372fb8a8067f670216ed",
        "TASK214_BASE",
    )
    _stop(
        obj.get("mode") == "T0_OFFLINE_CUSTODY_REHYDRATED_BOUNDED_LEDGER_EXECUTION",
        "TASK214_MODE",
    )
    _stop(
        set(obj["promoted_questions"]) == {"ACC_Q1", "ACC_Q2", "ACC_Q3", "FIN_Q3"},
        "TASK214_PROMOTED_SET",
    )
    _stop(
        set(obj["semantic_blockers"])
        == {"CTRL_Q2", "INFRA_Q2", "PLAN_Q3", "PROC_Q1", "PROC_Q2", "PROC_Q3"},
        "TASK214_BLOCKED_SET",
    )
    bounds = obj["claim_boundaries"]
    for key in (
        "bounded_projection_equals_full_ledger",
        "top30_classification_equals_full_list",
        "stage_arithmetic_equals_legal_net_expenditure",
        "rests_payable_equals_current_year_expenditure",
        "revenue_equals_expenditure",
        "funding_source_equals_expenditure_destination",
        "semantic_blocker_may_be_bypassed_by_text_similarity",
        "nearest_period_substitution",
    ):
        _stop(bounds[key] is False, f"TASK214_BOUNDARY_{key}")
    _stop(bounds["source_snapshot_remains_canonical"] is True, "TASK214_SOURCE_CANONICAL")
    _stop(bounds["source_row_counts_must_reconcile"] is True, "TASK214_ROW_RECONCILE")
    _stop(all(v is False for v in obj["runtime_remote_effects"].values()), "TASK214_REMOTE")
    return obj


def load_projection() -> dict[str, Any]:
    manifest = _load_json(FIXTURE_DIR / "TASK_214_PROJECTION_MANIFEST.json")
    _stop(
        manifest.get("schema") == "TASK214_CUSTODY_REHYDRATED_BOUNDED_LEDGER_PROJECTIONS_V1",
        "TASK214_FIXTURE_SCHEMA",
    )
    views: dict[str, Any] = {}
    views["ACC_Q1_STAGE_TOTALS"] = _load_json(FIXTURE_DIR / "TASK_214_ACC_Q1_STAGE_TOTALS.json")
    acc2_meta = _load_json(FIXTURE_DIR / "TASK_214_ACC_Q2_CLASSIFICATION_META.json")
    acc2_rows: list[list[Any]] = []
    for name in (
        "TASK_214_ACC_Q2_TOP30_COMPACT_01_10.json",
        "TASK_214_ACC_Q2_TOP30_COMPACT_11_20.json",
        "TASK_214_ACC_Q2_TOP30_COMPACT_21_30.json",
    ):
        acc2_rows.extend(_load_json(FIXTURE_DIR / name))
    views["ACC_Q2_CLASSIFICATION_TOP30"] = {
        **acc2_meta,
        "rows": acc2_rows,
    }
    views["ACC_Q3_RESTS_PAYABLE"] = _load_json(
        FIXTURE_DIR / "TASK_214_ACC_Q3_RESTS_PAYABLE.json"
    )
    fin = _load_json(FIXTURE_DIR / "TASK_214_FIN_Q3_FUNDING_SOURCES.json")
    apps: list[dict[str, Any]] = []
    for name in (
        "TASK_214_FIN_Q3_EDU_APPS_01_10.json",
        "TASK_214_FIN_Q3_EDU_APPS_11_19.json",
    ):
        apps.extend(_load_json(FIXTURE_DIR / name))
    eti = _load_json(FIXTURE_DIR / "TASK_214_FIN_Q3_ETI_ROWS.json")
    views["FIN_Q3_REVENUE_SOURCES"] = {
        **fin,
        "education_application_totals": apps,
        "eti_rows": eti,
    }
    return {
        **manifest,
        "views": views,
    }


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    projection = load_projection()
    src = projection["source_snapshots"]
    expected = contract["source_snapshots"]
    _stop(src == expected, "TASK214_SOURCE_SNAPSHOT_DRIFT")

    acc1 = projection["views"]["ACC_Q1_STAGE_TOTALS"]
    _stop(acc1["tce_source_rows_covered"] == 39779, "TASK214_ACC1_ROWS")
    _stop(acc1["education_function_rows"] == 8224, "TASK214_ACC1_EDU_ROWS")
    by_stage = {row[0]: row for row in acc1["all_entities_by_source_stage"]}
    _stop(by_stage["Empenhado"][1:] == [6956, "1759388496.22"], "TASK214_EMPENHADO")
    _stop(by_stage["Reforço"][1:] == [757, "46507977.05"], "TASK214_REFORCO")
    _stop(by_stage["Anulação"][1:] == [684, "65259446.13"], "TASK214_ANULACAO")
    _stop(by_stage["Valor Liquidado"][1:] == [16460, "1024476679.69"], "TASK214_LIQUIDADO")
    _stop(by_stage["Valor Pago"][1:] == [14922, "921567699.04"], "TASK214_PAGO")
    edu_stages = _sum_stage_rows(acc1["education_function_by_month_source_stage"], 1, 7)
    _stop(edu_stages["Empenhado"]["amount_brl"] == "337824523.73", "TASK214_EDU_EMPENHADO")
    _stop(edu_stages["Reforço"]["amount_brl"] == "34418997.78", "TASK214_EDU_REFORCO")
    _stop(edu_stages["Anulação"]["amount_brl"] == "3481109.44", "TASK214_EDU_ANULACAO")
    _stop(edu_stages["Valor Liquidado"]["amount_brl"] == "262452288.06", "TASK214_EDU_LIQUIDADO")
    _stop(edu_stages["Valor Pago"]["amount_brl"] == "227797802.44", "TASK214_EDU_PAGO")
    _stop(_commitment_arithmetic(edu_stages) == "368762412.07", "TASK214_EDU_ARITHMETIC")

    acc2 = projection["views"]["ACC_Q2_CLASSIFICATION_TOP30"]
    _stop(acc2["meta"]["classification_universe_group_count"] == 422, "TASK214_ACC2_GROUPS")
    _stop(acc2["meta"]["classification_universe_source_rows"] == 39779, "TASK214_ACC2_ROWS")
    _stop(
        acc2["meta"]["classification_universe_sha256"]
        == "b23725c508ca1b9e8995e7d6f0df5184057f046cd96d697495fcc01d699084ec",
        "TASK214_ACC2_SHA",
    )
    _stop(len(acc2["rows"]) == 30, "TASK214_ACC2_TOP30")

    acc3 = projection["views"]["ACC_Q3_RESTS_PAYABLE"]
    _stop(acc3["covered_source_rows"] == 4 and len(acc3["rows"]) == 4, "TASK214_ACC3_ROWS")
    by_key = {(row["event_month"], row["scope_name"]): row for row in acc3["rows"]}
    _stop(
        by_key[(4, "SECRETARIA DE EDUCACAO")]["total_balance_brl"] == "3010505.55",
        "TASK214_ACC3_EDU_APR",
    )
    _stop(
        by_key[(4, "RESTOS A PAGAR (EXCETO INTRAORCAM.) (I)")]["total_balance_brl"]
        == "51053179.39",
        "TASK214_ACC3_MUNI_APR",
    )

    fin = projection["views"]["FIN_Q3_REVENUE_SOURCES"]
    _stop(fin["funding_source_total_source_rows"] == 2286, "TASK214_FIN_ROWS")
    _stop(len(fin["funding_source_totals"]) == 8, "TASK214_FIN_SOURCES")
    _stop(len(fin["education_application_totals"]) == 19, "TASK214_FIN_APPS")
    signals = fin["canonical_signals"]
    _stop(signals["all_organs_net_revenue_jan_jul_brl"] == "1297518731.15", "TASK214_FIN_ALL")
    _stop(signals["prefeitura_net_revenue_jan_jul_brl"] == "1117414208.00", "TASK214_FIN_PREF")
    _stop(signals["broad_education_application_net_brl"] == "241960964.18", "TASK214_FIN_EDU")
    _stop(signals["fundeb_linked_net_brl"] == "118066203.65", "TASK214_FIN_FUNDEB")
    _stop(signals["eti_all_linked_net_brl"] == "3692142.87", "TASK214_FIN_ETI")
    _stop(
        sum(int(row["source_row_count"]) for row in fin["funding_source_totals"]) == 2286,
        "TASK214_FIN_SOURCE_ROW_RECONCILE",
    )
    _stop(
        sum(int(row["source_row_count"]) for row in fin["education_application_totals"]) == 351,
        "TASK214_FIN_APP_ROW_RECONCILE",
    )
    full_edu = sum((Decimal(row["amount_sum_brl"]) for row in fin["education_application_totals"]), Decimal("0"))
    full_fundeb = sum(
        (Decimal(row["amount_sum_brl"]) for row in fin["education_application_totals"] if row["fundeb_classification_any"]),
        Decimal("0"),
    )
    eti = fin["eti_rows"]
    _stop(eti["covered_source_rows"] == 7 and len(eti["rows"]) == 7, "TASK214_FIN_ETI_ROWS")
    full_eti = sum((Decimal(row["amount_brl"]) for row in eti["rows"]), Decimal("0"))
    direct_eti = sum(
        (Decimal(row["amount_brl"]) for row in eti["rows"] if row["eti_direct_transfer"]),
        Decimal("0"),
    )
    interest_eti = sum(
        (Decimal(row["amount_brl"]) for row in eti["rows"] if row["eti_financial_remuneration"]),
        Decimal("0"),
    )
    _stop(f"{full_edu:.2f}" == "241960964.18", "TASK214_FIN_EDU_RECOMPUTE")
    _stop(f"{full_fundeb:.2f}" == "118066203.65", "TASK214_FIN_FUNDEB_RECOMPUTE")
    _stop(f"{full_eti:.2f}" == "3692142.87", "TASK214_FIN_ETI_RECOMPUTE")
    _stop(f"{direct_eti:.2f}" == "3606418.18", "TASK214_FIN_ETI_DIRECT")
    _stop(f"{interest_eti:.2f}" == "85724.69", "TASK214_FIN_ETI_INTEREST")
    _stop(eti["all_linked_net_brl"] == "3692142.87", "TASK214_FIN_ETI_PIN")
    _stop(eti["direct_transfer_net_brl"] == "3606418.18", "TASK214_FIN_ETI_DIRECT_PIN")
    _stop(eti["financial_remuneration_net_brl"] == "85724.69", "TASK214_FIN_ETI_INTEREST_PIN")

    return {
        "schema": "TASK214_CUSTODY_LEDGER_PROJECTIONS_VALIDATION_V1",
        "status": "PASS",
        "accounting_source_rows": expected["ACCOUNTING_LEDGER"]["row_count"],
        "tce_source_rows": 39779,
        "revenue_source_rows": 2286,
        "classification_groups": 422,
        "classification_display_rows": 30,
        "promoted_question_count": 4,
        "semantic_blocker_count": 6,
        "network": False,
        "drive_read": False,
        "drive_write": False,
        "llm": False,
    }


def _mark(filters: dict[str, Any], *names: str) -> None:
    for name in names:
        if filters[name]["status"] == "PENDING":
            filters[name]["status"] = "APPLIED"


def _no_school_or_facets(
    text: str,
    context: Mapping[str, Any],
    question_id: str,
    filters: dict[str, Any],
    *,
    allowed_facets: set[str] | None = None,
) -> dict[str, Any] | None:
    out = _task209_contract()
    if context["school"].get("status") == "RESOLVED":
        return _unsupported(
            text,
            context,
            question_id,
            filters,
            f"{question_id} não possui granularidade escolar estruturada nesta projeção contábil/fiscal.",
            out,
        )
    facets = set(context.get("policy_service_facets") or [])
    allowed = set(allowed_facets or set())
    unsupported_facets = facets - allowed
    if unsupported_facets:
        return _unsupported(
            text,
            context,
            question_id,
            filters,
            f"{question_id} não converte as facetas {sorted(unsupported_facets)} em identidade contábil.",
            out,
        )
    if facets and filters["POLICY_SERVICE_FACETS"]["status"] == "PENDING":
        filters["POLICY_SERVICE_FACETS"]["status"] = "APPLIED_BY_RECIPE_SCOPE"
    return None


def _period_window(
    context: Mapping[str, Any],
    *,
    supported_year: int,
    max_month: int,
    allow_month: bool = True,
    allow_year_to_month: bool = True,
    allow_year: bool = True,
) -> tuple[str, int, int] | None:
    period = context["period"]
    if period.get("status") != "RESOLVED":
        return ("DEFAULT_YTD", 1, max_month)
    if int(period.get("year") or 0) != supported_year:
        return None
    mode = period.get("mode")
    if mode == "YEAR" and allow_year:
        return ("YEAR_OBSERVED_YTD", 1, max_month)
    if mode == "YEAR_TO_MONTH" and allow_year_to_month:
        end = int(period.get("end_month") or 0)
        if 1 <= end <= max_month:
            return ("YEAR_TO_MONTH", 1, end)
        return None
    if mode == "MONTH" and allow_month:
        month = int(period.get("month") or 0)
        if 1 <= month <= max_month:
            return ("MONTH", month, month)
        return None
    return None


def _sum_stage_rows(rows: list[list[Any]], start: int, end: int) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for month, stage, count, amount in rows:
        if start <= int(month) <= end:
            slot = out.setdefault(str(stage), {"row_count": 0, "amount_brl": Decimal("0")})
            slot["row_count"] += int(count)
            slot["amount_brl"] += Decimal(str(amount))
    return {
        stage: {"row_count": slot["row_count"], "amount_brl": f"{slot['amount_brl']:.2f}"}
        for stage, slot in sorted(out.items())
    }


def _commitment_arithmetic(stages: Mapping[str, Mapping[str, Any]]) -> str:
    emp = Decimal(stages.get("Empenhado", {}).get("amount_brl", "0"))
    ref = Decimal(stages.get("Reforço", {}).get("amount_brl", "0"))
    anu = Decimal(stages.get("Anulação", {}).get("amount_brl", "0"))
    return f"{emp + ref - anu:.2f}"


def _source_provenance(contract: Mapping[str, Any], product: str, view: str) -> dict[str, Any]:
    src = contract["source_snapshots"][product]
    return {
        "product": product,
        "projection_view": view,
        "source_snapshot_id": src["snapshot_id"],
        "source_content_sha256": src["content_sha256"],
        "source_gzip_sha256": src["gzip_sha256"],
        "source_drive_id": src["drive_id"],
        "source_row_count": src["row_count"],
        "projection_is_source_snapshot": False,
    }


def _execute_acc_q1(
    *,
    text: str,
    context: Mapping[str, Any],
    contract: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> dict[str, Any]:
    out = _task209_contract()
    filters = _base_filter_accounting(context)
    stop = _no_school_or_facets(text, context, "ACC_Q1", filters)
    if stop is not None:
        return stop
    window = _period_window(context, supported_year=2026, max_month=7)
    if window is None:
        return _unsupported(
            text, context, "ACC_Q1", filters,
            "ACC_Q1 possui observações TCE somente entre janeiro e julho de 2026; nenhum período foi aproximado.",
            out,
        )
    mode, start, end = window
    rows = projection["views"]["ACC_Q1_STAGE_TOTALS"]["by_month_source_stage"]
    stages = _sum_stage_rows(rows, start, end)
    _mark(filters, "PERIOD", "GRANULARITY")
    facts = [
        {
            "kind": "ACCOUNTING_SOURCE_STAGE_TOTALS",
            "period": f"2026-{start:02d}" if start == end else f"2026-01..2026-{end:02d}",
            "period_mode": mode,
            "observed_ytd_not_full_year": mode in {"DEFAULT_YTD", "YEAR_OBSERVED_YTD", "YEAR_TO_MONTH"},
            "source_stages": stages,
            "commitment_plus_reinforcement_minus_reversal_arithmetic_brl": _commitment_arithmetic(stages),
            "legal_net_expenditure_claim": False,
            "text": (
                f"Execução observada no TCE ({'mês' if start == end else 'acumulado'} até {end:02d}/2026): "
                f"Empenhado R$ {stages.get('Empenhado',{}).get('amount_brl','0.00')}; "
                f"Reforço R$ {stages.get('Reforço',{}).get('amount_brl','0.00')}; "
                f"Anulação R$ {stages.get('Anulação',{}).get('amount_brl','0.00')}; "
                f"Liquidado R$ {stages.get('Valor Liquidado',{}).get('amount_brl','0.00')}; "
                f"Pago R$ {stages.get('Valor Pago',{}).get('amount_brl','0.00')}."
            ),
        }
    ]
    return _finalize(
        state="ANSWERED_CONTEXTUALLY", text=text, context=context, question_id="ACC_Q1",
        filter_accounting=filters, facts=facts,
        time_reference=[facts[0]["period"]], comparisons=[],
        provenance=[
            _source_provenance(contract, "ACCOUNTING_LEDGER", "ACC_Q1_STAGE_TOTALS"),
            {
                "product": "TASK214_BOUNDED_PROJECTION",
                "tce_source_rows_reconciled": 39779,
                "projection_view": "ACC_Q1_STAGE_TOTALS",
            },
        ],
        cautions=[
            "SOURCE_STAGE_SEMANTICS_PRESERVED",
            "COMMITMENT_REINFORCEMENT_REVERSAL_ARITHMETIC_NE_LEGAL_NET_EXPENDITURE",
            "OBSERVED_JAN_JUL_2026_NE_FULL_YEAR_2026",
            "BOUNDED_PROJECTION_NE_FULL_LEDGER_ROWS",
        ],
        contract=out,
    )


def _decode_acc2_rows(view: Mapping[str, Any]) -> list[dict[str, Any]]:
    columns = view["columns"]
    return [dict(zip(columns, row)) for row in view["rows"]]


def _execute_acc_q2(
    *,
    text: str,
    context: Mapping[str, Any],
    contract: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> dict[str, Any]:
    out = _task209_contract()
    filters = _base_filter_accounting(context)
    stop = _no_school_or_facets(text, context, "ACC_Q2", filters)
    if stop is not None:
        return stop
    period = context["period"]
    if period.get("status") == "RESOLVED":
        if period.get("mode") != "YEAR" or int(period.get("year") or 0) != 2026:
            return _unsupported(
                text, context, "ACC_Q2", filters,
                "ACC_Q2 possui somente a projeção classificatória integral Jan-Jul/2026; mês específico não é inferido a partir do ranking anual-observado.",
                out,
            )
        filters["PERIOD"]["status"] = "APPLIED"
    filters["GRANULARITY"]["status"] = "APPLIED"
    view = projection["views"]["ACC_Q2_CLASSIFICATION_TOP30"]
    rows = _decode_acc2_rows(view)
    facts: list[dict[str, Any]] = [
        {
            "kind": "CLASSIFICATION_UNIVERSE",
            "source_rows": view["meta"]["classification_universe_source_rows"],
            "group_count": view["meta"]["classification_universe_group_count"],
            "universe_sha256": view["meta"]["classification_universe_sha256"],
            "displayed_group_count": len(rows),
            "display_selection": view["meta"]["selection"],
            "top30_equals_full_list": False,
            "period": "2026-01..2026-07",
            "text": (
                f"Universo classificatório: {view['meta']['classification_universe_group_count']} grupos "
                f"reconciliados com {view['meta']['classification_universe_source_rows']} lançamentos; "
                "os 30 grupos exibidos são uma projeção ordenada, não a lista completa."
            ),
        }
    ]
    for rank, row in enumerate(rows, start=1):
        facts.append(
            {
                "kind": "CLASSIFICATION_TOP_GROUP",
                "rank": rank,
                **row,
                "period": "2026-01..2026-07",
                "text": (
                    f"#{rank} {row['function']} | programa {row['program_code']} {row['program_name']} | "
                    f"ação {row['action_code']} {row['action_name']} | fonte {row['funding_source']} | "
                    f"aplicação {row['application_code']} | aritmética de empenho R$ {row['commitment_arithmetic_brl']}."
                ),
            }
        )
    return _finalize(
        state="ANSWERED_CONTEXTUALLY", text=text, context=context, question_id="ACC_Q2",
        filter_accounting=filters, facts=facts,
        time_reference=["2026-01..2026-07"], comparisons=[],
        provenance=[
            _source_provenance(contract, "ACCOUNTING_LEDGER", "ACC_Q2_CLASSIFICATION_TOP30"),
            {
                "product": "TASK214_BOUNDED_PROJECTION",
                "classification_universe_group_count": 422,
                "classification_universe_source_rows": 39779,
                "classification_universe_sha256": view["meta"]["classification_universe_sha256"],
                "display_projection": "TOP30",
            },
        ],
        cautions=[
            "TOP30_CLASSIFICATION_NE_FULL_CLASSIFICATION_LIST",
            "EXPENSE_ELEMENT_DISPLAY_IS_COUNT_PLUS_TWO_DETERMINISTIC_EXAMPLES",
            "COMMITMENT_ARITHMETIC_NE_LEGAL_NET_EXPENDITURE",
            "OBSERVED_JAN_JUL_2026_NE_FULL_YEAR_2026",
        ],
        contract=out,
    )


def _select_rests_rows(view: Mapping[str, Any], month: int) -> list[dict[str, Any]]:
    rows = [dict(row) for row in view["rows"] if int(row["event_month"]) == month]
    rows.sort(key=lambda row: row["scope_type"])
    return rows


def _execute_acc_q3(
    *,
    text: str,
    context: Mapping[str, Any],
    contract: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> dict[str, Any]:
    out = _task209_contract()
    filters = _base_filter_accounting(context)
    stop = _no_school_or_facets(text, context, "ACC_Q3", filters)
    if stop is not None:
        return stop
    period = context["period"]
    month: int
    if period.get("status") != "RESOLVED":
        month = 4
    else:
        if int(period.get("year") or 0) != 2026:
            return _unsupported(text, context, "ACC_Q3", filters, "ACC_Q3 possui snapshots RREO somente em 2026.", out)
        mode = period.get("mode")
        if mode == "MONTH":
            month = int(period.get("month") or 0)
        elif mode == "YEAR_TO_MONTH":
            month = int(period.get("end_month") or 0)
        else:
            return _unsupported(
                text, context, "ACC_Q3", filters,
                "ACC_Q3 requer fevereiro/2026 ou abril/2026 (ou ausência de período, que usa o último snapshot materializado: abril).",
                out,
            )
        if month not in {2, 4}:
            return _finalize(
                state="EXPLICIT_CONTEXT_GAP", text=text, context=context, question_id="ACC_Q3",
                filter_accounting={
                    **filters,
                    "PERIOD": {**filters["PERIOD"], "status": "APPLIED_TO_ZERO_MATCH_QUERY"},
                    "GRANULARITY": {**filters["GRANULARITY"], "status": "APPLIED"},
                },
                facts=[{
                    "kind": "EXACT_RESTS_PERIOD_GAP",
                    "requested_month": month,
                    "available_exact_months": [2, 4],
                    "nearest_month_substitution": False,
                    "text": "Não existe snapshot exato de Restos a Pagar para o mês solicitado; fevereiro e abril não foram usados como aproximação.",
                }],
                time_reference=[], provenance=[
                    _source_provenance(contract, "ACCOUNTING_LEDGER", "ACC_Q3_RESTS_PAYABLE")
                ],
                cautions=["NO_NEAREST_PERIOD_SUBSTITUTION","RESTS_PAYABLE_NE_CURRENT_YEAR_EXPENDITURE"],
                gap_scope="TASK214_EXACT_RESTS_PAYABLE_SNAPSHOT",
                contract=out,
            )
        filters["PERIOD"]["status"] = "APPLIED"
    filters["GRANULARITY"]["status"] = "APPLIED"
    view = projection["views"]["ACC_Q3_RESTS_PAYABLE"]
    rows = _select_rests_rows(view, month)
    _stop(len(rows) == 2, "TASK214_ACC3_SCOPE_ROWS")
    facts=[]
    for row in rows:
        facts.append({
            "kind":"RESTS_PAYABLE_SNAPSHOT",
            "period":row["period"],
            "scope_name":row["scope_name"],
            "scope_type":row["scope_type"],
            "total_balance_brl":row["total_balance_brl"],
            "processed_balance_brl":row["processed"]["balance_brl"],
            "nonprocessed_balance_brl":row["nonprocessed"]["balance_brl"],
            "text":(
                f"{row['scope_name']} em {row['period']}: saldo total R$ {row['total_balance_brl']}; "
                f"processados R$ {row['processed']['balance_brl']}; "
                f"não processados R$ {row['nonprocessed']['balance_brl']}."
            ),
        })
    comparisons=[]
    if period.get("status") != "RESOLVED" and month == 4:
        feb = _select_rests_rows(view, 2)
        feb_by_scope={r["scope_type"]:r for r in feb}
        for row in rows:
            old=feb_by_scope[row["scope_type"]]
            comparisons.append(
                f"{row['scope_name']}: fev R$ {old['total_balance_brl']} → abr R$ {row['total_balance_brl']}."
            )
    return _finalize(
        state="ANSWERED_CONTEXTUALLY",text=text,context=context,question_id="ACC_Q3",
        filter_accounting=filters,facts=facts,time_reference=[f"2026-{month:02d}"],
        comparisons=comparisons,
        provenance=[
            _source_provenance(contract,"ACCOUNTING_LEDGER","ACC_Q3_RESTS_PAYABLE"),
            {"product":"RREO_RESTS_PAYABLE","covered_source_rows":4,"selected_exact_month":month},
        ],
        cautions=[
            "RESTS_PAYABLE_NE_CURRENT_YEAR_EXPENDITURE",
            "PROCESSED_NE_NONPROCESSED",
            "RREO_AGGREGATE_NE_TCESP_GRANULAR_TRANSACTION",
            "NO_NEAREST_PERIOD_SUBSTITUTION",
        ],
        contract=out,
    )


def _month_value(row: Mapping[str, Any], start: int, end: int) -> Decimal:
    total=Decimal("0")
    for month_text, amount in row.get("month_amounts_brl", {}).items():
        month=int(month_text)
        if start <= month <= end:
            total += Decimal(str(amount))
    return total


def _execute_fin_q3(
    *,
    text: str,
    context: Mapping[str, Any],
    contract: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> dict[str, Any]:
    out=_task209_contract()
    filters=_base_filter_accounting(context)
    stop=_no_school_or_facets(
        text,
        context,
        "FIN_Q3",
        filters,
        allowed_facets={"FINANCIAMENTO_FUNDEB"},
    )
    if stop is not None:
        return stop
    window=_period_window(context,supported_year=2026,max_month=7)
    if window is None:
        return _unsupported(
            text,context,"FIN_Q3",filters,
            "FIN_Q3 possui receitas materializadas somente de janeiro a julho de 2026; nenhum mês futuro ou outro ano foi aproximado.",
            out,
        )
    mode,start,end=window
    view=projection["views"]["FIN_Q3_REVENUE_SOURCES"]
    funding=[]
    for row in view["funding_source_totals"]:
        value=_month_value(row,start,end)
        funding.append({
            "funding_source":row["funding_source"],
            "value_brl":f"{value:.2f}",
            "source_row_count_full_jan_jul":row["source_row_count"],
        })
    apps=view["education_application_totals"]
    fundeb=sum((_month_value(row,start,end) for row in apps if row["fundeb_classification_any"]),Decimal("0"))
    eti_rows=view["eti_rows"]["rows"]
    eti=sum(
        (
            Decimal(row["amount_brl"])
            for row in eti_rows
            if start <= int(row["revenue_month"]) <= end
        ),
        Decimal("0"),
    )
    eti_direct=sum(
        (
            Decimal(row["amount_brl"])
            for row in eti_rows
            if row["eti_direct_transfer"] and start <= int(row["revenue_month"]) <= end
        ),
        Decimal("0"),
    )
    eti_interest=sum(
        (
            Decimal(row["amount_brl"])
            for row in eti_rows
            if row["eti_financial_remuneration"] and start <= int(row["revenue_month"]) <= end
        ),
        Decimal("0"),
    )
    broad_edu=sum((_month_value(row,start,end) for row in apps),Decimal("0"))
    _mark(filters,"PERIOD","GRANULARITY")
    facts=[
        {
            "kind":"REVENUE_FUNDING_SOURCE_TOTALS",
            "period":f"2026-{start:02d}" if start==end else f"2026-01..2026-{end:02d}",
            "period_mode":mode,
            "observed_ytd_not_full_year":mode in {"DEFAULT_YTD","YEAR_OBSERVED_YTD","YEAR_TO_MONTH"},
            "funding_sources":funding,
            "text":f"Receitas por fonte no recorte observado até {end:02d}/2026, sem converter fonte em destino de gasto.",
        },
        {
            "kind":"EDUCATION_REVENUE_APPLICATION_SIGNALS",
            "period":f"2026-{start:02d}" if start==end else f"2026-01..2026-{end:02d}",
            "fundeb_linked_brl":f"{fundeb:.2f}",
            "eti_linked_brl":f"{eti:.2f}",
            "eti_direct_transfer_brl":f"{eti_direct:.2f}",
            "eti_financial_remuneration_brl":f"{eti_interest:.2f}",
            "broad_education_application_brl":f"{broad_edu:.2f}",
            "fundeb_is_revenue_classification_not_expenditure_identity":True,
            "text":(
                f"Aplicações de receita ligadas ao FUNDEB: R$ {fundeb:.2f}; "
                f"ETI: R$ {eti:.2f} (transferência direta R$ {eti_direct:.2f}; remuneração financeira R$ {eti_interest:.2f}); "
                f"conjunto amplo de aplicações educacionais: R$ {broad_edu:.2f}."
            ),
        },
    ]
    return _finalize(
        state="ANSWERED_CONTEXTUALLY",text=text,context=context,question_id="FIN_Q3",
        filter_accounting=filters,facts=facts,time_reference=[facts[0]["period"]],comparisons=[],
        provenance=[
            _source_provenance(contract,"REVENUE_LEDGER","FIN_Q3_REVENUE_SOURCES"),
            {
                "product":"TASK214_BOUNDED_PROJECTION",
                "revenue_source_rows_reconciled":2286,
                "education_application_source_rows":view["education_application_source_rows"],
                "funding_source_category_count":len(view["funding_source_totals"]),
                "education_application_category_count":len(apps),
                "eti_source_rows_reconciled":len(eti_rows),
            },
        ],
        cautions=[
            "REVENUE_NE_EXPENDITURE",
            "FUNDING_SOURCE_CLASSIFICATION_NE_EXPENDITURE_DESTINATION",
            "FUNDEB_REVENUE_CLASSIFICATION_NE_FUNDEB_EXPENDITURE",
            "ETI_DIRECT_TRANSFER_NE_ETI_FINANCIAL_REMUNERATION",
            "OBSERVED_JAN_JUL_2026_NE_FULL_YEAR_2026",
        ],
        contract=out,
    )


def _semantic_blocker(
    *,
    text: str,
    context: Mapping[str, Any],
    question_id: str,
    reason: str,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    out=_task209_contract()
    filters=_base_filter_accounting(context)
    for item in filters.values():
        if item["status"]=="PENDING":
            item["status"]="BLOCKED_BY_TASK214_SEMANTIC_IDENTITY_GATE"
    return _finalize(
        state="EXPLICIT_CONTEXT_GAP",text=text,context=context,question_id=question_id,
        filter_accounting=filters,
        facts=[{
            "kind":"TASK214_SEMANTIC_BLOCKER",
            "blocker":reason,
            "weak_join_used":False,
            "text":"Os ledgers locais já existem, mas esta pergunta exige uma identidade/correspondência entre produtos que ainda não foi provada; disponibilidade simultânea não autoriza o join.",
        }],
        time_reference=[],comparisons=[],
        provenance=[{
            "product":"TASK214_CUSTODY_REHYDRATION",
            "accounting_snapshot_id":contract["source_snapshots"]["ACCOUNTING_LEDGER"]["snapshot_id"],
            "revenue_snapshot_id":contract["source_snapshots"]["REVENUE_LEDGER"]["snapshot_id"],
            "blocker":reason,
        }],
        cautions=[
            "PAYLOAD_PRESENT_BUT_CROSS_PRODUCT_IDENTITY_NOT_PROVEN",
            "WEAK_JOIN_FORBIDDEN",
            "TEXT_AMOUNT_DATE_SIMILARITY_NE_IDENTITY",
        ],
        gap_scope="TASK214_CROSS_PRODUCT_IDENTITY_OR_COHERENCE",
        contract=out,
    )


def execute_contextual_query_v5(
    text: str,
    *,
    generated_at: str,
    software_version: str,
    reference_date: str | None = None,
    context_school_code: str | None = None,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract=load_contract(contract_path)
    validate_contract(contract_path)
    _stop(bool(generated_at),"TASK214_GENERATED_AT")
    _stop(bool(software_version),"TASK214_SOFTWARE_VERSION")
    context=bind_context(
        text,reference_date=reference_date,context_school_code=context_school_code
    )
    if context.get("state")!="CONTEXT_BOUND":
        return execute_contextual_query_v4(
            text,generated_at=generated_at,software_version=software_version,
            reference_date=reference_date,context_school_code=context_school_code,
        )
    qids=list(context.get("selected_question_ids") or [])
    if len(qids)!=1:
        return execute_contextual_query_v4(
            text,generated_at=generated_at,software_version=software_version,
            reference_date=reference_date,context_school_code=context_school_code,
        )
    qid=qids[0]
    if qid in contract["semantic_blockers"]:
        return _semantic_blocker(
            text=text,context=context,question_id=qid,
            reason=contract["semantic_blockers"][qid],contract=contract,
        )
    if qid not in set(contract["promoted_questions"]):
        return execute_contextual_query_v4(
            text,generated_at=generated_at,software_version=software_version,
            reference_date=reference_date,context_school_code=context_school_code,
        )
    projection=load_projection()
    if qid=="ACC_Q1":
        return _execute_acc_q1(text=text,context=context,contract=contract,projection=projection)
    if qid=="ACC_Q2":
        return _execute_acc_q2(text=text,context=context,contract=contract,projection=projection)
    if qid=="ACC_Q3":
        return _execute_acc_q3(text=text,context=context,contract=contract,projection=projection)
    if qid=="FIN_Q3":
        return _execute_fin_q3(text=text,context=context,contract=contract,projection=projection)
    raise Task214ExecutionStop(f"TASK214_UNREACHABLE_PROMOTED:{qid}")


def render_contextual_answer_v5(answer: Mapping[str, Any]) -> dict[str, Any]:
    return render_contextual_answer_markdown(answer)
