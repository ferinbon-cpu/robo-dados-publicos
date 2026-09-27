"""Fail-closed T0 review of the F01 PPA scoped Silver v2 candidate."""
from __future__ import annotations

import hashlib
import json
from typing import Any

TASK = "TASK_046_F01_PPA_SCOPED_SILVER_V2_CANDIDATE_REVIEW"
MODE = "T0_OFFLINE_CANDIDATE_REVIEW"
BASE_SHA = "1b4273d9ab3c1ad4dc98dfee1fe0ad55c8281173"
V1_SHA256 = "0cba09dade1c09224e549e817a859c63edb12a6fb0a5223c5ddb8aa5fe6dc730"
V2_SHA256 = "1326c17b53b12064a04cc84123b0414ea77a3e80a8f62fe7cea0dc13eafdd280"
TARGET_NAME = "F01_PPA_JOM_2026_2029_SCOPED_VALIDATED_PROGRAM_2001__1326c17b53b1__silver_v2.json"
TASK045_RESULT = "STOP_TASK045_EITI_FINANCIAL_IDENTITY_CHAIN_STILL_INCOMPLETE_AFTER_BOUNDED_READONLY_REVIEW"


class Task046Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task046Error(code)


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def validate_task046_evidence(evidence: dict[str, Any], task045: dict[str, Any], task042: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK046_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK046_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK046_BASE_SHA_MISMATCH")

    _require(task045.get("task") == "TASK_045_F01_BOUNDED_EXISTING_CUSTODY_READONLY_REVIEW", "TASK046_TASK045_ID_MISMATCH")
    _require(task045.get("result") == TASK045_RESULT, "TASK046_TASK045_RESULT_MISMATCH")
    _require((task045.get("promotion") or {}).get("ppa_review_row_resolved") is True, "TASK046_TASK045_PPA_ROW_NOT_RESOLVED")
    _require((task045.get("promotion") or {}).get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK046_TASK045_EITI_STATUS_MISMATCH")

    _require(task042.get("task") == "TASK_042_F01_PPA_LDO_SCOPED_SILVER_CREATE_ONLY_READBACK", "TASK046_TASK042_ID_MISMATCH")
    _require(task042.get("result") == "PASS_TASK042_PPA_LDO_SCOPED_SILVER_CREATE_ONLY_READBACK_VERIFIED", "TASK046_TASK042_RESULT_MISMATCH")
    _require((task042.get("ppa") or {}).get("sha256") == V1_SHA256, "TASK046_V1_PERSISTED_SHA_MISMATCH")
    _require(((task042.get("ppa") or {}).get("readback") or {}).get("verified") is True, "TASK046_V1_READBACK_NOT_VERIFIED")

    candidate = evidence.get("candidate") or {}
    _require(candidate.get("contract") == "F01_PPA_JOM_2026_2029_SCOPED_VALIDATED_PROGRAM_2001_SILVER_V2", "TASK046_CONTRACT_MISMATCH")
    _require(candidate.get("scope") == "SCOPED_PROGRAM_2001_AND_SELECTED_ACTIONS_V2_NOT_COMPLETE_PPA_PARSE", "TASK046_SCOPE_MISMATCH")
    source = candidate.get("source") or {}
    _require(source.get("drive_file_id") == "1ez1B_mJ428IxTIUht1AHM9-I5SCotKXj", "TASK046_SOURCE_ID_MISMATCH")
    _require(source.get("sha256") == "cb65f29c772eb7133c902e827884a4ed19d8c09f64586b8de9d6483023d9133a", "TASK046_SOURCE_SHA_MISMATCH")

    p = candidate.get("program_2001") or {}
    actions = p.get("selected_actions") or []
    _require(len(actions) == 4, "TASK046_ACTION_COUNT_MISMATCH")
    by_key = {(a.get("action_code"), a.get("education_level")): a for a in actions}
    em = by_key.get(("2690", "ENSINO MEDIO E SUPERIOR")) or {}
    _require((em.get("function"), em.get("subfunction")) == ("12", "362"), "TASK046_EM_FUNCTION_MISMATCH")
    _require([em.get("2026"), em.get("2027"), em.get("2028"), em.get("2029"), em.get("total")] == [16020,15520,15521,15522,62583], "TASK046_EM_VALUES_MISMATCH")
    _require(em.get("physical_metas") == {"2026":180,"2027":190,"2028":200,"2029":210}, "TASK046_EM_METAS_MISMATCH")
    _require(em.get("validation") == "DIRECT_PRIMARY_JOM_VISUAL_SOURCE_VERIFICATION_TASK045", "TASK046_EM_VALIDATION_MISMATCH")
    _require(em.get("eiti_specific") is False, "TASK046_EM_EITI_SCOPE_WEAKENED")

    al = by_key.get(("2720", "MULTIETAPA")) or {}
    _require([al.get("2026"), al.get("2027"), al.get("2028"), al.get("2029"), al.get("total")] == [28000,29120,30430,32256,119806], "TASK046_2720_VALUES_MISMATCH")
    _require(al.get("eiti_specific") is False, "TASK046_2720_EITI_SCOPE_WEAKENED")

    resolved = p.get("resolved_review_rows") or []
    _require(len(resolved) == 1, "TASK046_RESOLUTION_HISTORY_COUNT_MISMATCH")
    _require(resolved[0].get("prior_status") == "PARSER_REVIEW_REQUIRED", "TASK046_RESOLUTION_PRIOR_STATUS_MISMATCH")
    _require(resolved[0].get("resolution_task") == "TASK_045_F01_BOUNDED_EXISTING_CUSTODY_READONLY_REVIEW", "TASK046_RESOLUTION_TASK_MISMATCH")
    _require(p.get("excluded_review_rows") == [], "TASK046_OLD_EXCLUDED_ROW_NOT_CLEARED")

    provenance = candidate.get("provenance") or {}
    _require(provenance.get("supersedes_silver_v1_candidate_sha256") == V1_SHA256, "TASK046_V1_PROVENANCE_MISMATCH")
    _require(provenance.get("task045_result") == TASK045_RESULT, "TASK046_TASK045_PROVENANCE_MISMATCH")

    guard = candidate.get("guardrails") or {}
    for key in ("complete_ppa_parse_claim", "silent_cross_source_substitution", "llm_numeric_reconstruction", "program_2001_total_attribution_to_eiti", "compliance_conclusion", "gold_authorized"):
        _require(guard.get(key) is False, f"TASK046_GUARDRAIL_{key.upper()}_WEAKENED")
    _require(guard.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK046_EITI_IDENTITY_WEAKENED")

    _require(canonical_sha256(candidate) == V2_SHA256, "TASK046_CANONICAL_HASH_MISMATCH")
    _require(evidence.get("candidate_sha256") == V2_SHA256, "TASK046_CANDIDATE_PIN_MISMATCH")
    target = evidence.get("target") or {}
    _require(target.get("folder_id") == "1_wl3Y90-RYKSBXUg53My5K6lxCUnIBNo", "TASK046_TARGET_FOLDER_MISMATCH")
    _require(target.get("file_name") == TARGET_NAME, "TASK046_TARGET_NAME_MISMATCH")
    _require(target.get("create_only") is True and target.get("overwrite") is False, "TASK046_CREATE_ONLY_POLICY_MISMATCH")

    readiness = evidence.get("readiness") or {}
    _require(readiness.get("decision") == "READY_FOR_SCOPED_SILVER_V2_CREATE_ONLY_SEPARATE_AUTH_REQUIRED", "TASK046_READINESS_MISMATCH")
    _require(readiness.get("remote_write_authorized") is False, "TASK046_REMOTE_WRITE_PREAUTHORIZED")
    _require(readiness.get("v1_preserved") is True, "TASK046_V1_PRESERVATION_LOST")

    effects = evidence.get("effects") or {}
    expected_effects = {"source_network":0,"drive_read":0,"drive_write":0,"ocr":0,"bronze":0,"silver":0,"gold":0,"serving":0,"publication":0}
    _require(effects == expected_effects, "TASK046_EFFECTS_MISMATCH")
    promo = evidence.get("promotion") or {}
    _require(promo.get("silver_v2") is False, "TASK046_SILVER_V2_PROMOTION_FORBIDDEN")
    _require(promo.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK046_F01_STATUS_MISMATCH")
    _require(promo.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK046_PROMOTION_EITI_STATUS_MISMATCH")
    for key in ("gold", "serving", "publication"):
        _require(promo.get(key) is False, f"TASK046_{key.upper()}_PROMOTION_FORBIDDEN")

    _require(evidence.get("result") == "PASS_TASK046_PPA_SCOPED_SILVER_V2_CANDIDATE_READY_NO_WRITE", "TASK046_RESULT_MISMATCH")
    return {
        "status": "PASS_TASK046_PPA_SCOPED_SILVER_V2_CANDIDATE_REVIEW",
        "candidate_sha256": V2_SHA256,
        "target_name": TARGET_NAME,
        "remote_write_authorized": False,
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
    }
