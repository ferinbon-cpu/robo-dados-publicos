from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from robo_dados_publicos.analytics.base_v05_network_series import to_product_rows as task181_rows
from robo_dados_publicos.analytics.observatory_products import (
    build_fiscal_series,
    build_product_catalog,
    build_school_indicator_series,
    query_observatory,
)
from robo_dados_publicos.analytics.school_indicator_library_seed import to_long_rows as task180_rows
from robo_dados_publicos.analytics.v08_censo_panel import aggregate_long_rows as task182_rows


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ANSWERABILITY = ROOT / "config/observatory_semantic_answerability.v1.json"
DEFAULT_ONTOLOGY = ROOT / "config/observatory_question_ontology.v1.json"
DEFAULT_CROSSWALK = ROOT / "config/existing_custody_product_ingestion_crosswalk.v1.json"
DEFAULT_PRODUCTS = ROOT / "config/observatory_query_products.v1.json"


class Task183Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task183Stop(code)


def _load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_contract(
    answerability_path: str | Path = DEFAULT_ANSWERABILITY,
    ontology_path: str | Path = DEFAULT_ONTOLOGY,
    crosswalk_path: str | Path = DEFAULT_CROSSWALK,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    a = _load(answerability_path)
    o = _load(ontology_path)
    c = _load(crosswalk_path)
    _stop(a.get("schema") == "OBSERVATORY_SEMANTIC_ANSWERABILITY_V1", "TASK183_ANSWERABILITY_SCHEMA")
    _stop(o.get("schema") == "LIMEIRA_OBSERVATORY_QUESTION_ONTOLOGY_V1", "TASK183_ONTOLOGY_SCHEMA")
    _stop(c.get("schema") == "EXISTING_CUSTODY_PRODUCT_INGESTION_CROSSWALK_V1", "TASK183_CROSSWALK_SCHEMA")
    _stop(all(v is False for v in a["remote_effects"].values()), "TASK183_REMOTE_EFFECT")
    return a, o, c


def validate_contract() -> dict[str, Any]:
    answerability, ontology, crosswalk = load_contract()
    ontology_questions = {
        (domain["id"], question)
        for domain in ontology["domains"]
        for question in domain["questions"]
    }
    configured_questions = {
        (row["domain_id"], row["text"])
        for row in answerability["questions"]
    }
    _stop(configured_questions == ontology_questions, "TASK183_QUESTION_SET_MISMATCH")
    _stop(len(answerability["questions"]) == 38, "TASK183_QUESTION_COUNT")
    _stop(len({row["id"] for row in answerability["questions"]}) == 38, "TASK183_DUPLICATE_QUESTION_ID")
    _stop(
        all(row["recipe"] in answerability["recipes"] for row in answerability["questions"]),
        "TASK183_UNKNOWN_RECIPE",
    )
    known_products = set(_load(DEFAULT_PRODUCTS)["products"])
    for recipe in answerability["recipes"].values():
        for signal in recipe["signals"]:
            _stop(signal["product"] in known_products, "TASK183_UNKNOWN_PRODUCT")
            _stop(signal["kind"] in answerability["signal_kinds"], "TASK183_SIGNAL_KIND")
            if signal["kind"] == "METRIC":
                _stop(bool(signal.get("ids")), "TASK183_METRIC_IDS")
                _stop(signal.get("match", "ANY") in {"ANY", "ALL"}, "TASK183_METRIC_MATCH")
    _stop(set(crosswalk["products"]) == known_products, "TASK183_CROSSWALK_PRODUCT_SET")
    return {
        "schema": "TASK183_CONTRACT_VALIDATION_V1",
        "status": "PASS",
        "question_count": 38,
        "domain_count": 15,
        "recipe_count": len(answerability["recipes"]),
        "network": False,
        "drive_write": False,
        "serving": False,
    }


def _school_key(row: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("scope_level") or ""),
        str(row.get("scope_id") or ""),
        str(row.get("period") or ""),
        str(row.get("indicator_id") or ""),
        str(row.get("source_family") or ""),
    )


def _fiscal_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("entity_id") or ""),
        str(row.get("period") or ""),
        str(row.get("metric_id") or ""),
        str(row.get("source_family") or ""),
    )


def _dedupe_or_stop(
    rows: Iterable[Mapping[str, Any]],
    *,
    key_fn,
    code: str,
) -> list[dict[str, Any]]:
    by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    for raw in rows:
        row = dict(raw)
        key = key_fn(row)
        _stop(all(str(part) for part in key), f"{code}_EMPTY_KEY")
        previous = by_key.get(key)
        if previous is None:
            by_key[key] = row
            continue
        if previous != row:
            raise Task183Stop(f"{code}_CONFLICT")
    return [by_key[key] for key in sorted(by_key)]


def fused_source_rows() -> dict[str, Any]:
    t180_school, t180_missing = task180_rows()
    t181 = task181_rows()
    t182_school = task182_rows()

    school_rows = _dedupe_or_stop(
        [*t180_school, *t181["school_rows"], *t182_school],
        key_fn=_school_key,
        code="TASK183_SCHOOL",
    )
    fiscal_rows = _dedupe_or_stop(
        t181["fiscal_rows"],
        key_fn=_fiscal_key,
        code="TASK183_FISCAL",
    )
    _stop(len(school_rows) == 1017, "TASK183_FUSED_SCHOOL_ROW_COUNT")
    _stop(len(fiscal_rows) == 38, "TASK183_FUSED_FISCAL_ROW_COUNT")
    return {
        "school_rows": school_rows,
        "fiscal_rows": fiscal_rows,
        "source_block_counts": {
            "TASK_180_SCHOOL": len(t180_school),
            "TASK_181_SCHOOL": len(t181["school_rows"]),
            "TASK_181_FISCAL": len(t181["fiscal_rows"]),
            "TASK_182_SCHOOL": len(t182_school),
        },
        "missing_ledgers": {
            "TASK_180": t180_missing,
            "TASK_181": t181["missing_ledger"],
        },
        "deferred_source_role_review": t181["deferred_source_role_review"],
    }


def build_fused_products(*, generated_at: str, software_version: str) -> dict[str, dict[str, Any]]:
    source = fused_source_rows()
    school = build_school_indicator_series(
        source["school_rows"],
        generated_at=generated_at,
        software_version=software_version,
    )
    fiscal = build_fiscal_series(
        source["fiscal_rows"],
        generated_at=generated_at,
        software_version=software_version,
    )

    product_contract = _load(DEFAULT_PRODUCTS)
    inverse_domains: dict[str, list[str]] = defaultdict(list)
    for domain_id, product_names in product_contract["domain_product_routes"].items():
        for product_name in product_names:
            inverse_domains[product_name].append(domain_id)

    catalog = build_product_catalog(
        {
            "SCHOOL_INDICATOR_SERIES": school,
            "FISCAL_SERIES": fiscal,
        },
        generated_at=generated_at,
        software_version=software_version,
        coverage_domains={
            "SCHOOL_INDICATOR_SERIES": inverse_domains["SCHOOL_INDICATOR_SERIES"],
            "FISCAL_SERIES": inverse_domains["FISCAL_SERIES"],
        },
        readiness={
            "SCHOOL_INDICATOR_SERIES": "READY_WITH_CAUTION",
            "FISCAL_SERIES": "READY_WITH_CAUTION",
        },
    )
    return {
        "SCHOOL_INDICATOR_SERIES": school,
        "FISCAL_SERIES": fiscal,
        "QUERY_PRODUCT_CATALOG": catalog,
    }


def metric_inventory(products: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    rows = []
    for product_name in ("SCHOOL_INDICATOR_SERIES", "FISCAL_SERIES"):
        product = products.get(product_name)
        if not product:
            continue
        field = "indicator_id" if product_name == "SCHOOL_INDICATOR_SERIES" else "metric_id"
        grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for row in product.get("rows", []):
            grouped[str(row[field])].append(row)
        for metric_id in sorted(grouped):
            metric_rows = grouped[metric_id]
            rows.append({
                "product_name": product_name,
                "metric_id": metric_id,
                "row_count": len(metric_rows),
                "periods": sorted({str(row.get("period") or "") for row in metric_rows if row.get("period")}),
                "scope_levels": sorted({str(row.get("scope_level") or "") for row in metric_rows if row.get("scope_level")}),
                "scope_ids": sorted({str(row.get("scope_id") or "") for row in metric_rows if row.get("scope_id")}),
                "source_families": sorted({str(row.get("source_family") or "") for row in metric_rows if row.get("source_family")}),
                "quality_statuses": sorted({str(row.get("quality_status") or "") for row in metric_rows if row.get("quality_status")}),
            })
    return {
        "schema": "OBSERVATORY_MATERIALIZED_METRIC_INVENTORY_V1",
        "metric_count": len(rows),
        "metrics": rows,
    }


def _metric_lookup(products: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    result: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for product_name, product in products.items():
        if product_name == "SCHOOL_INDICATOR_SERIES":
            field = "indicator_id"
        elif product_name == "FISCAL_SERIES":
            field = "metric_id"
        else:
            continue
        for row in product.get("rows", []):
            result[product_name][str(row.get(field) or "")].append(dict(row))
    return result


def _eval_metric_signal(
    signal: Mapping[str, Any],
    lookup: Mapping[str, Mapping[str, list[dict[str, Any]]]],
) -> dict[str, Any]:
    product = str(signal["product"])
    ids = [str(x) for x in signal["ids"]]
    match = str(signal.get("match") or "ANY")
    min_periods = int(signal.get("min_periods") or 1)
    scopes_required = set(str(x) for x in signal.get("scope_levels_required") or [])

    id_results = []
    for metric_id in ids:
        rows = list(lookup.get(product, {}).get(metric_id, []))
        periods = {str(row.get("period") or "") for row in rows if row.get("period")}
        scopes = {str(row.get("scope_level") or "") for row in rows if row.get("scope_level")}
        exists = bool(rows)
        period_ok = len(periods) >= min_periods
        scopes_ok = scopes_required <= scopes
        full = exists and period_ok and scopes_ok
        partial = exists and not full
        id_results.append({
            "metric_id": metric_id,
            "exists": exists,
            "period_count": len(periods),
            "periods": sorted(periods),
            "scope_levels": sorted(scopes),
            "min_periods_required": min_periods,
            "scope_levels_required": sorted(scopes_required),
            "full": full,
            "partial": partial,
        })

    if match == "ALL":
        full = all(x["full"] for x in id_results)
        partial = not full and any(x["exists"] for x in id_results)
    else:
        full = any(x["full"] for x in id_results)
        partial = not full and any(x["exists"] for x in id_results)

    missing = [
        x["metric_id"]
        for x in id_results
        if not x["full"]
    ]
    return {
        "kind": "METRIC",
        "product": product,
        "match": match,
        "state": "FULL" if full else ("PARTIAL" if partial else "NONE"),
        "metrics": id_results,
        "missing_or_insufficient_metrics": missing,
    }


def _row_has_any(row: Mapping[str, Any], field: str, values: set[str]) -> bool:
    raw = row.get(field)
    if isinstance(raw, list):
        observed = {str(x) for x in raw}
    elif raw is None:
        observed = set()
    else:
        observed = {str(raw)}
    return bool(observed & values)


def _eval_product_signal(
    signal: Mapping[str, Any],
    products: Mapping[str, Mapping[str, Any]],
    crosswalk: Mapping[str, Any],
) -> dict[str, Any]:
    product_name = str(signal["product"])
    product = products.get(product_name)
    if product is None:
        return {
            "kind": "PRODUCT",
            "product": product_name,
            "state": "NONE",
            "readiness": _product_readiness_status(product_name, products, crosswalk),
            "content_gaps": ["PRODUCT_NOT_BUNDLED"],
            "matching_row_count": 0,
        }

    rows = [dict(row) for row in product.get("rows", [])]
    gaps: list[str] = []

    required_capabilities = {str(x) for x in signal.get("required_capabilities") or []}
    observed_capabilities = {str(x) for x in product.get("capabilities") or []}
    for capability in sorted(required_capabilities - observed_capabilities):
        gaps.append(f"CAPABILITY:{capability}")

    min_rows = int(signal.get("min_rows") or 0)
    if min_rows and len(rows) < min_rows:
        gaps.append(f"MIN_ROWS:{min_rows}")

    criteria = dict(signal.get("row_criteria") or {})
    matching_rows = rows
    if criteria:
        filtered = []
        for row in rows:
            ok = True
            for field, allowed in criteria.items():
                if not field.endswith("_any"):
                    raise Task183Stop("TASK183_PRODUCT_CRITERIA_FIELD")
                source_field = field[:-4]
                if not _row_has_any(row, source_field, {str(x) for x in allowed}):
                    ok = False
                    break
            if ok:
                filtered.append(row)
        matching_rows = filtered
        min_matching = int(signal.get("min_matching_rows") or 1)
        if len(matching_rows) < min_matching:
            gaps.append(
                "ROW_CRITERIA:"
                + ",".join(sorted(criteria))
                + f":MIN_MATCHING:{min_matching}"
            )

    required_doc_roles = dict(signal.get("required_document_role_pairs") or {})
    for document_type, roles in sorted(required_doc_roles.items()):
        if not any(
            str(row.get("document_type") or "") == str(document_type)
            and str(row.get("evidence_role") or "") in {str(x) for x in roles}
            for row in rows
        ):
            gaps.append(
                f"DOCUMENT_ROLE:{document_type}:"
                + "|".join(sorted(str(x) for x in roles))
            )

    required_family_roles = dict(signal.get("required_source_family_role_pairs") or {})
    for family, roles in sorted(required_family_roles.items()):
        if not any(
            str(row.get("source_family") or "") == str(family)
            and str(row.get("evidence_role") or "") in {str(x) for x in roles}
            for row in rows
        ):
            gaps.append(
                f"SOURCE_FAMILY_ROLE:{family}:"
                + "|".join(sorted(str(x) for x in roles))
            )

    return {
        "kind": "PRODUCT",
        "product": product_name,
        "state": "FULL" if not gaps else "PARTIAL",
        "readiness": "BUNDLED",
        "content_gaps": gaps,
        "row_count": len(rows),
        "matching_row_count": len(matching_rows),
    }


def _product_readiness_status(
    product_name: str,
    products: Mapping[str, Mapping[str, Any]],
    crosswalk: Mapping[str, Any],
) -> str:
    if product_name in products:
        return "BUNDLED"
    status = str(crosswalk["products"][product_name]["current_status"])
    if status == "NO_NEW_CUSTODY_INPUT_REQUIRED":
        return "ROUTE_READY_PRODUCT_NOT_BUNDLED"
    if status in {
        "READY_FROM_EXISTING_CUSTODY",
        "READY_PARTIAL_ONLY",
        "DOCUMENT_INDEX_READY_NUMERIC_NOT_READY",
    }:
        return "SOURCE_READY_NOT_MATERIALIZED"
    return "EXPLICIT_GAP"


def question_answerability(
    products: Mapping[str, Mapping[str, Any]],
    *,
    answerability_path: str | Path = DEFAULT_ANSWERABILITY,
    crosswalk_path: str | Path = DEFAULT_CROSSWALK,
) -> dict[str, Any]:
    answerability = _load(answerability_path)
    crosswalk = _load(crosswalk_path)
    lookup = _metric_lookup(products)

    question_rows = []
    counts = Counter()
    for question in answerability["questions"]:
        recipe = answerability["recipes"][question["recipe"]]
        signal_results = []
        absent_products = set()
        for signal in recipe["signals"]:
            if signal["kind"] == "METRIC":
                result = _eval_metric_signal(signal, lookup)
                signal_results.append(result)
                if result["state"] == "NONE":
                    absent_products.add(str(signal["product"]))
            else:
                result = _eval_product_signal(signal, products, crosswalk)
                signal_results.append(result)
                if result["state"] == "NONE":
                    absent_products.add(str(signal["product"]))

        states = [row["state"] for row in signal_results]
        if states and all(state == "FULL" for state in states):
            status = "MATERIALIZED_ANSWERABLE"
        elif any(state in {"FULL", "PARTIAL"} for state in states):
            status = "MATERIALIZED_PARTIAL"
        else:
            readiness = {
                _product_readiness_status(name, products, crosswalk)
                for name in absent_products
            }
            if "ROUTE_READY_PRODUCT_NOT_BUNDLED" in readiness:
                status = "ROUTE_READY_PRODUCT_NOT_BUNDLED"
            elif "SOURCE_READY_NOT_MATERIALIZED" in readiness:
                status = "SOURCE_READY_NOT_MATERIALIZED"
            else:
                status = "EXPLICIT_GAP"

        missing_metrics = sorted({
            metric
            for result in signal_results
            if result["kind"] == "METRIC"
            for metric in result["missing_or_insufficient_metrics"]
        })
        required_nonbundled_products = sorted({
            result["product"]
            for result in signal_results
            if result["kind"] == "PRODUCT" and result["state"] == "NONE"
        })
        product_content_gaps = sorted({
            f"{result['product']}::{gap}"
            for result in signal_results
            if result["kind"] == "PRODUCT"
            for gap in result.get("content_gaps", [])
            if gap != "PRODUCT_NOT_BUNDLED"
        })
        counts[status] += 1
        question_rows.append({
            "question_id": question["id"],
            "domain_id": question["domain_id"],
            "question": question["text"],
            "recipe": question["recipe"],
            "status": status,
            "signal_results": signal_results,
            "missing_or_insufficient_metrics": missing_metrics,
            "required_nonbundled_products": required_nonbundled_products,
            "product_content_gaps": product_content_gaps,
        })

    domain_rows = []
    for domain_id in sorted({row["domain_id"] for row in question_rows}):
        subset = [row for row in question_rows if row["domain_id"] == domain_id]
        domain_counts = Counter(row["status"] for row in subset)
        if domain_counts["MATERIALIZED_ANSWERABLE"] == len(subset):
            domain_status = "MATERIALIZED_ANSWERABLE"
        elif domain_counts["MATERIALIZED_ANSWERABLE"] or domain_counts["MATERIALIZED_PARTIAL"]:
            domain_status = "MATERIALIZED_PARTIAL"
        elif domain_counts["ROUTE_READY_PRODUCT_NOT_BUNDLED"]:
            domain_status = "ROUTE_READY_PRODUCT_NOT_BUNDLED"
        elif domain_counts["SOURCE_READY_NOT_MATERIALIZED"]:
            domain_status = "SOURCE_READY_NOT_MATERIALIZED"
        else:
            domain_status = "EXPLICIT_GAP"
        domain_rows.append({
            "domain_id": domain_id,
            "status": domain_status,
            "question_count": len(subset),
            "question_status_counts": dict(sorted(domain_counts.items())),
        })

    return {
        "schema": "OBSERVATORY_SEMANTIC_QUESTION_ANSWERABILITY_REPORT_V1",
        "question_count": len(question_rows),
        "domain_count": len(domain_rows),
        "status_counts": dict(sorted(counts.items())),
        "questions": question_rows,
        "domains": domain_rows,
        "product_presence_is_not_answerability": True,
        "llm_may_fill_missing_numeric_evidence": False,
    }


def sample_packet_summaries(products: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    samples = [
        {
            "id": "LEARNING_2025",
            "domain_id": "LEARNING_FLOW",
            "question_text": "Como estao IDEB, SAEB e SARESP?",
            "timeframe": "2025",
        },
        {
            "id": "RAFAEL_EQUITY_2025",
            "domain_id": "EQUITY_INCLUSION",
            "question_text": "Como estao contexto social, PPI e inclusao?",
            "timeframe": "2025",
            "school_or_unit": "35470600",
        },
        {
            "id": "FINANCING_2025",
            "domain_id": "FINANCING",
            "question_text": "Que indicadores fiscais de educacao estao materializados?",
            "timeframe": "2025",
        },
    ]
    output = []
    for sample in samples:
        packet = query_observatory(
            sample["domain_id"],
            products,
            question_text=sample["question_text"],
            timeframe=sample.get("timeframe"),
            school_or_unit=sample.get("school_or_unit"),
        )
        output.append({
            "sample_id": sample["id"],
            "domain_id": sample["domain_id"],
            "packet_id": packet["packet_id"],
            "packet_sha256": packet["packet_sha256"],
            "numeric_record_count": len(packet["numeric_records"]),
            "document_record_count": len(packet["document_records"]),
            "product_gap_count": len(packet["product_gaps"]),
            "used_snapshots": packet["used_snapshots"],
        })
    return output


def build_knowledge_pack(*, generated_at: str, software_version: str) -> dict[str, Any]:
    validate_contract()
    fused = fused_source_rows()
    products = build_fused_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    inventory = metric_inventory(products)
    answerability = question_answerability(products)
    samples = sample_packet_summaries(products)
    return {
        "schema": "OBSERVATORY_EXISTING_CUSTODY_KNOWLEDGE_PACK_V1",
        "generated_at": generated_at,
        "software_version": software_version,
        "products": products,
        "source_block_counts": fused["source_block_counts"],
        "metric_inventory": inventory,
        "answerability": answerability,
        "sample_packet_summaries": samples,
        "missing_ledgers": fused["missing_ledgers"],
        "deferred_source_role_review": fused["deferred_source_role_review"],
        "remote_effects": {
            "network": False,
            "drive_write": False,
            "serving": False,
            "publication": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(validate_contract(), ensure_ascii=False, indent=2, sort_keys=True))
