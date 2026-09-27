"""Fail-closed review of TASK 045 bounded existing-custody F01 evidence."""
from __future__ import annotations

from typing import Any

TASK = "TASK_045_F01_BOUNDED_EXISTING_CUSTODY_READONLY_REVIEW"
MODE = "T1_EXISTING_CUSTODY_READONLY"
BASE_SHA = "8c9638859fef42527d99181f846f264a545e9af6"
PPA_FILE_ID = "1ez1B_mJ428IxTIUht1AHM9-I5SCotKXj"
PPA_SHA256 = "cb65f29c772eb7133c902e827884a4ed19d8c09f64586b8de9d6483023d9133a"
LOA_FILE_ID = "1bRpmMxacX16P1tJBvam-55OOPTYuQnIA"
LOA_SHA256 = "37ea54d85cc5428622b296881a279a17e1aeefd7574576e7a3414443bbee64c4"
PPA_PAGES = [15, 16]
LOA_PAGES = [153, 154, 155, 156, 170, 171, 172, 173, 174, 175]
RENDER_CHAIN_SHA256 = "eb24c0c0686f25b90d7b9d23fb740e7e09600392122f43dc08557e18a179ce0e"
RESULT = "STOP_TASK045_EITI_FINANCIAL_IDENTITY_CHAIN_STILL_INCOMPLETE_AFTER_BOUNDED_READONLY_REVIEW"


class Task045Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task045Error(code)


def validate_task045_evidence(evidence: dict[str, Any], task044: dict[str, Any], task043: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK045_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK045_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK045_BASE_SHA_MISMATCH")

    _require(task044.get("task") == "TASK_044_F01_NEXT_EVIDENCE_READONLY_GATE_DESIGN", "TASK045_TASK044_ID_MISMATCH")
    _require(task044.get("result") == "PASS_TASK044_NEXT_EVIDENCE_READONLY_GATE_DESIGNED_NOT_AUTHORIZED", "TASK045_TASK044_RESULT_MISMATCH")
    _require(task043.get("task") == "TASK_043_F01_BUDGET_LAWS_SCOPED_RECONCILIATION", "TASK045_TASK043_ID_MISMATCH")
    _require(task043.get("result") == "PASS_TASK043_SCOPED_BUDGET_LAW_RECONCILIATION_NO_FINANCIAL_IDENTITY_PROMOTION", "TASK045_TASK043_RESULT_MISMATCH")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "TASK045_OWNER_AUTH_MISSING")
    _require(auth.get("owner_message") == "Autorizado e prossiga", "TASK045_OWNER_MESSAGE_MISMATCH")
    _require(auth.get("authorized_against_sha") == BASE_SHA, "TASK045_AUTH_SHA_MISMATCH")
    _require(auth.get("scope") == "EXACT_TASK044_SELECTED_PAGES_EXISTING_CUSTODY_READONLY", "TASK045_AUTH_SCOPE_MISMATCH")
    _require(auth.get("authorization_consumed") is True, "TASK045_AUTH_NOT_CONSUMED")
    _require(auth.get("future_blanket_authorizations_accepted") is False, "TASK045_FUTURE_BLANKET_AUTH_FORBIDDEN")

    scope = evidence.get("scope") or {}
    _require(scope.get("ppa_pages") == PPA_PAGES, "TASK045_PPA_PAGE_SET_DRIFT")
    _require(scope.get("loa_pages") == LOA_PAGES, "TASK045_LOA_PAGE_SET_DRIFT")
    _require(scope.get("selected_pages_total") == 12, "TASK045_PAGE_BUDGET_MISMATCH")
    _require(scope.get("unique_drive_source_files") == 2, "TASK045_FILE_SCOPE_MISMATCH")

    sources = evidence.get("source_verification") or {}
    ppa = sources.get("ppa") or {}
    loa = sources.get("loa") or {}
    _require((ppa.get("file_id"), ppa.get("sha256"), ppa.get("pdf_pages"), ppa.get("hash_verified")) == (PPA_FILE_ID, PPA_SHA256, 107, True), "TASK045_PPA_SOURCE_PIN_MISMATCH")
    _require((loa.get("file_id"), loa.get("sha256"), loa.get("pdf_pages"), loa.get("hash_verified")) == (LOA_FILE_ID, LOA_SHA256, 631, True), "TASK045_LOA_SOURCE_PIN_MISMATCH")

    render = evidence.get("render_review") or {}
    _require(render.get("dpi") == 220, "TASK045_RENDER_DPI_MISMATCH")
    _require(render.get("selected_pages_rendered") == 12, "TASK045_RENDER_PAGE_COUNT_MISMATCH")
    _require(render.get("render_chain_sha256") == RENDER_CHAIN_SHA256, "TASK045_RENDER_CHAIN_MISMATCH")
    _require(render.get("ocr_used") is False, "TASK045_OCR_FORBIDDEN")

    ppa2690 = evidence.get("ppa_2690_resolution") or {}
    expected_years = {"2026": 16020, "2027": 15520, "2028": 15521, "2029": 15522, "total": 62583}
    expected_metas = {"2026": 180, "2027": 190, "2028": 200, "2029": 210}
    _require(ppa2690.get("page") == 15, "TASK045_PPA2690_PAGE_MISMATCH")
    _require(ppa2690.get("action_code") == "2690", "TASK045_PPA2690_CODE_MISMATCH")
    _require(ppa2690.get("label") == "TRANSPORTE ESCOLAR", "TASK045_PPA2690_LABEL_MISMATCH")
    _require(ppa2690.get("education_level") == "ENSINO MEDIO E SUPERIOR", "TASK045_PPA2690_LEVEL_MISMATCH")
    _require((ppa2690.get("function"), ppa2690.get("subfunction")) == ("12", "362"), "TASK045_PPA2690_FUNCTION_MISMATCH")
    _require(ppa2690.get("financial_units") == "R$ milhares medios / 2025", "TASK045_PPA2690_UNIT_MISMATCH")
    _require(ppa2690.get("year_values") == expected_years, "TASK045_PPA2690_VALUES_MISMATCH")
    _require(ppa2690.get("physical_metas") == expected_metas, "TASK045_PPA2690_METAS_MISMATCH")
    _require(ppa2690.get("prior_status") == "PARSER_REVIEW_REQUIRED", "TASK045_PPA2690_PRIOR_STATUS_MISMATCH")
    _require(ppa2690.get("review_status") == "RESOLVED_DIRECT_PRIMARY_JOM_VISUAL_SOURCE", "TASK045_PPA2690_NOT_DIRECTLY_RESOLVED")
    _require(ppa2690.get("promoted_in_task045") is False, "TASK045_PPA2690_REMOTE_PROMOTION_FORBIDDEN")

    loa_fields = evidence.get("loa_explicit_fields") or {}
    a2690 = loa_fields.get("12.362.2001.2690") or {}
    _require((a2690.get("unit_code"), a2690.get("unit_name")) == ("10.04.00", "ENSINO MEDIO E SUPERIOR"), "TASK045_LOA2690_UNIT_MISMATCH")
    _require((a2690.get("program_code"), a2690.get("function"), a2690.get("subfunction")) == ("2001", "12", "362"), "TASK045_LOA2690_KEY_MISMATCH")
    _require(a2690.get("appropriation_brl") == 6152000, "TASK045_LOA2690_APPROPRIATION_MISMATCH")
    _require(a2690.get("funding_sources") == {"01_TESOURO": 943000, "02_TRANSFERENCIAS_E_CONVENIOS_ESTADUAIS_VINCULADOS": 5209000}, "TASK045_LOA2690_SOURCE_BREAKDOWN_MISMATCH")
    _require(a2690.get("expense_nature") == "UNKNOWN_NOT_EXPLICIT_ON_SELECTED_PAGES", "TASK045_LOA2690_EXPENSE_NATURE_INFERRED")
    _require(a2690.get("execution_stage") == "NOT_APPLICABLE_TO_LOA_ENACTMENT_READ", "TASK045_LOA2690_EXECUTION_STAGE_INFERRED")

    a2720 = loa_fields.get("12.306.2001.2720") or {}
    _require((a2720.get("unit_code"), a2720.get("unit_name")) == ("10.05.00", "ALIMENTACAO ESCOLAR"), "TASK045_LOA2720_UNIT_MISMATCH")
    _require((a2720.get("program_code"), a2720.get("function"), a2720.get("subfunction")) == ("2001", "12", "306"), "TASK045_LOA2720_KEY_MISMATCH")
    _require(a2720.get("appropriation_brl") == 28000000, "TASK045_LOA2720_APPROPRIATION_MISMATCH")
    _require(a2720.get("funding_sources") == {"01_TESOURO": 8680000, "05_TRANSFERENCIAS_E_CONVENIOS_FEDERAIS_VINCULADOS": 19320000}, "TASK045_LOA2720_SOURCE_BREAKDOWN_MISMATCH")
    _require(a2720.get("expense_nature") == "UNKNOWN_NOT_EXPLICIT_ON_SELECTED_PAGES", "TASK045_LOA2720_EXPENSE_NATURE_INFERRED")
    _require(a2720.get("execution_stage") == "NOT_APPLICABLE_TO_LOA_ENACTMENT_READ", "TASK045_LOA2720_EXECUTION_STAGE_INFERRED")

    divergence = evidence.get("material_text_visual_divergence") or {}
    _require(divergence.get("observed") is True, "TASK045_REQUIRED_DIVERGENCE_NOT_RECORDED")
    _require(divergence.get("pages") == [173, 174], "TASK045_DIVERGENCE_PAGE_MISMATCH")
    _require(divergence.get("text_layer_amount_brl") == 29000000, "TASK045_DIVERGENCE_TEXT_AMOUNT_MISMATCH")
    _require(divergence.get("visual_source_amount_brl") == 28000000, "TASK045_DIVERGENCE_VISUAL_AMOUNT_MISMATCH")
    _require(divergence.get("silent_repair") is False, "TASK045_SILENT_REPAIR_FORBIDDEN")
    _require(divergence.get("automatic_promotion") is False, "TASK045_DIVERGENCE_AUTOPROMOTION_FORBIDDEN")
    _require(divergence.get("resolution") == "REVIEW_STOP_DIRECT_VISUAL_SOURCE_RECORDED", "TASK045_DIVERGENCE_POLICY_MISMATCH")

    rec = evidence.get("reconciliation") or {}
    r2690 = rec.get("2690") or {}
    _require(r2690.get("ppa_2026_brl") == 16020000, "TASK045_REC2690_PPA_AMOUNT_MISMATCH")
    _require(r2690.get("loa_2026_brl") == 6152000, "TASK045_REC2690_LOA_AMOUNT_MISMATCH")
    _require(r2690.get("delta_loa_minus_ppa_brl") == -9868000, "TASK045_REC2690_DELTA_MISMATCH")
    _require(r2690.get("exact_amount_alignment") is False, "TASK045_REC2690_FALSE_ALIGNMENT")
    _require(r2690.get("status") == "PROGRAM_ACTION_KEY_CONTINUITY_PROVEN_WITH_PPA_LOA_AMOUNT_DIVERGENCE_NO_FINANCIAL_IDENTITY", "TASK045_REC2690_STATUS_MISMATCH")
    r2720 = rec.get("2720") or {}
    _require(r2720.get("ppa_2026_brl") == 28000000 and r2720.get("loa_2026_brl") == 28000000, "TASK045_REC2720_AMOUNT_MISMATCH")
    _require(r2720.get("exact_amount_alignment") is True, "TASK045_REC2720_ALIGNMENT_LOST")
    _require(r2720.get("status") == "PROGRAM_ACTION_AND_2026_AMOUNT_ALIGNMENT_PROVEN_NO_FINANCIAL_IDENTITY", "TASK045_REC2720_STATUS_MISMATCH")

    promo = evidence.get("promotion") or {}
    _require(promo.get("ppa_review_row_resolved") is True, "TASK045_PPA_RESOLUTION_LOST")
    _require(promo.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK045_F01_STATUS_MISMATCH")
    _require(promo.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK045_EITI_IDENTITY_WEAKENED")
    for key in ("drive_write", "silver_write", "gold", "serving", "publication"):
        _require(promo.get(key) is False, f"TASK045_PROMOTION_{key.upper()}_FORBIDDEN")

    effects = evidence.get("effects") or {}
    _require(effects.get("unique_drive_source_files_read") == 2, "TASK045_EFFECT_SOURCE_FILE_COUNT_MISMATCH")
    _require(effects.get("selected_pages_read") == 12, "TASK045_EFFECT_PAGE_COUNT_MISMATCH")
    _require(effects.get("local_full_file_materializations_for_hash_and_render") == 2, "TASK045_EFFECT_MATERIALIZATION_COUNT_MISMATCH")
    for key in ("source_network", "drive_write", "ocr", "bronze", "silver_write", "gold", "serving", "publication", "retry", "pagination"):
        _require(effects.get(key) == 0, f"TASK045_EFFECT_{key.upper()}_NONZERO")

    _require(evidence.get("result") == RESULT, "TASK045_RESULT_MISMATCH")
    return {
        "status": RESULT,
        "ppa_2690_resolved": True,
        "ppa_2690_2026_brl": 16020000,
        "loa_2690_2026_brl": 6152000,
        "loa_2720_2026_brl": 28000000,
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
        "new_remote_write": False,
    }
