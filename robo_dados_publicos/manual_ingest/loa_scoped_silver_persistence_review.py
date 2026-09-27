"""Fail-closed review of TASK 040 scoped LOA Silver persistence."""
from __future__ import annotations

from typing import Any

TASK = "TASK_040_LOA_SCOPED_SILVER_CREATE_ONLY_READBACK"
BASE_SHA = "4a6e271add0282689dc933a24387a69830f90465"
RUN_ID = 33648450680
JOB_ID = 100308986739
ARTIFACT_ID = 9853733406
ARTIFACT_DIGEST = "sha256:115b84e17dc569e185383debdc5f6da68b3da6092148c4b18e17ce88611cd521"
CANDIDATE_SHA256 = "3894ede7c67e60d3e12795dec3964d78baf24ff350355d98f3825dd5f81caf4c"
CANDIDATE_MD5 = "762d67dc0b1fe5824b2886892d1fef45"
TARGET_NAME = "F01_LOA_JOM_2026_SCOPED_VALIDATED_STRUCTURE__3894ede7c67e__silver_v1.json"
TARGET_FOLDER = "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo"


class Task040ReviewError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task040ReviewError(code)


def validate_task040_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK040_TASK_MISMATCH")
    _require(evidence.get("mode") == "T2_EXACT_ONE_CREATE_ONLY_SCOPED_SILVER_WITH_READBACK", "TASK040_MODE_MISMATCH")
    _require(evidence.get("base_implementation_sha") == BASE_SHA, "TASK040_BASE_SHA_MISMATCH")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "TASK040_OWNER_AUTH_MISSING")
    _require(auth.get("authorized_against_sha") == BASE_SHA, "TASK040_AUTH_SHA_MISMATCH")
    _require(auth.get("scope") == "EXACTLY_ONE_SCOPED_SILVER_CREATE_ONLY_PLUS_ONE_READBACK", "TASK040_AUTH_SCOPE_MISMATCH")
    _require(auth.get("authorization_consumed") is True, "TASK040_AUTH_NOT_CONSUMED")
    _require(auth.get("future_blanket_authorizations_accepted") is False, "TASK040_FUTURE_BLANKET_AUTH_FORBIDDEN")

    run = evidence.get("github_run") or {}
    _require(run.get("run_id") == RUN_ID, "TASK040_RUN_ID_MISMATCH")
    _require(run.get("job_id") == JOB_ID, "TASK040_JOB_ID_MISMATCH")
    _require(run.get("conclusion") == "success", "TASK040_RUN_NOT_SUCCESS")
    _require(run.get("artifact_id") == ARTIFACT_ID, "TASK040_ARTIFACT_ID_MISMATCH")
    _require(run.get("artifact_digest") == ARTIFACT_DIGEST, "TASK040_ARTIFACT_DIGEST_MISMATCH")

    target = evidence.get("target") or {}
    _require(target.get("folder_id") == TARGET_FOLDER, "TASK040_TARGET_FOLDER_MISMATCH")
    _require(target.get("file_name") == TARGET_NAME, "TASK040_TARGET_NAME_MISMATCH")
    _require(target.get("mime_type") == "application/json", "TASK040_TARGET_MIME_MISMATCH")

    candidate = evidence.get("candidate") or {}
    _require(candidate.get("contract") == "F01_LOA_JOM_2026_SCOPED_VALIDATED_STRUCTURE_SILVER_V1", "TASK040_CONTRACT_MISMATCH")
    _require(candidate.get("scope") == "SCOPED_VALIDATED_STRUCTURE_NOT_COMPLETE_LOA_PARSE", "TASK040_SCOPE_MISMATCH")
    _require(candidate.get("bytes") == 2664, "TASK040_BYTES_MISMATCH")
    _require(candidate.get("sha256") == CANDIDATE_SHA256, "TASK040_SHA256_MISMATCH")
    _require(candidate.get("md5") == CANDIDATE_MD5, "TASK040_MD5_MISMATCH")
    _require(candidate.get("complete_loa_claim") is False, "TASK040_COMPLETE_LOA_CLAIM_FORBIDDEN")
    _require(candidate.get("financial_identity_eiti") == "EVIDENCIA_INSUFICIENTE", "TASK040_EITI_IDENTITY_WEAKENED")

    effects = evidence.get("effects") or {}
    expected_effects = {
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
    _require(effects == expected_effects, "TASK040_EFFECTS_MISMATCH")

    readback = evidence.get("readback") or {}
    _require(readback.get("verified") is True, "TASK040_READBACK_NOT_VERIFIED")
    _require(readback.get("byte_identity") is True, "TASK040_BYTE_IDENTITY_NOT_VERIFIED")
    _require(readback.get("bytes") == 2664, "TASK040_READBACK_BYTES_MISMATCH")
    _require(readback.get("sha256") == CANDIDATE_SHA256, "TASK040_READBACK_SHA_MISMATCH")
    _require(readback.get("md5") == CANDIDATE_MD5, "TASK040_READBACK_MD5_MISMATCH")

    promotion = evidence.get("promotion") or {}
    _require(promotion.get("silver") is True, "TASK040_SILVER_NOT_PROMOTED")
    _require(promotion.get("silver_scope") == "SCOPED_VALIDATED_STRUCTURE_NOT_COMPLETE_LOA_PARSE", "TASK040_SILVER_SCOPE_MISMATCH")
    _require(promotion.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK040_F01_STATUS_MISMATCH")
    for key in ("gold", "serving", "publication"):
        _require(promotion.get(key) is False, f"TASK040_{key.upper()}_FORBIDDEN")

    _require(evidence.get("remote_file_id_persisted") is False, "TASK040_REMOTE_ID_PERSISTED")
    _require(evidence.get("owner_decision_required") is False, "TASK040_OWNER_DECISION_UNEXPECTED")
    _require(evidence.get("result") == "PASS_TASK040_SCOPED_SILVER_CREATE_ONLY_READBACK_VERIFIED", "TASK040_RESULT_MISMATCH")

    return {
        "status": "PASS_TASK040_SCOPED_SILVER_PERSISTENCE_REVIEW",
        "f01_status": "SILVER_SCOPED_PARTIAL_VALIDATED",
        "candidate_sha256": CANDIDATE_SHA256,
        "gold_authorized": False,
        "future_blanket_authorizations_accepted": False,
    }
