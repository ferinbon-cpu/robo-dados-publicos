"""Fail-closed review of TASK 042 PPA/LDO scoped Silver persistence."""
from __future__ import annotations

from typing import Any

TASK = "TASK_042_F01_PPA_LDO_SCOPED_SILVER_CREATE_ONLY_READBACK"
BASE_SHA = "319b4ac04c191f17f19f46ea47ce7da24b4ed50e"
TARGET_FOLDER = "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo"
PPA_SHA256 = "0cba09dade1c09224e549e817a859c63edb12a6fb0a5223c5ddb8aa5fe6dc730"
PPA_MD5 = "0b35160ccaece5c6b7eb29786576a7b7"
PPA_BYTES = 2812
PPA_NAME = "F01_PPA_JOM_2026_2029_SCOPED_VALIDATED_PROGRAM_2001__0cba09dade1c__silver_v1.json"
LDO_SHA256 = "4719631a3dd476efe8c760f2b9ce07eba15d678c85b56e95345af70237f02182"
LDO_MD5 = "1dc39a4ac76aaabdb64e776eb30ac51b"
LDO_BYTES = 1544
LDO_NAME = "F01_LDO_JOM_2026_SCOPED_STRUCTURAL_MARKERS__4719631a3dd4__silver_v1.json"


class Task042ReviewError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task042ReviewError(code)


def _validate_candidate(record: dict[str, Any], *, family: str) -> None:
    if family == "PPA":
        expected = {
            "file_name": PPA_NAME,
            "contract": "F01_PPA_JOM_2026_2029_SCOPED_VALIDATED_PROGRAM_2001_SILVER_V1",
            "scope": "SCOPED_PROGRAM_2001_AND_SELECTED_ACTIONS_NOT_COMPLETE_PPA_PARSE",
            "bytes": PPA_BYTES,
            "sha256": PPA_SHA256,
            "md5": PPA_MD5,
        }
    else:
        expected = {
            "file_name": LDO_NAME,
            "contract": "F01_LDO_JOM_2026_SCOPED_STRUCTURAL_MARKERS_SILVER_V1",
            "scope": "SCOPED_LEGAL_IDENTITY_AND_STRUCTURAL_MARKERS_NOT_COMPLETE_LDO_PARSE",
            "bytes": LDO_BYTES,
            "sha256": LDO_SHA256,
            "md5": LDO_MD5,
        }
    for key, value in expected.items():
        _require(record.get(key) == value, f"TASK042_{family}_{key.upper()}_MISMATCH")

    readback = record.get("readback") or {}
    _require(readback.get("verified") is True, f"TASK042_{family}_READBACK_NOT_VERIFIED")
    _require(readback.get("byte_identity") is True, f"TASK042_{family}_BYTE_IDENTITY_NOT_VERIFIED")
    for key in ("bytes", "sha256", "md5"):
        _require(readback.get(key) == expected[key], f"TASK042_{family}_READBACK_{key.upper()}_MISMATCH")


def validate_task042_evidence(evidence: dict[str, Any], task041: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK042_TASK_MISMATCH")
    _require(evidence.get("mode") == "T2_EXACT_TWO_CREATE_ONLY_SCOPED_SILVER_WITH_READBACK", "TASK042_MODE_MISMATCH")
    _require(evidence.get("base_implementation_sha") == BASE_SHA, "TASK042_BASE_SHA_MISMATCH")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "TASK042_OWNER_AUTH_MISSING")
    _require(auth.get("owner_message") == "Prossiga", "TASK042_OWNER_MESSAGE_MISMATCH")
    _require(auth.get("authorized_against_sha") == BASE_SHA, "TASK042_AUTH_SHA_MISMATCH")
    _require(auth.get("scope") == "EXACTLY_TWO_SCOPED_SILVER_CREATE_ONLY_PLUS_TWO_READBACKS", "TASK042_AUTH_SCOPE_MISMATCH")
    _require(auth.get("authorization_consumed") is True, "TASK042_AUTH_NOT_CONSUMED")
    _require(auth.get("future_blanket_authorizations_accepted") is False, "TASK042_BLANKET_AUTH_FORBIDDEN")

    execution = evidence.get("execution") or {}
    _require(execution.get("channel") == "CHAT_FILES_LIBRARY_GOOGLE_DRIVE_CREATE_ONLY", "TASK042_EXECUTION_CHANNEL_MISMATCH")
    _require(execution.get("target_folder_id") == TARGET_FOLDER, "TASK042_TARGET_FOLDER_MISMATCH")
    _require(execution.get("preflight_inventory_performed") is True, "TASK042_PREFLIGHT_NOT_PERFORMED")
    _require(execution.get("target_name_collisions") == 0, "TASK042_TARGET_COLLISION")

    _require(task041.get("task") == "TASK_041_F01_JOM_NATIVE_PPA_LDO_READINESS_REVIEW", "TASK042_TASK041_ID_MISMATCH")
    _require(task041.get("result") == "PASS_TASK041_JOM_NATIVE_PPA_LDO_SCOPED_SILVER_CANDIDATES_READY_NO_WRITE", "TASK042_TASK041_RESULT_MISMATCH")
    _require(task041.get("ppa_candidate_sha256") == PPA_SHA256, "TASK042_TASK041_PPA_HASH_MISMATCH")
    _require(task041.get("ldo_candidate_sha256") == LDO_SHA256, "TASK042_TASK041_LDO_HASH_MISMATCH")
    readiness = task041.get("readiness") or {}
    expected_ready = "READY_FOR_SCOPED_SILVER_CREATE_ONLY_SEPARATE_AUTH_REQUIRED"
    _require(readiness.get("ppa") == expected_ready, "TASK042_TASK041_PPA_NOT_READY")
    _require(readiness.get("ldo") == expected_ready, "TASK042_TASK041_LDO_NOT_READY")

    _validate_candidate(evidence.get("ppa") or {}, family="PPA")
    _validate_candidate(evidence.get("ldo") or {}, family="LDO")

    expected_effects = {
        "public_source_get": 0,
        "drive_inventory_requests": 1,
        "drive_creates": 2,
        "drive_readbacks": 2,
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
    _require((evidence.get("effects") or {}) == expected_effects, "TASK042_EFFECTS_MISMATCH")

    promotion = evidence.get("promotion") or {}
    _require(promotion.get("ppa_silver") is True, "TASK042_PPA_SILVER_NOT_PROMOTED")
    _require(promotion.get("ldo_silver") is True, "TASK042_LDO_SILVER_NOT_PROMOTED")
    _require(promotion.get("loa_silver_existing") is True, "TASK042_LOA_EXISTING_SILVER_LOST")
    _require(promotion.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK042_F01_STATUS_MISMATCH")
    _require(promotion.get("scoped_silver_families") == ["LOA", "PPA", "LDO"], "TASK042_SCOPED_FAMILY_SET_MISMATCH")
    _require(promotion.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK042_EITI_IDENTITY_WEAKENED")
    for key in ("gold", "serving", "publication"):
        _require(promotion.get(key) is False, f"TASK042_{key.upper()}_FORBIDDEN")

    _require(evidence.get("remote_file_ids_persisted") is False, "TASK042_REMOTE_IDS_PERSISTED")
    _require(evidence.get("owner_decision_required") is False, "TASK042_OWNER_DECISION_UNEXPECTED")
    _require(evidence.get("result") == "PASS_TASK042_PPA_LDO_SCOPED_SILVER_CREATE_ONLY_READBACK_VERIFIED", "TASK042_RESULT_MISMATCH")

    return {
        "status": "PASS_TASK042_PPA_LDO_SCOPED_SILVER_PERSISTENCE_REVIEW",
        "f01_status": "SILVER_SCOPED_PARTIAL_VALIDATED",
        "scoped_silver_families": ["LOA", "PPA", "LDO"],
        "ppa_sha256": PPA_SHA256,
        "ldo_sha256": LDO_SHA256,
        "gold_authorized": False,
    }
