"""Fail-closed T0 review of the LOA scoped Silver v2 candidate after TASK 045."""
from __future__ import annotations

import hashlib
import json
from typing import Any

TASK = "TASK_048_F01_LOA_SCOPED_SILVER_V2_CANDIDATE_REVIEW"
MODE = "T0_OFFLINE_CANDIDATE_REVIEW"
BASE_SHA = "2f21e4b90244ead35503638941a9a6c596374cd0"
TASK045_RESULT = "STOP_TASK045_EITI_FINANCIAL_IDENTITY_CHAIN_STILL_INCOMPLETE_AFTER_BOUNDED_READONLY_REVIEW"
V1_SHA = "3894ede7c67e60d3e12795dec3964d78baf24ff350355d98f3825dd5f81caf4c"
CANDIDATE_SHA = "9f04a7202d03a58687d5382565777f15887b056ba28c65d9c01e226af7d3ef25"
TARGET_NAME = "F01_LOA_JOM_2026_SCOPED_VALIDATED_STRUCTURE__9f04a7202d03__silver_v2.json"
TARGET_FOLDER = "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo"


class Task048Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task048Error(code)


def canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def validate_task048_evidence(evidence: dict[str, Any], task045: dict[str, Any], task040: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK048_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK048_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK048_BASE_SHA_MISMATCH")

    _require(task045.get("task") == "TASK_045_F01_BOUNDED_EXISTING_CUSTODY_READONLY_REVIEW", "TASK048_TASK045_ID_MISMATCH")
    _require(task045.get("result") == TASK045_RESULT, "TASK048_TASK045_RESULT_MISMATCH")
    _require((task045.get("promotion") or {}).get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK048_TASK045_EITI_STATUS_MISMATCH")

    _require(task040.get("task") == "TASK_040_LOA_SCOPED_SILVER_CREATE_ONLY_READBACK", "TASK048_TASK040_ID_MISMATCH")
    _require((task040.get("candidate") or {}).get("sha256") == V1_SHA, "TASK048_V1_HASH_MISMATCH")
    _require((task040.get("readback") or {}).get("verified") is True, "TASK048_V1_READBACK_NOT_VERIFIED")

    payload = evidence.get("candidate_payload") or {}
    _require(payload.get("contract") == "F01_LOA_JOM_2026_SCOPED_VALIDATED_STRUCTURE_SILVER_V2", "TASK048_CONTRACT_MISMATCH")
    _require(payload.get("scope") == "SCOPED_VALIDATED_STRUCTURE_AND_ENRICHED_ACTION_FIELDS_NOT_COMPLETE_LOA_PARSE", "TASK048_SCOPE_MISMATCH")

    source = payload.get("source") or {}
    _require(source.get("sha256") == "37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4", "TASK048_SOURCE_HASH_MISMATCH")
    _require(source.get("drive_file_id") == "1bRpmMxacX16P1tJBvam-55OOPTYuQnIA", "TASK048_SOURCE_ID_MISMATCH")

    records = {row.get("action_code"): row for row in payload.get("validated_action_records") or []}
    _require(set(records) == {"12.362.2001.2690", "12.306.2001.2720"}, "TASK048_ACTION_SET_MISMATCH")

    a2690 = records["12.362.2001.2690"]
    _require(a2690.get("unit_code") == "10.04.00", "TASK048_2690_UNIT_MISMATCH")
    _require(a2690.get("appropriation_brl") == 6152000, "TASK048_2690_AMOUNT_MISMATCH")
    _require(a2690.get("expense_group_breakdown_brl") == {"OUTRAS_DESPESAS_CORRENTES": 6142000, "INVESTIMENTOS": 10000}, "TASK048_2690_EXPENSE_GROUP_MISMATCH")
    _require(a2690.get("funding_sources_brl") == {"01_TESOURO": 943000, "02_TRANSFERENCIAS_E_CONVENIOS_ESTADUAIS_VINCULADOS": 5209000}, "TASK048_2690_SOURCE_MISMATCH")
    _require(a2690.get("expense_nature") == "UNKNOWN_NOT_EXPLICIT_ON_SELECTED_PAGES", "TASK048_2690_NATURE_INFERENCE")
    _require(a2690.get("eiti_specific") is False, "TASK048_2690_EITI_MISATTRIBUTION")

    a2720 = records["12.306.2001.2720"]
    _require(a2720.get("unit_code") == "10.05.00", "TASK048_2720_UNIT_MISMATCH")
    _require(a2720.get("appropriation_brl") == 28000000, "TASK048_2720_AMOUNT_MISMATCH")
    _require(a2720.get("expense_group_breakdown_brl") == {"OUTRAS_DESPESAS_CORRENTES": 27999000, "INVESTIMENTOS": 1000}, "TASK048_2720_EXPENSE_GROUP_MISMATCH")
    _require(a2720.get("funding_sources_brl") == {"01_TESOURO": 8680000, "05_TRANSFERENCIAS_E_CONVENIOS_FEDERAIS_VINCULADOS": 19320000}, "TASK048_2720_SOURCE_MISMATCH")
    _require(a2720.get("expense_nature") == "UNKNOWN_NOT_EXPLICIT_ON_SELECTED_PAGES", "TASK048_2720_NATURE_INFERENCE")
    _require(a2720.get("eiti_specific") is False, "TASK048_2720_EITI_MISATTRIBUTION")

    drift = payload.get("material_text_visual_divergence") or {}
    _require(drift.get("observed") is True, "TASK048_TEXT_VISUAL_DRIFT_REMOVED")
    _require(drift.get("text_layer_amount_brl") == 29000000, "TASK048_TEXT_DRIFT_AMOUNT_MISMATCH")
    _require(drift.get("visual_source_amount_brl") == 28000000, "TASK048_VISUAL_AMOUNT_MISMATCH")
    _require(drift.get("silent_repair") is False, "TASK048_SILENT_REPAIR_ENABLED")
    _require(drift.get("automatic_promotion") is False, "TASK048_AUTO_PROMOTION_ENABLED")

    guardrails = payload.get("guardrails") or {}
    for key in ("complete_loa_parse_claim", "ocr_numeric_source_truth", "silent_character_repair",
                "llm_numeric_reconstruction", "program_2001_total_attribution_to_eiti",
                "generic_action_attribution_to_eiti", "compliance_conclusion", "gold_authorized"):
        _require(guardrails.get(key) is False, f"TASK048_GUARDRAIL_{key.upper()}_WEAKENED")
    _require(guardrails.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK048_EITI_STATUS_MISMATCH")

    actual_sha = hashlib.sha256(canonical_payload_bytes(payload)).hexdigest()
    _require(actual_sha == CANDIDATE_SHA, "TASK048_CANDIDATE_HASH_MISMATCH")
    _require(evidence.get("candidate_payload_sha256") == CANDIDATE_SHA, "TASK048_DECLARED_HASH_MISMATCH")

    target = evidence.get("target") or {}
    _require(target.get("folder_id") == TARGET_FOLDER, "TASK048_TARGET_FOLDER_MISMATCH")
    _require(target.get("file_name") == TARGET_NAME, "TASK048_TARGET_NAME_MISMATCH")
    _require(target.get("create_only") is True and target.get("overwrite") is False, "TASK048_TARGET_CREATE_ONLY_WEAKENED")

    readiness = evidence.get("readiness") or {}
    _require(readiness.get("decision") == "READY_FOR_SCOPED_LOA_SILVER_V2_CREATE_ONLY_SEPARATE_AUTH_REQUIRED", "TASK048_READINESS_MISMATCH")
    _require(readiness.get("remote_write_authorized") is False, "TASK048_UNAUTHORIZED_WRITE_ENABLED")
    _require(readiness.get("v1_preserved") is True, "TASK048_V1_PRESERVATION_REMOVED")

    expected_effects = {"source_network":0,"drive_read":0,"drive_write":0,"ocr":0,"bronze":0,"silver":0,"gold":0,"serving":0,"publication":0}
    _require((evidence.get("effects") or {}) == expected_effects, "TASK048_EFFECTS_MISMATCH")
    _require(evidence.get("result") == "PASS_TASK048_LOA_SCOPED_SILVER_V2_CANDIDATE_READY_NO_WRITE", "TASK048_RESULT_MISMATCH")

    return {
        "status": "PASS_TASK048_LOA_SCOPED_SILVER_V2_CANDIDATE_REVIEW",
        "candidate_sha256": CANDIDATE_SHA,
        "target_name": TARGET_NAME,
        "remote_write_authorized": False,
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
        "gold_authorized": False,
    }
