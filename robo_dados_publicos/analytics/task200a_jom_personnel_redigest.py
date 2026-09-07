from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from robo_dados_publicos.analytics.observatory_products import build_jom_event_index
from robo_dados_publicos.analytics.task184_local_bundle import load_jom_events
from robo_dados_publicos.journal.semantic_layers import classify_event

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task200a_jom_personnel_redigest.v1.json"


class Task200AStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task200AStop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK200A_JOM_PERSONNEL_REDIGEST_V1", "TASK200A_SCHEMA")
    _stop(obj.get("issue") == 636, "TASK200A_ISSUE")
    _stop(obj.get("base_main_sha") == "fc89f34215d4cd9188ec98a4ee05a73a74bc5266", "TASK200A_BASE")
    _stop(obj["redigest"]["event_count"] == 10, "TASK200A_COUNT")
    _stop(obj["redigest"]["principal_subject"] == "EDUCATION_PERSONNEL", "TASK200A_SUBJECT")
    _stop(obj["redigest"]["native_text_only"] is True, "TASK200A_NATIVE")
    _stop(obj["redigest"]["ocr_used"] is False, "TASK200A_OCR")
    _stop(obj["redigest"]["event_identity_rewritten"] is False, "TASK200A_IDENTITY")
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK200A_REMOTE")
    return obj


def load_redigest_rows(path: str | Path = DEFAULT_CONTRACT) -> list[dict[str, Any]]:
    obj = load_contract(path)
    rows = json.loads((ROOT / obj["source_fixture"]).read_text(encoding="utf-8"))
    _stop(isinstance(rows, list) and len(rows) == 10, "TASK200A_FIXTURE_ROWS")
    ids = [str(row["event_id"]) for row in rows]
    _stop(len(set(ids)) == 10, "TASK200A_FIXTURE_IDS")
    allowed_actions = {
        "EXONERATION_REQUESTED",
        "EXONERATION_OFFICE",
        "RECTIFY_EFFECTIVE_APPOINTMENT",
        "REVOKE_EFFECTIVE_APPOINTMENT",
        "EFFECTIVE_APPOINTMENT_FROM_PUBLIC_COMPETITION",
    }
    for row in rows:
        _stop(row["principal_subject"] == "EDUCATION_PERSONNEL", "TASK200A_ROW_SUBJECT")
        _stop(row["principal_action"] in allowed_actions, "TASK200A_ROW_ACTION")
        _stop(bool(row["object_text_native"]), "TASK200A_ROW_TEXT")
        _stop(len(str(row["source_sha256"])) == 64, "TASK200A_ROW_SHA")
        _stop(len(str(row["page_native_text_sha256"])) == 64, "TASK200A_PAGE_SHA")
    return rows


def apply_personnel_redigest(
    events: list[dict[str, Any]],
    *,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    patches = {row["event_id"]: row for row in load_redigest_rows(contract_path)}
    by_id = {str(row["event_id"]): row for row in events}
    _stop(set(patches) <= set(by_id), "TASK200A_EVENT_NOT_FOUND")

    updated: list[dict[str, Any]] = []
    for source in events:
        row = dict(source)
        patch = patches.get(str(row["event_id"]))
        if patch is not None:
            _stop(row.get("object_text") in {None, ""}, "TASK200A_SOURCE_TEXT_NOT_BLANK")
            _stop(int(row.get("edition")) == int(patch["edition"]), "TASK200A_EDITION")
            _stop(int(row.get("page_number")) == int(patch["page_number"]), "TASK200A_PAGE")
            _stop(str(row.get("source_sha256")) == str(patch["source_sha256"]), "TASK200A_SOURCE_SHA")
            _stop(str(row.get("event_type")) == "PORTARIA", "TASK200A_EVENT_TYPE")
            row["object_text"] = patch["object_text_native"]
            row["excerpt_redacted"] = patch["object_text_native"]
        updated.append(row)

    _stop(len(updated) == len(events) == 303, "TASK200A_ROW_COUNT")
    return updated, {
        "patched_event_count": len(patches),
        "event_identity_rewritten": False,
        "native_text_only": True,
        "ocr_used": False,
    }


def build_task200a_jom_product(
    *,
    generated_at: str,
    software_version: str,
    contract_path: str | Path = DEFAULT_CONTRACT,
) -> dict[str, Any]:
    events, patch_stats = apply_personnel_redigest(
        load_jom_events(),
        contract_path=contract_path,
    )
    semantics = {row["event_id"]: classify_event(row) for row in events}
    selected = set(row["event_id"] for row in load_redigest_rows(contract_path))
    for event_id in selected:
        sem = semantics[event_id]
        _stop("EDUCATION" in sem["policy_domains"], "TASK200A_EDUCATION_DOMAIN")
        _stop("PERSONNEL" in sem["evidence_layers"], "TASK200A_PERSONNEL_LAYER")

    product = build_jom_event_index(
        events,
        semantics,
        generated_at=generated_at,
        software_version=software_version,
    )
    _stop(product["row_count"] == 303, "TASK200A_PRODUCT_ROWS")

    personnel_education = [
        row for row in product["rows"]
        if "EDUCATION" in set(row.get("policy_domains") or [])
        and "PERSONNEL" in set(row.get("evidence_layers") or [])
    ]
    _stop(len(personnel_education) >= 10, "TASK200A_PERSONNEL_COUNT")

    layer_counts = Counter()
    domain_counts = Counter()
    for sem in semantics.values():
        layer_counts.update(sem["evidence_layers"])
        domain_counts.update(sem["policy_domains"])

    product["task200a_overlay"] = {
        **patch_stats,
        "personnel_education_matching_rows": len(personnel_education),
        "evidence_layer_counts": dict(sorted(layer_counts.items())),
        "policy_domain_counts": dict(sorted(domain_counts.items())),
    }
    return product


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    rows = load_redigest_rows(path)
    return {
        "schema": "TASK200A_JOM_PERSONNEL_REDIGEST_VALIDATION_V1",
        "status": "PASS",
        "redigested_event_count": len(rows),
        "unique_editions": len({row["edition"] for row in rows}),
        "native_text_only": True,
        "ocr_used": False,
        "network": False,
        "drive_write": False,
    }
