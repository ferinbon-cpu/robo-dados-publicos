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
from robo_dados_publicos.productization.context_aware_execution import (
    _base_filter_accounting,
    _finalize,
    _unsupported,
    render_contextual_answer_markdown,
)
from robo_dados_publicos.productization.contextual_slot_binder import bind_context
from robo_dados_publicos.productization.generalized_context_execution import (
    build_context_capability_matrix,
    execute_contextual_query_v2,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task211_document_event_context_execution.v1.json"
TASK209_CONTRACT = ROOT / "config/task209_context_aware_execution.v1.json"


class Task211ExecutionStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task211ExecutionStop(code)


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
    _stop(obj.get("schema") == "TASK211_DOCUMENT_EVENT_CONTEXT_EXECUTION_V1", "TASK211_SCHEMA")
    _stop(obj.get("issue") == 666, "TASK211_ISSUE")
    _stop(
        obj.get("base_main_sha") == "a78a57d08d244b781ad0dcaa329a5285341b408c",
        "TASK211_BASE",
    )
    _stop(
        obj.get("mode") == "T0_OFFLINE_LOCAL_DOCUMENT_EVENT_CONTEXT_EXECUTION",
        "TASK211_MODE",
    )
    _stop(
        set(obj["local_document_event_products"])
        == {"JOM_EVENT_INDEX", "PLANNING_DOCUMENT_INDEX"},
        "TASK211_PRODUCTS",
    )
    _stop(obj["period"]["nearest_period_substitution"] is False, "TASK211_NEAREST_PERIOD")
    _stop(obj["period"]["month_coercion"] is False, "TASK211_MONTH_COERCION")
    _stop(
        obj["facet_filtering"]["object_text_semantic_guessing"] is False,
        "TASK211_TEXT_GUESSING",
    )
    _stop(
        obj["recipe_semantics"]["min_rows_are_global_coverage_gates_not_contextual_minimums"]
        is True,
        "TASK211_MIN_ROWS_SEMANTICS",
    )
    _stop(
        obj["recipe_semantics"]["required_source_family_role_pairs_require_all_families_inside_each_context_slice"]
        is False,
        "TASK211_SOURCE_DIVERSITY_SLICE",
    )
    bounds = obj["claim_boundaries"]
    _stop(bounds["school_identity_from_document_text_allowed"] is False, "TASK211_SCHOOL_TEXT_ID")
    _stop(bounds["context_zero_match_equals_global_absence"] is False, "TASK211_GLOBAL_ABSENCE")
    _stop(bounds["current_jom_materialization_equals_complete_year"] is False, "TASK211_JOM_YEAR")
    _stop(bounds["partial_recipe_signal_equals_full_answer"] is False, "TASK211_PARTIAL_FULL")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK211_REMOTE")
    return obj


def _task209_contract() -> dict[str, Any]:
    return json.loads(TASK209_CONTRACT.read_text(encoding="utf-8"))


def _question_index() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    cfg = current_answerability_config()
    by_id = {str(row["id"]): row for row in cfg["questions"]}
    _stop(len(by_id) == 38, "TASK211_QUESTION_COUNT")
    return cfg, by_id


def _recipe_products(recipe: Mapping[str, Any]) -> set[str]:
    return {str(signal["product"]) for signal in recipe.get("signals") or []}


def _document_event_recipe(
    recipe: Mapping[str, Any],
    *,
    local_products: set[str],
) -> bool:
    signals = list(recipe.get("signals") or [])
    return bool(signals) and all(
        signal.get("kind") == "PRODUCT"
        and str(signal.get("product") or "") in local_products
        for signal in signals
    )


def document_event_recipe_question_ids(
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> list[str]:
    contract = load_contract(contract_path)
    cfg, by_id = _question_index()
    local_products = set(contract["local_document_event_products"])
    result = []
    for qid, question in by_id.items():
        recipe = cfg["recipes"][question["recipe"]]
        if _document_event_recipe(recipe, local_products=local_products):
            result.append(qid)
    return sorted(result)


def build_extended_context_capability_matrix(
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    base = build_context_capability_matrix()
    derived = set(document_event_recipe_question_ids(contract_path=contract_path))
    expected = set(contract["expected_recipe_class_questions"])
    _stop(derived == expected, "TASK211_RECIPE_CLASS_DRIFT")

    special_overlap = set(contract["task209_special_overlap"])
    promoted = derived - special_overlap
    _stop(
        promoted == set(contract["new_generic_document_event_questions"]),
        "TASK211_PROMOTED_SET_DRIFT",
    )

    rows = []
    for raw in base["questions"]:
        row = deepcopy(raw)
        qid = str(row["question_id"])
        if qid in promoted:
            _stop(
                row["execution_class"] == "NOT_YET_CONTEXT_EXECUTABLE",
                "TASK211_EXPECTED_BASE_NOT_YET",
            )
            row["execution_class"] = "GENERIC_LOCAL_DOCUMENT_EVENT"
            row["filters"] = {
                "SCHOOL": "UNSUPPORTED_WITHOUT_STRUCTURED_SCHOOL_IDENTITY",
                "PERIOD": "EXACT_YEAR_SUPPORTED",
                "POLICY_SERVICE_FACETS": "STRUCTURED_TOPIC_FILTER_SUPPORTED",
                "GRANULARITY": "DOCUMENT_EVENT_SUPPORTED",
            }
        rows.append(row)

    counts = Counter(str(row["execution_class"]) for row in rows)
    target = {str(k): int(v) for k, v in contract["extended_matrix_target"].items()}
    _stop(dict(counts) == target, "TASK211_MATRIX_COUNTS")
    _stop(len(rows) == 38, "TASK211_MATRIX_ROWS")

    material = {
        "question_ids": [row["question_id"] for row in rows],
        "execution_class_counts": dict(sorted(counts.items())),
        "rows": rows,
    }
    return {
        "schema": "TASK211_EXTENDED_CONTEXT_CAPABILITY_MATRIX_V1",
        "question_count": 38,
        "document_event_recipe_question_count": len(derived),
        "new_generic_document_event_count": len(promoted),
        "execution_class_counts": dict(sorted(counts.items())),
        "questions": rows,
        "matrix_sha256": _sha(material),
        "semantic_answerability_equals_contextual_executability": False,
        "remote_effects": deepcopy(contract["remote_effects"]),
    }


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(path)
    matrix = build_extended_context_capability_matrix(contract_path=path)
    _stop(matrix["question_count"] == 38, "TASK211_VALIDATE_COUNT")
    _stop(matrix["document_event_recipe_question_count"] == 10, "TASK211_VALIDATE_CLASS")
    _stop(matrix["new_generic_document_event_count"] == 9, "TASK211_VALIDATE_NEW")
    _stop(
        matrix["execution_class_counts"] == contract["extended_matrix_target"],
        "TASK211_VALIDATE_MATRIX",
    )
    return {
        "schema": "TASK211_DOCUMENT_EVENT_CONTEXT_EXECUTION_VALIDATION_V1",
        "status": "PASS",
        "question_count": 38,
        "document_event_recipe_question_count": 10,
        "new_generic_document_event_count": 9,
        "execution_class_counts": dict(matrix["execution_class_counts"]),
        "matrix_sha256": matrix["matrix_sha256"],
        "network": False,
        "drive_read": False,
        "drive_write": False,
        "llm": False,
    }


def _period_years(value: Any) -> set[int]:
    text = str(value or "").strip()
    if len(text) == 4 and text.isdigit():
        return {int(text)}
    if (
        len(text) == 9
        and text[:4].isdigit()
        and text[4] == "-"
        and text[5:].isdigit()
    ):
        first = int(text[:4])
        last = int(text[5:])
        if last >= first:
            return set(range(first, last + 1))
    if len(text) >= 4 and text[:4].isdigit():
        return {int(text[:4])}
    return set()


def _row_matches_year(
    product_name: str,
    row: Mapping[str, Any],
    year: int,
) -> bool:
    if product_name == "JOM_EVENT_INDEX":
        return year in _period_years(row.get("publication_date"))
    if product_name == "PLANNING_DOCUMENT_INDEX":
        return year in _period_years(row.get("period"))
    raise Task211ExecutionStop("TASK211_UNKNOWN_PRODUCT_YEAR")


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
            raise Task211ExecutionStop(f"TASK211_UNSUPPORTED_ROW_CRITERION:{key}")
        field = key[:-4]
        allowed = _values(allowed_raw)
        observed = _values(row.get(field))
        if not (allowed & observed):
            return False
    return True


def _recipe_eligible_rows(
    product_name: str,
    product: Mapping[str, Any],
    signal: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = [dict(row) for row in product.get("rows", [])]
    criteria = dict(signal.get("row_criteria") or {})
    if criteria:
        rows = [row for row in rows if _row_criteria_match(row, criteria)]

    family_roles = dict(signal.get("required_source_family_role_pairs") or {})
    if family_roles:
        rows = [
            row
            for row in rows
            if str(row.get("source_family") or "") in family_roles
            and str(row.get("evidence_role") or "")
            in set(family_roles[str(row.get("source_family") or "")])
        ]

    document_roles = dict(signal.get("required_document_role_pairs") or {})
    if document_roles:
        rows = [
            row
            for row in rows
            if str(row.get("document_type") or "") in document_roles
            and str(row.get("evidence_role") or "")
            in set(document_roles[str(row.get("document_type") or "")])
        ]

    rows.sort(key=_canonical_json)
    return rows


def _facet_topics() -> dict[str, list[str]]:
    obj = _task209_contract()
    return {
        str(k): [str(x) for x in v]
        for k, v in obj["policy_facet_topics"].items()
    }


def _row_matches_facets(
    product_name: str,
    row: Mapping[str, Any],
    facets: list[str],
    mappings: Mapping[str, list[str]],
) -> bool:
    if not facets:
        return True
    field = (
        "education_topics"
        if product_name == "JOM_EVENT_INDEX"
        else "topics"
    )
    observed = _values(row.get(field))
    for facet in facets:
        allowed = set(mappings[facet])
        if not (allowed & observed):
            return False
    return True


def _contextual_rows(
    product_name: str,
    rows: list[dict[str, Any]],
    *,
    year: int | None,
    facets: list[str],
    mappings: Mapping[str, list[str]],
) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        if year is not None and not _row_matches_year(product_name, row, year):
            continue
        if not _row_matches_facets(product_name, row, facets, mappings):
            continue
        result.append(row)
    return result


def _required_document_types_present(
    rows: list[dict[str, Any]],
    signal: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    required = sorted(
        str(x)
        for x in (signal.get("required_document_role_pairs") or {})
    )
    if not required:
        return True, []
    observed = {
        str(row.get("document_type") or "")
        for row in rows
        if row.get("document_type")
    }
    missing = sorted(set(required) - observed)
    return not missing, missing


def _jom_identity(row: Mapping[str, Any]) -> str:
    return str(row.get("event_id") or row.get("provenance_ref") or "")


def _planning_identity(row: Mapping[str, Any]) -> str:
    return f"{row.get('document_id')}|{row.get('locator')}"


def _selected_identity_sha(
    product_name: str,
    rows: list[dict[str, Any]],
) -> str:
    ids = (
        sorted(_jom_identity(row) for row in rows)
        if product_name == "JOM_EVENT_INDEX"
        else sorted(_planning_identity(row) for row in rows)
    )
    return _sha(ids)


def _counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        for value in _values(row.get(field)):
            counter[value] += 1
    return dict(sorted(counter.items()))


def _jom_sample(
    rows: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            bool(str(row.get("object_text") or "").strip()),
            str(row.get("publication_date") or ""),
            _jom_identity(row),
        ),
        reverse=True,
    )[:limit]


def _planning_sample(
    rows: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda row: (
            str(row.get("period") or ""),
            str(row.get("document_type") or ""),
            str(row.get("document_id") or ""),
            str(row.get("locator") or ""),
        ),
    )[:limit]


def _event_fact(row: Mapping[str, Any]) -> dict[str, Any]:
    object_text = str(row.get("object_text") or "").strip()
    detail = object_text if object_text else "objeto textual não materializado neste índice"
    return {
        "kind": "JOM_EVENT",
        "event_id": row.get("event_id"),
        "publication_date": row.get("publication_date"),
        "event_type": row.get("event_type"),
        "policy_domains": list(row.get("policy_domains") or []),
        "evidence_layers": list(row.get("evidence_layers") or []),
        "education_topics": list(row.get("education_topics") or []),
        "text": (
            f"{row.get('publication_date')} | {row.get('event_type')} | "
            f"{detail} | event_id={row.get('event_id')}."
        ),
    }


def _planning_fact(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "kind": "PLANNING_DOCUMENT",
        "document_id": row.get("document_id"),
        "document_type": row.get("document_type"),
        "period": row.get("period"),
        "evidence_role": row.get("evidence_role"),
        "quality_status": row.get("quality_status"),
        "topics": list(row.get("topics") or []),
        "text": (
            f"{row.get('document_type')} | período={row.get('period')} | "
            f"papel={row.get('evidence_role')} | {row.get('text_redacted')} "
            f"| locator={row.get('locator')}."
        ),
    }


def _row_provenance(
    product_name: str,
    row: Mapping[str, Any],
) -> dict[str, Any]:
    base = {
        "product": product_name,
        "source_family": row.get("source_family"),
        "source_sha256": row.get("source_sha256"),
        "provenance_ref": row.get("provenance_ref"),
    }
    if product_name == "JOM_EVENT_INDEX":
        base.update(
            {
                "event_id": row.get("event_id"),
                "publication_date": row.get("publication_date"),
                "event_type": row.get("event_type"),
                "source_locator": deepcopy(row.get("source_locator")),
            }
        )
    else:
        base.update(
            {
                "document_id": row.get("document_id"),
                "document_type": row.get("document_type"),
                "period": row.get("period"),
                "evidence_role": row.get("evidence_role"),
                "quality_status": row.get("quality_status"),
                "locator": row.get("locator"),
            }
        )
    return {k: v for k, v in base.items() if v not in (None, "", [], {})}


def _context_gap(
    *,
    text: str,
    context: Mapping[str, Any],
    question_id: str,
    filters: dict[str, Any],
    signal_status: list[dict[str, Any]],
    products: Mapping[str, Mapping[str, Any]],
    year: int | None,
    facets: list[str],
    task209_contract: Mapping[str, Any],
) -> dict[str, Any]:
    for key in ("PERIOD", "POLICY_SERVICE_FACETS"):
        if filters[key]["status"] == "PENDING":
            filters[key]["status"] = "APPLIED_TO_ZERO_OR_INCOMPLETE_RECIPE"
    filters["GRANULARITY"]["status"] = "APPLIED"

    provenance = []
    for name in sorted({row["product"] for row in signal_status}):
        product = products[name]
        provenance.append(
            {
                "product": name,
                "snapshot_id": product.get("snapshot_id"),
                "content_sha256": product.get("content_sha256"),
                "local_row_count": len(product.get("rows", [])),
            }
        )
    provenance.append(
        {
            "context_recipe_signal_status": signal_status,
            "requested_year": year,
            "requested_facets": facets,
        }
    )
    return _finalize(
        state="EXPLICIT_CONTEXT_GAP",
        text=text,
        context=context,
        question_id=question_id,
        filter_accounting=filters,
        facts=[
            {
                "kind": "DOCUMENT_EVENT_CONTEXT_GAP",
                "text": (
                    "O recorte documental/eventual exato não satisfaz todas as partes da "
                    "receita canônica com os produtos locais materializados. Isso não prova ausência global."
                ),
            }
        ],
        time_reference=[str(year)] if year is not None else [],
        provenance=provenance,
        cautions=[
            "EXACT_CONTEXT_GAP_NE_GLOBAL_ABSENCE",
            "PARTIAL_RECIPE_SIGNAL_NE_FULL_ANSWER",
            "CURRENT_LOCAL_DOCUMENT_EVENT_CORPUS_ONLY",
            "NO_NEAREST_PERIOD_SUBSTITUTION",
        ],
        gap_scope="CURRENT_LOCAL_DOCUMENT_EVENT_PRODUCTS_EXACT_CONTEXT",
        contract=task209_contract,
    )


def _execute_document_event(
    *,
    text: str,
    context: Mapping[str, Any],
    question_id: str,
    generated_at: str,
    software_version: str,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    task209_contract = _task209_contract()
    filters = _base_filter_accounting(context)

    if context["school"].get("status") == "RESOLVED":
        return _unsupported(
            text,
            context,
            question_id,
            filters,
            (
                "This document/event executor has no structured school identity dimension; "
                "school identity was not inferred from object_text."
            ),
            task209_contract,
        )

    period = context["period"]
    year: int | None = None
    if period.get("status") == "RESOLVED":
        if period.get("mode") != "YEAR":
            return _unsupported(
                text,
                context,
                question_id,
                filters,
                (
                    "TASK211 supports exact YEAR document/event context only; "
                    "month and year-to-month are not coerced to a year."
                ),
                task209_contract,
            )
        year = int(period["year"])

    facets = [str(x) for x in context.get("policy_service_facets") or []]
    mappings = _facet_topics()
    for facet in facets:
        if facet not in mappings or not mappings[facet]:
            return _unsupported(
                text,
                context,
                question_id,
                filters,
                f"Facet {facet} has no structured TASK211 topic mapping; text guessing was not used.",
                task209_contract,
            )

    cfg, by_id = _question_index()
    question = by_id[question_id]
    recipe = cfg["recipes"][question["recipe"]]
    local_products = set(contract["local_document_event_products"])
    _stop(
        _document_event_recipe(recipe, local_products=local_products),
        "TASK211_EXECUTOR_RECIPE_CLASS",
    )

    products = build_current_products(
        generated_at=generated_at,
        software_version=software_version,
    )

    all_selected: dict[str, list[dict[str, Any]]] = {}
    signal_status: list[dict[str, Any]] = []
    all_satisfied = True
    for index, signal in enumerate(recipe["signals"], start=1):
        product_name = str(signal["product"])
        product = products[product_name]
        eligible = _recipe_eligible_rows(product_name, product, signal)
        selected = _contextual_rows(
            product_name,
            eligible,
            year=year,
            facets=facets,
            mappings=mappings,
        )
        document_types_ok, missing_document_types = _required_document_types_present(
            selected,
            signal,
        )
        satisfied = bool(selected) and document_types_ok
        all_satisfied = all_satisfied and satisfied
        all_selected.setdefault(product_name, []).extend(selected)
        signal_status.append(
            {
                "signal_index": index,
                "product": product_name,
                "eligible_row_count_before_context": len(eligible),
                "context_matching_row_count": len(selected),
                "satisfied": satisfied,
                "missing_required_document_types": missing_document_types,
                "global_min_rows_not_reapplied_to_slice": (
                    signal.get("min_rows")
                    if signal.get("min_rows") is not None
                    else signal.get("min_matching_rows")
                ),
                "source_family_diversity_not_required_inside_slice": bool(
                    signal.get("required_source_family_role_pairs")
                ),
            }
        )

    if not all_satisfied:
        return _context_gap(
            text=text,
            context=context,
            question_id=question_id,
            filters=filters,
            signal_status=signal_status,
            products=products,
            year=year,
            facets=facets,
            task209_contract=task209_contract,
        )

    if filters["PERIOD"]["status"] == "PENDING":
        filters["PERIOD"]["status"] = "APPLIED"
    if filters["POLICY_SERVICE_FACETS"]["status"] == "PENDING":
        filters["POLICY_SERVICE_FACETS"]["status"] = "APPLIED"
    filters["GRANULARITY"]["status"] = "APPLIED"

    facts: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    cautions = {
        "CONTEXTUAL_SLICE_NE_GLOBAL_RECIPE_COVERAGE_GATE",
        "PUBLICATION_NE_IMPLEMENTATION",
        "NORMATIVE_ACT_NE_IMPLEMENTATION",
        "PLANNING_NE_ACCOUNTING_EXECUTION",
        "NO_TEXT_BASED_SCHOOL_IDENTITY_INFERENCE",
    }

    for product_name in sorted(all_selected):
        deduped = {
            _canonical_json(row): row
            for row in all_selected[product_name]
        }
        rows = [deduped[key] for key in sorted(deduped)]
        product = products[product_name]
        if product_name == "JOM_EVENT_INDEX":
            sample = _jom_sample(
                rows,
                limit=int(contract["display"]["jom_max_event_facts"]),
            )
            event_type_counts = _counts(rows, "event_type")
            layer_counts = _counts(rows, "evidence_layers")
            domain_counts = _counts(rows, "policy_domains")
            facts.append(
                {
                    "kind": "DOCUMENT_EVENT_SUMMARY",
                    "product": product_name,
                    "matched_row_count": len(rows),
                    "displayed_row_count": len(sample),
                    "event_type_counts": event_type_counts,
                    "evidence_layer_counts": layer_counts,
                    "policy_domain_counts": domain_counts,
                    "matched_identity_sha256": _selected_identity_sha(product_name, rows),
                    "text": (
                        f"JOM_EVENT_INDEX: {len(rows)} eventos no recorte exato; "
                        f"{len(sample)} eventos exibidos de forma determinística."
                    ),
                }
            )
            facts.extend(_event_fact(row) for row in sample)
            provenance.append(
                {
                    "product": product_name,
                    "snapshot_id": product.get("snapshot_id"),
                    "content_sha256": product.get("content_sha256"),
                    "matched_row_count": len(rows),
                    "displayed_row_count": len(sample),
                    "matched_identity_sha256": _selected_identity_sha(product_name, rows),
                }
            )
            provenance.extend(_row_provenance(product_name, row) for row in sample)
            cautions.add("CURRENT_MATERIALIZED_JOM_CORPUS_NE_COMPLETE_YEAR")
            if len(sample) < len(rows):
                cautions.add("DISPLAY_SAMPLE_NE_ALL_MATCHING_EVENTS")
        else:
            sample = _planning_sample(
                rows,
                limit=int(contract["display"]["planning_max_document_facts"]),
            )
            facts.append(
                {
                    "kind": "DOCUMENT_EVENT_SUMMARY",
                    "product": product_name,
                    "matched_row_count": len(rows),
                    "displayed_row_count": len(sample),
                    "document_type_counts": _counts(rows, "document_type"),
                    "source_family_counts": _counts(rows, "source_family"),
                    "evidence_role_counts": _counts(rows, "evidence_role"),
                    "matched_identity_sha256": _selected_identity_sha(product_name, rows),
                    "text": (
                        f"PLANNING_DOCUMENT_INDEX: {len(rows)} segmentos documentais "
                        f"no recorte exato; {len(sample)} exibidos."
                    ),
                }
            )
            facts.extend(_planning_fact(row) for row in sample)
            provenance.append(
                {
                    "product": product_name,
                    "snapshot_id": product.get("snapshot_id"),
                    "content_sha256": product.get("content_sha256"),
                    "matched_row_count": len(rows),
                    "displayed_row_count": len(sample),
                    "matched_identity_sha256": _selected_identity_sha(product_name, rows),
                }
            )
            provenance.extend(_row_provenance(product_name, row) for row in sample)

        for row in rows:
            if row.get("caution"):
                cautions.add(str(row["caution"]))

    return _finalize(
        state="ANSWERED_CONTEXTUALLY",
        text=text,
        context=context,
        question_id=question_id,
        filter_accounting=filters,
        facts=facts,
        time_reference=[str(year)] if year is not None else [],
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
    )


def execute_contextual_query_v3(
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
    _stop(bool(generated_at), "TASK211_GENERATED_AT")
    _stop(bool(software_version), "TASK211_SOFTWARE_VERSION")

    context = bind_context(
        text,
        reference_date=reference_date,
        context_school_code=context_school_code,
    )
    if context["state"] != "CONTEXT_BOUND":
        return execute_contextual_query_v2(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )

    qids = list(context.get("selected_question_ids") or [])
    if len(qids) != 1 or not _context_filter_requested(context):
        return execute_contextual_query_v2(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )

    qid = qids[0]
    promoted = set(contract["new_generic_document_event_questions"])
    if qid not in promoted:
        return execute_contextual_query_v2(
            text,
            generated_at=generated_at,
            software_version=software_version,
            reference_date=reference_date,
            context_school_code=context_school_code,
        )

    return _execute_document_event(
        text=text,
        context=context,
        question_id=qid,
        generated_at=generated_at,
        software_version=software_version,
        contract=contract,
    )


def render_contextual_answer_v3(
    answer: Mapping[str, Any],
) -> dict[str, Any]:
    return render_contextual_answer_markdown(answer)
