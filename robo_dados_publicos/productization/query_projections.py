from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from robo_dados_publicos.productization.question_readiness import build_current_productization_audit

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task204_ledger_query_projections.v1.json"


class Task204Stop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task204Stop(code)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK204_LEDGER_QUERY_PROJECTIONS_V1", "TASK204_SCHEMA")
    _stop(obj.get("issue") == 651, "TASK204_ISSUE")
    _stop(obj.get("base_main_sha") == "f3eac969cfafb0988fe8123b9340b1a52dd12762", "TASK204_BASE")
    _stop(obj["baseline"]["query_projection_backlog_count"] == 11, "TASK204_BASELINE_BACKLOG")
    _stop(obj["expected_after"]["human_ready_count"] == 38, "TASK204_EXPECTED_READY")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK204_REMOTE")
    return obj


def _load_projection(product_name: str, contract: Mapping[str, Any]) -> dict[str, Any]:
    spec = contract["projections"][product_name]
    path = ROOT / str(spec["path"])
    obj = json.loads(path.read_text(encoding="utf-8"))
    expected_schema = "TASK204_ACCOUNTING_QUERY_PROJECTION_V1" if product_name == "ACCOUNTING_LEDGER" else "TASK204_REVENUE_QUERY_PROJECTION_V1"
    _stop(obj.get("schema") == expected_schema, f"TASK204_{product_name}_SCHEMA")
    _stop(obj.get("source_product") == product_name, f"TASK204_{product_name}_PRODUCT")
    _stop(obj.get("source_drive_id") == spec["source_drive_id"], f"TASK204_{product_name}_DRIVE")
    _stop(obj.get("source_row_count") == spec["source_row_count"], f"TASK204_{product_name}_ROWS")
    _stop(obj.get("source_content_sha256") == spec["source_content_sha256"], f"TASK204_{product_name}_CONTENT_SHA")
    _stop(obj.get("source_gzip_sha256") == spec["source_gzip_sha256"], f"TASK204_{product_name}_GZIP_SHA")
    stored_projection_sha = str(obj.get("projection_sha256") or "")
    without_projection_sha = dict(obj)
    without_projection_sha.pop("projection_sha256", None)
    _stop(_sha(without_projection_sha) == stored_projection_sha == spec["projection_sha256"], f"TASK204_{product_name}_PROJECTION_SHA")
    _stop(obj.get("projection_role") == "DERIVED_QUERY_CACHE_NOT_SOURCE_OF_TRUTH", f"TASK204_{product_name}_ROLE")
    sections = dict(obj.get("sections") or {})
    expected_counts = dict(spec["section_counts"])
    _stop(set(sections) == set(expected_counts), f"TASK204_{product_name}_SECTION_SET")
    for name, expected_count in expected_counts.items():
        rows = sections[name]
        _stop(isinstance(rows, list), f"TASK204_{product_name}_{name}_TYPE")
        _stop(len(rows) == int(expected_count), f"TASK204_{product_name}_{name}_COUNT")
        _stop(obj["section_sha256"][name] == _sha(rows), f"TASK204_{product_name}_{name}_SHA")
    return obj


def load_projections(contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, dict[str, Any]]:
    contract = load_contract(contract_path)
    return {product: _load_projection(product, contract) for product in sorted(contract["projections"])}


def projection_packet(question_id: str, *, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(contract_path)
    route = contract["question_projection_routes"].get(question_id)
    _stop(route is not None, "TASK204_QUESTION_NOT_PROJECTED")
    projections = load_projections(contract_path)
    product = str(route["product"])
    projection = projections[product]
    section_names = [str(x) for x in route["sections"]]
    _stop(bool(section_names), "TASK204_EMPTY_ROUTE")
    section_payload: dict[str, Any] = {}
    for name in section_names:
        _stop(name in projection["sections"], "TASK204_UNKNOWN_SECTION")
        rows = projection["sections"][name]
        _stop(bool(rows), "TASK204_EMPTY_SECTION")
        section_payload[name] = rows
    packet = {
        "schema": "OBSERVATORY_LOCAL_QUERY_PROJECTION_PACKET_V1",
        "question_id": question_id,
        "source_product": product,
        "source_snapshot_id": projection["source_snapshot_id"],
        "source_content_sha256": projection["source_content_sha256"],
        "source_drive_id": projection["source_drive_id"],
        "projection_sha256": projection["projection_sha256"],
        "sections": section_payload,
        "claim_boundaries": dict(contract["claim_boundaries"]),
    }
    packet["packet_sha256"] = _sha(packet)
    return packet


def build_projection_readiness(*, generated_at: str, software_version: str, contract_path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    contract = load_contract(contract_path)
    baseline = build_current_productization_audit(generated_at=generated_at, software_version=software_version)
    _stop(baseline["semantic_answerability"] == contract["baseline"]["semantic_answerability"], "TASK204_SEMANTIC_BASELINE")
    _stop(baseline["productization_counts"] == contract["baseline"]["productization_counts"], "TASK204_PRODUCTIZATION_BASELINE")
    _stop(baseline["query_projection_backlog_count"] == contract["baseline"]["query_projection_backlog_count"], "TASK204_BACKLOG_BASELINE")
    baseline_by_id = {row["question_id"]: row for row in baseline["questions"]}
    routes = dict(contract["question_projection_routes"])
    _stop(set(routes) == set(baseline["query_projection_backlog_questions"]), "TASK204_ROUTE_SET")
    rows = []
    for qid in sorted(baseline_by_id):
        before = baseline_by_id[qid]
        if before["human_answer_ready"]:
            state, packet_sha, source_product = "RECORD_BACKED", None, None
        else:
            packet = projection_packet(qid, contract_path=contract_path)
            state = "PROJECTION_BACKED"
            packet_sha = packet["packet_sha256"]
            source_product = packet["source_product"]
        rows.append({
            "question_id": qid,
            "domain_id": before["domain_id"],
            "question": before["question"],
            "semantic_status": before["semantic_status"],
            "before_productization_status": before["productization_status"],
            "productization_status": state,
            "human_answer_ready": True,
            "projection_source_product": source_product,
            "projection_packet_sha256": packet_sha,
        })
    counts = dict(sorted(Counter(row["productization_status"] for row in rows).items()))
    _stop(counts == contract["expected_after"]["readiness_counts"], "TASK204_READINESS_COUNTS")
    human_ready_count = sum(bool(row["human_answer_ready"]) for row in rows)
    _stop(human_ready_count == contract["expected_after"]["human_ready_count"], "TASK204_READY_COUNT")
    return {
        "schema": "OBSERVATORY_QUESTION_PRODUCTIZATION_READINESS_V2",
        "question_count": len(rows),
        "semantic_answerability": dict(baseline["semantic_answerability"]),
        "productization_counts": counts,
        "human_ready_count": human_ready_count,
        "query_projection_backlog_count": 0,
        "query_projection_backlog_questions": [],
        "questions": rows,
        "semantics": {
            "semantic_answerability_equals_source_payload": False,
            "source_ledger_equals_query_projection": False,
            "query_projection_equals_explanation": False,
            "capability_metadata_may_supply_numeric_value": False,
            "llm_may_fill_missing_numeric_evidence": False,
        },
        "remote_effects": {"network": False, "drive_read": False, "drive_write": False, "serving": False, "publication": False, "schedule": False, "recurrence": False},
    }
