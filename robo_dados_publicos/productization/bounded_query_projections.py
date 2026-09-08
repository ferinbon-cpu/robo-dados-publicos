from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.analytics.current_observatory_answerability import (
    current_answerability_config,
    current_question_answerability,
)
from robo_dados_publicos.analytics.observatory_products import query_observatory
from robo_dados_publicos.productization.question_readiness import (
    build_question_readiness,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task204_bounded_query_projections.v1.json"


class Task204ProjectionStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task204ProjectionStop(code)


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
    _stop(obj.get("schema") == "TASK204_BOUNDED_QUERY_PROJECTIONS_V1", "TASK204_SCHEMA")
    _stop(obj.get("issue") == 652, "TASK204_ISSUE")
    _stop(
        obj.get("base_main_sha") == "f3eac969cfafb0988fe8123b9340b1a52dd12762",
        "TASK204_BASE",
    )
    acct = obj["source_snapshots"]["ACCOUNTING_LEDGER"]
    revenue = obj["source_snapshots"]["REVENUE_LEDGER"]
    _stop(acct["row_count"] == 39783, "TASK204_ACCOUNTING_ROWS")
    _stop(acct["gzip_bytes"] == 7845217, "TASK204_ACCOUNTING_BYTES")
    _stop(
        acct["gzip_sha256"]
        == "5447581813677855ac8edcc70e6a90164ef1caa7799df544cc0a08d62ada25b0",
        "TASK204_ACCOUNTING_GZIP_SHA",
    )
    _stop(
        acct["content_sha256"]
        == "64503339d8352a2f61e1ee8596e9a7ab4dcd6237d1d84010682b4203992b4cb8",
        "TASK204_ACCOUNTING_CONTENT_SHA",
    )
    _stop(revenue["row_count"] == 2286, "TASK204_REVENUE_ROWS")
    _stop(revenue["gzip_bytes"] == 246707, "TASK204_REVENUE_BYTES")
    _stop(
        revenue["gzip_sha256"]
        == "02c644bfaf35a70a981967afdc15e0d0e548ed7df30a6da54e21435b17564847",
        "TASK204_REVENUE_GZIP_SHA",
    )
    _stop(
        revenue["content_sha256"]
        == "fd110fa5c0c2a2583c475a191fef23669c9453a2dbf015a92036247c03d3b8e6",
        "TASK204_REVENUE_CONTENT_SHA",
    )
    _stop(acct["verified_in_task204"] is True, "TASK204_ACCOUNTING_NOT_VERIFIED")
    _stop(revenue["verified_in_task204"] is True, "TASK204_REVENUE_NOT_VERIFIED")
    _stop(
        len(obj["question_projection_map"])
        == obj["expected_transition"]["task204_bounded_projection_covered"]
        == 11,
        "TASK204_PROJECTION_QUESTION_COUNT",
    )
    _stop(
        obj["expected_transition"]["ontology_summary_renderable"] == 38,
        "TASK204_RENDERABLE_EXPECTATION",
    )
    _stop(
        obj["expected_transition"]["arbitrary_drilldown_full_ledger_local"] is False,
        "TASK204_NO_FULL_LOCAL_LEDGER",
    )
    semantics = obj["semantics"]
    _stop(semantics["projection_replaces_source_snapshot"] is False, "TASK204_SOURCE_REPLACEMENT")
    _stop(semantics["projection_is_source_of_truth"] is False, "TASK204_PROJECTION_SOURCE_TRUTH")
    _stop(semantics["source_snapshot_remains_canonical"] is True, "TASK204_CANONICAL_SOURCE")
    _stop(
        semantics["capability_metadata_may_supply_numeric_value"] is False,
        "TASK204_CAPABILITY_NUMERIC",
    )
    _stop(
        semantics["bounded_projection_may_supply_pinned_derived_value"] is True,
        "TASK204_PROJECTION_NUMERIC",
    )
    _stop(semantics["revenue_ne_expenditure"] is True, "TASK204_REVENUE_GUARD")
    _stop(
        semantics["rests_payable_ne_current_year_expenditure"] is True,
        "TASK204_RESTS_GUARD",
    )
    _stop(semantics["selected_rankings_are_exhaustive"] is False, "TASK204_RANKING_GUARD")
    _stop(semantics["llm_may_fill_missing_numeric_evidence"] is False, "TASK204_LLM_NUMERIC")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK204_REMOTE")
    return obj


def validate_projection_values(
    path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    obj = load_contract(path)
    views = obj["projection_views"]

    stages = views["ACCOUNTING_EDUCATION_STAGE_TOTALS"]
    _stop(stages["source_transaction_rows"] == 8224, "TASK204_EDUCATION_ROWS")
    _stop(
        stages["through_april"]
        == {
            "empenhado_liquido_brl": "319000956.31",
            "liquidado_brl": "138279835.79",
            "pago_brl": "104176664.15",
        },
        "TASK204_APRIL_TOTALS",
    )
    _stop(
        stages["through_july"]["empenhado_liquido_brl"] == "368762412.07",
        "TASK204_JULY_COMMITTED",
    )
    _stop(
        stages["through_july"]["liquidado_brl"] == "262452288.06",
        "TASK204_JULY_LIQUIDATED",
    )
    _stop(
        stages["through_july"]["pago_brl"] == "227797802.44",
        "TASK204_JULY_PAID",
    )

    program = views["ACCOUNTING_PROGRAM_ACTION_SUMMARY"]
    _stop(program["distinct_program_action_pairs"] == 22, "TASK204_PROGRAM_ACTION_COUNT")
    _stop(
        program["program_2001_totals"]["empenhado_liquido_brl"] == "361812552.63",
        "TASK204_PROGRAM_2001_COMMITTED",
    )
    _stop(
        program["program_2001_totals"]["pago_brl"] == "223896806.58",
        "TASK204_PROGRAM_2001_PAID",
    )

    funding = views["ACCOUNTING_FUNDING_APPLICATION_SUMMARY"]
    _stop(funding["distinct_funding_application_pairs"] == 39, "TASK204_FUNDING_PAIR_COUNT")
    expense = views["ACCOUNTING_EXPENSE_ELEMENT_SUMMARY"]
    _stop(expense["distinct_expense_elements"] == 93, "TASK204_EXPENSE_ELEMENT_COUNT")

    procurement = views["ACCOUNTING_PROCUREMENT_SUPPLIER_MODALITY_SUMMARY"]
    _stop(procurement["formal_procurement_rows"] == 1779, "TASK204_PROCUREMENT_ROWS")
    _stop(procurement["cnpj_rows"] == 1751, "TASK204_PROCUREMENT_CNPJ_ROWS")
    _stop(procurement["person_rows_redacted"] == 28, "TASK204_PROCUREMENT_PERSON_ROWS")
    _stop(
        procurement["person_supplier_names_or_identifiers_persisted"] is False,
        "TASK204_PROCUREMENT_PERSON_PII",
    )
    encoded_procurement = json.dumps(procurement, ensure_ascii=False).casefold()
    _stop("pessoa física -" not in encoded_procurement, "TASK204_PERSON_PUBLIC_ID_LEAK")

    control = views["ACCOUNTING_COMMITMENT_CONTROL_SUMMARY"]
    _stop(control["unique_commitment_numbers"] == 1139, "TASK204_COMMITMENT_COUNT")
    _stop(control["unique_official_record_ids"] == 8224, "TASK204_OFFICIAL_RECORD_COUNT")

    rests = views["ACCOUNTING_RESTS_PAYABLE_SUMMARY"]
    april_education = next(
        row for row in rests["education"]
        if row["period"] == "2026-04"
    )
    _stop(april_education["total_balance_brl"] == "3010505.55", "TASK204_RESTS_APRIL_EDU")

    revenue = views["REVENUE_EDUCATION_FUNDING_APPLICATION_SUMMARY"]["net_totals"]
    _stop(revenue["education_application_brl"] == "241960964.18", "TASK204_REVENUE_EDUCATION")
    _stop(revenue["fundeb_linked_brl"] == "118066203.65", "TASK204_REVENUE_FUNDEB")
    _stop(revenue["education_tesouro_brl"] == "109552581.52", "TASK204_REVENUE_TESOURO")
    _stop(revenue["education_state_transfers_brl"] == "119045512.07", "TASK204_REVENUE_STATE")
    _stop(revenue["education_federal_transfers_brl"] == "13362870.59", "TASK204_REVENUE_FEDERAL")
    _stop(revenue["eti_all_linked_brl"] == "3692142.87", "TASK204_REVENUE_ETI")

    return {
        "schema": "TASK204_BOUNDED_QUERY_PROJECTION_VALIDATION_V1",
        "status": "PASS",
        "projection_view_count": len(views),
        "projection_question_count": len(obj["question_projection_map"]),
        "accounting_source_rows": obj["source_snapshots"]["ACCOUNTING_LEDGER"]["row_count"],
        "revenue_source_rows": obj["source_snapshots"]["REVENUE_LEDGER"]["row_count"],
        "network": False,
        "drive_write": False,
        "serving": False,
        "publication": False,
    }


def projection_views_for_question(
    question_id: str,
    *,
    path: str | Path = DEFAULT_CONTRACT,
) -> list[dict[str, Any]]:
    obj = load_contract(path)
    names = list(obj["question_projection_map"].get(question_id, []))
    return [
        {
            "projection_view": name,
            "value": obj["projection_views"][name],
            "source_snapshots": obj["source_snapshots"],
            "projection_is_source_of_truth": False,
            "source_snapshot_remains_canonical": True,
        }
        for name in names
    ]


def build_renderable_packet(
    question_id: str,
    products: Mapping[str, Mapping[str, Any]],
    *,
    path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    obj = load_contract(path)
    config = current_answerability_config()
    question = next(
        (row for row in config["questions"] if row["id"] == question_id),
        None,
    )
    _stop(question is not None, "TASK204_UNKNOWN_QUESTION")
    base_packet = query_observatory(
        question["domain_id"],
        products,
        question_text=question["text"],
    )
    projections = projection_views_for_question(question_id, path=path)
    material = {
        "question_id": question_id,
        "domain_id": question["domain_id"],
        "base_packet_id": base_packet["packet_id"],
        "base_packet_sha256": base_packet["packet_sha256"],
        "projection_views": projections,
        "source_snapshot_ids": {
            name: spec["snapshot_id"]
            for name, spec in sorted(obj["source_snapshots"].items())
        },
    }
    digest = _sha(material)
    return {
        "schema": "OBSERVATORY_RENDERABLE_PACKET_V1",
        "renderable_packet_id": "RPK_" + digest[:24],
        "renderable_packet_sha256": digest,
        "question_id": question_id,
        "domain_id": question["domain_id"],
        "question": question["text"],
        "base_evidence_packet": base_packet,
        "bounded_projection_views": projections,
        "projection_count": len(projections),
        "ontology_summary_scope": True,
        "arbitrary_drilldown_full_ledger_local": False,
        "projection_replaces_source_snapshot": False,
        "source_snapshot_remains_canonical": True,
        "llm_numeric_truth_allowed": False,
    }


def build_task204_renderability_audit(
    products: Mapping[str, Mapping[str, Any]],
    *,
    path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    obj = load_contract(path)
    validate_projection_values(path)
    semantic = current_question_answerability(products)
    _stop(semantic["status_counts"] == {"MATERIALIZED_ANSWERABLE": 38}, "TASK204_SEMANTIC_38")
    baseline = build_question_readiness(products)
    _stop(
        baseline["productization_counts"]
        == {
            "CAPABILITY_ONLY": 3,
            "MIXED_RECORD_AND_CAPABILITY": 8,
            "RECORD_BACKED": 27,
        },
        "TASK204_TASK203_BASELINE",
    )
    mapped = set(obj["question_projection_map"])
    baseline_backlog = set(baseline["query_projection_backlog_questions"])
    _stop(mapped == baseline_backlog, "TASK204_BACKLOG_MAP_MISMATCH")

    rows = []
    for row in baseline["questions"]:
        qid = row["question_id"]
        if row["human_answer_ready"]:
            backing = "LOCAL_RECORD_BACKED"
            projection_count = 0
        else:
            projections = projection_views_for_question(qid, path=path)
            _stop(bool(projections), "TASK204_MISSING_PROJECTION")
            backing = "BOUNDED_SOURCE_PINNED_PROJECTION_BACKED"
            projection_count = len(projections)

        packet = build_renderable_packet(qid, products, path=path)
        _stop(
            packet["projection_count"] == projection_count,
            "TASK204_PACKET_PROJECTION_COUNT",
        )
        rows.append(
            {
                "question_id": qid,
                "domain_id": row["domain_id"],
                "question": row["question"],
                "task203_productization_status": row["productization_status"],
                "task204_renderability_backing": backing,
                "ontology_summary_renderable": True,
                "projection_count": projection_count,
                "renderable_packet_id": packet["renderable_packet_id"],
                "renderable_packet_sha256": packet["renderable_packet_sha256"],
            }
        )

    counts = Counter(row["task204_renderability_backing"] for row in rows)
    _stop(len(rows) == 38, "TASK204_QUESTION_COUNT")
    _stop(
        counts
        == {
            "LOCAL_RECORD_BACKED": 27,
            "BOUNDED_SOURCE_PINNED_PROJECTION_BACKED": 11,
        },
        "TASK204_RENDERABILITY_COUNTS",
    )
    _stop(all(row["ontology_summary_renderable"] for row in rows), "TASK204_NOT_ALL_RENDERABLE")

    return {
        "schema": "TASK204_ONTOLOGY_SUMMARY_RENDERABILITY_AUDIT_V1",
        "question_count": 38,
        "semantic_answerability": dict(semantic["status_counts"]),
        "task203_productization_counts": dict(baseline["productization_counts"]),
        "task204_renderability_counts": dict(sorted(counts.items())),
        "ontology_summary_renderable_count": 38,
        "bounded_projection_question_count": len(mapped),
        "bounded_projection_questions": sorted(mapped),
        "questions": sorted(rows, key=lambda x: x["question_id"]),
        "semantics": {
            "ontology_summary_renderable_ne_arbitrary_drilldown_complete": True,
            "arbitrary_drilldown_full_ledger_local": False,
            "projection_replaces_source_snapshot": False,
            "source_snapshot_remains_canonical": True,
            "selected_rankings_are_exhaustive": False,
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
