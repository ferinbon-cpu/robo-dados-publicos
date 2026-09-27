"""Fail-closed offline review of the owner-authorized LOA scoped Silver v2 persistence."""
from __future__ import annotations

from typing import Any

TASK = "TASK_050_F01_LOA_SCOPED_SILVER_V2_CREATE_ONLY_READBACK"
MODE = "T2_CREATE_ONLY_ONE_SCOPED_SILVER_V2_WITH_READBACK"
BASE_SHA = "647f432e7a98d61532e56bdd1f61a36748bbc0e0"
TARGET_SHA = "9f04a7202d03a58687d5382565777f15887b056ba28c65d9c01e226af7d3ef25"
V1_SHA = "3894ede7c67e60d3e12795dec3964d78baf24ff350355d98f3825dd5f81caf4c"
TARGET_NAME = "F01_LOA_JOM_2026_SCOPED_VALIDATED_STRUCTURE__9f04a7202d03__silver_v2.json"
TARGET_FOLDER = "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo"


class Task050ReviewError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task050ReviewError(code)


def validate_task050_evidence(evidence: dict[str, Any], task048: dict[str, Any], task040: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK050_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK050_MODE_MISMATCH")
    _require(evidence.get("base_implementation_sha") == BASE_SHA, "TASK050_BASE_SHA_MISMATCH")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "TASK050_OWNER_AUTH_MISSING")
    _require(auth.get("authorized_against_sha") == BASE_SHA, "TASK050_AUTH_SHA_MISMATCH")
    _require(auth.get("authorization_consumed_for_silver_write") is True, "TASK050_AUTH_NOT_CONSUMED")

    _require(task048.get("task") == "TASK_048_F01_LOA_SCOPED_SILVER_V2_CANDIDATE_REVIEW", "TASK050_TASK048_ID_MISMATCH")
    _require(task048.get("candidate_payload_sha256") == TARGET_SHA, "TASK050_TASK048_HASH_MISMATCH")
    _require((task048.get("target") or {}).get("file_name") == TARGET_NAME, "TASK050_TASK048_NAME_MISMATCH")
    _require((task048.get("readiness") or {}).get("decision") == "READY_FOR_SCOPED_LOA_SILVER_V2_CREATE_ONLY_SEPARATE_AUTH_REQUIRED", "TASK050_TASK048_NOT_READY")

    _require(task040.get("task") == "TASK_040_LOA_SCOPED_SILVER_CREATE_ONLY_READBACK", "TASK050_TASK040_ID_MISMATCH")
    _require((task040.get("candidate") or {}).get("sha256") == V1_SHA, "TASK050_V1_HASH_MISMATCH")
    _require((task040.get("readback") or {}).get("verified") is True, "TASK050_V1_READBACK_NOT_VERIFIED")

    execution = evidence.get("execution") or {}
    _require(execution.get("target_folder_id") == TARGET_FOLDER, "TASK050_TARGET_FOLDER_MISMATCH")
    _require(execution.get("preflight_inventory_performed") is True, "TASK050_PREFLIGHT_NOT_PERFORMED")
    _require(execution.get("target_name_collision_observed") is False, "TASK050_COLLISION_OBSERVED")

    loa = evidence.get("loa") or {}
    _require(loa.get("file_name") == TARGET_NAME, "TASK050_TARGET_NAME_MISMATCH")
    _require(loa.get("contract") == "F01_LOA_JOM_2026_SCOPED_VALIDATED_STRUCTURE_SILVER_V2", "TASK050_CONTRACT_MISMATCH")
    _require(loa.get("scope") == "SCOPED_VALIDATED_STRUCTURE_AND_ENRICHED_ACTION_FIELDS_NOT_COMPLETE_LOA_PARSE", "TASK050_SCOPE_MISMATCH")
    _require(loa.get("bytes") == 3866, "TASK050_BYTE_COUNT_MISMATCH")
    _require(loa.get("sha256") == TARGET_SHA, "TASK050_HASH_MISMATCH")
    _require(loa.get("v1_preserved") is True and loa.get("v1_sha256") == V1_SHA, "TASK050_V1_NOT_PRESERVED")

    rb = loa.get("readback") or {}
    _require(rb.get("verified") is True, "TASK050_READBACK_NOT_VERIFIED")
    _require(rb.get("byte_identity") is True, "TASK050_READBACK_NOT_IDENTICAL")
    _require(rb.get("bytes") == 3866 and rb.get("sha256") == TARGET_SHA, "TASK050_READBACK_HASH_OR_BYTES_MISMATCH")

    effects = evidence.get("effects") or {}
    expected = {
        "public_source_get": 0,
        "drive_inventory_requests": 1,
        "drive_creates": 1,
        "drive_readbacks": 1,
        "overwrite": 0,
        "replace": 0,
        "delete": 0,
        "cleanup": 0,
        "retry": 0,
        "ocr": 0,
        "bronze": 0,
        "gold": 0,
        "serving": 0,
        "publication": 0,
    }
    _require(effects == expected, "TASK050_EFFECTS_MISMATCH")

    promotion = evidence.get("promotion") or {}
    _require(promotion.get("loa_silver_v2") is True, "TASK050_SILVER_V2_NOT_PROMOTED")
    _require(promotion.get("loa_silver_v1_preserved") is True, "TASK050_V1_PRESERVATION_REMOVED")
    _require(promotion.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK050_F01_STATUS_MISMATCH")
    _require(promotion.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK050_EITI_STATUS_MISMATCH")
    _require(promotion.get("gold") is False and promotion.get("serving") is False and promotion.get("publication") is False, "TASK050_DOWNSTREAM_PROMOTION_ENABLED")

    _require(evidence.get("result") == "PASS_TASK050_LOA_SCOPED_SILVER_V2_CREATE_ONLY_READBACK_VERIFIED", "TASK050_RESULT_MISMATCH")

    return {
        "status": "PASS_TASK050_LOA_SCOPED_SILVER_V2_PERSISTENCE_REVIEW",
        "target_sha256": TARGET_SHA,
        "target_name": TARGET_NAME,
        "readback_verified": True,
        "f01_status": "SILVER_SCOPED_PARTIAL_VALIDATED",
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
        "gold": False,
    }
