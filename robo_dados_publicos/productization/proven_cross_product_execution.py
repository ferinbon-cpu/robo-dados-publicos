from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
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
from robo_dados_publicos.productization.custody_ledger_projection_execution import (
    execute_contextual_query_v5,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task215_proven_cross_product_crosswalk.v1.json"
TASK209_CONTRACT = ROOT / "config/task209_context_aware_execution.v1.json"


class Task215CrosswalkStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task215CrosswalkStop(code)


def _load(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _task209_contract() -> dict[str, Any]:
    obj = _load(TASK209_CONTRACT)
    _stop(obj.get("output_schema") == "OBSERVATORY_CONTEXTUAL_ANSWER_V1", "TASK215_OUTPUT_SCHEMA")
    return obj


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = _load(path)
    _stop(obj.get("schema") == "TASK215_PROVEN_CROSS_PRODUCT_CROSSWALK_V1", "TASK215_SCHEMA")
    _stop(obj.get("issue") == 674, "TASK215_ISSUE")
    _stop(
        obj.get("base_main_sha") == "85f221125591cd686e5384851e31e511bd1f114c",
        "TASK215_BASE",
    )
    _stop(
        obj.get("mode") == "T0_OFFLINE_AUTHORITATIVE_STRUCTURED_CROSSWALK_EXECUTION",
        "TASK215_MODE",
    )
    _stop(obj.get("promoted_questions") == ["PLAN_Q3"], "TASK215_PROMOTED_SET")
    _stop(
        set(obj["retained_semantic_blockers"])
        == {"CTRL_Q2", "INFRA_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"},
        "TASK215_RETAINED_BLOCKERS",
    )
    _stop(obj["plan_q3"]["supported_year"] == 2026, "TASK215_YEAR")
    _stop(obj["plan_q3"]["school_context_supported"] is False, "TASK215_SCHOOL")
    _stop(
        obj["join_strength"]["PLAN_Q3"] == "AUTHORITATIVE_STRUCTURED_DIMENSIONAL_CROSSWALK",
        "TASK215_JOIN_STRENGTH",
    )
    _stop(obj["join_strength"]["transaction_identity_claim"] is False, "TASK215_TRANSACTION_ID")
    _stop(obj["join_strength"]["fuzzy_text_match_used"] is False, "TASK215_FUZZY")
    _stop(obj["join_strength"]["amount_match_used"] is False, "TASK215_AMOUNT_JOIN")
    _stop(obj["join_strength"]["date_proximity_match_used"] is False, "TASK215_DATE_JOIN")
    for key in (
        "whole_plan_coherence_claim",
        "whole_loa_coverage_claim",
        "ppa_ldo_whole_execution_alignment_claim",
        "causal_claim",
        "normative_coherence_judgment",
    ):
        _stop(obj["plan_q3"][key] is False, f"TASK215_BOUNDARY_{key}")
    _stop(all(v is False for v in obj["runtime_remote_effects"].values()), "TASK215_REMOTE")
    return obj


def _pct(value: str, denominator: str) -> str:
    return str(
        (Decimal(value) / Decimal(denominator) * Decimal("100")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    )


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    crosswalk = _load(ROOT / contract["crosswalk_fixture"])
    audit = _load(ROOT / contract["audit_fixture"])

    _stop(crosswalk.get("schema") == "TASK215_PLANNING_ACCOUNTING_CROSSWALK_V1", "TASK215_CROSSWALK_SCHEMA")
    _stop(len(crosswalk["rows"]) == 2, "TASK215_CROSSWALK_ROWS")
    by_segment = {row["planning"]["segment_id"]: row for row in crosswalk["rows"]}

    food = by_segment["LOA2026_ACTION_12.306.2001.2720"]
    _stop(food["planning"]["appropriation_brl"] == "28000000.00", "TASK215_FOOD_APPROPRIATION")
    _stop(food["accounting_source_rows"] == 434, "TASK215_FOOD_ROWS")
    _stop(food["accounting_filter"] == {
        "fiscal_year": 2026,
        "function": "EDUCAÇÃO",
        "subfunction": "ALIMENTAÇÃO E NUTRIÇÃO",
        "program_code": "2001",
        "action_code": "2720",
    }, "TASK215_FOOD_FILTER")
    _stop(food["commitment_arithmetic_brl"] == "26225933.51", "TASK215_FOOD_ARITHMETIC")
    _stop(food["source_stage_amounts_brl"]["Valor Liquidado"] == "14756899.27", "TASK215_FOOD_LIQ")
    _stop(food["source_stage_amounts_brl"]["Valor Pago"] == "14756899.27", "TASK215_FOOD_PAID")
    _stop(_pct(food["commitment_arithmetic_brl"], food["planning"]["appropriation_brl"]) == "93.66", "TASK215_FOOD_PCT_COMMIT")
    _stop(_pct(food["source_stage_amounts_brl"]["Valor Liquidado"], food["planning"]["appropriation_brl"]) == "52.70", "TASK215_FOOD_PCT_LIQ")
    _stop(_pct(food["source_stage_amounts_brl"]["Valor Pago"], food["planning"]["appropriation_brl"]) == "52.70", "TASK215_FOOD_PCT_PAID")

    transport = by_segment["LOA2026_ACTION_12.362.2001.2690"]
    _stop(transport["planning"]["appropriation_brl"] == "6152000.00", "TASK215_TRANS_APPROPRIATION")
    _stop(transport["accounting_action_unrestricted_rows"] == 78, "TASK215_TRANS_UNRESTRICTED_ROWS")
    _stop(sum(transport["accounting_subfunction_row_counts"].values()) == 78, "TASK215_TRANS_SUBFUNCTION_SUM")
    _stop(transport["accounting_subfunction_row_counts"] == {
        "ENSINO FUNDAMENTAL": 39,
        "EDUCAÇÃO INFANTIL": 19,
        "ENSINO MÉDIO": 20,
    }, "TASK215_TRANS_SUBFUNCTION_COUNTS")
    _stop(transport["accounting_source_rows"] == 20, "TASK215_TRANS_SCOPED_ROWS")
    _stop(transport["accounting_filter"] == {
        "fiscal_year": 2026,
        "function": "EDUCAÇÃO",
        "subfunction": "ENSINO MÉDIO",
        "program_code": "2001",
        "action_code": "2690",
    }, "TASK215_TRANS_FILTER")
    _stop(transport["subfunction_restriction_required"] is True, "TASK215_TRANS_SCOPE_REQUIRED")
    _stop(transport["commitment_arithmetic_brl"] == "2393081.04", "TASK215_TRANS_ARITHMETIC")
    _stop(transport["source_stage_amounts_brl"]["Valor Liquidado"] == "209450.16", "TASK215_TRANS_LIQ")
    _stop(transport["source_stage_amounts_brl"]["Valor Pago"] == "209450.16", "TASK215_TRANS_PAID")
    _stop(_pct(transport["commitment_arithmetic_brl"], transport["planning"]["appropriation_brl"]) == "38.90", "TASK215_TRANS_PCT_COMMIT")
    _stop(_pct(transport["source_stage_amounts_brl"]["Valor Liquidado"], transport["planning"]["appropriation_brl"]) == "3.40", "TASK215_TRANS_PCT_LIQ")
    _stop(_pct(transport["source_stage_amounts_brl"]["Valor Pago"], transport["planning"]["appropriation_brl"]) == "3.40", "TASK215_TRANS_PCT_PAID")

    mappings = {
        (row.get("function_code"), row.get("function_label"), row.get("subfunction_code"), row.get("subfunction_label"))
        for row in contract["official_functional_classification"]["mapping"]
    }
    _stop(("12", "EDUCAÇÃO", None, None) in mappings, "TASK215_FUNCTION_12")
    _stop((None, None, "306", "ALIMENTAÇÃO E NUTRIÇÃO") in mappings, "TASK215_SUBFUNCTION_306")
    _stop((None, None, "362", "ENSINO MÉDIO") in mappings, "TASK215_SUBFUNCTION_362")

    _stop(audit.get("schema") == "TASK215_REMAINING_IDENTITY_AUDIT_V1", "TASK215_AUDIT_SCHEMA")
    _stop(audit["jom"]["source_row_count"] == 303, "TASK215_JOM_ROWS")
    _stop(audit["jom"]["procurement_shaped_event_count"] == 138, "TASK215_PROC_ROWS")
    _stop(audit["jom"]["procurement_with_structured_cnpj"] == 46, "TASK215_PROC_CNPJ")
    _stop(audit["jom"]["structured_cnpj_overlap_with_tce_supplier_identity_count"] == 31, "TASK215_PROC_OVERLAP")
    _stop(audit["jom"]["event_level_procurement_identity_proven"] is False, "TASK215_PROC_EVENT_ID")
    _stop(audit["infrastructure"]["exact_named_school_identity_proven_count"] == 0, "TASK215_INFRA_SCHOOL_ID")

    return {
        "schema": "TASK215_PROVEN_CROSS_PRODUCT_CROSSWALK_VALIDATION_V1",
        "status": "PASS",
        "promoted_question_count": 1,
        "retained_semantic_blocker_count": 5,
        "planning_accounting_crosswalk_rows": 2,
        "procurement_shaped_jom_events": 138,
        "procurement_cnpj_overlap_suppliers": 31,
        "network": False,
        "drive_read": False,
        "drive_write": False,
        "llm": False,
    }


def _selected_segments(
    context: Mapping[str, Any],
    contract: Mapping[str, Any],
    crosswalk: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    facets = set(context.get("policy_service_facets") or [])
    supported = contract["plan_q3"]["supported_facets"]
    unsupported = sorted(facets - set(supported))
    by_segment = {row["planning"]["segment_id"]: row for row in crosswalk["rows"]}
    if unsupported:
        return [], unsupported
    if not facets:
        return list(crosswalk["rows"]), []
    selected = [by_segment[supported[facet]] for facet in sorted(facets)]
    return selected, []


def _plan_q3(
    *,
    text: str,
    context: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    out = _task209_contract()
    filters = _base_filter_accounting(context)

    if context["school"].get("status") == "RESOLVED":
        return _unsupported(
            text,
            context,
            "PLAN_Q3",
            filters,
            "O crosswalk TASK215 é municipal/programático e não possui identidade escolar estruturada.",
            out,
        )

    period = context["period"]
    if period.get("status") == "RESOLVED":
        if period.get("mode") != "YEAR" or int(period.get("year") or 0) != 2026:
            return _unsupported(
                text,
                context,
                "PLAN_Q3",
                filters,
                "O crosswalk materializado liga a LOA 2026 à execução TCE observada Jan-Jul/2026; nenhum outro período é substituído.",
                out,
            )
        filters["PERIOD"]["status"] = "APPLIED"

    crosswalk = _load(ROOT / contract["crosswalk_fixture"])
    selected, unsupported_facets = _selected_segments(context, contract, crosswalk)
    if unsupported_facets:
        if filters["POLICY_SERVICE_FACETS"]["status"] == "PENDING":
            filters["POLICY_SERVICE_FACETS"]["status"] = "APPLIED_TO_ZERO_MATCH_QUERY"
        if filters["GRANULARITY"]["status"] == "PENDING":
            filters["GRANULARITY"]["status"] = "APPLIED"
        return _finalize(
            state="EXPLICIT_CONTEXT_GAP",
            text=text,
            context=context,
            question_id="PLAN_Q3",
            filter_accounting=filters,
            facts=[{
                "kind": "SCOPED_CROSSWALK_FACET_GAP",
                "unsupported_facets": unsupported_facets,
                "supported_facets": sorted(contract["plan_q3"]["supported_facets"]),
                "text": (
                    "A TASK215 possui crosswalk validado apenas para ALIMENTACAO e TRANSPORTE; "
                    "a faceta solicitada não foi aproximada."
                ),
            }],
            time_reference=[],
            comparisons=[],
            provenance=[{
                "product": "TASK215_PLANNING_ACCOUNTING_CROSSWALK",
                "crosswalk_row_count": len(crosswalk["rows"]),
            }],
            cautions=[
                "SCOPED_CROSSWALK_NE_WHOLE_PLAN_COHERENCE",
                "NO_NEAREST_OR_SIMILAR_FACET_SUBSTITUTION",
            ],
            gap_scope="TASK215_SCOPED_PLANNING_ACCOUNTING_CROSSWALK",
            contract=out,
        )

    if filters["POLICY_SERVICE_FACETS"]["status"] == "PENDING":
        filters["POLICY_SERVICE_FACETS"]["status"] = "APPLIED_BY_CROSSWALK_SCOPE"
    if filters["GRANULARITY"]["status"] == "PENDING":
        filters["GRANULARITY"]["status"] = "APPLIED"

    facts: list[dict[str, Any]] = []
    comparisons: list[str] = []
    provenance: list[dict[str, Any]] = []
    for row in selected:
        plan = row["planning"]
        stages = row["source_stage_amounts_brl"]
        facts.append({
            "kind": "SCOPED_PLANNING_EXECUTION_CROSSWALK",
            "crosswalk_id": row["crosswalk_id"],
            "relation_strength": row["relation_strength"],
            "planning_document_id": plan["document_id"],
            "planning_locator": plan["locator"],
            "planning_action_code": plan["action_code"],
            "planning_label": plan["label"],
            "appropriation_brl": plan["appropriation_brl"],
            "planning_funding_sources_brl": plan["funding_sources_brl"],
            "accounting_filter": row["accounting_filter"],
            "accounting_source_rows": row["accounting_source_rows"],
            "source_stage_amounts_brl": stages,
            "commitment_arithmetic_brl": row["commitment_arithmetic_brl"],
            "appropriation_relative_pct": row["appropriation_relative_pct"],
            "accounting_commitment_arithmetic_by_funding_source_brl": row["accounting_commitment_arithmetic_by_funding_source_brl"],
            "transaction_identity_claim": False,
            "whole_plan_coherence_claim": False,
            "text": (
                f"{plan['label']}: LOA 2026 autorizou R$ {plan['appropriation_brl']}; "
                f"no TCE Jan-Jul/2026, a aritmética empenho+reforço-anulação foi R$ {row['commitment_arithmetic_brl']} "
                f"({row['appropriation_relative_pct']['commitment_arithmetic']}% da dotação), "
                f"liquidado R$ {stages['Valor Liquidado']} ({row['appropriation_relative_pct']['liquidated']}%) "
                f"e pago R$ {stages['Valor Pago']} ({row['appropriation_relative_pct']['paid']}%)."
            ),
        })
        comparisons.append(
            f"{plan['label']}: autorização LOA R$ {plan['appropriation_brl']} ↔ "
            f"execução observada Jan-Jul/2026 pelo mesmo recorte funcional/programático."
        )
        provenance.extend([
            {
                "product": "PLANNING_DOCUMENT_INDEX",
                "document_id": plan["document_id"],
                "locator": plan["locator"],
                "source_sha256": contract["planning_source"]["primary_jom_sha256"],
                "evidence_role": "PRIMARY_SUBSTANTIVE",
            },
            {
                "product": "ACCOUNTING_LEDGER",
                "snapshot_id": contract["accounting_source"]["snapshot_id"],
                "content_sha256": contract["accounting_source"]["content_sha256"],
                "source_gzip_sha256": contract["accounting_source"]["gzip_sha256"],
                "exact_filter": row["accounting_filter"],
                "source_row_count": row["accounting_source_rows"],
            },
        ])

    provenance.append({
        "product": "OFFICIAL_FUNCTIONAL_CLASSIFICATION",
        "authority": contract["official_functional_classification"]["authority"],
        "source_url": contract["official_functional_classification"]["source_url"],
        "runtime_network_dependency": False,
    })

    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id="PLAN_Q3",
        filter_accounting=filters,
        facts=facts,
        time_reference=["LOA 2026", "TCE 2026-01..2026-07"],
        comparisons=comparisons,
        provenance=provenance,
        cautions=[
            "SCOPED_TWO_SEGMENTS_NE_WHOLE_PLAN_COHERENCE",
            "LOA_AUTHORIZATION_NE_ACCOUNTING_EXECUTION",
            "AUTHORITATIVE_STRUCTURED_CROSSWALK_NE_TRANSACTION_IDENTITY",
            "COMMITMENT_ARITHMETIC_NE_LEGAL_NET_EXPENDITURE",
            "TCE_JAN_JUL_2026_NE_FULL_YEAR_2026",
            "NO_CAUSAL_OR_NORMATIVE_COHERENCE_JUDGMENT",
        ],
        contract=out,
    )


def execute_contextual_query_v6(
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
    _stop(bool(generated_at), "TASK215_GENERATED_AT")
    _stop(bool(software_version), "TASK215_SOFTWARE_VERSION")

    context = bind_context(
        text,
        reference_date=reference_date,
        context_school_code=context_school_code,
    )
    if context.get("state") != "CONTEXT_BOUND":
        return execute_contextual_query_v5(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )
    qids = list(context.get("selected_question_ids") or [])
    if len(qids) != 1 or qids[0] != "PLAN_Q3":
        return execute_contextual_query_v5(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )
    return _plan_q3(text=text, context=context, contract=contract)


def render_contextual_answer_v6(answer: Mapping[str, Any]) -> dict[str, Any]:
    return render_contextual_answer_markdown(answer)
