from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.analytics.observatory_knowledge_pack import (
    build_fused_products,
    question_answerability,
)
from robo_dados_publicos.analytics.observatory_products import (
    build_jom_event_index,
    build_planning_document_index,
    build_product_catalog,
    query_observatory,
)
from robo_dados_publicos.journal.semantic_layers import classify_event


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task184_local_product_bundle.v1.json"
PRODUCT_CONTRACT = ROOT / "config/observatory_query_products.v1.json"


class Task184Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task184Stop(code)


def _load(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = _load(path)
    _stop(obj.get("schema") == "TASK184_LOCAL_PRODUCT_BUNDLE_V1", "TASK184_SCHEMA")
    _stop(obj.get("mode") == "T0_OFFLINE_EXISTING_CUSTODY_REAL_ROWS_ONLY", "TASK184_MODE")
    _stop(obj["accounting"]["bundle_status"] == "NOT_MATERIALIZED", "TASK184_ACCOUNTING_STATUS")
    _stop(obj["accounting"]["raw_payload_persisted"] is False, "TASK184_ACCOUNTING_RAW_GUARD")
    _stop(obj["accounting"]["synthetic_fixture_allowed"] is False, "TASK184_ACCOUNTING_SYNTHETIC_GUARD")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK184_REMOTE_EFFECT")
    return obj


def load_jom_events(contract_path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    contract = load_contract(contract_path)
    path = ROOT / contract["jom"]["fixture"]
    events = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    _stop(len(events) == contract["jom"]["source_row_count"], "TASK184_JOM_ROW_COUNT")
    ids = [str(row.get("event_id") or "") for row in events]
    _stop(all(ids), "TASK184_JOM_EVENT_ID")
    _stop(len(set(ids)) == len(ids), "TASK184_JOM_DUPLICATE_ID")
    _stop(
        all(row.get("extraction_status") == "VALIDATED" for row in events),
        "TASK184_JOM_EXTRACTION_STATUS",
    )
    _stop(
        all(row.get("confidence_class") == "VALIDATED" for row in events),
        "TASK184_JOM_CONFIDENCE",
    )
    _stop(
        all(row.get("gold_id") == row.get("event_id") for row in events),
        "TASK184_JOM_GOLD_ID",
    )
    _stop(
        all(
            isinstance(row.get("source_sha256"), str)
            and len(row["source_sha256"]) == 64
            for row in events
        ),
        "TASK184_JOM_SOURCE_SHA",
    )
    return events


def build_jom_product(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    events = load_jom_events(contract_path)
    semantics = {row["event_id"]: classify_event(row) for row in events}
    product = build_jom_event_index(
        events,
        semantics,
        generated_at=generated_at,
        software_version=software_version,
    )
    layer_counts = Counter()
    domain_counts = Counter()
    topic_counts = Counter()
    payment_candidates = 0
    for sem in semantics.values():
        layer_counts.update(sem["evidence_layers"])
        domain_counts.update(sem["policy_domains"])
        topic_counts.update(sem["education_topics"])
        payment_candidates += int(bool(sem["payment_evidence_candidate"]))
        _stop(sem["semantic_classification_proves_payment"] is False, "TASK184_JOM_PAYMENT_PROOF")
        _stop(sem["semantic_classification_proves_financial_identity"] is False, "TASK184_JOM_FINANCIAL_IDENTITY")
        _stop(sem["semantic_classification_proves_policy_identity"] is False, "TASK184_JOM_POLICY_IDENTITY")
    return product, {
        "event_count": len(events),
        "event_type_counts": dict(sorted(Counter(row["event_type"] for row in events).items())),
        "evidence_layer_counts": dict(sorted(layer_counts.items())),
        "policy_domain_counts": dict(sorted(domain_counts.items())),
        "education_topic_counts": dict(sorted(topic_counts.items())),
        "payment_evidence_candidate_count": payment_candidates,
        "semantics_recomputed": True,
        "event_identity_rewritten": False,
    }


def load_planning_rows(contract_path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    contract = load_contract(contract_path)
    rows = _load(ROOT / contract["planning"]["fixture"])
    _stop(isinstance(rows, list) and bool(rows), "TASK184_PLANNING_FIXTURE")
    sources = {
        row["document_id"]: row
        for row in contract["planning"]["sources"]
    }
    keys = set()
    for row in rows:
        doc_id = str(row.get("document_id") or "")
        _stop(doc_id in sources, "TASK184_PLANNING_UNKNOWN_DOCUMENT")
        source = sources[doc_id]
        _stop(row.get("source_family") == source["source_family"], "TASK184_PLANNING_SOURCE_FAMILY")
        _stop(row.get("source_sha256") == source["sha256"], "TASK184_PLANNING_SOURCE_SHA")
        key = (doc_id, str(row.get("locator") or ""))
        _stop(all(key), "TASK184_PLANNING_KEY")
        _stop(key not in keys, "TASK184_PLANNING_DUPLICATE_KEY")
        keys.add(key)
        _stop(bool(row.get("text_redacted")), "TASK184_PLANNING_TEXT")
        _stop(bool(row.get("evidence_role")), "TASK184_PLANNING_ROLE")
        if row.get("document_type") == "LOA":
            _stop(
                row.get("evidence_role") == "PRIMARY_METADATA_ONLY",
                "TASK184_LOA_SUBSTANTIVE_OVERCLAIM",
            )
            _stop(row.get("quality_status") == "PARTIAL", "TASK184_LOA_QUALITY")
        if row.get("source_family") in {"CME", "MUNICIPAL_LEGISLATION"}:
            _stop(
                row.get("evidence_role") == "PRIMARY_NORMATIVE",
                "TASK184_NORMATIVE_ROLE",
            )
    return rows


def build_planning_product(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = load_planning_rows(contract_path)
    product = build_planning_document_index(
        rows,
        generated_at=generated_at,
        software_version=software_version,
    )
    return product, {
        "row_count": len(rows),
        "document_count": len({row["document_id"] for row in rows}),
        "document_type_counts": dict(sorted(Counter(row["document_type"] for row in rows).items())),
        "evidence_role_counts": dict(sorted(Counter(row["evidence_role"] for row in rows).items())),
        "primary_substantive_document_types": sorted({
            row["document_type"]
            for row in rows
            if row["evidence_role"] == "PRIMARY_SUBSTANTIVE"
        }),
        "primary_normative_source_families": sorted({
            row["source_family"]
            for row in rows
            if row["evidence_role"] == "PRIMARY_NORMATIVE"
        }),
        "loa_substantive_parsed": False,
    }


def _catalog(
    substantive: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
    software_version: str,
) -> dict[str, Any]:
    contract = _load(PRODUCT_CONTRACT)
    inverse: dict[str, list[str]] = defaultdict(list)
    for domain_id, products in contract["domain_product_routes"].items():
        for product_name in products:
            inverse[product_name].append(domain_id)
    return build_product_catalog(
        substantive,
        generated_at=generated_at,
        software_version=software_version,
        coverage_domains={
            name: inverse.get(name, [])
            for name in substantive
        },
        readiness={
            name: "READY_WITH_CAUTION"
            for name in substantive
        },
    )


def _with_catalog(
    products: Mapping[str, Mapping[str, Any]],
    *,
    generated_at: str,
    software_version: str,
) -> dict[str, dict[str, Any]]:
    substantive = {
        name: product
        for name, product in products.items()
        if name != "QUERY_PRODUCT_CATALOG"
    }
    catalog = _catalog(
        substantive,
        generated_at=generated_at,
        software_version=software_version,
    )
    return {**substantive, "QUERY_PRODUCT_CATALOG": catalog}


def _report_map(report: Mapping[str, Any]) -> dict[str, str]:
    return {
        row["question_id"]: row["status"]
        for row in report["questions"]
    }


def _transition_report(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    b = _report_map(before)
    a = _report_map(after)
    changed = [
        {
            "question_id": qid,
            "before": b[qid],
            "after": a[qid],
        }
        for qid in sorted(b)
        if b[qid] != a[qid]
    ]
    return {
        "changed_question_count": len(changed),
        "changes": changed,
        "before_status_counts": dict(before["status_counts"]),
        "after_status_counts": dict(after["status_counts"]),
    }


def build_task184_bundle(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    contract = load_contract(contract_path)
    base_products = build_fused_products(
        generated_at=generated_at,
        software_version=software_version,
    )
    baseline = question_answerability(base_products)

    jom, jom_stats = build_jom_product(
        generated_at=generated_at,
        software_version=software_version,
        contract_path=contract_path,
    )
    planning, planning_stats = build_planning_product(
        generated_at=generated_at,
        software_version=software_version,
        contract_path=contract_path,
    )

    base_substantive = {
        name: product
        for name, product in base_products.items()
        if name != "QUERY_PRODUCT_CATALOG"
    }
    jom_only_products = _with_catalog(
        {**base_substantive, "JOM_EVENT_INDEX": jom},
        generated_at=generated_at,
        software_version=software_version,
    )
    planning_only_products = _with_catalog(
        {**base_substantive, "PLANNING_DOCUMENT_INDEX": planning},
        generated_at=generated_at,
        software_version=software_version,
    )
    final_products = _with_catalog(
        {
            **base_substantive,
            "JOM_EVENT_INDEX": jom,
            "PLANNING_DOCUMENT_INDEX": planning,
        },
        generated_at=generated_at,
        software_version=software_version,
    )

    after_jom = question_answerability(jom_only_products)
    after_planning = question_answerability(planning_only_products)
    final = question_answerability(final_products)

    sample_packets = {}
    for sample_id, domain_id, question_text in (
        ("JOM_RADAR", "JOURNAL_EVENT_RADAR", "Que eventos relevantes sairam no Jornal Oficial?"),
        ("SCHOOL_NORMS", "NORMS_SCHOOL_FUNCTIONING", "Que normas mudaram o funcionamento das escolas?"),
        ("PLANNING_2026", "PLANNING_BUDGET", "O que PPA, LDO e LOA estabelecem para 2026?"),
    ):
        packet = query_observatory(
            domain_id,
            final_products,
            question_text=question_text,
        )
        document_counts = Counter(
            str(row.get("query_product_name") or "")
            for row in packet["document_records"]
        )
        numeric_counts = Counter(
            str(row.get("query_product_name") or "")
            for row in packet["numeric_records"]
        )
        sample_packets[sample_id] = {
            "packet_id": packet["packet_id"],
            "packet_sha256": packet["packet_sha256"],
            "numeric_record_count": len(packet["numeric_records"]),
            "document_record_count": len(packet["document_records"]),
            "document_record_counts_by_product": dict(sorted(document_counts.items())),
            "numeric_record_counts_by_product": dict(sorted(numeric_counts.items())),
            "product_gap_count": len(packet["product_gaps"]),
            "used_snapshots": packet["used_snapshots"],
        }

    return {
        "schema": "TASK184_LOCAL_KNOWLEDGE_PACK_BUNDLE_V1",
        "generated_at": generated_at,
        "software_version": software_version,
        "products": final_products,
        "product_stats": {
            "JOM_EVENT_INDEX": jom_stats,
            "PLANNING_DOCUMENT_INDEX": planning_stats,
            "ACCOUNTING_LEDGER": {
                "materialized": False,
                "reason": contract["accounting"]["reason"],
                "task172_observed_rows": contract["accounting"]["task172_live_row_count_observed"],
                "raw_payload_persisted": False,
            },
        },
        "answerability": {
            "baseline": baseline,
            "jom_only": after_jom,
            "planning_only": after_planning,
            "final": final,
            "gain_jom_independent": _transition_report(baseline, after_jom),
            "gain_planning_independent": _transition_report(baseline, after_planning),
            "gain_final": _transition_report(baseline, final),
            "gain_accounting": {
                "changed_question_count": 0,
                "reason": "NO_REAL_ACCOUNTING_ROWS_PERSISTED_TO_MATERIALIZE",
            },
        },
        "sample_packets": sample_packets,
        "guards": {
            "publication_ne_execution": True,
            "planning_ne_execution": True,
            "loa_metadata_ne_substantive_annex_coverage": True,
            "accounting_not_synthesized": True,
            "llm_may_fill_missing_numeric_evidence": False,
        },
        "remote_effects": {
            "network": False,
            "drive_write": False,
            "serving": False,
            "publication": False,
        },
    }


if __name__ == "__main__":
    print(json.dumps(load_contract(), ensure_ascii=False, indent=2, sort_keys=True))
