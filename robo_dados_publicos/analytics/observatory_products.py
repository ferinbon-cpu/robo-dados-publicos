from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from robo_dados_publicos.router.observatory import route_observatory_question


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/observatory_query_products.v1.json"
DEFAULT_ONTOLOGY = ROOT / "config/observatory_question_ontology.v1.json"


class Task176Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task176Stop(code)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "OBSERVATORY_QUERY_PRODUCTS_V1", "TASK176_CONTRACT_SCHEMA")
    _stop(obj.get("mode") == "T0_OFFLINE_DERIVED_QUERY_PRODUCT_MATERIALIZATION", "TASK176_CONTRACT_MODE")
    _stop(obj.get("role") == "DERIVED_QUERY_CACHE_NOT_SOURCE_OF_TRUTH", "TASK176_ROLE")
    return obj


def validate_contract(
    path: str | Path = DEFAULT_CONTRACT,
    ontology_path: str | Path = DEFAULT_ONTOLOGY,
) -> dict[str, Any]:
    contract = load_contract(path)
    ontology = json.loads(Path(ontology_path).read_text(encoding="utf-8"))
    products = contract["products"]
    _stop(
        set(products) == {
            "SCHOOL_INDICATOR_SERIES",
            "JOM_EVENT_INDEX",
            "ACCOUNTING_LEDGER",
            "FISCAL_SERIES",
            "PLANNING_DOCUMENT_INDEX",
            "QUERY_PRODUCT_CATALOG",
        },
        "TASK176_PRODUCT_SET",
    )
    ontology_ids = {x["id"] for x in ontology["domains"]}
    _stop(set(contract["domain_product_routes"]) == ontology_ids, "TASK176_DOMAIN_COVERAGE")
    _stop(len(ontology_ids) == 15, "TASK176_DOMAIN_COUNT")
    _stop(
        contract["materialization_rules"]["generated_at"] == "CALLER_SUPPLIED_REQUIRED_NOT_CURRENT_CLOCK",
        "TASK176_GENERATED_AT_RULE",
    )
    _stop(contract["materialization_rules"]["query_products_replace_source_layers"] is False, "TASK176_SOURCE_REPLACEMENT")
    _stop(contract["query_api"]["numeric_truth_from_structured_records_only"] is True, "TASK176_NUMERIC_TRUTH")
    _stop(contract["query_api"]["document_truth_requires_locator"] is True, "TASK176_DOCUMENT_LOCATOR")
    _stop(contract["query_api"]["weak_join_can_create_identity"] is False, "TASK176_WEAK_JOIN")
    effects = contract["remote_effects"]
    _stop(all(v is False for v in effects.values()), "TASK176_REMOTE_EFFECT")
    return {
        "schema": "TASK176_QUERY_PRODUCT_CONTRACT_VALIDATION_V1",
        "status": "PASS",
        "product_count": len(products),
        "domain_count": len(ontology_ids),
        "network": False,
        "drive_write": False,
        "serving": False,
        "publication": False,
    }


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, str):
        return " ".join(value.split())
    return value


def _normalize_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {str(k): _normalize_scalar(v) for k, v in row.items()}


def _primary_key_tuple(row: Mapping[str, Any], primary_key: list[str]) -> tuple[str, ...]:
    return tuple(str(row.get(k, "")) for k in primary_key if k != "snapshot_id")


def _validate_sha256(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text.lower())


def _base_row(
    product_name: str,
    row: Mapping[str, Any],
    *,
    generated_at: str,
    software_version: str,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    spec = contract["products"][product_name]
    obj = _normalize_row(row)
    for field in spec["required_fields"]:
        _stop(field in obj and obj[field] is not None, f"TASK176_REQUIRED_{product_name}_{field}")
    for field in (
        "observation_period",
        "source_family",
        "source_sha256",
        "provenance_ref",
        "quality_status",
        "caution",
    ):
        _stop(field in obj and obj[field] is not None, f"TASK176_COMMON_{product_name}_{field}")
    _stop(_validate_sha256(obj["source_sha256"]), f"TASK176_SHA_{product_name}")
    _stop(obj["quality_status"] in contract["quality_enum"], f"TASK176_QUALITY_{product_name}")
    if spec["source_families"]:
        _stop(obj["source_family"] in spec["source_families"], f"TASK176_SOURCE_FAMILY_{product_name}")
    obj["product_schema"] = spec["schema"]
    obj["generated_at"] = generated_at
    obj["software_version"] = software_version
    return obj


def materialize_product(
    product_name: str,
    rows: Iterable[Mapping[str, Any]],
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    _stop(product_name in contract["products"], "TASK176_UNKNOWN_PRODUCT")
    _stop(product_name != "QUERY_PRODUCT_CATALOG", "TASK176_USE_CATALOG_BUILDER")
    _stop(bool(generated_at), "TASK176_GENERATED_AT_REQUIRED")
    _stop(bool(software_version), "TASK176_SOFTWARE_VERSION_REQUIRED")
    spec = contract["products"][product_name]
    base_rows = [
        _base_row(
            product_name,
            row,
            generated_at=generated_at,
            software_version=software_version,
            contract=contract,
        )
        for row in rows
    ]
    key_without_snapshot = [k for k in spec["primary_key"] if k != "snapshot_id"]
    base_rows.sort(key=lambda row: _primary_key_tuple(row, key_without_snapshot))
    content_sha256 = _sha(base_rows)
    snapshot_id = content_sha256[:24]
    materialized = [{**row, "snapshot_id": snapshot_id} for row in base_rows]
    return {
        "product_name": product_name,
        "product_schema": spec["schema"],
        "snapshot_id": snapshot_id,
        "content_sha256": content_sha256,
        "row_count": len(materialized),
        "generated_at": generated_at,
        "software_version": software_version,
        "rows": materialized,
    }


def build_school_indicator_series(
    rows: Iterable[Mapping[str, Any]],
    *,
    generated_at: str,
    software_version: str,
) -> dict[str, Any]:
    return materialize_product(
        "SCHOOL_INDICATOR_SERIES",
        rows,
        generated_at=generated_at,
        software_version=software_version,
    )


def build_jom_event_index(
    events: Iterable[Mapping[str, Any]],
    semantics_by_event: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
    software_version: str,
) -> dict[str, Any]:
    rows = []
    for event in events:
        event_id = str(event.get("event_id") or "")
        _stop(bool(event_id), "TASK176_JOM_EVENT_ID")
        sem = semantics_by_event.get(event_id)
        _stop(sem is not None, "TASK176_JOM_SEMANTICS_MISSING")
        rows.append(
            {
                "event_id": event_id,
                "publication_date": event.get("publication_date"),
                "event_type": event.get("event_type"),
                "policy_domains": list(sem.get("policy_domains") or []),
                "evidence_layers": list(sem.get("evidence_layers") or []),
                "financial_stages": list(sem.get("financial_stages") or []),
                "education_topics": list(sem.get("education_topics") or []),
                "source_locator": {
                    "source_id": event.get("source_id"),
                    "edition": event.get("edition"),
                    "page_number": event.get("page_number"),
                    "start_line": event.get("start_line"),
                    "end_line": event.get("end_line"),
                },
                "process_number": event.get("process_number"),
                "contract_number": event.get("contract_number"),
                "bidding_number": event.get("bidding_number"),
                "cnpj": event.get("cnpj"),
                "value_brl": event.get("value_brl"),
                "object_text": event.get("object_text"),
                "target_act_type": event.get("target_act_type"),
                "target_act_number": event.get("target_act_number"),
                "observation_period": str(event.get("publication_date") or ""),
                "source_family": "JORNAL_OFICIAL",
                "source_sha256": event.get("source_sha256"),
                "provenance_ref": event_id,
                "quality_status": "VALIDATED",
                "caution": "PUBLICATION_NE_IMPLEMENTATION_AND_SEMANTIC_FACETS_NE_IDENTITY",
            }
        )
    return materialize_product(
        "JOM_EVENT_INDEX",
        rows,
        generated_at=generated_at,
        software_version=software_version,
    )


def build_accounting_ledger(
    observations: Iterable[Mapping[str, Any]],
    *,
    generated_at: str,
    software_version: str,
) -> dict[str, Any]:
    rows = []
    capabilities: set[str] = set()
    observed_stages: set[str] = set()
    for obs in observations:
        dims = dict(obs.get("programmatic_dimensions") or {})
        keys = dict(obs.get("transaction_keys") or {})
        stage = str(obs.get("stage") or "")
        observed_stages.add(stage)
        if keys.get("fiscal_year_plus_empenho"):
            capabilities.add("COMMITMENT_NUMBER")
        if obs.get("supplier_name") or obs.get("supplier_public_id"):
            capabilities.add("SUPPLIER_AMOUNT")
        if obs.get("event_date"):
            capabilities.add("EVENT_DATE")
        if any(dims.get(k) for k in ("function", "subfunction", "program_code", "program_name", "action_code", "action_name")):
            capabilities.add("PROGRAMMATIC_CLASSIFICATION")
        if dims.get("funding_source") or dims.get("application_code"):
            capabilities.add("FUNDING_SOURCE_APPLICATION")
        if dims.get("expense_element"):
            capabilities.add("EXPENSE_ELEMENT")
        if obs.get("source_description") or obs.get("history_text"):
            capabilities.add("SOURCE_DESCRIPTION")
        text = " ".join(
            str(x or "")
            for x in (
                dims.get("function"),
                dims.get("subfunction"),
                dims.get("program_name"),
                dims.get("action_name"),
                *(obs.get("policy_domain_hints") or []),
            )
        ).upper()
        if "EDUCA" in text:
            capabilities.add("EDUCATION_CLASSIFICATION")
        if obs.get("rests_payable_status") is not None:
            capabilities.add("RESTS_PAYABLE")

        rows.append(
            {
                **dict(obs),
                "function": dims.get("function"),
                "subfunction": dims.get("subfunction"),
                "program_code": dims.get("program_code"),
                "action_code": dims.get("action_code"),
                "funding_source": dims.get("funding_source"),
                "application_code": dims.get("application_code"),
                "commitment_number": keys.get("fiscal_year_plus_empenho"),
                "observation_period": str(obs.get("fiscal_year") or ""),
                "source_family": "TCE_SP_EXPENSES",
                "source_sha256": obs.get("source_record_hash"),
                "provenance_ref": obs.get("observation_id"),
                "quality_status": "VALIDATED",
                "caution": "CONTROL_RECORD_NE_MUNICIPAL_PRIMARY_POLICY_IDENTITY",
            }
        )
    if "COMMITMENT" in observed_stages:
        capabilities.add("COMMITMENT_AMOUNTS")
    if "LIQUIDATION" in observed_stages:
        capabilities.add("LIQUIDATION_AMOUNTS")
    if "PAYMENT" in observed_stages:
        capabilities.add("PAYMENT_AMOUNTS")
    if "REVERSAL" in observed_stages:
        capabilities.add("REVERSAL_EVENTS")

    product = materialize_product(
        "ACCOUNTING_LEDGER",
        rows,
        generated_at=generated_at,
        software_version=software_version,
    )
    product["capabilities"] = sorted(capabilities)
    product["observed_stages"] = sorted(observed_stages)
    return product


def build_fiscal_series(
    rows: Iterable[Mapping[str, Any]],
    *,
    generated_at: str,
    software_version: str,
) -> dict[str, Any]:
    return materialize_product(
        "FISCAL_SERIES",
        rows,
        generated_at=generated_at,
        software_version=software_version,
    )


def build_planning_document_index(
    rows: Iterable[Mapping[str, Any]],
    *,
    generated_at: str,
    software_version: str,
) -> dict[str, Any]:
    return materialize_product(
        "PLANNING_DOCUMENT_INDEX",
        rows,
        generated_at=generated_at,
        software_version=software_version,
    )


def build_product_catalog(
    products: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
    software_version: str,
    coverage_domains: Mapping[str, list[str]] | None = None,
    readiness: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    contract = load_contract()
    coverage_domains = coverage_domains or {}
    readiness = readiness or {}
    rows = []
    for product_name in sorted(products):
        product = products[product_name]
        _stop(product_name in contract["products"], "TASK176_CATALOG_UNKNOWN_PRODUCT")
        _stop(product_name != "QUERY_PRODUCT_CATALOG", "TASK176_CATALOG_RECURSION")
        source_families = sorted(
            {
                str(row.get("source_family"))
                for row in product.get("rows", [])
                if row.get("source_family")
            }
        )
        rows.append(
            {
                "product_name": product_name,
                "product_schema": product["product_schema"],
                "snapshot_id": product["snapshot_id"],
                "row_count": int(product["row_count"]),
                "coverage_domains": sorted(coverage_domains.get(product_name, [])),
                "source_families": source_families,
                "readiness": readiness.get(product_name, "READY_WITH_CAUTION"),
                "content_sha256": product["content_sha256"],
                "generated_at": generated_at,
                "software_version": software_version,
                "caution": "DERIVED_QUERY_CACHE_NOT_SOURCE_OF_TRUTH",
            }
        )
    rows.sort(key=lambda x: (x["product_name"], x["snapshot_id"]))
    content_sha256 = _sha(rows)
    snapshot_id = content_sha256[:24]
    rows = [{**row, "catalog_snapshot_id": snapshot_id} for row in rows]
    return {
        "product_name": "QUERY_PRODUCT_CATALOG",
        "product_schema": contract["products"]["QUERY_PRODUCT_CATALOG"]["schema"],
        "snapshot_id": snapshot_id,
        "content_sha256": content_sha256,
        "row_count": len(rows),
        "generated_at": generated_at,
        "software_version": software_version,
        "rows": rows,
    }


def _source_family_set(plan: Mapping[str, Any]) -> set[str]:
    return {
        str(row.get("source_family"))
        for row in plan.get("source_plan", [])
        if row.get("source_family")
    }


def _record_matches_context(row: Mapping[str, Any], context: Mapping[str, Any]) -> bool:
    timeframe = str(context.get("timeframe") or "").strip()
    if timeframe:
        candidates = [
            str(row.get("period") or ""),
            str(row.get("observation_period") or ""),
            str(row.get("fiscal_year") or ""),
            str(row.get("publication_date") or ""),
        ]
        if not any(timeframe in candidate for candidate in candidates):
            return False
    unit = str(context.get("school_or_unit") or "").strip().casefold()
    if unit:
        candidates = [
            str(row.get("scope_id") or "").casefold(),
            str(row.get("school_name") or "").casefold(),
            str(row.get("school_code") or "").casefold(),
            str(row.get("entity_name") or "").casefold(),
        ]
        if not any(unit == candidate or unit in candidate for candidate in candidates if candidate):
            return False
    return True


def query_products(
    query_plan: Mapping[str, Any],
    products: Mapping[str, Mapping[str, Any]],
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    _stop(query_plan.get("schema") == "UNIFIED_OBSERVATORY_QUERY_PLAN_V1", "TASK176_QUERY_PLAN_SCHEMA")
    domain_id = str(query_plan.get("domain_id") or "")
    _stop(domain_id in contract["domain_product_routes"], "TASK176_QUERY_DOMAIN")
    source_families = _source_family_set(query_plan)
    desired_products = list(contract["domain_product_routes"][domain_id])
    for product_name, spec in contract["products"].items():
        if product_name == "QUERY_PRODUCT_CATALOG":
            continue
        if set(spec.get("source_families") or []) & source_families and product_name not in desired_products:
            desired_products.append(product_name)
    context = dict(query_plan.get("context") or {})

    numeric_records: list[dict[str, Any]] = []
    document_records: list[dict[str, Any]] = []
    catalog_records: list[dict[str, Any]] = []
    product_gaps: list[dict[str, Any]] = []
    used_snapshots: dict[str, str] = {}

    for product_name in desired_products:
        product = products.get(product_name)
        if not product:
            product_gaps.append(
                {
                    "product_name": product_name,
                    "gap": "PRODUCT_NOT_MATERIALIZED",
                    "effect": "EXPLICIT_GAP_NO_INVENTED_EVIDENCE",
                }
            )
            continue
        used_snapshots[product_name] = str(product.get("snapshot_id") or "")
        for row in product.get("rows", []):
            family = str(row.get("source_family") or "")
            if family and source_families and family not in source_families:
                continue
            if not _record_matches_context(row, context):
                continue
            record = dict(row)
            record["query_product_name"] = product_name
            record.setdefault("product_name", product_name)
            if product_name in {"SCHOOL_INDICATOR_SERIES", "ACCOUNTING_LEDGER", "FISCAL_SERIES"}:
                numeric_records.append(record)
            elif product_name in {"JOM_EVENT_INDEX", "PLANNING_DOCUMENT_INDEX"}:
                if product_name == "PLANNING_DOCUMENT_INDEX":
                    _stop(bool(row.get("locator")), "TASK176_DOCUMENT_LOCATOR_MISSING")
                document_records.append(record)
            elif product_name == "QUERY_PRODUCT_CATALOG":
                catalog_records.append(record)

    numeric_records.sort(key=lambda x: _canonical_bytes(x))
    document_records.sort(key=lambda x: _canonical_bytes(x))
    catalog_records.sort(key=lambda x: _canonical_bytes(x))

    packet_material = {
        "domain_id": domain_id,
        "route_mode": query_plan.get("route_mode"),
        "used_snapshots": used_snapshots,
        "numeric_records": numeric_records,
        "document_records": document_records,
        "catalog_records": catalog_records,
        "product_gaps": product_gaps,
    }
    packet_sha256 = _sha(packet_material)
    return {
        "schema": "OBSERVATORY_EVIDENCE_PACKET_V1",
        "packet_id": "EVPK_" + packet_sha256[:24],
        "packet_sha256": packet_sha256,
        "domain_id": domain_id,
        "route_mode": query_plan.get("route_mode"),
        "used_snapshots": used_snapshots,
        "numeric_records": numeric_records,
        "document_records": document_records,
        "catalog_records": catalog_records,
        "product_gaps": product_gaps,
        "upstream_evidence_gaps": list(query_plan.get("evidence_gaps") or []),
        "join_semantics": {
            "strong_allowed": contract["join_strengths"]["STRONG"],
            "contextual_only": contract["join_strengths"]["CONTEXTUAL"],
            "weak_only": contract["join_strengths"]["WEAK"],
            "weak_can_create_identity": False,
        },
        "answer_contract": list(query_plan.get("answer_contract") or []),
        "numeric_truth_from_structured_records_only": True,
        "llm_numeric_truth_allowed": False,
        "source_layers_replaced": False,
    }



def coverage_report(
    products: Mapping[str, Mapping[str, Any]],
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    rows = []
    counts = {"READY_PRODUCTS": 0, "PARTIAL_PRODUCTS": 0, "NO_PRODUCTS": 0}
    for domain_id, required_products in contract["domain_product_routes"].items():
        plan = route_observatory_question(domain_id)
        allowed_families = _source_family_set(plan)
        available = []
        missing = []
        for name in required_products:
            product = products.get(name)
            if product is None:
                missing.append(name)
                continue
            if name == "QUERY_PRODUCT_CATALOG":
                available.append(name)
                continue
            row_families = {
                str(row.get("source_family"))
                for row in product.get("rows", [])
                if row.get("source_family")
            }
            if row_families & allowed_families:
                available.append(name)
            else:
                missing.append(name)
        if not missing:
            status = "READY_PRODUCTS"
        elif available:
            status = "PARTIAL_PRODUCTS"
        else:
            status = "NO_PRODUCTS"
        counts[status] += 1
        rows.append(
            {
                "domain_id": domain_id,
                "status": status,
                "required_products": list(required_products),
                "available_products": available,
                "missing_products": missing,
                "snapshot_ids": {
                    name: products[name].get("snapshot_id")
                    for name in available
                },
            }
        )
    rows.sort(key=lambda x: x["domain_id"])
    return {
        "schema": "OBSERVATORY_QUERY_PRODUCT_COVERAGE_V1",
        "domain_count": len(rows),
        "counts": counts,
        "domains": rows,
        "all_domains_explicit": len(rows) == 15,
        "network": False,
        "drive_write": False,
        "serving_write": False,
    }


def query_observatory(
    domain_id: str,
    products: Mapping[str, Mapping[str, Any]],
    *,
    question_text: str = "",
    timeframe: str | None = None,
    school_or_unit: str | None = None,
    policy_or_service: str | None = None,
    desired_granularity: str | None = None,
) -> dict[str, Any]:
    plan = route_observatory_question(
        domain_id,
        question_text=question_text,
        timeframe=timeframe,
        school_or_unit=school_or_unit,
        policy_or_service=policy_or_service,
        desired_granularity=desired_granularity,
    )
    return query_products(plan, products)


if __name__ == "__main__":
    print(json.dumps(validate_contract(), ensure_ascii=False, indent=2, sort_keys=True))
