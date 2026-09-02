"""Fail-closed review of TASK 047 PPA scoped Silver v2 persistence."""
from __future__ import annotations

from typing import Any

TASK = "TASK_047_F01_PPA_SCOPED_SILVER_V2_CREATE_ONLY_READBACK"
MODE = "T2_CREATE_ONLY_ONE_SCOPED_SILVER_V2_WITH_READBACK"
BASE_SHA = "f28ba1153d2567f46723493dc6704ee7b4a7184e"
TARGET_SHA = "1326c17b53b12064a04cc84123b0414ea77a3e80a8f62fe7cea0dc13eafdd280"
TARGET_BYTES = 3726
TARGET_NAME = "F01_PPA_JOM_2026_2029_SCOPED_VALIDATED_PROGRAM_2001__1326c17b53b1__silver_v2.json"


class Task047Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task047Error(code)


def validate_task047_evidence(evidence: dict[str, Any], task046: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK047_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK047_MODE_MISMATCH")
    _require(evidence.get("base_implementation_sha") == BASE_SHA, "TASK047_BASE_SHA_MISMATCH")

    _require(task046.get("task") == "TASK_046_F01_PPA_SCOPED_SILVER_V2_CANDIDATE_REVIEW", "TASK047_TASK046_ID_MISMATCH")
    _require(task046.get("candidate_sha256") == TARGET_SHA, "TASK047_TASK046_SHA_MISMATCH")
    _require((task046.get("target") or {}).get("file_name") == TARGET_NAME, "TASK047_TASK046_TARGET_MISMATCH")
    _require((task046.get("readiness") or {}).get("decision") == "READY_FOR_SCOPED_SILVER_V2_CREATE_ONLY_SEPARATE_AUTH_REQUIRED", "TASK047_TASK046_READINESS_MISMATCH")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "TASK047_OWNER_AUTH_REQUIRED")
    _require(auth.get("owner_message") == "PROSSIGA E ATUALIZE O DRIVE", "TASK047_OWNER_MESSAGE_MISMATCH")
    _require(auth.get("authorization_consumed_for_silver_write") is True, "TASK047_AUTH_NOT_CONSUMED")

    execution = evidence.get("execution") or {}
    _require(execution.get("target_folder_id") == "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo", "TASK047_FOLDER_MISMATCH")
    _require(execution.get("preflight_inventory_performed") is True, "TASK047_PREFLIGHT_REQUIRED")
    _require(execution.get("target_name_collision_observed") is False, "TASK047_COLLISION_FORBIDDEN")

    ppa = evidence.get("ppa") or {}
    _require(ppa.get("file_name") == TARGET_NAME, "TASK047_FILENAME_MISMATCH")
    _require(ppa.get("sha256") == TARGET_SHA, "TASK047_SHA_MISMATCH")
    _require(ppa.get("bytes") == TARGET_BYTES, "TASK047_BYTES_MISMATCH")
    _require(ppa.get("v1_preserved") is True, "TASK047_V1_MUST_BE_PRESERVED")
    _require(bool(ppa.get("remote_file_id")), "TASK047_REMOTE_FILE_ID_REQUIRED")
    rb = ppa.get("readback") or {}
    _require(rb.get("verified") is True and rb.get("byte_identity") is True, "TASK047_READBACK_REQUIRED")
    _require(rb.get("sha256") == TARGET_SHA and rb.get("bytes") == TARGET_BYTES, "TASK047_READBACK_IDENTITY_MISMATCH")

    effects = evidence.get("effects") or {}
    expected = {
        "public_source_get": 0, "drive_inventory_requests": 1, "drive_creates": 1,
        "drive_readbacks": 1, "overwrite": 0, "replace": 0, "delete": 0,
        "cleanup": 0, "retry": 0, "ocr": 0, "bronze": 0, "gold": 0,
        "serving": 0, "publication": 0,
    }
    _require(effects == expected, "TASK047_EFFECTS_MISMATCH")

    promotion = evidence.get("promotion") or {}
    _require(promotion.get("ppa_silver_v2") is True, "TASK047_SILVER_V2_NOT_RECORDED")
    _require(promotion.get("ppa_silver_v1_preserved") is True, "TASK047_SILVER_V1_NOT_PRESERVED")
    _require(promotion.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK047_F01_STATUS_MISMATCH")
    _require(promotion.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK047_EITI_STATUS_WEAKENED")
    for key in ("gold", "serving", "publication"):
        _require(promotion.get(key) is False, f"TASK047_{key.upper()}_FORBIDDEN")

    _require(evidence.get("result") == "PASS_TASK047_PPA_SCOPED_SILVER_V2_CREATE_ONLY_READBACK_VERIFIED", "TASK047_RESULT_MISMATCH")
    return {
        "status": "PASS_TASK047_PPA_SCOPED_SILVER_V2_PERSISTENCE_REVIEW",
        "sha256": TARGET_SHA,
        "bytes": TARGET_BYTES,
        "f01_status": "SILVER_SCOPED_PARTIAL_VALIDATED",
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
        "gold": False,
    }
