from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.analytics.current_observatory_answerability import (
    current_answerability_config,
    current_question_answerability,
)
from robo_dados_publicos.analytics.current_observatory_bundle import (
    build_current_products,
)
from robo_dados_publicos.analytics.observatory_products import query_observatory


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task203_current_bundle_productization.v1.json"


class ProductizationReadinessStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise ProductizationReadinessStop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK203_CURRENT_BUNDLE_PRODUCTIZATION_V1", "TASK203_SCHEMA")
    _stop(obj.get("issue") == 649, "TASK203_ISSUE")
    _stop(
        obj.get("base_main_sha") == "10dea8a216fa1c52060c61e83977fe3a874a0554",
        "TASK203_BASE",
    )
    _stop(
        obj["canonical_answerability"]["expected_status_counts"]
        == {"MATERIALIZED_ANSWERABLE": 38},
        "TASK203_ANSWERABILITY_EXPECTATION",
    )
    _stop(
        sum(obj["expected_productization_counts"].values()) == 38,
        "TASK203_PRODUCTIZATION_TOTAL",
    )
    _stop(
        obj["expected_query_projection_backlog_count"] == 11,
        "TASK203_BACKLOG_COUNT",
    )
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK203_REMOTE")
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
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


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
                _stop(field.endswith("_any"), "TASK203_PRODUCT_CRITERIA_FIELD")
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


def _matching_metric_rows(
    signal: Mapping[str, Any],
    product: Mapping[str, Any],
) -> list[dict[str, Any]]:
    ids = {str(x) for x in signal["ids"]}
    if signal["product"] == "SCHOOL_INDICATOR_SERIES":
        field = "indicator_id"
    elif signal["product"] == "FISCAL_SERIES":
        field = "metric_id"
    else:
        raise ProductizationReadinessStop("TASK203_UNKNOWN_METRIC_PRODUCT")
    rows = [
        dict(row)
        for row in product.get("rows", [])
        if str(row.get(field) or "") in ids
    ]
    rows.sort(key=_row_identity)
    return rows


def _record_ref(product_name: str, row: Mapping[str, Any]) -> dict[str, Any]:
    ref = {"product": product_name}
    for field in (
        "indicator_id",
        "metric_id",
        "scope_level",
        "scope_id",
        "period",
        "event_id",
        "document_id",
        "locator",
        "school_code",
        "geo_id",
        "source_family",
        "source_sha256",
        "provenance_ref",
        "quality_status",
    ):
        value = row.get(field)
        if value not in (None, "", [], {}):
            ref[field] = value
    return ref


def _signal_trace(
    signal: Mapping[str, Any],
    result: Mapping[str, Any],
    products: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    product_name = str(signal["product"])
    product = products[product_name]
    if signal["kind"] == "METRIC":
        rows = _matching_metric_rows(signal, product)
    else:
        rows = _matching_product_rows(signal, product)

    local_count = len(rows)
    declared_count = int(product.get("row_count") or 0)
    required_capabilities = sorted(str(x) for x in signal.get("required_capabilities") or [])
    observed_capabilities = sorted(str(x) for x in product.get("capabilities") or [])

    if local_count > 0:
        backing = "LOCAL_RECORDS"
    elif result.get("state") == "FULL" and signal["kind"] == "PRODUCT":
        backing = "CAPABILITY_METADATA_ONLY"
    else:
        backing = "UNEXPECTED_EMPTY"

    _stop(
        not (backing == "CAPABILITY_METADATA_ONLY" and signal["kind"] == "METRIC"),
        "TASK203_METRIC_CAPABILITY_ONLY_FORBIDDEN",
    )
    return {
        "kind": signal["kind"],
        "product": product_name,
        "answerability_state": result["state"],
        "backing": backing,
        "local_record_count": local_count,
        "declared_product_row_count": declared_count,
        "required_capabilities": required_capabilities,
        "observed_capabilities": observed_capabilities,
        "remote_snapshot_drive_id": product.get("remote_snapshot_drive_id"),
        "remote_manifest_drive_id": product.get("remote_manifest_drive_id"),
        "sample_record_refs": [
            _record_ref(product_name, row)
            for row in rows[:5]
        ],
    }


def _productization_state(traces: list[Mapping[str, Any]]) -> str:
    backings = [str(row["backing"]) for row in traces]
    _stop(backings and "UNEXPECTED_EMPTY" not in backings, "TASK203_UNEXPECTED_EMPTY_SIGNAL")
    local = sum(x == "LOCAL_RECORDS" for x in backings)
    metadata = sum(x == "CAPABILITY_METADATA_ONLY" for x in backings)
    if local == len(backings):
        return "RECORD_BACKED"
    if local and metadata:
        return "MIXED_RECORD_AND_CAPABILITY"
    if metadata == len(backings):
        return "CAPABILITY_ONLY"
    raise ProductizationReadinessStop("TASK203_UNCLASSIFIED_READINESS")


def build_question_readiness(
    products: Mapping[str, Mapping[str, Any]],
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    config = current_answerability_config()
    report = current_question_answerability(products)
    _stop(report["status_counts"] == {"MATERIALIZED_ANSWERABLE": 38}, "TASK203_SEMANTIC_38")
    by_question = {row["question_id"]: row for row in report["questions"]}

    rows = []
    for question in config["questions"]:
        qid = str(question["id"])
        semantic = by_question[qid]
        recipe = config["recipes"][question["recipe"]]
        _stop(
            len(recipe["signals"]) == len(semantic["signal_results"]),
            "TASK203_SIGNAL_ALIGNMENT",
        )
        traces = [
            _signal_trace(signal, result, products)
            for signal, result in zip(recipe["signals"], semantic["signal_results"])
        ]
        state = _productization_state(traces)
        packet = query_observatory(
            question["domain_id"],
            products,
            question_text=question["text"],
        )
        rows.append(
            {
                "question_id": qid,
                "domain_id": question["domain_id"],
                "question": question["text"],
                "recipe": question["recipe"],
                "semantic_status": semantic["status"],
                "productization_status": state,
                "human_answer_ready": state == "RECORD_BACKED",
                "query_packet_id": packet["packet_id"],
                "query_packet_sha256": packet["packet_sha256"],
                "query_numeric_record_count": len(packet["numeric_records"]),
                "query_document_record_count": len(packet["document_records"]),
                "query_catalog_record_count": len(packet["catalog_records"]),
                "query_product_gap_count": len(packet["product_gaps"]),
                "signal_traces": traces,
            }
        )

    rows.sort(key=lambda x: x["question_id"])
    counts = dict(sorted(Counter(row["productization_status"] for row in rows).items()))
    expected_counts = dict(sorted(contract["expected_productization_counts"].items()))
    _stop(counts == expected_counts, "TASK203_PRODUCTIZATION_COUNTS")

    mixed = sorted(
        row["question_id"]
        for row in rows
        if row["productization_status"] == "MIXED_RECORD_AND_CAPABILITY"
    )
    capability_only = sorted(
        row["question_id"]
        for row in rows
        if row["productization_status"] == "CAPABILITY_ONLY"
    )
    _stop(
        mixed == sorted(contract["expected_mixed_questions"]),
        "TASK203_MIXED_SET",
    )
    _stop(
        capability_only == sorted(contract["expected_capability_only_questions"]),
        "TASK203_CAPABILITY_ONLY_SET",
    )
    backlog = sorted(mixed + capability_only)
    _stop(
        len(backlog) == contract["expected_query_projection_backlog_count"],
        "TASK203_BACKLOG_SIZE",
    )
    _stop(
        all(row["query_product_gap_count"] == 0 for row in rows),
        "TASK203_QUERY_PRODUCT_GAP",
    )

    return {
        "schema": "OBSERVATORY_QUESTION_PRODUCTIZATION_READINESS_V1",
        "question_count": len(rows),
        "semantic_answerability": dict(report["status_counts"]),
        "productization_counts": counts,
        "human_ready_count": sum(bool(row["human_answer_ready"]) for row in rows),
        "query_projection_backlog_count": len(backlog),
        "query_projection_backlog_questions": backlog,
        "questions": rows,
        "semantics": {
            "semantic_answerability_equals_local_renderability": False,
            "capability_metadata_may_supply_numeric_value": False,
            "human_answer_ready_requires_record_backing_for_all_recipe_signals": True,
            "llm_may_fill_missing_numeric_evidence": False,
        },
        "remote_effects": {
            "network": False,
            "drive_read": False,
            "drive_write": False,
            "serving": False,
            "publication": False,
            "schedule": False,
            "recurrence": False,
        },
    }


def build_current_productization_audit(
    *,
    generated_at: str,
    software_version: str,
) -> dict[str, Any]:
    products = build_current_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    return build_question_readiness(products)
