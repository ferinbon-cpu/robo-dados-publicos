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
from robo_dados_publicos.productization.school_infrastructure_context_execution import (
    execute_contextual_query_v7,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task219aa_tda_strong_procurement_bridge.v1.json"
TASK209_CONTRACT = ROOT / "config/task209_context_aware_execution.v1.json"


class Task219AAStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task219AAStop(code)


def _load(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _output_contract() -> dict[str, Any]:
    obj = _load(TASK209_CONTRACT)
    _stop(obj.get("output_schema") == "OBSERVATORY_CONTEXTUAL_ANSWER_V1", "TASK219AA_OUTPUT_SCHEMA")
    return obj


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = _load(path)
    _stop(obj.get("schema") == "TASK219AA_TDA_STRONG_PROCUREMENT_BRIDGE_V1", "TASK219AA_SCHEMA")
    _stop(obj.get("issue") == 744, "TASK219AA_ISSUE")
    _stop(obj.get("parent_issue") == 691, "TASK219AA_PARENT")
    _stop(
        obj.get("base_main_sha") == "beeb45082b41828a84d0858bc43e606856934260",
        "TASK219AA_BASE",
    )
    _stop(
        obj.get("mode") == "T0_OFFLINE_OPERATOR_PROVIDED_OFFICIAL_TDA_CANONIZATION_AND_CTRL_Q2_EXECUTION",
        "TASK219AA_MODE",
    )
    _stop(obj.get("upstream_executor") == "TASK218_CONTEXTUAL_EXECUTION_V7", "TASK219AA_UPSTREAM")
    _stop(obj.get("promoted_questions") == ["CTRL_Q2"], "TASK219AA_PROMOTED")
    _stop(
        obj.get("contextual_coverage") == {
            "canonical_questions_total": 38,
            "before": 34,
            "after": 35,
        },
        "TASK219AA_COVERAGE",
    )
    _stop(
        set(obj["retained_semantic_blockers"]) == {"PROC_Q1", "PROC_Q2", "PROC_Q3"},
        "TASK219AA_RETAINED_BLOCKERS",
    )
    identity = obj["identity_policy"]
    _stop(identity["strong_edge"] == "EXACT_TYPED_MUNICIPAL_PROCUREMENT_IDENTIFIER_E00010_2026", "TASK219AA_STRONG_EDGE")
    _stop(identity["tda_typed_procurement_identifier"] == "E00010/2026", "TASK219AA_PROC_KEY")
    _stop(identity["contract_document_identifier"] == "45/2026", "TASK219AA_CONTRACT_ID")
    _stop(identity["administrative_process_identifier"] == "902.281/2025", "TASK219AA_PROCESS_ID")
    _stop(identity["legal_bidding_identifier"] == "10/2026", "TASK219AA_BIDDING_ID")
    _stop(identity["tda_commitment_identifier"] == "03286-01", "TASK219AA_COMMITMENT_ID")
    for key in (
        "supplier_cnpj_is_identity_edge",
        "amount_is_identity_edge",
        "date_is_identity_edge",
        "object_text_is_identity_edge",
        "semantic_similarity_is_identity_edge",
    ):
        _stop(identity[key] is False, f"TASK219AA_WEAK_EDGE_{key}")
    _stop(all(v is False for v in obj["claim_boundaries"].values()), "TASK219AA_BOUNDARIES")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK219AA_REMOTE")
    return obj


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    evidence = _load(ROOT / contract["evidence_fixture"])
    _stop(
        evidence.get("schema") == "TASK219AA_TDA_STRONG_PROCUREMENT_BRIDGE_CANONIZATION_V1",
        "TASK219AA_EVIDENCE_SCHEMA",
    )
    _stop(evidence.get("status") == "PASS_STRONG_MUNICIPAL_CONTRACT_TO_COMMITMENT_IDENTITY", "TASK219AA_EVIDENCE_STATUS")
    _stop(evidence["identity_graph"]["strong_contract_to_commitment_identity_proven"] is True, "TASK219AA_IDENTITY_NOT_PROVEN")
    _stop(evidence["identity_graph"]["weak_join_used"] is False, "TASK219AA_WEAK_JOIN")

    edges = evidence["identity_graph"]["edges"]
    process_edges = [row for row in edges if row.get("strength") == "PROCUREMENT_PROCESS_IDENTITY"]
    _stop(len(process_edges) == 1, "TASK219AA_PROCESS_EDGE_COUNT")
    _stop(process_edges[0].get("keys") == ["E00010/2026"], "TASK219AA_PROCESS_EDGE_KEY")

    artifacts = {row["kind"]: row for row in evidence["operator_artifacts"]}
    pdf = artifacts["OFFICIAL_TDA_CONTRACT_DOCUMENT_PDF"]
    _stop(pdf["sha256"] == "1c202a188bd3a2a6dc0babc0d29e8c56594462f80b1e64df2c551b5b3be7f5a3", "TASK219AA_PDF_HASH")
    _stop(pdf["bounded_facts"]["contract_number"] == "45/2026", "TASK219AA_PDF_CONTRACT")
    _stop(pdf["bounded_facts"]["administrative_process"] == "902.281/2025", "TASK219AA_PDF_PROCESS")
    _stop(pdf["bounded_facts"]["bidding_number"] == "10/2026", "TASK219AA_PDF_BIDDING")
    _stop(pdf["bounded_facts"]["contract_total_brl"] == "210000.00", "TASK219AA_PDF_VALUE")

    export = artifacts["OFFICIAL_TDA_EMPENHADO_XLSX_EXPORT"]
    _stop(export["sha256"] == "08c10cb019f93ec408b4b8d30afa5474594a13a36d030e988a1503007c175735", "TASK219AA_XLSX_HASH")
    _stop(export["row_count"] == 1, "TASK219AA_XLSX_ROWS")
    row = export["bounded_row"]
    _stop(row["procurement_process_typed"] == "E00010/2026", "TASK219AA_XLSX_PROC_KEY")
    _stop(row["commitment_number"] == "03286-01", "TASK219AA_XLSX_COMMITMENT")
    _stop(row["committed_original_brl"] == "174999.99", "TASK219AA_XLSX_COMMITTED")
    _stop(row["processed_brl"] == "35000.00", "TASK219AA_XLSX_PROCESSED")
    _stop(row["paid_brl"] == "35000.00", "TASK219AA_XLSX_PAID")

    current = evidence["current_execution"]
    _stop(current["contracted_brl"] == "210000.00", "TASK219AA_CURRENT_CONTRACTED")
    _stop(current["committed_brl"] == "174999.99", "TASK219AA_CURRENT_COMMITTED")
    _stop(current["processed_brl"] == "35000.00", "TASK219AA_CURRENT_PROCESSED")
    _stop(current["paid_brl"] == "35000.00", "TASK219AA_CURRENT_PAID")
    _stop(current["payment_document_count_observed"] == 2, "TASK219AA_PAYMENT_DOCUMENTS")

    hist = evidence["historical_tcesp_reconciliation"]
    _stop(hist["paid_brl"] == "17500.00", "TASK219AA_TCESP_HISTORICAL_PAID")
    _stop(hist["source_scope"] == "Jan-Jul 2026", "TASK219AA_TCESP_SCOPE")
    _stop(hist["exact_tda_to_tcesp_commitment_format_identity_claim"] is False, "TASK219AA_TCESP_FORMAT_GUARD")

    _stop(evidence["promotion"]["question_id"] == "CTRL_Q2", "TASK219AA_PROMOTION_QID")
    _stop(evidence["promotion"]["contextual_paths_after"] == 35, "TASK219AA_PROMOTION_COVERAGE")
    _stop(evidence["not_promoted"]["question_ids"] == ["PROC_Q1", "PROC_Q2", "PROC_Q3"], "TASK219AA_NOT_PROMOTED")
    _stop(all(v is False for v in evidence["claim_boundaries"].values()), "TASK219AA_EVIDENCE_BOUNDARIES")
    _stop(all(v is False for v in evidence["remote_effects"].values()), "TASK219AA_EVIDENCE_REMOTE")

    return {
        "schema": "TASK219AA_TDA_STRONG_PROCUREMENT_BRIDGE_VALIDATION_V1",
        "status": "PASS",
        "promoted_question": "CTRL_Q2",
        "contextual_paths_before": 34,
        "contextual_paths_after": 35,
        "retained_semantic_blockers": 3,
        "strong_contract_to_commitment_identity_proven": True,
        "weak_join_used": False,
        "network": False,
        "drive_read": False,
        "drive_write": False,
        "llm": False,
    }


def _ctrl_q2(
    *,
    text: str,
    context: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    out = _output_contract()
    filters = _base_filter_accounting(context)

    if context["school"].get("status") == "RESOLVED":
        return _unsupported(
            text,
            context,
            "CTRL_Q2",
            filters,
            "A cadeia de corroboração TASK219AA é municipal/contratual e não possui identidade escolar estruturada.",
            out,
        )

    period = context["period"]
    if period.get("status") == "RESOLVED":
        if period.get("mode") != "YEAR" or int(period.get("year") or 0) != 2026:
            return _unsupported(
                text,
                context,
                "CTRL_Q2",
                filters,
                "A cadeia forte materializada nesta tarefa é de 2026; nenhum outro período é substituído.",
                out,
            )
        filters["PERIOD"]["status"] = "APPLIED"

    if filters["POLICY_SERVICE_FACETS"]["status"] == "PENDING":
        return _unsupported(
            text,
            context,
            "CTRL_Q2",
            filters,
            "A cadeia TASK219AA não generaliza a corroboração para uma faceta temática solicitada.",
            out,
        )
    if filters["GRANULARITY"]["status"] == "PENDING":
        filters["GRANULARITY"]["status"] = "APPLIED_MUNICIPAL_CONTRACT_CHAIN"

    evidence = _load(ROOT / contract["evidence_fixture"])
    current = evidence["current_execution"]
    hist = evidence["historical_tcesp_reconciliation"]

    facts = [
        {
            "kind": "PROVEN_CROSS_SOURCE_CONTROL_CORROBORATION",
            "relation_strength": "EXACT_TYPED_PROCUREMENT_PROCESS_IDENTITY",
            "contract_number": "45/2026",
            "administrative_process": "902.281/2025",
            "legal_bidding_identifier": "10/2026",
            "tda_procurement_process_identifier": "E00010/2026",
            "tda_commitment_number": current["commitment_number_tda"],
            "supplier_name": "Med Doctor Acessórios Ltda",
            "supplier_cnpj": "37457979000131",
            "object": "Locação de sistema de endoscopia",
            "contracted_brl": current["contracted_brl"],
            "committed_brl": current["committed_brl"],
            "processed_brl": current["processed_brl"],
            "paid_brl": current["paid_brl"],
            "text": (
                "No caso materializado, o Jornal/contrato oficial identifica Contrato 45/2026, Processo 902.281/2025 "
                "e Pregão Eletrônico 10/2026. O módulo Contratos do TDA representa esse pregão como E00010/2026; "
                "a extração oficial de Empenhado usa exatamente E00010/2026 para o empenho 03286-01. "
                "Nesse empenho o TDA registra R$ 174.999,99 empenhados e R$ 35.000,00 processados/pagos."
            ),
        },
        {
            "kind": "HISTORICAL_TCESP_INDEPENDENT_CORROBORATION_WITH_FORMAT_GUARD",
            "source_scope": hist["source_scope"],
            "tcesp_commitment_number": hist["tcesp_commitment_number"],
            "supplier_cnpj": hist["supplier_cnpj"],
            "committed_brl": hist["committed_brl"],
            "liquidated_brl": hist["liquidated_brl"],
            "paid_brl": hist["paid_brl"],
            "exact_tda_to_tcesp_commitment_format_identity_claim": False,
            "text": (
                "O snapshot TCESP Jan-Jul/2026 registra para o mesmo fornecedor e objeto o empenho 3286-2026, "
                "R$ 174.999,99 empenhados e R$ 17.500,00 liquidados/pagos. Ele é mantido como corroboração "
                "contábil histórica independente; esta tarefa não declara equivalência formal entre os formatos "
                "03286-01 e 3286-2026 sem prova adicional."
            ),
        },
    ]

    provenance = [
        {
            "product": "JOM_EVENT_INDEX",
            "event_id": evidence["canonical_jom_seed"]["event_id"],
            "edition": evidence["canonical_jom_seed"]["edition"],
            "publication_date": evidence["canonical_jom_seed"]["publication_date"],
        },
        {
            "product": "OFFICIAL_TDA_CONTRACT_DOCUMENT",
            "sha256": next(row["sha256"] for row in evidence["operator_artifacts"] if row["kind"] == "OFFICIAL_TDA_CONTRACT_DOCUMENT_PDF"),
            "raw_committed": False,
        },
        {
            "product": "OFFICIAL_TDA_EMPENHADO_EXPORT",
            "sha256": next(row["sha256"] for row in evidence["operator_artifacts"] if row["kind"] == "OFFICIAL_TDA_EMPENHADO_XLSX_EXPORT"),
            "raw_committed": False,
        },
        {
            "product": "TDA_CONTRACTS_EXACT_FILTER_OBSERVATION",
            "sha256": next(row["sha256"] for row in evidence["operator_artifacts"] if row["kind"] == "OFFICIAL_TDA_CONTRACTS_UI_EXACT_FILTER_OBSERVATION"),
            "raw_committed": False,
        },
        {
            "product": "TCESP_TASK219H_HISTORICAL_SNAPSHOT",
            "source_scope": hist["source_scope"],
            "upstream_evidence": hist["upstream_evidence"],
        },
    ]

    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id="CTRL_Q2",
        filter_accounting=filters,
        facts=facts,
        time_reference=[
            "Contrato/JOM: março de 2026",
            "TDA: execução observada até pagamento de 25/08/2026",
            "TCESP histórico: Jan-Jul/2026",
        ],
        comparisons=[
            "R$ 210.000,00 contratado; R$ 174.999,99 empenhado; R$ 35.000,00 processado/pago no TDA atual observado.",
            "O TCESP histórico Jan-Jul registrava R$ 17.500,00 pagos; não é tratado como conflito com o TDA posterior.",
        ],
        provenance=provenance,
        cautions=[
            "ONE_PROVEN_CHAIN_NE_EXHAUSTIVE_MUNICIPAL_PROCUREMENT",
            "EXACT_TYPED_PROCUREMENT_KEY_CREATES_IDENTITY_NOT_CNPJ_AMOUNT_DATE_OBJECT",
            "CONTRACTED_NE_COMMITTED_NE_PROCESSED_NE_PAID",
            "PAID_NE_CONTRACT_COMPLETED",
            "NO_CONTRACT_EXECUTION_PERCENTAGE_INFERRED",
            "TDA_COMMITMENT_FORMAT_NE_TCESP_COMMITMENT_FORMAT_WITHOUT_ADDITIONAL_PROOF",
            "CURRENT_TDA_NE_HISTORICAL_TCESP_SNAPSHOT",
        ],
        gap_scope=None,
        contract=out,
    )


def execute_contextual_query_v8(
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
    _stop(bool(generated_at), "TASK219AA_GENERATED_AT")
    _stop(bool(software_version), "TASK219AA_SOFTWARE_VERSION")

    context = bind_context(
        text,
        reference_date=reference_date,
        context_school_code=context_school_code,
    )
    if context.get("state") != "CONTEXT_BOUND":
        return execute_contextual_query_v7(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )
    qids = list(context.get("selected_question_ids") or [])
    if len(qids) != 1 or qids[0] != "CTRL_Q2":
        return execute_contextual_query_v7(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )
    return _ctrl_q2(text=text, context=context, contract=contract)


def render_contextual_answer_v8(answer: Mapping[str, Any]) -> dict[str, Any]:
    return render_contextual_answer_markdown(answer)
