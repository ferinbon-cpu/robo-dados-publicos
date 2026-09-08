from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from robo_dados_publicos.analytics.current_observatory_answerability import (
    current_answerability_config,
)
from robo_dados_publicos.analytics.current_observatory_bundle import (
    build_current_products,
)
from robo_dados_publicos.productization.bounded_query_projections import (
    build_renderable_packet,
    build_task204_renderability_audit,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task205_human_answer_renderer.v1.json"


class Task205AnswerStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task205AnswerStop(code)


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
    _stop(obj.get("schema") == "TASK205_HUMAN_ANSWER_RENDERER_V1", "TASK205_SCHEMA")
    _stop(obj.get("issue") == 654, "TASK205_ISSUE")
    _stop(
        obj.get("base_main_sha") == "fa6a4d8bd4c04d28986266d1ba2f079b43dbc70a",
        "TASK205_BASE",
    )
    _stop(
        obj.get("mode") == "T0_OFFLINE_DETERMINISTIC_OBSERVATORY_ANSWER_RENDERER",
        "TASK205_MODE",
    )
    _stop(obj.get("input_schema") == "OBSERVATORY_RENDERABLE_PACKET_V1", "TASK205_INPUT")
    _stop(obj.get("output_card_schema") == "OBSERVATORY_HUMAN_ANSWER_CARD_V1", "TASK205_CARD_SCHEMA")
    _stop(obj.get("output_render_schema") == "OBSERVATORY_HUMAN_ANSWER_RENDER_V1", "TASK205_RENDER_SCHEMA")
    _stop(obj.get("expected_question_count") == 38, "TASK205_QUESTION_COUNT")
    required = obj.get("required_answer_parts")
    _stop(
        required
        == [
            "NUMBER_OR_FACT",
            "TIME_REFERENCE",
            "COMPARISON_OR_TREND",
            "PLAIN_LANGUAGE_EXPLANATION",
            "SOURCE_AND_PROVENANCE",
            "CAUTION_OR_LIMIT",
        ],
        "TASK205_ANSWER_PARTS",
    )
    _stop(len(obj.get("domain_explanations") or {}) == 15, "TASK205_DOMAIN_EXPLANATIONS")
    _stop(bool(obj.get("unavailable_marker")), "TASK205_UNAVAILABLE")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK205_REMOTE")
    return obj


def _row_has_any(row: Mapping[str, Any], field: str, values: set[str]) -> bool:
    raw = row.get(field)
    if isinstance(raw, list):
        observed = {str(x) for x in raw}
    elif raw is None:
        observed = set()
    else:
        observed = {str(raw)}
    return bool(observed & values)


def _row_identity(row: Mapping[str, Any]) -> str:
    return _canonical_json(row)


def _matching_metric_rows(
    signal: Mapping[str, Any],
    product: Mapping[str, Any],
) -> list[dict[str, Any]]:
    ids = {str(x) for x in signal.get("ids") or []}
    product_name = str(signal["product"])
    if product_name == "SCHOOL_INDICATOR_SERIES":
        field = "indicator_id"
    elif product_name == "FISCAL_SERIES":
        field = "metric_id"
    else:
        raise Task205AnswerStop("TASK205_UNKNOWN_METRIC_PRODUCT")
    rows = [
        dict(row)
        for row in product.get("rows", [])
        if str(row.get(field) or "") in ids
    ]
    rows.sort(key=_row_identity)
    return rows


def _matching_product_rows(
    signal: Mapping[str, Any],
    product: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = [dict(row) for row in product.get("rows", [])]
    selectors_used = False
    selected: dict[str, dict[str, Any]] = {}

    criteria = dict(signal.get("row_criteria") or {})
    if criteria:
        selectors_used = True
        for row in rows:
            ok = True
            for field, allowed in criteria.items():
                _stop(field.endswith("_any"), "TASK205_CRITERIA_FIELD")
                source_field = field[:-4]
                if not _row_has_any(row, source_field, {str(x) for x in allowed}):
                    ok = False
                    break
            if ok:
                selected[_row_identity(row)] = row

    required_doc_roles = dict(signal.get("required_document_role_pairs") or {})
    if required_doc_roles:
        selectors_used = True
        for row in rows:
            for document_type, roles in required_doc_roles.items():
                if (
                    str(row.get("document_type") or "") == str(document_type)
                    and str(row.get("evidence_role") or "") in {str(x) for x in roles}
                ):
                    selected[_row_identity(row)] = row

    required_family_roles = dict(signal.get("required_source_family_role_pairs") or {})
    if required_family_roles:
        selectors_used = True
        for row in rows:
            for family, roles in required_family_roles.items():
                if (
                    str(row.get("source_family") or "") == str(family)
                    and str(row.get("evidence_role") or "") in {str(x) for x in roles}
                ):
                    selected[_row_identity(row)] = row

    if not selectors_used:
        for row in rows:
            selected[_row_identity(row)] = row

    return [selected[key] for key in sorted(selected)]


def _matching_rows(
    signal: Mapping[str, Any],
    products: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    product_name = str(signal["product"])
    product = products[product_name]
    if signal["kind"] == "METRIC":
        return _matching_metric_rows(signal, product)
    return _matching_product_rows(signal, product)


def _trim_text(value: Any, max_chars: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _format_number(value: Any) -> str:
    if isinstance(value, float):
        text = f"{value:.12f}".rstrip("0").rstrip(".")
        return text or "0"
    return str(value)


def _local_fact_text(row: Mapping[str, Any], *, max_chars: int) -> str:
    period = row.get("period") or row.get("observation_period") or row.get("publication_date")
    scope = row.get("scope_id") or row.get("geo_id") or row.get("entity_id")

    if row.get("indicator_id") is not None:
        name = row.get("indicator_name") or row.get("indicator_id")
        text = f"{name}: {_format_number(row.get('value'))} {row.get('unit') or ''}".strip()
        if scope:
            text += f" | escopo={scope}"
        if period:
            text += f" | período={period}"
        return _trim_text(text, max_chars)

    if row.get("metric_id") is not None:
        name = row.get("metric_name") or row.get("metric_id")
        text = f"{name}: {_format_number(row.get('value'))} {row.get('unit') or ''}".strip()
        if scope:
            text += f" | escopo={scope}"
        if period:
            text += f" | período={period}"
        return _trim_text(text, max_chars)

    if row.get("document_id") is not None:
        label = f"{row.get('document_type') or 'DOCUMENT'} {row.get('document_id')}"
        body = row.get("text_redacted") or ""
        text = f"{label}: {body}"
        if period:
            text += f" | período={period}"
        if row.get("locator"):
            text += f" | locator={_canonical_json(row.get('locator'))}"
        return _trim_text(text, max_chars)

    if row.get("event_id") is not None:
        label = row.get("event_type") or "JOM_EVENT"
        body = (
            row.get("object_text")
            or row.get("target_act_number")
            or row.get("contract_number")
            or row.get("process_number")
            or row.get("event_id")
        )
        text = f"{label}: {body}"
        if period:
            text += f" | publicação={period}"
        return _trim_text(text, max_chars)

    if row.get("product_name") is not None and row.get("row_count") is not None:
        text = (
            f"Produto {row.get('product_name')}: {row.get('row_count')} registros"
            f" | readiness={row.get('readiness') or 'NA'}"
        )
        return _trim_text(text, max_chars)

    semantic_fields = {}
    for key in (
        "geo_level",
        "geo_id",
        "period",
        "value",
        "unit",
        "context",
        "stage",
        "amount_brl",
        "funding_source",
        "application_code",
        "program_code",
        "action_code",
    ):
        if row.get(key) not in (None, "", [], {}):
            semantic_fields[key] = row.get(key)
    _stop(bool(semantic_fields), "TASK205_UNFORMATTABLE_LOCAL_ROW")
    return _trim_text(_canonical_json(semantic_fields), max_chars)


def _projection_fact_texts(
    name: str,
    value: Mapping[str, Any],
    *,
    max_chars: int,
) -> list[str]:
    facts: list[str] = []

    if name == "ACCOUNTING_EDUCATION_STAGE_TOTALS":
        for period_key, label in (("through_april", "até abril/2026"), ("through_july", "até julho/2026")):
            row = value[period_key]
            facts.append(
                f"Educação {label}: empenhado líquido R$ {row['empenhado_liquido_brl']}; "
                f"liquidado R$ {row['liquidado_brl']}; pago R$ {row['pago_brl']}."
            )

    elif name == "ACCOUNTING_PROGRAM_ACTION_SUMMARY":
        row = value["program_2001_totals"]
        facts.append(
            f"Programa {row['program_code']} — {row['program_name']}: "
            f"empenhado líquido R$ {row['empenhado_liquido_brl']}; "
            f"liquidado R$ {row['liquidado_brl']}; pago R$ {row['pago_brl']}."
        )
        facts.append(
            f"O snapshot contém {value['distinct_program_action_pairs']} pares programa/ação; "
            f"a lista exibida pela projeção é selecionada, não exaustiva."
        )

    elif name == "ACCOUNTING_FUNDING_APPLICATION_SUMMARY":
        facts.append(
            f"O recorte de Educação contém {value['distinct_funding_application_pairs']} pares fonte/aplicação."
        )
        for row in value.get("selected_pairs", [])[:4]:
            facts.append(
                f"{row['funding_source']} | {row['application_code']}: "
                f"empenhado líquido R$ {row['empenhado_liquido_brl']}; pago R$ {row['pago_brl']}."
            )

    elif name == "ACCOUNTING_EXPENSE_ELEMENT_SUMMARY":
        facts.append(
            f"O recorte de Educação contém {value['distinct_expense_elements']} elementos de despesa."
        )
        for row in value.get("selected_elements", [])[:4]:
            facts.append(
                f"{row['expense_element']}: empenhado líquido R$ {row['empenhado_liquido_brl']}; "
                f"pago R$ {row['pago_brl']}."
            )

    elif name == "ACCOUNTING_PROCUREMENT_SUPPLIER_MODALITY_SUMMARY":
        facts.append(
            f"Há {value['formal_procurement_rows']} registros formais de contratação no recorte; "
            f"{value['cnpj_rows']} são linhas de pessoa jurídica e {value['person_rows_redacted']} "
            "linhas de pessoa física permanecem agregadas/redigidas."
        )
        for row in value.get("selected_legal_entity_groups", [])[:4]:
            facts.append(
                f"{row['supplier_name']} | {row['procurement_modality']}: "
                f"empenhado líquido R$ {row['empenhado_liquido_brl']}; pago R$ {row['pago_brl']}."
            )

    elif name == "ACCOUNTING_COMMITMENT_CONTROL_SUMMARY":
        facts.append(
            f"O recorte contém {value['unique_commitment_numbers']} números de empenho únicos "
            f"em {value['unique_official_record_ids']} registros oficiais."
        )
        facts.append("Estágios observados: " + _canonical_json(value["source_stage_counts"]))

    elif name == "ACCOUNTING_RESTS_PAYABLE_SUMMARY":
        for row in value.get("education", []):
            facts.append(
                f"Restos a pagar da Educação em {row['period']}: processados R$ {row['processed_balance_brl']}; "
                f"não processados R$ {row['nonprocessed_balance_brl']}; total R$ {row['total_balance_brl']}."
            )

    elif name == "REVENUE_EDUCATION_FUNDING_APPLICATION_SUMMARY":
        row = value["net_totals"]
        facts.extend(
            [
                f"Receitas com aplicação em Educação jan-jul/2026: R$ {row['education_application_brl']}.",
                f"Tesouro vinculado à Educação jan-jul/2026: R$ {row['education_tesouro_brl']}.",
                f"Transferências estaduais vinculadas à Educação jan-jul/2026: R$ {row['education_state_transfers_brl']}.",
                f"Transferências federais vinculadas à Educação jan-jul/2026: R$ {row['education_federal_transfers_brl']}.",
                f"Receitas vinculadas ao FUNDEB jan-jul/2026: R$ {row['fundeb_linked_brl']}.",
                f"Receitas vinculadas à ETI jan-jul/2026: R$ {row['eti_all_linked_brl']}.",
            ]
        )

    else:
        facts.append(f"{name}: {_canonical_json(value)}")

    return [_trim_text(x, max_chars) for x in facts]


def _period_values(rows: Iterable[Mapping[str, Any]]) -> list[str]:
    values: set[str] = set()
    for row in rows:
        for field in ("period", "observation_period", "publication_date"):
            raw = row.get(field)
            if raw not in (None, ""):
                values.add(str(raw))
    return sorted(values)


def _projection_time_references(projections: Iterable[Mapping[str, Any]]) -> list[str]:
    refs: set[str] = set()
    for item in projections:
        name = item["projection_view"]
        value = item["value"]
        scope = str(value.get("scope") or "")
        if scope:
            refs.add(scope)
        if name == "ACCOUNTING_EDUCATION_STAGE_TOTALS":
            refs.update({"2026-04", "2026-07"})
        elif name == "ACCOUNTING_RESTS_PAYABLE_SUMMARY":
            refs.update(str(row["period"]) for row in value.get("education", []))
        elif name == "REVENUE_EDUCATION_FUNDING_APPLICATION_SUMMARY":
            refs.add("2026-01..2026-07")
    return sorted(refs)


def _decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _local_comparisons(rows: list[dict[str, Any]]) -> list[str]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        metric_id = row.get("indicator_id") or row.get("metric_id")
        if not metric_id:
            continue
        period = row.get("period") or row.get("observation_period")
        if period in (None, "") or _decimal(row.get("value")) is None:
            continue
        scope = str(row.get("scope_id") or row.get("geo_id") or row.get("entity_id") or "")
        unit = str(row.get("unit") or "")
        groups.setdefault((str(metric_id), scope, unit), []).append(row)

    comparisons: list[str] = []
    for (metric_id, scope, unit), items in sorted(groups.items()):
        by_period: dict[str, dict[str, Any]] = {}
        for row in items:
            by_period[str(row.get("period") or row.get("observation_period"))] = row
        if len(by_period) < 2:
            continue
        periods = sorted(by_period)
        first = by_period[periods[0]]
        last = by_period[periods[-1]]
        label = first.get("indicator_name") or first.get("metric_name") or metric_id
        scope_text = f" | escopo={scope}" if scope else ""
        comparisons.append(
            f"{label}{scope_text}: {periods[0]}={_format_number(first['value'])} {unit} → "
            f"{periods[-1]}={_format_number(last['value'])} {unit}."
        )
    return comparisons[:6]


def _projection_comparisons(projections: Iterable[Mapping[str, Any]]) -> list[str]:
    comparisons: list[str] = []
    for item in projections:
        if item["projection_view"] != "ACCOUNTING_EDUCATION_STAGE_TOTALS":
            continue
        value = item["value"]
        a = value["through_april"]
        j = value["through_july"]
        comparisons.append(
            "Educação abril→julho/2026: "
            f"empenhado líquido R$ {a['empenhado_liquido_brl']} → R$ {j['empenhado_liquido_brl']}; "
            f"liquidado R$ {a['liquidado_brl']} → R$ {j['liquidado_brl']}; "
            f"pago R$ {a['pago_brl']} → R$ {j['pago_brl']}."
        )
    return comparisons


def _provenance_ref(
    product_name: str,
    row: Mapping[str, Any],
) -> dict[str, Any]:
    ref: dict[str, Any] = {"product": product_name}
    for field in (
        "source_family",
        "source_sha256",
        "provenance_ref",
        "period",
        "observation_period",
        "publication_date",
        "scope_id",
        "geo_id",
        "document_id",
        "event_id",
        "locator",
        "source_locator",
    ):
        value = row.get(field)
        if value not in (None, "", [], {}):
            ref[field] = value
    return ref


def _dedupe_json(items: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for item in items:
        obj = dict(item)
        deduped[_canonical_json(obj)] = obj
    return [deduped[key] for key in sorted(deduped)]


def _validate_renderable_packet(packet: Mapping[str, Any]) -> None:
    _stop(packet.get("schema") == "OBSERVATORY_RENDERABLE_PACKET_V1", "TASK205_PACKET_SCHEMA")
    _stop(str(packet.get("renderable_packet_id") or "").startswith("RPK_"), "TASK205_PACKET_ID")
    sha = str(packet.get("renderable_packet_sha256") or "")
    _stop(len(sha) == 64 and all(ch in "0123456789abcdef" for ch in sha), "TASK205_PACKET_SHA")
    _stop(packet.get("projection_replaces_source_snapshot") is False, "TASK205_PACKET_SOURCE_REPLACEMENT")
    _stop(packet.get("source_snapshot_remains_canonical") is True, "TASK205_PACKET_SOURCE_CANONICAL")
    _stop(packet.get("llm_numeric_truth_allowed") is False, "TASK205_PACKET_LLM_NUMERIC")


def _answer_material_without_hash(card: Mapping[str, Any]) -> dict[str, Any]:
    return {key: deepcopy(value) for key, value in card.items() if key != "answer_card_sha256"}


def validate_answer_card(
    card: Mapping[str, Any],
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    _stop(card.get("schema") == contract["output_card_schema"], "TASK205_CARD_OUTPUT_SCHEMA")
    _stop(bool(str(card.get("question_id") or "")), "TASK205_CARD_QUESTION_ID")
    _stop(bool(str(card.get("question") or "")), "TASK205_CARD_QUESTION")
    _stop(bool(str(card.get("domain_id") or "")), "TASK205_CARD_DOMAIN")
    _stop(bool(card.get("NUMBER_OR_FACT")), "TASK205_CARD_FACT")
    _stop(bool(card.get("TIME_REFERENCE")), "TASK205_CARD_TIME")
    _stop(bool(card.get("COMPARISON_OR_TREND")), "TASK205_CARD_COMPARISON")
    _stop(bool(str(card.get("PLAIN_LANGUAGE_EXPLANATION") or "")), "TASK205_CARD_EXPLANATION")
    _stop(bool(card.get("SOURCE_AND_PROVENANCE")), "TASK205_CARD_PROVENANCE")
    _stop(bool(card.get("CAUTION_OR_LIMIT")), "TASK205_CARD_CAUTION")
    _stop(card.get("llm_used") is False, "TASK205_CARD_LLM")
    _stop(card.get("numeric_invention_performed") is False, "TASK205_CARD_NUMERIC_INVENTION")
    _stop(card.get("causal_effect_created") is False, "TASK205_CARD_CAUSAL")
    sha = str(card.get("answer_card_sha256") or "")
    _stop(len(sha) == 64 and all(ch in "0123456789abcdef" for ch in sha), "TASK205_CARD_SHA")
    recomputed = _sha(_answer_material_without_hash(card))
    _stop(recomputed == sha, "TASK205_CARD_SHA_MISMATCH")
    return deepcopy(dict(card))


def build_answer_card(
    question_id: str,
    products: Mapping[str, Mapping[str, Any]],
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    config = current_answerability_config()
    question = next((row for row in config["questions"] if row["id"] == question_id), None)
    _stop(question is not None, "TASK205_UNKNOWN_QUESTION")
    recipe = config["recipes"][question["recipe"]]

    packet = build_renderable_packet(question_id, products)
    _validate_renderable_packet(packet)

    max_samples = int(contract["limits"]["max_sample_records_per_signal"])
    max_chars = int(contract["limits"]["max_fact_text_chars"])

    local_fact_rows: list[tuple[str, dict[str, Any]]] = []
    all_matching_rows: list[dict[str, Any]] = []
    local_facts: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    cautions: set[str] = set()

    for signal_index, signal in enumerate(recipe["signals"], start=1):
        product_name = str(signal["product"])
        rows = _matching_rows(signal, products)
        if rows:
            all_matching_rows.extend(rows)
            for row in rows[:max_samples]:
                local_fact_rows.append((product_name, row))
                local_facts.append(
                    {
                        "kind": "LOCAL_RECORD",
                        "signal_index": signal_index,
                        "product": product_name,
                        "text": _local_fact_text(row, max_chars=max_chars),
                    }
                )
                provenance.append(_provenance_ref(product_name, row))
                if row.get("caution"):
                    cautions.add(str(row["caution"]))
            if len(rows) > max_samples:
                cautions.add(
                    f"{product_name}:SAMPLE_{max_samples}_OF_{len(rows)}_RECIPE_MATCHING_RECORDS_NOT_EXHAUSTIVE"
                )

    projection_facts: list[dict[str, Any]] = []
    projections = list(packet.get("bounded_projection_views") or [])
    for projection in projections:
        name = str(projection["projection_view"])
        for text in _projection_fact_texts(name, projection["value"], max_chars=max_chars):
            projection_facts.append(
                {
                    "kind": "BOUNDED_PROJECTION",
                    "projection_view": name,
                    "text": text,
                }
            )
        for source_name, spec in sorted((projection.get("source_snapshots") or {}).items()):
            provenance.append(
                {
                    "product": source_name,
                    "snapshot_id": spec.get("snapshot_id"),
                    "drive_id": spec.get("drive_id"),
                    "content_sha256": spec.get("content_sha256"),
                    "gzip_sha256": spec.get("gzip_sha256"),
                }
            )
        cautions.add("BOUNDED_PROJECTION_NE_SOURCE_SNAPSHOT")
        cautions.add("SOURCE_SNAPSHOT_REMAINS_CANONICAL")
        cautions.add("SELECTED_PROJECTION_RANKINGS_MAY_BE_NON_EXHAUSTIVE")

    facts = local_facts + projection_facts
    _stop(bool(facts), "TASK205_NO_FACTS")

    time_refs = sorted(
        set(_period_values(all_matching_rows))
        | set(_projection_time_references(projections))
    )
    if not time_refs:
        time_refs = [contract["unavailable_marker"]]

    comparisons = _local_comparisons(all_matching_rows) + _projection_comparisons(projections)
    comparisons = list(dict.fromkeys(comparisons))
    if not comparisons:
        comparisons = [contract["unavailable_marker"]]

    provenance = _dedupe_json(provenance)
    provenance = provenance[: int(contract["limits"]["max_provenance_refs"])]
    _stop(bool(provenance), "TASK205_NO_PROVENANCE")

    cautions.add("FORMATTING_ALLOWED_INFERENCE_FORBIDDEN")
    if packet.get("projection_count", 0):
        cautions.add("ONTOLOGY_SUMMARY_RENDERABLE_NE_ARBITRARY_FULL_LEDGER_DRILLDOWN_LOCAL")
    cautions_list = sorted(cautions)[: int(contract["limits"]["max_cautions"])]
    _stop(bool(cautions_list), "TASK205_NO_CAUTION")

    backing = (
        "BOUNDED_SOURCE_PINNED_PROJECTION_BACKED"
        if packet.get("projection_count", 0)
        else "LOCAL_RECORD_BACKED"
    )
    card: dict[str, Any] = {
        "schema": contract["output_card_schema"],
        "question_id": question_id,
        "domain_id": question["domain_id"],
        "question": question["text"],
        "recipe": question["recipe"],
        "backing": backing,
        "source_renderable_packet_id": packet["renderable_packet_id"],
        "source_renderable_packet_sha256": packet["renderable_packet_sha256"],
        "NUMBER_OR_FACT": facts,
        "TIME_REFERENCE": time_refs,
        "COMPARISON_OR_TREND": comparisons,
        "PLAIN_LANGUAGE_EXPLANATION": contract["domain_explanations"][question["domain_id"]],
        "SOURCE_AND_PROVENANCE": provenance,
        "CAUTION_OR_LIMIT": cautions_list,
        "llm_used": False,
        "numeric_invention_performed": False,
        "causal_effect_created": False,
        "remote_effects": deepcopy(contract["remote_effects"]),
    }
    card["answer_card_sha256"] = _sha(card)
    return validate_answer_card(card, contract_path=contract_path)


def render_answer_card_markdown(
    card: Mapping[str, Any],
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    validated = validate_answer_card(card, contract_path=contract_path)

    lines = [
        f"# {validated['question']}",
        "",
        f"- **Question ID:** {validated['question_id']}",
        f"- **Domínio:** {validated['domain_id']}",
        f"- **Backing:** {validated['backing']}",
        f"- **Answer card SHA-256:** {validated['answer_card_sha256']}",
        f"- **Renderable packet:** {validated['source_renderable_packet_id']}",
        "",
        "## Número ou fato",
        "",
    ]
    for fact in validated["NUMBER_OR_FACT"]:
        lines.append(f"- {fact['text']}")

    lines.extend(["", "## Referência temporal", ""])
    for item in validated["TIME_REFERENCE"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Comparação ou tendência", ""])
    for item in validated["COMPARISON_OR_TREND"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Explicação em linguagem simples",
            "",
            validated["PLAIN_LANGUAGE_EXPLANATION"],
            "",
            "## Fonte e proveniência",
            "",
        ]
    )
    for ref in validated["SOURCE_AND_PROVENANCE"]:
        lines.append(f"- {_canonical_json(ref)}")

    lines.extend(["", "## Cautelas e limites", ""])
    for item in validated["CAUTION_OR_LIMIT"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Salvaguardas do renderer",
            "",
            "- Nenhum número foi inventado pelo renderer.",
            "- Nenhuma relação causal foi criada pelo renderer.",
            "- Nenhuma chamada a LLM, rede, Drive, serving ou publicação foi executada.",
        ]
    )

    markdown = "\n".join(lines).rstrip() + "\n"
    return {
        "schema": contract["output_render_schema"],
        "question_id": validated["question_id"],
        "answer_card_sha256": validated["answer_card_sha256"],
        "format": "MARKDOWN",
        "markdown": markdown,
        "markdown_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        "llm_used": False,
        "remote_effects_performed": False,
    }


def build_human_answer_bundle(
    products: Mapping[str, Mapping[str, Any]],
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    task204 = build_task204_renderability_audit(products)
    _stop(task204["ontology_summary_renderable_count"] == 38, "TASK205_TASK204_RENDERABILITY")
    config = current_answerability_config()
    question_ids = [str(row["id"]) for row in config["questions"]]
    _stop(len(question_ids) == contract["expected_question_count"], "TASK205_CONFIG_QUESTION_COUNT")

    cards: list[dict[str, Any]] = []
    renders: list[dict[str, Any]] = []
    for question_id in question_ids:
        card = build_answer_card(question_id, products, contract_path=contract_path)
        render = render_answer_card_markdown(card, contract_path=contract_path)
        cards.append(card)
        renders.append(render)

    cards.sort(key=lambda x: x["question_id"])
    renders.sort(key=lambda x: x["question_id"])
    _stop(len(cards) == 38 and len(renders) == 38, "TASK205_BUNDLE_COUNT")
    _stop(len({x["answer_card_sha256"] for x in cards}) == 38, "TASK205_CARD_HASH_UNIQUENESS")
    _stop(len({x["markdown_sha256"] for x in renders}) == 38, "TASK205_MARKDOWN_HASH_UNIQUENESS")

    backing_counts: dict[str, int] = {}
    comparison_available = 0
    marker = contract["unavailable_marker"]
    for card in cards:
        backing_counts[card["backing"]] = backing_counts.get(card["backing"], 0) + 1
        if card["COMPARISON_OR_TREND"] != [marker]:
            comparison_available += 1

    _stop(
        backing_counts
        == {
            "LOCAL_RECORD_BACKED": 27,
            "BOUNDED_SOURCE_PINNED_PROJECTION_BACKED": 11,
        },
        "TASK205_BACKING_COUNTS",
    )

    material = {
        "cards": cards,
        "renders": [
            {
                "question_id": row["question_id"],
                "answer_card_sha256": row["answer_card_sha256"],
                "markdown_sha256": row["markdown_sha256"],
            }
            for row in renders
        ],
    }
    bundle_sha = _sha(material)
    return {
        "schema": "OBSERVATORY_HUMAN_ANSWER_BUNDLE_V1",
        "question_count": 38,
        "answer_card_count": len(cards),
        "markdown_render_count": len(renders),
        "backing_counts": dict(sorted(backing_counts.items())),
        "comparison_available_count": comparison_available,
        "comparison_unavailable_count": 38 - comparison_available,
        "bundle_sha256": bundle_sha,
        "cards": cards,
        "renders": renders,
        "llm_used": False,
        "remote_effects": deepcopy(contract["remote_effects"]),
    }


def build_current_human_answer_bundle(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    products = build_current_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    return build_human_answer_bundle(products, contract_path=contract_path)
