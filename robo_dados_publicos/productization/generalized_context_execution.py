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
from robo_dados_publicos.productization.context_aware_execution import (
    _base_filter_accounting,
    _finalize,
    _row_ref,
    _unsupported,
    execute_contextual_query as execute_task209,
    render_contextual_answer_markdown,
)
from robo_dados_publicos.productization.contextual_slot_binder import bind_context


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task210_generalized_context_execution.v1.json"
PRODUCT_CONTRACT = ROOT / "config/observatory_query_products.v1.json"


class Task210ExecutionStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task210ExecutionStop(code)


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
    _stop(obj.get("schema") == "TASK210_GENERALIZED_CONTEXT_EXECUTION_V1", "TASK210_SCHEMA")
    _stop(obj.get("issue") == 664, "TASK210_ISSUE")
    _stop(
        obj.get("base_main_sha") == "3de45f63f9c93b393f1f60ec70ec6787c26a1085",
        "TASK210_BASE",
    )
    _stop(
        obj.get("mode")
        == "T0_OFFLINE_CONTEXT_CAPABILITY_MATRIX_AND_GENERIC_LOCAL_METRIC_EXECUTION",
        "TASK210_MODE",
    )
    _stop(
        set(obj["task209_special_questions"]) == {"FIN_Q1", "NETWORK_Q3", "NORMS_Q2"},
        "TASK210_SPECIAL_SET",
    )
    _stop(
        set(obj["capability_dimensions"])
        == {"SCHOOL", "PERIOD", "POLICY_SERVICE_FACETS", "GRANULARITY"},
        "TASK210_DIMENSIONS",
    )
    bounds = obj["claim_boundaries"]
    _stop(
        bounds["semantic_answerability_equals_contextual_executability"] is False,
        "TASK210_ANSWERABILITY_BOUNDARY",
    )
    _stop(bounds["complete_recipe_required_for_answer"] is True, "TASK210_COMPLETE_RECIPE")
    _stop(bounds["nearest_period_substitution_allowed"] is False, "TASK210_NEAREST_PERIOD")
    _stop(bounds["mixed_product_recipe_auto_promoted"] is False, "TASK210_MIXED_PROMOTION")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK210_REMOTE")
    return obj


def _product_contract() -> dict[str, Any]:
    obj = json.loads(PRODUCT_CONTRACT.read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "OBSERVATORY_QUERY_PRODUCTS_V1", "TASK210_PRODUCT_SCHEMA")
    return obj


def _question_index() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    cfg = current_answerability_config()
    by_id = {str(row["id"]): row for row in cfg["questions"]}
    _stop(len(by_id) == 38, "TASK210_QUESTION_COUNT")
    return cfg, by_id


def _recipe_products(recipe: Mapping[str, Any]) -> list[str]:
    return sorted({str(signal["product"]) for signal in recipe["signals"]})


def _generic_school_metric_recipe(recipe: Mapping[str, Any]) -> bool:
    signals = list(recipe.get("signals") or [])
    return bool(signals) and all(
        signal.get("kind") == "METRIC"
        and signal.get("product") == "SCHOOL_INDICATOR_SERIES"
        for signal in signals
    )


def generic_school_metric_question_ids() -> list[str]:
    cfg, by_id = _question_index()
    result = []
    for qid, question in by_id.items():
        recipe = cfg["recipes"][question["recipe"]]
        if _generic_school_metric_recipe(recipe):
            result.append(qid)
    return sorted(result)


def _product_dimension_inventory(product_names: list[str]) -> list[dict[str, Any]]:
    products = _product_contract()["products"]
    rows = []
    for name in product_names:
        spec = products[name]
        dims = set(str(x) for x in spec.get("query_dimensions") or [])
        rows.append(
            {
                "product": name,
                "query_dimensions": sorted(dims),
                "school_dimension_declared": bool(
                    dims
                    & {
                        "school_code",
                        "scope_id",
                        "geo_id",
                    }
                ),
                "period_dimension_declared": bool(
                    dims
                    & {
                        "period",
                        "publication_date",
                        "fiscal_year",
                        "revenue_month",
                    }
                ),
                "facet_dimension_declared": bool(
                    dims
                    & {
                        "topics",
                        "education_topics",
                        "policy_domains",
                        "evidence_layers",
                        "education_application",
                        "fundeb_classification",
                        "eti_classification",
                    }
                ),
                "granularity_dimension_declared": bool(
                    dims & {"scope_level", "geo_level", "network"}
                ),
            }
        )
    return rows


def build_context_capability_matrix(
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    cfg, by_id = _question_index()
    special = set(contract["task209_special_questions"])
    generic = set(generic_school_metric_question_ids())
    expected_generic = set(contract["generic_school_metric_recipe_questions_expected"])
    _stop(generic == expected_generic, "TASK210_GENERIC_CLASS_DRIFT")

    rows = []
    for qid in sorted(by_id):
        question = by_id[qid]
        recipe = cfg["recipes"][question["recipe"]]
        products = _recipe_products(recipe)
        if qid in special:
            execution_class = "TASK209_SPECIAL"
        elif qid in generic:
            execution_class = "GENERIC_LOCAL_SCHOOL_METRIC"
        else:
            execution_class = "NOT_YET_CONTEXT_EXECUTABLE"

        consumed_facets = sorted(
            contract["recipe_consumed_facets"].get(qid, [])
        )
        if execution_class == "GENERIC_LOCAL_SCHOOL_METRIC":
            filters = {
                "SCHOOL": "EXACT_LOCAL_SUPPORTED",
                "PERIOD": "EXACT_YEAR_SUPPORTED",
                "POLICY_SERVICE_FACETS": (
                    "APPLIED_BY_RECIPE_SCOPE"
                    if consumed_facets
                    else "NO_GENERIC_FACET_FILTER"
                ),
                "GRANULARITY": "SCHOOL_OR_NETWORK_SUPPORTED",
            }
        elif execution_class == "TASK209_SPECIAL":
            filters = {
                dimension: "TASK209_SPECIAL_CONTRACT"
                for dimension in contract["capability_dimensions"]
            }
        else:
            filters = {
                dimension: "NOT_YET_CONTEXT_EXECUTABLE"
                for dimension in contract["capability_dimensions"]
            }

        rows.append(
            {
                "question_id": qid,
                "domain_id": question["domain_id"],
                "question": question["text"],
                "recipe": question["recipe"],
                "recipe_products": products,
                "recipe_signal_kinds": sorted(
                    {str(x["kind"]) for x in recipe["signals"]}
                ),
                "generic_school_metric_recipe": qid in generic,
                "execution_class": execution_class,
                "recipe_consumed_facets": consumed_facets,
                "filters": filters,
                "product_dimension_inventory": _product_dimension_inventory(products),
            }
        )

    counts: dict[str, int] = {}
    for row in rows:
        counts[row["execution_class"]] = counts.get(row["execution_class"], 0) + 1

    _stop(len(rows) == 38, "TASK210_MATRIX_COUNT")
    _stop(
        counts
        == {
            "GENERIC_LOCAL_SCHOOL_METRIC": 8,
            "NOT_YET_CONTEXT_EXECUTABLE": 27,
            "TASK209_SPECIAL": 3,
        },
        "TASK210_MATRIX_CLASS_COUNTS",
    )
    material = {
        "question_ids": [row["question_id"] for row in rows],
        "execution_class_counts": counts,
        "rows": rows,
    }
    return {
        "schema": "TASK210_CONTEXT_CAPABILITY_MATRIX_V1",
        "question_count": 38,
        "generic_school_metric_recipe_count": len(generic),
        "task209_special_count": len(special),
        "new_generic_execution_class_count": counts["GENERIC_LOCAL_SCHOOL_METRIC"],
        "not_yet_context_executable_count": counts["NOT_YET_CONTEXT_EXECUTABLE"],
        "execution_class_counts": dict(sorted(counts.items())),
        "questions": rows,
        "matrix_sha256": _sha(material),
        "semantic_answerability_equals_contextual_executability": False,
        "remote_effects": deepcopy(contract["remote_effects"]),
    }


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    matrix = build_context_capability_matrix(contract_path=path)
    _stop(matrix["question_count"] == 38, "TASK210_VALIDATE_COUNT")
    _stop(matrix["generic_school_metric_recipe_count"] == 9, "TASK210_VALIDATE_GENERIC")
    _stop(matrix["task209_special_count"] == 3, "TASK210_VALIDATE_SPECIAL")
    _stop(matrix["new_generic_execution_class_count"] == 8, "TASK210_VALIDATE_NEW_GENERIC")
    _stop(matrix["not_yet_context_executable_count"] == 27, "TASK210_VALIDATE_NOT_YET")
    return {
        "schema": "TASK210_GENERALIZED_CONTEXT_EXECUTION_VALIDATION_V1",
        "status": "PASS",
        "question_count": 38,
        "generic_school_metric_recipe_count": 9,
        "new_generic_execution_class_count": 8,
        "task209_special_count": 3,
        "not_yet_context_executable_count": 27,
        "matrix_sha256": matrix["matrix_sha256"],
        "network": False,
        "drive_read": False,
        "drive_write": False,
        "llm": False,
    }


def _scope_rows(
    product: Mapping[str, Any],
    *,
    school_code: str | None,
) -> list[dict[str, Any]]:
    result = []
    for raw in product.get("rows", []):
        row = dict(raw)
        level = str(row.get("scope_level") or "")
        if school_code is not None:
            if level != "SCHOOL":
                continue
            if str(row.get("scope_id") or "") != school_code:
                continue
        else:
            if level != "NETWORK":
                continue
            network = str(row.get("network") or "")
            if network and network != "MUNICIPAL":
                continue
        result.append(row)
    return result


def _rows_for_signal_at_period(
    rows: list[dict[str, Any]],
    signal: Mapping[str, Any],
    period: str,
) -> list[dict[str, Any]]:
    ids = {str(x) for x in signal.get("ids") or []}
    selected = [
        row
        for row in rows
        if str(row.get("period") or "") == period
        and str(row.get("indicator_id") or "") in ids
    ]
    selected.sort(key=_canonical_json)
    observed = {str(row.get("indicator_id") or "") for row in selected}
    match = str(signal.get("match") or "ANY")
    if match == "ALL":
        return selected if ids <= observed else []
    _stop(match == "ANY", "TASK210_SIGNAL_MATCH")
    return selected if bool(ids & observed) else []


def _signal_periods(
    rows: list[dict[str, Any]],
    signal: Mapping[str, Any],
) -> set[str]:
    candidates = sorted(
        {
            str(row.get("period") or "")
            for row in rows
            if str(row.get("period") or "").isdigit()
            and len(str(row.get("period") or "")) == 4
        }
    )
    return {
        period
        for period in candidates
        if _rows_for_signal_at_period(rows, signal, period)
    }


def _complete_recipe_periods(
    rows: list[dict[str, Any]],
    recipe: Mapping[str, Any],
) -> set[str]:
    signal_sets = [_signal_periods(rows, signal) for signal in recipe["signals"]]
    if not signal_sets:
        return set()
    result = set(signal_sets[0])
    for periods in signal_sets[1:]:
        result &= periods
    return result


def _fact_from_row(
    row: Mapping[str, Any],
    *,
    school_name: str | None,
) -> dict[str, Any]:
    name = str(row.get("indicator_name") or row.get("indicator_id") or "")
    value = row.get("value")
    unit = str(row.get("unit") or "")
    scope_label = school_name or "rede municipal"
    return {
        "kind": "GENERIC_LOCAL_METRIC",
        "metric_id": row.get("indicator_id"),
        "metric_name": name,
        "period": row.get("period"),
        "scope_level": row.get("scope_level"),
        "scope_id": row.get("scope_id"),
        "value": value,
        "unit": unit,
        "text": (
            f"{name}: {value} {unit} | escopo={scope_label} | período={row.get('period')}."
        ),
    }


def _generic_gap(
    *,
    text: str,
    context: Mapping[str, Any],
    question_id: str,
    filters: dict[str, Any],
    product: Mapping[str, Any],
    requested_period: str | None,
    recipe: Mapping[str, Any],
    scoped_rows: list[dict[str, Any]],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    signal_status = []
    for index, signal in enumerate(recipe["signals"], start=1):
        if requested_period is None:
            periods = sorted(_signal_periods(scoped_rows, signal))
            satisfied = bool(periods)
        else:
            rows = _rows_for_signal_at_period(scoped_rows, signal, requested_period)
            periods = [requested_period] if rows else []
            satisfied = bool(rows)
        signal_status.append(
            {
                "signal_index": index,
                "ids": list(signal.get("ids") or []),
                "match": signal.get("match", "ANY"),
                "satisfied": satisfied,
                "matching_periods": periods,
            }
        )

    if filters["PERIOD"]["status"] == "PENDING":
        filters["PERIOD"]["status"] = "APPLIED_TO_INCOMPLETE_RECIPE"
    if filters["SCHOOL"]["status"] == "PENDING":
        filters["SCHOOL"]["status"] = "APPLIED_TO_INCOMPLETE_RECIPE"
    if filters["GRANULARITY"]["status"] == "PENDING":
        filters["GRANULARITY"]["status"] = "APPLIED_TO_INCOMPLETE_RECIPE"

    return _finalize(
        state="EXPLICIT_CONTEXT_GAP",
        text=text,
        context=context,
        question_id=question_id,
        filter_accounting=filters,
        facts=[
            {
                "kind": "CONTEXT_RECIPE_GAP",
                "text": (
                    "O contexto exato solicitado não contém evidência suficiente para satisfazer "
                    "todas as partes da receita canônica. Evidência parcial não foi promovida a resposta completa."
                ),
            }
        ],
        time_reference=[requested_period] if requested_period else [],
        provenance=[
            {
                "product": "SCHOOL_INDICATOR_SERIES",
                "snapshot_id": product.get("snapshot_id"),
                "content_sha256": product.get("content_sha256"),
                "declared_row_count": product.get("row_count"),
                "local_scoped_row_count": len(scoped_rows),
                "requested_period": requested_period,
                "recipe_signal_status": signal_status,
            }
        ],
        cautions=[
            "INCOMPLETE_CONTEXT_RECIPE_NE_FULL_ANSWER",
            "EXACT_CONTEXT_GAP_NE_GLOBAL_ABSENCE",
            "NO_NEAREST_PERIOD_SUBSTITUTION",
            "SEMANTIC_ANSWERABILITY_NE_CONTEXTUAL_EXECUTABILITY",
        ],
        gap_scope="CURRENT_LOCAL_SCHOOL_INDICATOR_SERIES_EXACT_CONTEXT",
        contract=contract,
    )


def _execute_generic_school_metric(
    *,
    text: str,
    context: Mapping[str, Any],
    question_id: str,
    generated_at: str,
    software_version: str,
    task210_contract: Mapping[str, Any],
) -> dict[str, Any]:
    task209_contract = json.loads(
        (ROOT / "config/task209_context_aware_execution.v1.json").read_text(encoding="utf-8")
    )
    filters = _base_filter_accounting(context)
    cfg, by_id = _question_index()
    question = by_id[question_id]
    recipe = cfg["recipes"][question["recipe"]]
    _stop(_generic_school_metric_recipe(recipe), "TASK210_GENERIC_RECIPE_EXPECTED")

    school = context["school"]
    school_code = (
        str(school["school_code"])
        if school.get("status") == "RESOLVED"
        else None
    )
    school_name = (
        str(school["school_name"])
        if school.get("status") == "RESOLVED"
        else None
    )

    granularity = str(context["granularity"].get("value") or "")
    if school_code is not None:
        if granularity != "SCHOOL":
            return _unsupported(
                text,
                context,
                question_id,
                filters,
                "Generic TASK210 metric execution supports one exact SCHOOL scope; SCHOOL_VS_NETWORK remains a special comparison class.",
                task209_contract,
            )
    elif granularity not in {"NETWORK", "MUNICIPALITY"}:
        return _unsupported(
            text,
            context,
            question_id,
            filters,
            "Generic TASK210 metric execution without a school uses the municipal NETWORK scope.",
            task209_contract,
        )

    period = context["period"]
    requested_period: str | None = None
    if period.get("status") == "RESOLVED":
        if period.get("mode") != "YEAR":
            return _unsupported(
                text,
                context,
                question_id,
                filters,
                "Generic TASK210 metric execution supports exact YEAR context only; month and year-to-month are not snapped to a year.",
                task209_contract,
            )
        requested_period = str(period["year"])

    facets = set(str(x) for x in context.get("policy_service_facets") or [])
    consumed = set(task210_contract["recipe_consumed_facets"].get(question_id, []))
    if facets:
        if not facets <= consumed:
            return _unsupported(
                text,
                context,
                question_id,
                filters,
                "One or more requested policy/service facets are not consumed by this generic metric recipe.",
                task209_contract,
            )
        filters["POLICY_SERVICE_FACETS"]["status"] = "APPLIED_BY_RECIPE_SCOPE"

    products = build_current_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    product = products["SCHOOL_INDICATOR_SERIES"]
    scoped_rows = _scope_rows(product, school_code=school_code)
    complete_periods = sorted(_complete_recipe_periods(scoped_rows, recipe))

    if requested_period is not None:
        if requested_period not in complete_periods:
            return _generic_gap(
                text=text,
                context=context,
                question_id=question_id,
                filters=filters,
                product=product,
                requested_period=requested_period,
                recipe=recipe,
                scoped_rows=scoped_rows,
                contract=task209_contract,
            )
        selected_period = requested_period
    else:
        if not complete_periods:
            return _generic_gap(
                text=text,
                context=context,
                question_id=question_id,
                filters=filters,
                product=product,
                requested_period=None,
                recipe=recipe,
                scoped_rows=scoped_rows,
                contract=task209_contract,
            )
        selected_period = complete_periods[-1]

    selected_rows: list[dict[str, Any]] = []
    cautions = {
        "GENERIC_RECIPE_METRIC_SELECTION_NE_CAUSAL_EXPLANATION",
        "SEMANTIC_ANSWERABILITY_NE_CONTEXTUAL_EXECUTABILITY",
    }
    historical_recipe = False
    for signal in recipe["signals"]:
        rows = _rows_for_signal_at_period(scoped_rows, signal, selected_period)
        _stop(bool(rows), "TASK210_SELECTED_PERIOD_RECIPE_DRIFT")
        selected_rows.extend(rows)
        if int(signal.get("min_periods") or 1) > 1:
            historical_recipe = True
        for row in rows:
            if row.get("caution"):
                cautions.add(str(row["caution"]))
    if historical_recipe:
        cautions.add("CONTEXTUAL_SINGLE_YEAR_SNAPSHOT_NE_HISTORICAL_TREND")

    deduped = {
        _canonical_json(row): row
        for row in selected_rows
    }
    selected_rows = [deduped[key] for key in sorted(deduped)]
    facts = [
        _fact_from_row(row, school_name=school_name)
        for row in selected_rows
    ]
    provenance = [
        _row_ref("SCHOOL_INDICATOR_SERIES", row)
        for row in selected_rows
    ]

    if filters["SCHOOL"]["status"] == "PENDING":
        filters["SCHOOL"]["status"] = "APPLIED"
    if filters["PERIOD"]["status"] == "PENDING":
        filters["PERIOD"]["status"] = "APPLIED"
    filters["GRANULARITY"]["status"] = "APPLIED"

    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id=question_id,
        filter_accounting=filters,
        facts=facts,
        time_reference=[selected_period],
        comparisons=[],
        provenance=provenance,
        cautions=sorted(cautions),
        contract=task209_contract,
    )


def _context_filter_requested(context: Mapping[str, Any]) -> bool:
    return (
        context["school"].get("status") == "RESOLVED"
        or context["period"].get("status") == "RESOLVED"
        or bool(context.get("policy_service_facets"))
        or context["granularity"].get("value") in {"SCHOOL", "SCHOOL_VS_NETWORK", "NETWORK"}
    )


def execute_contextual_query_v2(
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
    _stop(bool(generated_at), "TASK210_GENERATED_AT")
    _stop(bool(software_version), "TASK210_SOFTWARE_VERSION")

    context = bind_context(
        text,
        reference_date=reference_date,
        context_school_code=context_school_code,
    )
    if context["state"] != "CONTEXT_BOUND":
        return execute_task209(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )

    qids = list(context.get("selected_question_ids") or [])
    if len(qids) != 1:
        return execute_task209(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )
    qid = qids[0]

    if qid in set(contract["task209_special_questions"]):
        return execute_task209(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )

    if not _context_filter_requested(context):
        return execute_task209(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )

    generic_ids = set(generic_school_metric_question_ids())
    if qid not in generic_ids:
        return execute_task209(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )

    return _execute_generic_school_metric(
        text=text,
        context=context,
        question_id=qid,
        generated_at=generated_at,
        software_version=software_version,
        task210_contract=contract,
    )


def render_contextual_answer_v2(
    answer: Mapping[str, Any],
) -> dict[str, Any]:
    return render_contextual_answer_markdown(answer)
