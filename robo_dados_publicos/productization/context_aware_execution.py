from __future__ import annotations

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
from robo_dados_publicos.productization.bounded_query_projections import (
    projection_views_for_question,
    validate_projection_values,
)
from robo_dados_publicos.productization.contextual_slot_binder import (
    bind_context,
)
from robo_dados_publicos.productization.natural_language_router import (
    route_and_render,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task209_context_aware_execution.v1.json"


class Task209ExecutionStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task209ExecutionStop(code)


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
    _stop(obj.get("schema") == "TASK209_CONTEXT_AWARE_EXECUTION_V1", "TASK209_SCHEMA")
    _stop(obj.get("issue") == 662, "TASK209_ISSUE")
    _stop(
        obj.get("base_main_sha") == "9ad955e876184ef999d3a88c0ff26e377384d1e3",
        "TASK209_BASE",
    )
    _stop(
        obj.get("mode") == "T0_OFFLINE_BOUNDED_CONTEXT_AWARE_QUERY_EXECUTION",
        "TASK209_MODE",
    )
    _stop(
        set(obj.get("states") or [])
        == {
            "ANSWERED_CONTEXTUALLY",
            "EXPLICIT_CONTEXT_GAP",
            "UNSUPPORTED_CONTEXT_COMBINATION",
            "BINDING_STOP",
            "LEGACY_UNCONTEXTUALIZED_PASSTHROUGH",
        },
        "TASK209_STATES",
    )
    _stop(
        set(obj["supported_contextual_questions"]) == {"FIN_Q1", "NETWORK_Q3", "NORMS_Q2"},
        "TASK209_SUPPORTED_QUESTIONS",
    )
    bounds = obj["claim_boundaries"]
    _stop(bounds["context_gap_means_global_absence"] is False, "TASK209_GAP_ABSENCE")
    _stop(
        bounds["context_gap_means_no_matching_evidence_in_current_materialized_corpus"] is True,
        "TASK209_GAP_SCOPE",
    )
    _stop(
        bounds["unsupported_context_may_snap_to_nearest_period"] is False,
        "TASK209_PERIOD_SNAP",
    )
    _stop(bounds["projection_replaces_source_snapshot"] is False, "TASK209_PROJECTION_REPLACE")
    _stop(bounds["source_snapshot_remains_canonical"] is True, "TASK209_SOURCE_CANONICAL")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK209_REMOTE")
    return obj


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    validate_projection_values()
    cfg = current_answerability_config()
    by_id = {str(q["id"]): q for q in cfg["questions"]}
    _stop(set(obj["supported_contextual_questions"]) <= set(by_id), "TASK209_QID_DRIFT")

    network_q = by_id["NETWORK_Q3"]
    recipe = cfg["recipes"][network_q["recipe"]]
    metric_ids: set[str] = set()
    for signal in recipe["signals"]:
        if signal.get("product") == "SCHOOL_INDICATOR_SERIES":
            metric_ids.update(str(x) for x in signal.get("ids") or [])
    _stop(
        metric_ids == set(obj["supported_contextual_questions"]["NETWORK_Q3"]["metrics"]),
        "TASK209_NETWORK_METRIC_DRIFT",
    )

    fin_views = projection_views_for_question("FIN_Q1")
    _stop(len(fin_views) == 1, "TASK209_FIN_VIEW_COUNT")
    _stop(
        fin_views[0]["projection_view"]
        == obj["supported_contextual_questions"]["FIN_Q1"]["projection_view"],
        "TASK209_FIN_VIEW_DRIFT",
    )
    return {
        "schema": "TASK209_CONTEXT_AWARE_EXECUTION_VALIDATION_V1",
        "status": "PASS",
        "supported_contextual_question_count": 3,
        "network_metrics": sorted(metric_ids),
        "network": False,
        "drive_write": False,
        "llm": False,
    }


def _row_ref(product_name: str, row: Mapping[str, Any]) -> dict[str, Any]:
    ref: dict[str, Any] = {"product": product_name}
    for field in (
        "snapshot_id",
        "source_family",
        "source_sha256",
        "provenance_ref",
        "scope_level",
        "scope_id",
        "school_code",
        "school_name",
        "period",
        "observation_period",
        "document_id",
        "document_type",
        "locator",
        "evidence_role",
        "quality_status",
    ):
        value = row.get(field)
        if value not in (None, "", [], {}):
            ref[field] = value
    return ref


def _dedupe_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {_canonical_json(item): item for item in items}
    return [by_key[key] for key in sorted(by_key)]


def _period_years(value: Any) -> set[int]:
    text = str(value or "").strip()
    if not text:
        return set()
    if len(text) >= 4 and text[:4].isdigit():
        first = int(text[:4])
    else:
        return set()
    if len(text) == 9 and text[4] == "-" and text[5:9].isdigit():
        last = int(text[5:9])
        if last >= first:
            return set(range(first, last + 1))
    return {first}


def _period_matches_year(row: Mapping[str, Any], year: int) -> bool:
    raw = row.get("period") or row.get("observation_period") or row.get("publication_date")
    return year in _period_years(raw)


def _base_filter_accounting(context: Mapping[str, Any]) -> dict[str, Any]:
    school = context["school"]
    period = context["period"]
    facets = list(context.get("policy_service_facets") or [])
    granularity = context["granularity"]
    return {
        "SCHOOL": {
            "requested": school.get("status") == "RESOLVED",
            "value": (
                {
                    "school_code": school.get("school_code"),
                    "school_name": school.get("school_name"),
                }
                if school.get("status") == "RESOLVED"
                else None
            ),
            "status": "PENDING" if school.get("status") == "RESOLVED" else "NOT_REQUESTED",
        },
        "PERIOD": {
            "requested": period.get("status") == "RESOLVED",
            "value": dict(period) if period.get("status") == "RESOLVED" else None,
            "status": "PENDING" if period.get("status") == "RESOLVED" else "NOT_REQUESTED",
        },
        "POLICY_SERVICE_FACETS": {
            "requested": bool(facets),
            "value": facets,
            "status": "PENDING" if facets else "NOT_REQUESTED",
        },
        "GRANULARITY": {
            "requested": bool(granularity.get("explicit"))
            or granularity.get("value") in {"SCHOOL", "SCHOOL_VS_NETWORK"},
            "value": granularity.get("value"),
            "status": "PENDING",
        },
    }


def _finalize(
    *,
    state: str,
    text: str,
    context: Mapping[str, Any],
    question_id: str | None,
    filter_accounting: Mapping[str, Any],
    facts: list[dict[str, Any]] | None = None,
    time_reference: list[str] | None = None,
    comparisons: list[str] | None = None,
    provenance: list[dict[str, Any]] | None = None,
    cautions: list[str] | None = None,
    gap_scope: str | None = None,
    legacy: Mapping[str, Any] | None = None,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    material = {
        "state": state,
        "question_id": question_id,
        "context_result_sha256": context.get("context_result_sha256"),
        "filter_accounting": deepcopy(dict(filter_accounting)),
        "facts": deepcopy(facts or []),
        "time_reference": list(time_reference or []),
        "comparisons": list(comparisons or []),
        "provenance": _dedupe_dicts(list(provenance or [])),
        "cautions": sorted(set(cautions or [])),
        "gap_scope": gap_scope,
        "legacy": deepcopy(dict(legacy)) if legacy is not None else None,
    }
    result = {
        "schema": contract["output_schema"],
        "input_text": text,
        "state": state,
        "question_id": question_id,
        "context": deepcopy(dict(context)),
        "filter_accounting": material["filter_accounting"],
        "NUMBER_OR_FACT": material["facts"],
        "TIME_REFERENCE": material["time_reference"],
        "COMPARISON_OR_TREND": material["comparisons"],
        "SOURCE_AND_PROVENANCE": material["provenance"],
        "CAUTION_OR_LIMIT": material["cautions"],
        "gap_scope": gap_scope,
        "legacy_task207_result": material["legacy"],
        "context_dropped": False,
        "text_is_truth_source": False,
        "numeric_invention_performed": False,
        "causal_effect_created": False,
        "llm_used": False,
        "remote_effects": deepcopy(contract["remote_effects"]),
    }
    result["answer_sha256"] = _sha(material)
    return result


def _unsupported(
    text: str,
    context: Mapping[str, Any],
    question_id: str | None,
    filters: dict[str, Any],
    reason: str,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    for entry in filters.values():
        if entry["status"] == "PENDING":
            entry["status"] = "UNSUPPORTED"
    return _finalize(
        state="UNSUPPORTED_CONTEXT_COMBINATION",
        text=text,
        context=context,
        question_id=question_id,
        filter_accounting=filters,
        facts=[{"kind": "STOP", "text": reason}],
        cautions=[
            "REQUESTED_CONTEXT_WAS_NOT_DROPPED",
            "UNSUPPORTED_CONTEXT_NE_NEAREST_AVAILABLE_CONTEXT",
        ],
        contract=contract,
    )


def _execute_fin_q1(
    text: str,
    context: Mapping[str, Any],
    filters: dict[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    spec = contract["supported_contextual_questions"]["FIN_Q1"]
    period = context["period"]
    if (
        period.get("status") != "RESOLVED"
        or period.get("mode") != "YEAR_TO_MONTH"
        or int(period.get("year") or 0) != int(spec["supported_year"])
    ):
        return _unsupported(
            text,
            context,
            "FIN_Q1",
            filters,
            "FIN_Q1 contextual execution currently requires an exact 2026 year-to-month boundary.",
            contract,
        )
    end_month = str(period.get("end_month"))
    view_key = spec["supported_year_to_month"].get(end_month)
    if not view_key:
        return _unsupported(
            text,
            context,
            "FIN_Q1",
            filters,
            "The requested month is not an exact materialized TASK204 education-stage projection; no nearest-period substitution was performed.",
            contract,
        )

    views = projection_views_for_question("FIN_Q1")
    projection = next(
        item for item in views
        if item["projection_view"] == spec["projection_view"]
    )
    value = projection["value"]
    row = value[view_key]
    month = int(end_month)
    month_names = {4: "abril", 7: "julho"}
    label = month_names[month]

    filters["PERIOD"]["status"] = "APPLIED"
    filters["GRANULARITY"]["status"] = "APPLIED"
    if filters["SCHOOL"]["status"] == "PENDING":
        return _unsupported(
            text,
            context,
            "FIN_Q1",
            filters,
            "School-level education spending is not materialized by this FIN_Q1 projection.",
            contract,
        )
    if filters["POLICY_SERVICE_FACETS"]["status"] == "PENDING":
        return _unsupported(
            text,
            context,
            "FIN_Q1",
            filters,
            "Policy/service-facet spending is not materialized by this FIN_Q1 projection.",
            contract,
        )

    facts = [
        {
            "kind": "HEADLINE",
            "stage_semantic": "LIQUIDATED_TO_DATE",
            "period": f"2026-01..2026-{month:02d}",
            "value_brl": row["liquidado_brl"],
            "text": f"Gasto da Educação liquidado até {label}/2026: R$ {row['liquidado_brl']}.",
        },
        {
            "kind": "ACCOUNTING_STAGES",
            "period": f"2026-01..2026-{month:02d}",
            "empenhado_liquido_brl": row["empenhado_liquido_brl"],
            "liquidado_brl": row["liquidado_brl"],
            "pago_brl": row["pago_brl"],
            "text": (
                f"Educação até {label}/2026: empenhado líquido R$ {row['empenhado_liquido_brl']}; "
                f"liquidado R$ {row['liquidado_brl']}; pago R$ {row['pago_brl']}."
            ),
        },
    ]
    comparisons: list[str] = []
    if month == 7:
        april = value["through_april"]
        comparisons.append(
            "Abril→julho/2026, sem misturar estágios: "
            f"liquidado R$ {april['liquidado_brl']} → R$ {row['liquidado_brl']}; "
            f"pago R$ {april['pago_brl']} → R$ {row['pago_brl']}."
        )

    source = projection["source_snapshots"]["ACCOUNTING_LEDGER"]
    provenance = [{
        "product": "ACCOUNTING_LEDGER",
        "projection_view": spec["projection_view"],
        "projection_key": view_key,
        "snapshot_id": source.get("snapshot_id"),
        "drive_id": source.get("drive_id"),
        "content_sha256": source.get("content_sha256"),
        "gzip_sha256": source.get("gzip_sha256"),
    }]
    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id="FIN_Q1",
        filter_accounting=filters,
        facts=facts,
        time_reference=[f"2026-01..2026-{month:02d}"],
        comparisons=comparisons,
        provenance=provenance,
        cautions=[
            "COMMITMENT_NE_LIQUIDATION_NE_PAYMENT",
            "BOUNDED_PROJECTION_NE_SOURCE_SNAPSHOT",
            "SOURCE_SNAPSHOT_REMAINS_CANONICAL",
            "FIN_Q1_HEADLINE_SEMANTIC_LIQUIDATED_TO_DATE",
        ],
        contract=contract,
    )


def _metric_rows(
    product: Mapping[str, Any],
    *,
    metric_id: str,
    scope_level: str,
    school_code: str | None = None,
    network: str | None = None,
) -> list[dict[str, Any]]:
    rows = []
    for raw in product.get("rows", []):
        row = dict(raw)
        if str(row.get("indicator_id") or "") != metric_id:
            continue
        if str(row.get("scope_level") or "") != scope_level:
            continue
        if school_code is not None and str(row.get("scope_id") or "") != school_code:
            continue
        if network is not None and str(row.get("network") or "") != network:
            continue
        rows.append(row)
    rows.sort(key=lambda x: (str(x.get("period") or ""), _canonical_json(x)))
    return rows


def _one_row_at_period(rows: list[dict[str, Any]], period: str, code: str) -> dict[str, Any]:
    matches = [row for row in rows if str(row.get("period") or "") == period]
    _stop(len(matches) == 1, code)
    return matches[0]


def _execute_network_q3(
    text: str,
    context: Mapping[str, Any],
    filters: dict[str, Any],
    products: Mapping[str, Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    spec = contract["supported_contextual_questions"]["NETWORK_Q3"]
    school = context["school"]
    if school.get("status") != "RESOLVED":
        return _unsupported(
            text,
            context,
            "NETWORK_Q3",
            filters,
            "NETWORK_Q3 contextual execution requires one resolved canonical school.",
            contract,
        )
    if context["granularity"].get("value") != "SCHOOL_VS_NETWORK":
        return _unsupported(
            text,
            context,
            "NETWORK_Q3",
            filters,
            "NETWORK_Q3 requires SCHOOL_VS_NETWORK granularity.",
            contract,
        )
    period = context["period"]
    requested_year: str | None = None
    if period.get("status") == "RESOLVED":
        if period.get("mode") != "YEAR":
            return _unsupported(
                text,
                context,
                "NETWORK_Q3",
                filters,
                "School/network indicator comparison currently supports an exact year or latest common year, not month-level periods.",
                contract,
            )
        requested_year = str(period["year"])

    product = products[spec["product"]]
    facts: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    time_refs: list[str] = []
    cautions: set[str] = {
        "SCHOOL_NETWORK_COMPARISON_NE_CAUSAL_EXPLANATION",
        "SCHOOL_POINT_NE_SIMPLE_SCHOOL_MEAN",
    }

    for metric_id in spec["metrics"]:
        school_rows = _metric_rows(
            product,
            metric_id=metric_id,
            scope_level=spec["school_scope_level"],
            school_code=str(school["school_code"]),
        )
        network_rows = _metric_rows(
            product,
            metric_id=metric_id,
            scope_level=spec["network_scope_level"],
            network=spec["network"],
        )
        school_periods = {str(row.get("period") or "") for row in school_rows}
        network_periods = {str(row.get("period") or "") for row in network_rows}
        common = sorted(
            p for p in (school_periods & network_periods)
            if len(p) == 4 and p.isdigit()
        )
        if requested_year is not None:
            if requested_year not in common:
                return _unsupported(
                    text,
                    context,
                    "NETWORK_Q3",
                    filters,
                    f"No exact common school/network {metric_id} row is materialized for {requested_year}; no nearest-year substitution was performed.",
                    contract,
                )
            selected_period = requested_year
        else:
            _stop(bool(common), f"TASK209_NETWORK_NO_COMMON_{metric_id}")
            selected_period = common[-1]

        school_row = _one_row_at_period(
            school_rows,
            selected_period,
            f"TASK209_NETWORK_SCHOOL_DUPLICATE_{metric_id}_{selected_period}",
        )
        network_row = _one_row_at_period(
            network_rows,
            selected_period,
            f"TASK209_NETWORK_NETWORK_DUPLICATE_{metric_id}_{selected_period}",
        )
        label = str(school_row.get("indicator_name") or metric_id)
        unit = str(school_row.get("unit") or "")
        facts.append({
            "kind": "SCHOOL_VS_NETWORK",
            "metric_id": metric_id,
            "metric_name": label,
            "period": selected_period,
            "school_code": school["school_code"],
            "school_name": school["school_name"],
            "school_value": school_row.get("value"),
            "network_value": network_row.get("value"),
            "unit": unit,
            "text": (
                f"{label} em {selected_period}: {school['school_name']}="
                f"{school_row.get('value')} {unit}; rede municipal="
                f"{network_row.get('value')} {unit}."
            ),
        })
        provenance.extend([
            _row_ref(spec["product"], school_row),
            _row_ref(spec["product"], network_row),
        ])
        time_refs.append(selected_period)
        if school_row.get("caution"):
            cautions.add(str(school_row["caution"]))
        if network_row.get("caution"):
            cautions.add(str(network_row["caution"]))

    filters["SCHOOL"]["status"] = "APPLIED"
    if filters["PERIOD"]["status"] == "PENDING":
        filters["PERIOD"]["status"] = "APPLIED"
    filters["GRANULARITY"]["status"] = "APPLIED"
    if filters["POLICY_SERVICE_FACETS"]["status"] == "PENDING":
        return _unsupported(
            text,
            context,
            "NETWORK_Q3",
            filters,
            "NETWORK_Q3 comparison does not consume a policy/service facet.",
            contract,
        )

    comparisons = [fact["text"] for fact in facts]
    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id="NETWORK_Q3",
        filter_accounting=filters,
        facts=facts,
        time_reference=sorted(set(time_refs)),
        comparisons=comparisons,
        provenance=provenance,
        cautions=sorted(cautions),
        contract=contract,
    )


def _execute_norms_q2(
    text: str,
    context: Mapping[str, Any],
    filters: dict[str, Any],
    products: Mapping[str, Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    spec = contract["supported_contextual_questions"]["NORMS_Q2"]
    facets = list(context.get("policy_service_facets") or [])
    if not facets:
        return _unsupported(
            text,
            context,
            "NORMS_Q2",
            filters,
            "NORMS_Q2 contextual execution requires at least one explicit policy/service facet.",
            contract,
        )
    facet_map = contract["policy_facet_topics"]
    for facet in facets:
        if not facet_map.get(facet):
            return _unsupported(
                text,
                context,
                "NORMS_Q2",
                filters,
                f"Facet {facet} has no bounded normative topic mapping in TASK209.",
                contract,
            )

    period = context["period"]
    requested_year: int | None = None
    if period.get("status") == "RESOLVED":
        if period.get("mode") != "YEAR":
            return _unsupported(
                text,
                context,
                "NORMS_Q2",
                filters,
                "Normative contextual execution currently supports an exact year, not month-level periods.",
                contract,
            )
        requested_year = int(period["year"])

    product = products[spec["product"]]
    selected: list[dict[str, Any]] = []
    for raw in product.get("rows", []):
        row = dict(raw)
        if str(row.get("evidence_role") or "") != spec["required_evidence_role"]:
            continue
        if str(row.get("quality_status") or "") != spec["required_quality_status"]:
            continue
        if spec["required_policy_domain"] not in set(str(x) for x in row.get("policy_domains") or []):
            continue
        if requested_year is not None and not _period_matches_year(row, requested_year):
            continue
        topics = set(str(x) for x in row.get("topics") or [])
        if not all(bool(topics & set(facet_map[facet])) for facet in facets):
            continue
        selected.append(row)
    selected.sort(key=_canonical_json)

    filters["POLICY_SERVICE_FACETS"]["status"] = "APPLIED" if selected else "APPLIED_TO_ZERO_MATCH_QUERY"
    if filters["PERIOD"]["status"] == "PENDING":
        filters["PERIOD"]["status"] = "APPLIED" if selected else "APPLIED_TO_ZERO_MATCH_QUERY"
    filters["GRANULARITY"]["status"] = "APPLIED"
    if filters["SCHOOL"]["status"] == "PENDING":
        return _unsupported(
            text,
            context,
            "NORMS_Q2",
            filters,
            "The current normative product is not school-specific; school context cannot be silently discarded.",
            contract,
        )

    if not selected:
        provenance = [{
            "product": spec["product"],
            "snapshot_id": product.get("snapshot_id"),
            "content_sha256": product.get("content_sha256"),
            "row_count": product.get("row_count"),
            "query_filter": {
                "year": requested_year,
                "facets": facets,
                "topics_by_facet": {facet: facet_map[facet] for facet in facets},
                "evidence_role": spec["required_evidence_role"],
                "quality_status": spec["required_quality_status"],
                "policy_domain": spec["required_policy_domain"],
            },
            "matching_rows": 0,
        }]
        return _finalize(
            state="EXPLICIT_CONTEXT_GAP",
            text=text,
            context=context,
            question_id="NORMS_Q2",
            filter_accounting=filters,
            facts=[{
                "kind": "CONTEXT_GAP",
                "text": (
                    "Nenhuma evidência normativa materializada no produto canônico atual satisfaz "
                    "simultaneamente todos os filtros solicitados. Isso não prova ausência global de mudança normativa."
                ),
            }],
            time_reference=[str(requested_year)] if requested_year is not None else [],
            provenance=provenance,
            cautions=[
                "CURRENT_MATERIALIZED_CORPUS_ZERO_MATCH_NE_GLOBAL_ABSENCE",
                "NORMATIVE_ACT_NE_IMPLEMENTATION",
                "REQUESTED_CONTEXT_WAS_NOT_DROPPED",
            ],
            gap_scope="CURRENT_MATERIALIZED_PLANNING_DOCUMENT_INDEX_ONLY",
            contract=contract,
        )

    facts = []
    provenance = []
    cautions: set[str] = {"NORMATIVE_ACT_NE_IMPLEMENTATION"}
    for row in selected:
        facts.append({
            "kind": "PRIMARY_NORMATIVE",
            "document_id": row.get("document_id"),
            "document_type": row.get("document_type"),
            "period": row.get("period"),
            "topics": row.get("topics"),
            "text": (
                f"{row.get('document_type')} {row.get('document_id')}: "
                f"{row.get('text_redacted')} | período={row.get('period')}"
            ),
        })
        provenance.append(_row_ref(spec["product"], row))
        if row.get("caution"):
            cautions.add(str(row["caution"]))

    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id="NORMS_Q2",
        filter_accounting=filters,
        facts=facts,
        time_reference=sorted({str(row.get("period")) for row in selected}),
        comparisons=[],
        provenance=provenance,
        cautions=sorted(cautions),
        contract=contract,
    )


def _context_filter_requested(context: Mapping[str, Any]) -> bool:
    return (
        context["school"].get("status") == "RESOLVED"
        or context["period"].get("status") == "RESOLVED"
        or bool(context.get("policy_service_facets"))
        or context["granularity"].get("value") in {"SCHOOL", "SCHOOL_VS_NETWORK"}
    )


def execute_contextual_query(
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
    _stop(bool(generated_at), "TASK209_GENERATED_AT")
    _stop(bool(software_version), "TASK209_SOFTWARE_VERSION")

    context = bind_context(
        text,
        reference_date=reference_date,
        context_school_code=context_school_code,
    )
    filters = _base_filter_accounting(context)

    if context["state"] != "CONTEXT_BOUND":
        for entry in filters.values():
            if entry["status"] == "PENDING":
                entry["status"] = "BINDING_STOP"
        return _finalize(
            state="BINDING_STOP",
            text=text,
            context=context,
            question_id=None,
            filter_accounting=filters,
            facts=[{
                "kind": "STOP",
                "text": f"TASK208 binding stopped with state {context['state']}.",
            }],
            cautions=["TASK208_BINDING_STOP_PROPAGATED"],
            contract=contract,
        )

    qids = list(context.get("selected_question_ids") or [])
    if not _context_filter_requested(context):
        legacy = route_and_render(text)
        for entry in filters.values():
            if entry["status"] == "PENDING":
                entry["status"] = "NOT_REQUESTED"
        return _finalize(
            state="LEGACY_UNCONTEXTUALIZED_PASSTHROUGH",
            text=text,
            context=context,
            question_id=qids[0] if len(qids) == 1 else None,
            filter_accounting=filters,
            legacy=legacy,
            cautions=["NO_CONTEXT_FILTER_REQUESTED_TASK205_TASK207_PATH_PRESERVED"],
            contract=contract,
        )

    if len(qids) != 1:
        return _unsupported(
            text,
            context,
            None,
            filters,
            "Context-aware compound execution is not yet supported; no contextual route was discarded.",
            contract,
        )
    qid = qids[0]
    if qid not in contract["supported_contextual_questions"]:
        return _unsupported(
            text,
            context,
            qid,
            filters,
            f"{qid} is not yet in the bounded TASK209 contextual execution set.",
            contract,
        )

    products = build_current_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    if qid == "FIN_Q1":
        return _execute_fin_q1(text, context, filters, contract)
    if qid == "NETWORK_Q3":
        return _execute_network_q3(text, context, filters, products, contract)
    if qid == "NORMS_Q2":
        return _execute_norms_q2(text, context, filters, products, contract)
    raise Task209ExecutionStop("TASK209_UNREACHABLE_QID")


def validate_answer(
    answer: Mapping[str, Any],
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    _stop(answer.get("schema") == contract["output_schema"], "TASK209_OUTPUT_SCHEMA")
    _stop(answer.get("state") in set(contract["states"]), "TASK209_OUTPUT_STATE")
    _stop(answer.get("context_dropped") is False, "TASK209_CONTEXT_DROPPED")
    _stop(answer.get("text_is_truth_source") is False, "TASK209_TEXT_TRUTH")
    _stop(answer.get("numeric_invention_performed") is False, "TASK209_NUMERIC_INVENTION")
    _stop(answer.get("causal_effect_created") is False, "TASK209_CAUSAL")
    _stop(answer.get("llm_used") is False, "TASK209_LLM")
    _stop(all(v is False for v in answer["remote_effects"].values()), "TASK209_OUTPUT_REMOTE")
    sha = str(answer.get("answer_sha256") or "")
    _stop(len(sha) == 64 and all(ch in "0123456789abcdef" for ch in sha), "TASK209_OUTPUT_SHA")
    if answer["state"] in {"ANSWERED_CONTEXTUALLY", "EXPLICIT_CONTEXT_GAP"}:
        _stop(bool(answer["NUMBER_OR_FACT"]), "TASK209_OUTPUT_FACT")
        _stop(bool(answer["SOURCE_AND_PROVENANCE"]), "TASK209_OUTPUT_PROVENANCE")
    return deepcopy(dict(answer))


def render_contextual_answer_markdown(
    answer: Mapping[str, Any],
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    validated = validate_answer(answer, contract_path=contract_path)

    if validated["state"] == "LEGACY_UNCONTEXTUALIZED_PASSTHROUGH":
        legacy = validated["legacy_task207_result"] or {}
        answers = list(legacy.get("answers") or [])
        markdown = "\n\n".join(str(x.get("markdown") or "").rstrip() for x in answers if x.get("markdown")).rstrip() + "\n"
        return {
            "schema": contract["render_schema"],
            "state": validated["state"],
            "question_id": validated["question_id"],
            "answer_sha256": validated["answer_sha256"],
            "format": "MARKDOWN",
            "markdown": markdown,
            "markdown_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
            "llm_used": False,
            "remote_effects_performed": False,
        }

    lines = [
        f"# {validated['input_text']}",
        "",
        f"- **Estado:** {validated['state']}",
        f"- **Question ID:** {validated['question_id'] or 'NA'}",
        f"- **Answer SHA-256:** {validated['answer_sha256']}",
        "",
        "## Filtros contextuais",
        "",
    ]
    for name in contract["required_filter_accounting"]:
        item = validated["filter_accounting"][name]
        lines.append(
            f"- **{name}:** {item['status']} | {_canonical_json(item.get('value'))}"
        )

    lines.extend(["", "## Número ou fato", ""])
    for fact in validated["NUMBER_OR_FACT"]:
        lines.append(f"- {fact['text']}")

    if validated["TIME_REFERENCE"]:
        lines.extend(["", "## Referência temporal", ""])
        for item in validated["TIME_REFERENCE"]:
            lines.append(f"- {item}")

    if validated["COMPARISON_OR_TREND"]:
        lines.extend(["", "## Comparação ou tendência", ""])
        for item in validated["COMPARISON_OR_TREND"]:
            lines.append(f"- {item}")

    if validated["SOURCE_AND_PROVENANCE"]:
        lines.extend(["", "## Fonte e proveniência", ""])
        for item in validated["SOURCE_AND_PROVENANCE"]:
            lines.append(f"- {_canonical_json(item)}")

    lines.extend(["", "## Cautelas e limites", ""])
    for item in validated["CAUTION_OR_LIMIT"]:
        lines.append(f"- {item}")
    if validated.get("gap_scope"):
        lines.append(f"- GAP_SCOPE={validated['gap_scope']}")

    lines.extend([
        "",
        "## Salvaguardas TASK 209",
        "",
        "- Nenhum filtro solicitado foi descartado silenciosamente.",
        "- Gap contextual significa zero correspondências no corpus materializado consultado, não ausência global.",
        "- Nenhum número ou fato documental foi inventado por linguagem natural.",
        "- Nenhuma relação causal foi criada.",
        "- Nenhuma chamada a LLM, rede, Drive, serving ou publicação foi executada.",
    ])
    markdown = "\n".join(lines).rstrip() + "\n"
    return {
        "schema": contract["render_schema"],
        "state": validated["state"],
        "question_id": validated["question_id"],
        "answer_sha256": validated["answer_sha256"],
        "format": "MARKDOWN",
        "markdown": markdown,
        "markdown_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        "llm_used": False,
        "remote_effects_performed": False,
    }
