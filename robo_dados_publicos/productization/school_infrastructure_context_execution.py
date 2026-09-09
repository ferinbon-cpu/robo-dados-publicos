from __future__ import annotations

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
from robo_dados_publicos.productization.proven_cross_product_execution import (
    execute_contextual_query_v6,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task218_infra_q2_contextual_execution.v1.json"
TASK209_CONTRACT = ROOT / "config/task209_context_aware_execution.v1.json"


class Task218InfrastructureStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task218InfrastructureStop(code)


def _load(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _output_contract() -> dict[str, Any]:
    obj = _load(TASK209_CONTRACT)
    _stop(obj.get("output_schema") == "OBSERVATORY_CONTEXTUAL_ANSWER_V1", "TASK218_OUTPUT_SCHEMA")
    return obj


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = _load(path)
    _stop(obj.get("schema") == "TASK218_INFRA_Q2_CONTEXTUAL_EXECUTION_V1", "TASK218_SCHEMA")
    _stop(obj.get("issue") == 680, "TASK218_ISSUE")
    _stop(
        obj.get("base_main_sha") == "aac5abef7e72233a4667ff570ec9af5ae8c41287",
        "TASK218_BASE",
    )
    _stop(obj.get("mode") == "T0_OFFLINE_CANONICAL_JOM_SCHOOL_INFRASTRUCTURE_CONTEXT_EXECUTION", "TASK218_MODE")
    _stop(obj.get("promoted_questions") == ["INFRA_Q2"], "TASK218_PROMOTED")
    cov = obj["contextual_coverage"]
    _stop(cov == {"canonical_questions_total": 38, "before": 33, "after": 34}, "TASK218_COVERAGE")
    _stop(
        set(obj["retained_semantic_blockers"]) == {"CTRL_Q2", "PROC_Q1", "PROC_Q2", "PROC_Q3"},
        "TASK218_BLOCKERS",
    )
    scope = obj["bounded_jom_scope"]
    _stop(scope["official_discovered_document_count"] == 99, "TASK218_DISCOVERY_COUNT")
    _stop(scope["previously_materialized_august_documents"] == 12, "TASK218_EXISTING_COUNT")
    _stop(scope["new_document_scope"] == 87, "TASK218_NEW_SCOPE")
    _stop(scope["task217d_clean_document_count"] + scope["task217d_uncovered_document_count"] == 87, "TASK218_217D_PARTITION")
    _stop(scope["task217f_recovered_document_count"] + scope["task217g_recovered_document_count"] == scope["task217d_uncovered_document_count"], "TASK218_RECOVERY_PARTITION")
    _stop(scope["remaining_uncovered_document_count"] == 0, "TASK218_ZERO_UNCOVERED")
    _stop(scope["content_scope_complete"] is True, "TASK218_COMPLETE_SCOPE")
    _stop(scope["full_calendar_year_claim"] is False, "TASK218_FULL_YEAR_GUARD")
    events = obj["proven_named_school_events"]
    _stop(len(events) == 1, "TASK218_EVENT_COUNT")
    _stop(events[0]["event_id"] == "JOEV_fab1a3c79f589f7ccc18", "TASK218_EVENT_ID")
    _stop(events[0]["school_code"] == "35295061", "TASK218_SCHOOL_CODE")
    _stop(events[0]["contract_number"] == "42/2026", "TASK218_CONTRACT_NUMBER")
    _stop(events[0]["published_value_brl"] == "71000.00", "TASK218_VALUE")
    _stop(
        obj["execution"]["policy_service_facets_supported"] == ["INFRAESTRUTURA"],
        "TASK218_FACET_SCOPE",
    )
    bounds = obj["claim_boundaries"]
    _stop(all(value is False for value in bounds.values()), "TASK218_CLAIM_BOUNDARIES")
    _stop(all(value is False for value in obj["remote_effects"].values()), "TASK218_REMOTE_EFFECTS")
    return obj


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    e = _load(ROOT / contract["runtime_proofs"]["task217e_config"])
    f2 = _load(ROOT / contract["runtime_proofs"]["task217f2_config"])
    g = _load(ROOT / contract["runtime_proofs"]["task217g_canonical_result"])

    _stop(e.get("schema") == "TASK217E_PARTIAL_REDIGEST_ADJUDICATION_V1", "TASK218_217E_SCHEMA")
    adj = e["manual_deterministic_adjudication"]
    _stop(adj["true_named_school_infrastructure_event_count"] == 1, "TASK218_217E_TRUE")
    _stop(adj["rejected_non_school_homonym_event_count"] == 6, "TASK218_217E_HOMONYMS")
    _stop(adj["true_events"][0]["event_id"] == contract["proven_named_school_events"][0]["event_id"], "TASK218_217E_EVENT")

    _stop(f2.get("schema") == "TASK217F2_RECOVERY_CANONIZATION_V1", "TASK218_217F2_SCHEMA")
    _stop([row["edition"] for row in f2["failures"]] == [7243,7253,7270,7287], "TASK218_217F2_REMAINING")
    _stop(f2["semantic_adjudication"]["physical_school_infrastructure_generic_events_after_guard"] == 0, "TASK218_217F2_ABSTRACT_GUARD")

    _stop(g.get("schema") == "TASK217G_RECOVERY_CANONICAL_RESULT_V1", "TASK218_217G_SCHEMA")
    result = g["result"]
    _stop(result["status"] == "PASS_COMPLETE_4_OVERSIZED_DOCUMENT_RECOVERY", "TASK218_217G_STATUS")
    _stop(result["complete_scope"] is True, "TASK218_217G_COMPLETE")
    _stop(result["validated_download_count"] == 4, "TASK218_217G_DOWNLOADS")
    _stop(result["failure_count"] == 0, "TASK218_217G_FAILURES")
    _stop(result["resolved_exact_school_infrastructure_event_count"] == 0, "TASK218_217G_EXACT")
    _stop(g["artifact"]["embedded_result_sha256"] == "c37e87017acef66634f7cccf60df917d841741bf5f021159c09d8329178447d9", "TASK218_217G_HASH")

    return {
        "schema": "TASK218_INFRA_Q2_CONTEXTUAL_EXECUTION_VALIDATION_V1",
        "status": "PASS",
        "promoted_question": "INFRA_Q2",
        "contextual_paths_before": 33,
        "contextual_paths_after": 34,
        "retained_semantic_blocker_count": 4,
        "bounded_jom_document_count": 99,
        "bounded_jom_content_scope_complete": True,
        "proven_named_school_event_count": 1,
        "network": False,
        "drive_read": False,
        "drive_write": False,
        "llm": False,
    }


def _infra_q2(
    *,
    text: str,
    context: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    out = _output_contract()
    filters = _base_filter_accounting(context)

    period = context["period"]
    if period.get("status") == "RESOLVED":
        if period.get("mode") != "YEAR" or int(period.get("year") or 0) != int(contract["execution"]["supported_year"]):
            return _unsupported(
                text,
                context,
                "INFRA_Q2",
                filters,
                "INFRA_Q2 está materializada somente para o recorte oficial JOM de 2026 até 08/09/2026; nenhum outro período é substituído.",
                out,
            )
        filters["PERIOD"]["status"] = "APPLIED_TO_BOUNDED_YEAR_TO_DATE_SCOPE"

    if filters["POLICY_SERVICE_FACETS"]["status"] == "PENDING":
        requested_facets = set(context.get("policy_service_facets") or [])
        supported_facets = set(contract["execution"]["policy_service_facets_supported"])
        if not requested_facets.issubset(supported_facets):
            return _unsupported(
                text,
                context,
                "INFRA_Q2",
                filters,
                "INFRA_Q2 aceita apenas a faceta intrínseca INFRAESTRUTURA; nenhuma outra faceta é aproximada.",
                out,
            )
        filters["POLICY_SERVICE_FACETS"]["status"] = "APPLIED_INTRINSIC_INFRASTRUCTURE_SCOPE"

    if filters["GRANULARITY"]["status"] == "PENDING":
        filters["GRANULARITY"]["status"] = "APPLIED"

    events = list(contract["proven_named_school_events"])
    school = context["school"]
    if school.get("status") == "RESOLVED":
        filters["SCHOOL"]["status"] = "APPLIED_EXACT_SCHOOL_CODE"
        code = str(school.get("school_code") or "")
        selected = [row for row in events if row["school_code"] == code]
        if not selected:
            return _finalize(
                state="EXPLICIT_CONTEXT_GAP",
                text=text,
                context=context,
                question_id="INFRA_Q2",
                filter_accounting=filters,
                facts=[{
                    "kind": "SCOPED_JOM_SCHOOL_INFRASTRUCTURE_GAP",
                    "school_code": code,
                    "school_name": school.get("school_name"),
                    "scope": "2026-01-01..2026-09-08",
                    "text": (
                        "Nenhum evento estruturado de infraestrutura com identidade escolar exata foi identificado "
                        "para esta escola no corpus JOM materializado de 01/01 a 08/09/2026. "
                        "Isso não prova que nenhuma obra, manutenção ou equipamento tenha existido fora desse registro."
                    ),
                }],
                time_reference=["JOM 2026-01-01..2026-09-08"],
                provenance=[{
                    "product": "TASK218_BOUNDED_JOM_SCHOOL_INFRASTRUCTURE",
                    "official_document_count": contract["bounded_jom_scope"]["official_discovered_document_count"],
                    "content_scope_complete": True,
                    "school_code_filter": code,
                }],
                cautions=[
                    "SCOPED_JOM_ZERO_MATCH_NE_REAL_WORLD_ABSENCE",
                    "JOM_PUBLICATION_NE_PHYSICAL_COMPLETION",
                    "BOUNDED_2026_THROUGH_09_08_NE_FULL_CALENDAR_YEAR",
                ],
                gap_scope="TASK218_BOUNDED_JOM_EXACT_SCHOOL_INFRASTRUCTURE",
                contract=out,
            )
    else:
        selected = events

    facts = []
    provenance = []
    for row in selected:
        facts.append({
            "kind": "PROVEN_NAMED_SCHOOL_INFRASTRUCTURE_EVENT",
            "event_id": row["event_id"],
            "school_code": row["school_code"],
            "school_name": row["school_name"],
            "publication_date": row["publication_date"],
            "edition": row["edition"],
            "page_number": row["page_number"],
            "event_type": row["event_type"],
            "contract_number": row["contract_number"],
            "process_number": row["process_number"],
            "published_value_brl": row["published_value_brl"],
            "claim_semantics": row["claim_semantics"],
            "text": (
                f"{row['school_name']}: o Jornal Oficial publicou o contrato {row['contract_number']} "
                f"(processo {row['process_number']}) para manutenção do reservatório de água da unidade, "
                f"com valor publicado de R$ 71.000,00. A publicação prova a contratação nominal da escola, "
                "não a conclusão física do serviço."
            ),
        })
        provenance.append({
            "product": "JOM_EXACT_NAMED_SCHOOL_INFRASTRUCTURE_EVENT",
            "event_id": row["event_id"],
            "edition": row["edition"],
            "page_number": row["page_number"],
            "publication_date": row["publication_date"],
            "source_sha256": row["source_sha256"],
            "school_code": row["school_code"],
        })

    provenance.extend([
        {
            "product": "TASK217C_OFFICIAL_JOM_DISCOVERY",
            "document_count": contract["bounded_jom_scope"]["official_discovered_document_count"],
            "result_sha256": contract["runtime_proofs"]["task217c_discovery_result_sha256"],
        },
        {
            "product": "TASK217G_FINAL_SCOPE_CLOSURE",
            "target_document_count": 4,
            "validated_document_count": 4,
            "embedded_result_sha256": "c37e87017acef66634f7cccf60df917d841741bf5f021159c09d8329178447d9",
        },
    ])

    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id="INFRA_Q2",
        filter_accounting=filters,
        facts=facts,
        time_reference=["JOM 2026-01-01..2026-09-08"],
        comparisons=[],
        provenance=provenance,
        cautions=[
            "JOM_PUBLICATION_NE_PHYSICAL_COMPLETION",
            "CONTRACT_NE_COMPLETED_WORK",
            "PROVEN_NAMED_SCHOOL_SET_NE_ALL_REAL_WORLD_INFRASTRUCTURE",
            "NO_NAMED_EVENT_NE_NO_REAL_WORLD_WORK",
            "BOUNDED_2026_THROUGH_09_08_NE_FULL_CALENDAR_YEAR",
            "NO_FUZZY_SCHOOL_IDENTITY",
        ],
        contract=out,
    )


def execute_contextual_query_v7(
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
    _stop(bool(generated_at), "TASK218_GENERATED_AT")
    _stop(bool(software_version), "TASK218_SOFTWARE_VERSION")

    context = bind_context(
        text,
        reference_date=reference_date,
        context_school_code=context_school_code,
    )
    if context.get("state") != "CONTEXT_BOUND":
        return execute_contextual_query_v6(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )
    qids = list(context.get("selected_question_ids") or [])
    if len(qids) != 1 or qids[0] != "INFRA_Q2":
        return execute_contextual_query_v6(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )
    return _infra_q2(text=text, context=context, contract=contract)


def render_contextual_answer_v7(answer: Mapping[str, Any]) -> dict[str, Any]:
    return render_contextual_answer_markdown(answer)
