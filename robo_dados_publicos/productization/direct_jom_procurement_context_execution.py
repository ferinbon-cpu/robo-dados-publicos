from __future__ import annotations

import hashlib
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
from robo_dados_publicos.productization.tda_control_corroboration_execution import (
    execute_contextual_query_v8,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task220_direct_jom_procurement_execution.v2.json"


class Task220Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task220Stop(code)


def _load(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = _load(path)
    _stop(obj.get("schema") == "TASK220_DIRECT_JOM_PROCUREMENT_EXECUTION_V2", "TASK220_SCHEMA")
    _stop(obj.get("task") == "TASK_220" and obj.get("issue") == 697, "TASK220_TASK")
    _stop(
        obj.get("base_main_sha") == "f53deb08789384a2f64f1ec856714a3189595882",
        "TASK220_BASE",
    )
    _stop(obj.get("upstream_executor") == "TASK219AA_CONTEXTUAL_EXECUTION_V8", "TASK220_UPSTREAM")
    _stop(obj.get("output_schema") == "OBSERVATORY_CONTEXTUAL_ANSWER_V1", "TASK220_OUTPUT")
    _stop(obj.get("promoted_questions") == ["PROC_Q1", "PROC_Q2", "PROC_Q3"], "TASK220_PROMOTED")
    _stop(
        obj.get("contextual_coverage") == {
            "canonical_questions_total": 38,
            "before": 35,
            "after": 38,
            "remaining_semantic_blockers": [],
        },
        "TASK220_COVERAGE",
    )
    scope = obj["bounded_jom_scope"]
    _stop(scope["start_date"] == "2026-01-01", "TASK220_SCOPE_START")
    _stop(scope["observed_through_date"] == "2026-09-08", "TASK220_SCOPE_END")
    _stop(scope["official_document_count"] == 99, "TASK220_SCOPE_DOCS")
    _stop(scope["content_processing_scope_complete"] is True, "TASK220_SCOPE_COMPLETE")
    _stop(scope["full_calendar_year_claim"] is False, "TASK220_SCOPE_YEAR_GUARD")
    _stop(scope["exhaustive_purchase_inventory_claim"] is False, "TASK220_SCOPE_INVENTORY_GUARD")
    counts = obj["corpus_counts"]
    _stop(counts["legacy_validated_event_rows"] == 303, "TASK220_LEGACY_ROWS")
    _stop(counts["new_sanitized_event_rows"] == 2408, "TASK220_NEW_ROWS")
    _stop(counts["combined_parsed_event_rows"] == 2711, "TASK220_COMBINED_ROWS")
    _stop(counts["legacy_procurement_shaped_rows"] == 138, "TASK220_LEGACY_PROC")
    _stop(counts["new_procurement_shaped_rows"] == 940, "TASK220_NEW_PROC")
    _stop(counts["combined_procurement_shaped_rows"] == 1078, "TASK220_COMBINED_PROC")
    _stop(
        counts["row_count_semantics"] == "PUBLICATION_EVENT_ROWS_NE_UNIQUE_PURCHASES_OR_CONTRACTS",
        "TASK220_ROW_SEMANTICS",
    )
    _stop(obj["context_policy"]["supported_year"] == 2026, "TASK220_YEAR")
    _stop(obj["context_policy"]["school_scope_supported"] is False, "TASK220_SCHOOL_GUARD")
    _stop(obj["context_policy"]["arbitrary_policy_service_facet_supported"] is False, "TASK220_FACET_GUARD")
    _stop(all(value is False for value in obj["hard_boundaries"].values()), "TASK220_BOUNDARIES")
    _stop(all(value is False for value in obj["remote_effects"].values()), "TASK220_REMOTE")
    return obj


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    sources = contract["source_evidence"]
    evidence = _load(ROOT / sources["canonical_fixture"])
    _stop(
        evidence.get("schema") == "TASK220_DIRECT_JOM_PROCUREMENT_EXECUTION_EVIDENCE_V2",
        "TASK220_EVIDENCE_SCHEMA",
    )
    _stop(
        evidence.get("status") == "PASS_BOUNDED_DIRECT_JOM_PROCUREMENT_EXECUTION_EVIDENCE",
        "TASK220_EVIDENCE_STATUS",
    )

    scope = evidence["scope"]
    _stop(scope["official_document_count"] == 99, "TASK220_EVIDENCE_DOCS")
    _stop(scope["content_processing_scope_complete"] is True, "TASK220_EVIDENCE_COMPLETE")
    _stop(scope["full_calendar_year_claim"] is False, "TASK220_EVIDENCE_YEAR_GUARD")
    _stop(scope["exhaustive_purchase_inventory_claim"] is False, "TASK220_EVIDENCE_INVENTORY_GUARD")

    legacy_path = ROOT / sources["task184_legacy_events"]
    _stop(
        _sha256(legacy_path) == "1afd82853402d2ea6db7ad28fb6564de4a4ab28570c16ea9c7e4e0366cb5c733",
        "TASK220_LEGACY_SHA",
    )
    legacy_rows = _load_jsonl(legacy_path)
    _stop(len(legacy_rows) == 303, "TASK220_LEGACY_ROW_COUNT")
    legacy_by_id = {row["event_id"]: row for row in legacy_rows}
    _stop(len(legacy_by_id) == 303, "TASK220_LEGACY_EVENT_ID_UNIQUE")

    q1 = {row["event_id"]: row for row in evidence["proc_q1_direct_object_examples"]}
    for event_id in (
        "JOEV_019179608e26b6ca746a",
        "JOEV_05ed3926ffe8382b2afe",
        "JOEV_07357f03181c3f43831c",
    ):
        _stop(event_id in legacy_by_id and event_id in q1, f"TASK220_Q1_LEGACY_{event_id}")
        source_row = legacy_by_id[event_id]
        material = q1[event_id]
        _stop(source_row.get("event_type") == material.get("event_type"), f"TASK220_Q1_TYPE_{event_id}")
        _stop(source_row.get("object_text") == material.get("object_text"), f"TASK220_Q1_OBJECT_{event_id}")
        _stop(source_row.get("edition") == material.get("edition"), f"TASK220_Q1_EDITION_{event_id}")
        _stop(source_row.get("publication_date") == material.get("publication_date"), f"TASK220_Q1_DATE_{event_id}")

    bundle = _load(ROOT / sources["task184_bundle"])
    _stop(bundle["jom"]["validated_rows"] == 303, "TASK220_BUNDLE_ROWS")
    _stop(bundle["jom"]["event_types"]["TERMO_ADITIVO_CONTRATO"] == 5, "TASK220_BUNDLE_ADDITIVES")
    _stop(bundle["jom"]["semantic_observations"]["procurement_contract_layer"] == 76, "TASK220_BUNDLE_PROC_LAYER")

    audit = _load(ROOT / sources["task215_identity_audit"])
    _stop(audit["jom"]["source_row_count"] == 303, "TASK220_AUDIT_ROWS")
    _stop(audit["jom"]["procurement_shaped_event_count"] == 138, "TASK220_AUDIT_PROC")
    _stop(audit["procurement"]["cnpj_alone_can_join_specific_contract"] is False, "TASK220_AUDIT_CNPJ_GUARD")

    full = _load(ROOT / sources["task219b_full_scope"])
    runtime = full["general_event_runtime_counts"]
    _stop(runtime["new_event_count"] == 2408, "TASK220_FULL_NEW_ROWS")
    _stop(runtime["procurement_shaped_event_count"] == 940, "TASK220_FULL_NEW_PROC")
    _stop(runtime["failure_count"] == 0, "TASK220_FULL_FAILURES")
    _stop(full["source_runtime"]["complete_87_of_87"] is True, "TASK220_FULL_87")
    _stop(
        full["source_runtime"]["events_sha256"]
        == "5ca4bf1411f6b8bfa6ad2b8fdede9937f495458963439fa579d40caa7d988c5b",
        "TASK220_FULL_EVENTS_SHA",
    )

    task218 = _load(ROOT / sources["task218_named_school_contract"])
    infra = task218["proven_named_school_events"]
    _stop(len(infra) == 1 and infra[0]["event_id"] == "JOEV_fab1a3c79f589f7ccc18", "TASK220_INFRA_EVENT")
    _stop(infra[0]["object_text"] if "object_text" in infra[0] else infra[0]["evidence"], "TASK220_INFRA_OBJECT")
    _stop(q1["JOEV_fab1a3c79f589f7ccc18"]["contract_number"] == infra[0]["contract_number"], "TASK220_INFRA_CONTRACT")
    _stop(q1["JOEV_fab1a3c79f589f7ccc18"]["process_number"] == infra[0]["process_number"], "TASK220_INFRA_PROCESS")
    _stop(q1["JOEV_fab1a3c79f589f7ccc18"]["published_value_brl"] == infra[0]["published_value_brl"], "TASK220_INFRA_VALUE")

    task219f = _load(ROOT / sources["task219f_contract45_jom"])
    seed = task219f["recovered_primary_jom_seed"]
    contract45 = q1["JOEV_083e522d4145e4d27580"]
    _stop(seed["event_id"] == contract45["event_id"], "TASK220_45_EVENT")
    _stop(seed["recovered_contract_number"] == contract45["contract_number"] == "45/2026", "TASK220_45_CONTRACT")
    _stop(seed["process_number"] == contract45["process_number"] == "902.281/2025", "TASK220_45_PROCESS")
    _stop(seed["bidding_number"] == contract45["bidding_number"] == "10/2026", "TASK220_45_BIDDING")
    _stop(seed["contractor"] == contract45["supplier_name"], "TASK220_45_SUPPLIER")
    _stop(seed["cnpj"] == contract45["supplier_cnpj"], "TASK220_45_CNPJ")
    _stop(seed["value_brl"] == contract45["published_value_brl"] == "210000.00", "TASK220_45_VALUE")

    q2 = evidence["proc_q2_same_publication_supplier_value_term"]
    _stop(len(q2) == 1, "TASK220_Q2_ROWS")
    q2row = q2[0]
    _stop(q2row["event_id"] == seed["event_id"], "TASK220_Q2_EVENT")
    _stop(q2row["supplier_name"] == seed["contractor"], "TASK220_Q2_SUPPLIER")
    _stop(q2row["published_value_brl"] == seed["value_brl"], "TASK220_Q2_VALUE")
    _stop(q2row["published_term_text"] == "12 meses contados a partir da data indicada na ordem de serviço", "TASK220_Q2_TERM")
    task219aa = _load(ROOT / sources["task219aa_operator_contract_bridge"])
    pdf = next(
        row for row in task219aa["operator_artifacts"]
        if row["kind"] == "OFFICIAL_TDA_CONTRACT_DOCUMENT_PDF"
    )
    _stop(pdf["sha256"] == q2row["operator_pdf_sha256"], "TASK220_Q2_PDF_HASH")
    _stop(pdf["bounded_facts"]["jom_edition"] == q2row["edition"], "TASK220_Q2_JOM_EDITION")
    _stop(pdf["bounded_facts"]["jom_publication_date"] == q2row["publication_date"], "TASK220_Q2_JOM_DATE")
    _stop(q2row["same_publication_fields_present"] is True, "TASK220_Q2_FIELDS")

    q3 = evidence["proc_q3_direct_change_or_new_tender"]
    _stop(q3["proven_change_signal"]["legacy_validated_count"] == 5, "TASK220_Q3_ADDITIVES")
    tender = q3["proven_new_tender_example"]
    tender_source = legacy_by_id[tender["event_id"]]
    _stop(tender_source["event_type"] == tender["event_type"] == "EDITAL", "TASK220_Q3_TENDER_TYPE")
    _stop(tender_source["object_text"] == tender["object_text"], "TASK220_Q3_TENDER_OBJECT")
    _stop(tender_source["bidding_number"] == tender["bidding_number"] == "326/2026", "TASK220_Q3_TENDER_ID")
    _stop(q3["absence_inference_allowed"] is False, "TASK220_Q3_ABSENCE_GUARD")
    _stop(q3["cross_event_relationship_inference_allowed"] is False, "TASK220_Q3_RELATION_GUARD")

    promotion = evidence["promotion"]
    _stop(promotion["questions"] == ["PROC_Q1", "PROC_Q2", "PROC_Q3"], "TASK220_PROMOTION_QIDS")
    _stop(promotion["before"] == 35 and promotion["after"] == 38, "TASK220_PROMOTION_COUNTS")
    _stop(promotion["remaining_semantic_blockers"] == [], "TASK220_PROMOTION_BLOCKERS")
    _stop(all(value is False for value in evidence["claim_boundaries"].values()), "TASK220_EVIDENCE_BOUNDARIES")
    _stop(all(value is False for value in evidence["remote_effects"].values()), "TASK220_EVIDENCE_REMOTE")

    return {
        "schema": "TASK220_DIRECT_JOM_PROCUREMENT_EXECUTION_VALIDATION_V2",
        "status": "PASS",
        "promoted_questions": ["PROC_Q1", "PROC_Q2", "PROC_Q3"],
        "contextual_paths_before": 35,
        "contextual_paths_after": 38,
        "remaining_semantic_blockers": [],
        "official_document_count": 99,
        "procurement_shaped_event_rows": 1078,
        "full_calendar_year_claim": False,
        "exhaustive_purchase_inventory_claim": False,
        "network": False,
        "drive_write": False,
        "llm": False,
    }


def _apply_supported_context(
    *,
    text: str,
    context: Mapping[str, Any],
    question_id: str,
    contract: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    filters = _base_filter_accounting(context)
    if context["school"].get("status") == "RESOLVED":
        return filters, _unsupported(
            text,
            context,
            question_id,
            filters,
            "A materialização TASK220 é municipal e não atribui contratos/licitações a uma escola sem identidade escolar explícita para esta pergunta.",
            contract,
        )

    period = context["period"]
    if period.get("status") == "RESOLVED":
        if period.get("mode") != "YEAR" or int(period.get("year") or 0) != 2026:
            return filters, _unsupported(
                text,
                context,
                question_id,
                filters,
                "TASK220 só materializa o recorte JOM de 2026 observado até 08/09/2026; nenhum outro período é substituído pelo mais próximo.",
                contract,
            )
        filters["PERIOD"]["status"] = "APPLIED_BOUNDED_2026_THROUGH_2026_09_08"

    if filters["POLICY_SERVICE_FACETS"]["status"] == "PENDING":
        return filters, _unsupported(
            text,
            context,
            question_id,
            filters,
            "TASK220 não generaliza os exemplos diretos do JOM para uma faceta temática arbitrária solicitada.",
            contract,
        )
    filters["GRANULARITY"]["status"] = "APPLIED_MUNICIPAL_JOM"
    return filters, None


def _common_provenance(evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "product": "JOM_EVENT_INDEX",
            "scope": "Limeira JOM 2026-01-01..2026-09-08",
            "official_document_count": evidence["scope"]["official_document_count"],
            "parsed_event_rows": evidence["corpus"]["combined"]["parsed_event_rows"],
            "procurement_shaped_event_rows": evidence["corpus"]["combined"]["procurement_shaped_event_rows"],
            "row_semantics": evidence["corpus"]["combined"]["row_semantics"],
        }
    ]


def _proc_q1(
    *,
    text: str,
    context: Mapping[str, Any],
    filters: Mapping[str, Any],
    contract: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    combined = evidence["corpus"]["combined"]
    facts: list[dict[str, Any]] = [
        {
            "kind": "BOUNDED_JOM_PROCUREMENT_PUBLICATION_SCOPE",
            "official_document_count": evidence["scope"]["official_document_count"],
            "parsed_event_rows": combined["parsed_event_rows"],
            "procurement_shaped_event_rows": combined["procurement_shaped_event_rows"],
            "unique_purchase_count_claim": False,
            "exhaustive_object_inventory_claim": False,
            "text": (
                "No recorte oficial processado de 99 edições/documentos do JOM até 08/09/2026, "
                "há 1.078 linhas de eventos com formato de contratação. Essas linhas são publicações, "
                "não 1.078 compras únicas, e o detalhe integral dessas 1.078 linhas não foi reidratado nesta camada."
            ),
        }
    ]
    provenance = _common_provenance(evidence)
    for row in evidence["proc_q1_direct_object_examples"]:
        fact = dict(row)
        fact["kind"] = "DIRECT_JOM_PROCUREMENT_OBJECT_EXAMPLE"
        fact["text"] = f"JOM publicou: {row['object_text']}"
        facts.append(fact)
        provenance.append(
            {
                "product": "JOM_EVENT_INDEX",
                "event_id": row["event_id"],
                "edition": row["edition"],
                "publication_date": row["publication_date"],
                "page_number": row["page_number"],
                "source": row["source"],
            }
        )

    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id="PROC_Q1",
        filter_accounting=filters,
        facts=facts,
        time_reference=["JOM 2026-01-01..2026-09-08"],
        comparisons=[
            "Exemplos diretos incluem mobiliário, materiais odontológicos, reforma do CASM, manutenção de reservatório escolar e locação de sistema de endoscopia."
        ],
        provenance=provenance,
        cautions=[
            "JOM_PUBLICATION_NE_PURCHASE_EXECUTION",
            "PROCUREMENT_EVENT_ROWS_NE_UNIQUE_PURCHASES",
            "BOUNDED_2026_THROUGH_2026_09_08_NE_FULL_CALENDAR_YEAR",
            "DIRECT_EXAMPLES_NE_EXHAUSTIVE_INVENTORY",
            "NO_CROSS_SOURCE_IDENTITY_OR_ACCOUNTING_CLAIM",
        ],
        gap_scope="O detalhe textual integral das 1.078 linhas de eventos de contratação do recorte completo não foi reidratado nesta camada; a resposta usa exemplos diretos preservados e não se apresenta como inventário exaustivo.",
        contract=contract,
    )


def _proc_q2(
    *,
    text: str,
    context: Mapping[str, Any],
    filters: Mapping[str, Any],
    contract: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    row = evidence["proc_q2_same_publication_supplier_value_term"][0]
    facts = [
        {
            "kind": "DIRECT_JOM_SUPPLIER_VALUE_TERM",
            **{key: value for key, value in row.items() if key not in {"term_basis"}},
            "text": (
                "No JOM edição 7210, o Contrato 45/2026 identifica Med Doctor Acessórios Ltda., "
                "valor publicado de R$ 210.000,00 e prazo de 12 meses contados a partir da data indicada "
                "na ordem de serviço."
            ),
        }
    ]
    provenance = _common_provenance(evidence) + [
        {
            "product": "JOM_EVENT_INDEX",
            "event_id": row["event_id"],
            "edition": row["edition"],
            "publication_date": row["publication_date"],
            "page_number": row["page_number"],
            "contract_number": row["contract_number"],
            "process_number": row["process_number"],
        },
        {
            "product": "OFFICIAL_JOM_REPRODUCTION_IN_CONTRACT_DOCUMENT",
            "operator_pdf_sha256": row["operator_pdf_sha256"],
            "raw_committed": False,
            "use": "same-publication term verification only",
        },
    ]
    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id="PROC_Q2",
        filter_accounting=filters,
        facts=facts,
        time_reference=["JOM edição 7210, 27/03/2026", "recorte JOM observado até 08/09/2026"],
        comparisons=[
            "O valor de R$ 210.000,00 é o valor publicado do contrato; esta resposta não o transforma em valor pago, liquidado ou executado."
        ],
        provenance=provenance,
        cautions=[
            "SAME_PUBLICATION_FIELDS_ONLY",
            "PUBLISHED_CONTRACT_VALUE_NE_PAID_AMOUNT",
            "CONTRACT_PUBLICATION_NE_ACCOUNTING_EXECUTION",
            "BOUNDED_EXAMPLE_NE_EXHAUSTIVE_SUPPLIER_INVENTORY",
            "NO_TDA_OR_TCESP_EXECUTION_VALUES_IN_PROC_Q2",
        ],
        gap_scope="A camada prova este caso fornecedor+valor+prazo no mesmo bloco/publicação; não generaliza para todos os fornecedores do recorte sem o detalhe integral reidratado.",
        contract=contract,
    )


def _proc_q3(
    *,
    text: str,
    context: Mapping[str, Any],
    filters: Mapping[str, Any],
    contract: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    q3 = evidence["proc_q3_direct_change_or_new_tender"]
    change = q3["proven_change_signal"]
    tender = q3["proven_new_tender_example"]
    facts = [
        {
            "kind": "DIRECT_JOM_CONTRACT_ADDITIVE_SIGNAL",
            "event_type": change["event_type"],
            "validated_publication_event_count": change["legacy_validated_count"],
            "count_scope": change["scope_of_count"],
            "text": "Sim para aditivos: o corpus detalhado retido contém 5 publicações validadas classificadas como TERMO_ADITIVO_CONTRATO no intervalo 14–29/08/2026.",
        },
        {
            "kind": "DIRECT_JOM_NEW_TENDER_EXAMPLE",
            **{key: value for key, value in tender.items() if key != "claim"},
            "text": (
                "Sim para nova licitação/aviso de contratação: o JOM de 27/08/2026 publicou o Edital/Dispensa 326/2026 "
                "para contratação de empresa para reforma do prédio do CASM."
            ),
        },
        {
            "kind": "APOSTILAMENTO_EVIDENCE_GAP",
            "status": q3["apostilamento_status"],
            "absence_claim": False,
            "text": "A existência ou inexistência de apostilamentos no recorte completo de 99 documentos não foi provada por esta camada detalhada retida; nenhuma ausência é inferida.",
        },
    ]
    provenance = _common_provenance(evidence) + [
        {
            "product": "JOM_EVENT_INDEX",
            "event_type": "TERMO_ADITIVO_CONTRATO",
            "validated_event_count": change["legacy_validated_count"],
            "scope": change["scope_of_count"],
        },
        {
            "product": "JOM_EVENT_INDEX",
            "event_id": tender["event_id"],
            "edition": tender["edition"],
            "publication_date": tender["publication_date"],
            "page_number": tender["page_number"],
        },
    ]
    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id="PROC_Q3",
        filter_accounting=filters,
        facts=facts,
        time_reference=["JOM 2026-01-01..2026-09-08", "contagem detalhada de aditivos: 2026-08-14..2026-08-29"],
        comparisons=[
            "Há evidência direta positiva de termos aditivos e de novo aviso de contratação; apostilamento permanece como lacuna, não como ausência."
        ],
        provenance=provenance,
        cautions=[
            "NO_APOSTILAMENTO_ABSENCE_INFERENCE",
            "NO_CROSS_EVENT_RELATIONSHIP_INFERENCE",
            "NEW_TENDER_PUBLICATION_NE_AWARD_CONTRACT_DELIVERY_PAYMENT",
            "ADDITIVE_PUBLICATION_COUNT_NE_UNIQUE_CONTRACT_CHANGE_COUNT",
            "BOUNDED_2026_THROUGH_2026_09_08_NE_FULL_CALENDAR_YEAR",
        ],
        gap_scope="Apostilamentos no recorte completo não estão detalhadamente demonstrados nem descartados nesta camada retida; relações entre aditivos e contratos também não são inferidas sem referência explícita.",
        contract=contract,
    )


def execute_contextual_query_v9(
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
    _stop(bool(generated_at), "TASK220_GENERATED_AT")
    _stop(bool(software_version), "TASK220_SOFTWARE_VERSION")

    context = bind_context(
        text,
        reference_date=reference_date,
        context_school_code=context_school_code,
    )
    if context.get("state") != "CONTEXT_BOUND":
        return execute_contextual_query_v8(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )
    qids = list(context.get("selected_question_ids") or [])
    if len(qids) != 1 or qids[0] not in {"PROC_Q1", "PROC_Q2", "PROC_Q3"}:
        return execute_contextual_query_v8(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )

    question_id = qids[0]
    filters, unsupported = _apply_supported_context(
        text=text,
        context=context,
        question_id=question_id,
        contract=contract,
    )
    if unsupported is not None:
        return unsupported
    evidence = _load(ROOT / contract["source_evidence"]["canonical_fixture"])

    if question_id == "PROC_Q1":
        return _proc_q1(text=text, context=context, filters=filters, contract=contract, evidence=evidence)
    if question_id == "PROC_Q2":
        return _proc_q2(text=text, context=context, filters=filters, contract=contract, evidence=evidence)
    return _proc_q3(text=text, context=context, filters=filters, contract=contract, evidence=evidence)


def render_contextual_answer_v9(answer: Mapping[str, Any]) -> dict[str, Any]:
    return render_contextual_answer_markdown(answer)


__all__ = [
    "Task220Stop",
    "load_contract",
    "validate_contract",
    "execute_contextual_query_v9",
    "render_contextual_answer_v9",
]
