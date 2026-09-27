from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/task200b_school_norms_primary_evidence.v1.json"
PLANNING_FIXTURE = ROOT / "docs/evidence/fixtures/TASK_184_PLANNING_PRIMARY_EVIDENCE.json"
CURRENT_ANSWERABILITY = ROOT / "config/observatory_semantic_answerability.v2.json"


class Task200BStop(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task200BStop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK200B_SCHOOL_NORMS_PRIMARY_EVIDENCE_V1", "TASK200B_SCHEMA")
    _stop(obj.get("parent_issue") == 636, "TASK200B_ISSUE")
    _stop(
        obj.get("base_main_sha") == "78e070f7bdd6bc03da037532ec3d0445c92c7e14",
        "TASK200B_BASE",
    )
    _stop(obj["gate"]["min_matching_rows"] == 2, "TASK200B_MIN_ROWS")
    _stop(
        set(obj["gate"]["required_source_families"]) == {"CME", "MUNICIPAL_LEGISLATION"},
        "TASK200B_FAMILIES",
    )
    _stop(all(v is False for v in obj["remote_effects"].values()), "TASK200B_REMOTE")
    return obj


def primary_normative_rows() -> list[dict[str, Any]]:
    obj = load_contract()
    expected = {row["document_id"]: row for row in obj["primary_sources"]}
    rows = json.loads(PLANNING_FIXTURE.read_text(encoding="utf-8"))
    selected = [row for row in rows if row.get("document_id") in expected]
    _stop(len(selected) == 2, "TASK200B_PRIMARY_COUNT")
    _stop({row["document_id"] for row in selected} == set(expected), "TASK200B_PRIMARY_IDS")
    for row in selected:
        pin = expected[row["document_id"]]
        _stop(row.get("source_family") == pin["source_family"], "TASK200B_SOURCE_FAMILY")
        _stop(row.get("source_sha256") == pin["source_sha256"], "TASK200B_SOURCE_SHA")
        _stop(row.get("evidence_role") == "PRIMARY_NORMATIVE", "TASK200B_ROLE")
        _stop(row.get("quality_status") == "VALIDATED", "TASK200B_QUALITY")
        _stop("EDUCATION" in set(row.get("policy_domains") or []), "TASK200B_DOMAIN")
        _stop("FULL_TIME_EDUCATION" in set(row.get("topics") or []), "TASK200B_TOPIC")
    return selected


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    rows = primary_normative_rows()
    current = json.loads(CURRENT_ANSWERABILITY.read_text(encoding="utf-8"))
    recipe = current["recipes"]["SCHOOL_NORMS"]
    _stop(len(recipe["signals"]) == 1, "TASK200B_SIGNAL_COUNT")
    signal = recipe["signals"][0]
    _stop(signal["kind"] == "PRODUCT", "TASK200B_SIGNAL_KIND")
    _stop(signal["product"] == "PLANNING_DOCUMENT_INDEX", "TASK200B_SIGNAL_PRODUCT")
    _stop(signal["min_matching_rows"] == 2, "TASK200B_SIGNAL_MIN")
    _stop("JOM_EVENT_INDEX" not in {s["product"] for s in recipe["signals"]}, "TASK200B_JOM_GATE")
    required = signal["required_source_family_role_pairs"]
    _stop(set(required) == {"CME", "MUNICIPAL_LEGISLATION"}, "TASK200B_REQUIRED_FAMILIES")
    _stop(
        all(roles == ["PRIMARY_NORMATIVE"] for roles in required.values()),
        "TASK200B_REQUIRED_ROLES",
    )
    criteria = signal["row_criteria"]
    _stop(criteria["policy_domains_any"] == ["EDUCATION"], "TASK200B_CRITERIA_DOMAIN")
    _stop(criteria["evidence_role_any"] == ["PRIMARY_NORMATIVE"], "TASK200B_CRITERIA_ROLE")
    _stop(criteria["quality_status_any"] == ["VALIDATED"], "TASK200B_CRITERIA_QUALITY")
    return {
        "schema": "TASK200B_SCHOOL_NORMS_PRIMARY_EVIDENCE_VALIDATION_V1",
        "status": "PASS",
        "primary_normative_rows": len(rows),
        "source_families": sorted({row["source_family"] for row in rows}),
        "historical_config_preserved": obj["answerability"]["historical_config"],
        "current_config": obj["answerability"]["current_config"],
        "recent_jom_is_required_gate": False,
        "network": False,
        "drive_write": False,
    }
