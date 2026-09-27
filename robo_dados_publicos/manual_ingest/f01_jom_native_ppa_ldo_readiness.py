"""Fail-closed review of JOM-native scoped Silver candidates for F01 PPA/LDO.

TASK 041 performs no source download and no layer write.  It pins the primary
Jornal Oficial custody observations, corrects the LDO page boundary, validates
only the directly reviewed PPA Program 2001 subset and LDO structural markers,
and leaves all downstream promotions disabled.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

TASK = "TASK_041_F01_JOM_NATIVE_PPA_LDO_READINESS_REVIEW"
MODE = "T0_OFFLINE_AND_EXISTING_CUSTODY_READ_ONLY_REVIEW"
BASE_SHA = "ea706547453830cf2df2ed9b1ea0e7fb3276c2ac"
PPA_CONTRACT = "F01_PPA_JOM_2026_2029_SCOPED_VALIDATED_PROGRAM_2001_SILVER_V1"
LDO_CONTRACT = "F01_LDO_JOM_2026_SCOPED_STRUCTURAL_MARKERS_SILVER_V1"
PPA_SHA256 = "cb65f29c772eb7133c902e827884a4ed19d8c09f64586b8de9d6483023d9133a"
LDO_SHA256 = "44d92a6ac948bbf43dcb3302733faac1a4ed5e592702f66c07f0c6ede4ecb73c"
PPA_CANDIDATE_SHA256 = "0cba09dade1c09224e549e817a859c63edb12a6fb0a5223c5ddb8aa5fe6dc730"
LDO_CANDIDATE_SHA256 = "4719631a3dd476efe8c760f2b9ce07eba15d678c85b56e95345af70237f02182"
LOA_SCOPED_SHA256 = "3894ede7c67e60d3e12795dec3964d78baf24ff350355d98f3825dd5f81caf4c"


class Task041Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task041Error(code)


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _validate_source(candidate: dict[str, Any], *, family: str) -> None:
    source = candidate.get("source") or {}
    if family == "PPA":
        expected = {
            "filename": "SOURCE_JOM_7119_2025-11-15_PPA_7213_2025.pdf",
            "drive_file_id": "1ez1B_mJ428IxTIUht1AHM9-I5SCotKXj",
            "sha256": PPA_SHA256,
            "bytes": 16867824,
            "total_pdf_pages": 107,
        }
    else:
        expected = {
            "filename": "SOURCE_JOM_7024_2025-07-08_LDO_7141_2025.pdf",
            "drive_file_id": "1U_E1I1Lbrq5WvedrDPygFuEfQj-ouOex",
            "sha256": LDO_SHA256,
            "bytes": 17615179,
            "total_pdf_pages": 79,
        }
    _require(source == expected, f"{family}_SOURCE_PIN_MISMATCH")


def _validate_ppa(candidate: dict[str, Any]) -> None:
    _require(candidate.get("contract") == PPA_CONTRACT, "PPA_CONTRACT_MISMATCH")
    _require(
        candidate.get("scope") == "SCOPED_PROGRAM_2001_AND_SELECTED_ACTIONS_NOT_COMPLETE_PPA_PARSE",
        "PPA_SCOPE_MISMATCH",
    )
    _validate_source(candidate, family="PPA")

    legal = candidate.get("legal_instrument") or {}
    _require(legal.get("law_number") == "7.213/2025", "PPA_LAW_MISMATCH")
    _require(legal.get("law_date") == "2025-11-12", "PPA_LAW_DATE_MISMATCH")
    _require(legal.get("period") == "2026-2029", "PPA_PERIOD_MISMATCH")
    _require(legal.get("journal_edition") == 7119, "PPA_EDITION_MISMATCH")
    _require(legal.get("publication_date") == "2025-11-15", "PPA_PUBLICATION_DATE_MISMATCH")
    _require(
        (legal.get("law_page_start"), legal.get("law_page_end"), legal.get("law_page_count")) == (5, 64, 60),
        "PPA_PRIMARY_JOM_BOUNDARY_MISMATCH",
    )

    text = candidate.get("text_layer") or {}
    _require(text.get("parser") == "pypdf" and text.get("parser_version") == "5.9.0", "PPA_PARSER_PIN_MISMATCH")
    _require(text.get("law_pages_with_native_text") == 60, "PPA_TEXT_PAGE_COUNT_MISMATCH")
    _require(text.get("law_pages_without_native_text") == 0, "PPA_TEXT_LAYER_INCOMPLETE")
    _require(text.get("table_text_extraction_complete") is False, "PPA_TABLE_EXTRACTION_OVERCLAIM")
    _require(text.get("page_text_rows_sha256") == "5114a6bac6b8d2accdf245dcea6105917e3fd90b016c80fdcc063f00cd6b3c70", "PPA_PAGE_TEXT_HASH_MISMATCH")
    _require(text.get("page_15_text_sha256") == "b6d44ee39efeed3b1acc3dccabbf56c73fb6914ef8ce15003d144c44a59e5eb4", "PPA_PAGE15_HASH_MISMATCH")
    _require(text.get("page_16_text_sha256") == "ef43c77374ee0e2159e99003ac6d49e5de7ac47611b12781f19c54bedec3e4c8", "PPA_PAGE16_HASH_MISMATCH")

    p = candidate.get("program_2001") or {}
    _require(p.get("program_code") == "2001", "PPA_PROGRAM_CODE_MISMATCH")
    _require(p.get("program_name") == "EDUCACAO QUE INCLUI E TRANSFORMA VIDAS", "PPA_PROGRAM_NAME_MISMATCH")
    _require(p.get("responsible_unit_code") == "10.00.00", "PPA_RESPONSIBLE_UNIT_MISMATCH")
    _require(p.get("responsible_unit_name") == "SECRETARIA DE EDUCACAO", "PPA_RESPONSIBLE_NAME_MISMATCH")

    indicator = p.get("indicator") or {}
    expected_indicator = {
        "name": "INDICE DE ALUNOS EM EDUCACAO INTEGRAL",
        "unit": "PERCENTUAL",
        "recent": 52,
        "2026": 53,
        "2027": 55,
        "2028": 57,
        "2029": 59,
        "final_ppa": 59,
        "source_page": 15,
        "validation": "DIRECT_PRIMARY_JOM_VISUAL_SOURCE_VERIFICATION",
    }
    _require(indicator == expected_indicator, "PPA_EITI_INDICATOR_OR_TARGET_DRIFT")

    actions = p.get("selected_actions") or []
    expected_actions = [
        (15, "2690", "TRANSPORTE ESCOLAR", "EDUCACAO INFANTIL", "12", "365", 3694, 3842, 4015, 4256, 15807),
        (15, "2690", "TRANSPORTE ESCOLAR", "ENSINO FUNDAMENTAL", "12", "361", 8720, 9069, 9477, 10046, 37312),
        (16, "2720", "ALIMENTACAO ESCOLAR", "MULTIETAPA", "12", "306", 28000, 29120, 30430, 32256, 119806),
    ]
    _require(len(actions) == 3, "PPA_SELECTED_ACTION_COUNT_MISMATCH")
    for action, expected in zip(actions, expected_actions):
        observed = (
            action.get("page"), action.get("action_code"), action.get("label"), action.get("education_level"),
            action.get("function"), action.get("subfunction"), action.get("2026"), action.get("2027"),
            action.get("2028"), action.get("2029"), action.get("total"),
        )
        _require(observed == expected, "PPA_SELECTED_ACTION_VALUE_DRIFT")
        _require(action.get("units") == "R$ milhares medios/2025", "PPA_ACTION_UNIT_MISMATCH")
        _require(action.get("validation") == "DIRECT_PRIMARY_JOM_VISUAL_SOURCE_VERIFICATION", "PPA_ACTION_VALIDATION_MISMATCH")
        _require(action.get("eiti_specific") is False, "PPA_ACTION_EITI_SCOPE_WEAKENED")

    excluded = p.get("excluded_review_rows") or []
    _require(len(excluded) == 1, "PPA_EXCLUDED_REVIEW_ROW_COUNT_MISMATCH")
    row = excluded[0]
    _require(row.get("action_code") == "2690", "PPA_EXCLUDED_ACTION_MISMATCH")
    _require(row.get("education_level") == "ENSINO MEDIO_E_SUPERIOR", "PPA_EXCLUDED_LEVEL_MISMATCH")
    _require(row.get("status") == "PARSER_REVIEW_REQUIRED" and row.get("promoted") is False, "PPA_AMBIGUOUS_ROW_PROMOTED")

    g = candidate.get("guardrails") or {}
    for key in ("complete_ppa_parse_claim", "silent_cross_source_substitution", "llm_numeric_reconstruction", "program_2001_total_attribution_to_eiti", "compliance_conclusion", "gold_authorized"):
        _require(g.get(key) is False, f"PPA_GUARDRAIL_{key.upper()}_WEAKENED")
    _require(g.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "PPA_EITI_IDENTITY_WEAKENED")


def _validate_ldo(candidate: dict[str, Any]) -> None:
    _require(candidate.get("contract") == LDO_CONTRACT, "LDO_CONTRACT_MISMATCH")
    _require(
        candidate.get("scope") == "SCOPED_LEGAL_IDENTITY_AND_STRUCTURAL_MARKERS_NOT_COMPLETE_LDO_PARSE",
        "LDO_SCOPE_MISMATCH",
    )
    _validate_source(candidate, family="LDO")

    legal = candidate.get("legal_instrument") or {}
    _require(legal.get("law_number") == "7.141/2025", "LDO_LAW_MISMATCH")
    _require(legal.get("law_date") == "2025-07-02", "LDO_LAW_DATE_MISMATCH")
    _require(legal.get("exercise") == 2026, "LDO_EXERCISE_MISMATCH")
    _require(legal.get("journal_edition") == 7024, "LDO_EDITION_MISMATCH")
    _require(legal.get("publication_date") == "2025-07-08", "LDO_PUBLICATION_DATE_MISMATCH")
    _require(
        (legal.get("law_page_start"), legal.get("law_page_end"), legal.get("law_page_count")) == (5, 38, 34),
        "LDO_PRIMARY_JOM_BOUNDARY_MISMATCH",
    )

    correction = candidate.get("boundary_correction") or {}
    _require(correction.get("supersedes_old_mapping") == "JOM_PAGES_5_41", "LDO_OLD_BOUNDARY_NOT_SUPERSEDED")
    _require(correction.get("correct_mapping") == "JOM_PAGES_5_38", "LDO_CORRECTED_BOUNDARY_MISMATCH")
    _require(correction.get("first_non_ldo_page") == 39, "LDO_FIRST_NON_LDO_PAGE_MISMATCH")
    _require(correction.get("first_non_ldo_document") == "PORTARIA 1.666/2025", "LDO_FIRST_NON_LDO_DOCUMENT_MISMATCH")
    _require(correction.get("status") == "CORRECTED_FROM_PRIMARY_JOM", "LDO_BOUNDARY_CORRECTION_STATUS_MISMATCH")

    text = candidate.get("text_layer") or {}
    _require(text.get("parser") == "pypdf" and text.get("parser_version") == "5.9.0", "LDO_PARSER_PIN_MISMATCH")
    _require(text.get("law_pages_with_native_text") == 34, "LDO_TEXT_PAGE_COUNT_MISMATCH")
    _require(text.get("law_pages_without_native_text") == 0, "LDO_TEXT_LAYER_INCOMPLETE")
    _require(text.get("page_text_rows_sha256") == "2f6cae56bc282df75f8decacece8dfac0eaeb4c79a347257ed29fd032d782939", "LDO_PAGE_TEXT_HASH_MISMATCH")

    markers = candidate.get("structural_markers") or []
    expected_markers = [
        ("METAS_FISCAIS", 5), ("RISCOS_FISCAIS", 6), ("RESERVA_CONTINGENCIA", 7),
        ("EDUCACAO", 8), ("PESSOAL", 9),
    ]
    _require(len(markers) == len(expected_markers), "LDO_MARKER_COUNT_MISMATCH")
    for marker, (key, page) in zip(markers, expected_markers):
        _require(marker.get("section_key") == key, "LDO_MARKER_ORDER_OR_KEY_MISMATCH")
        _require(marker.get("found") is True, "LDO_REQUIRED_MARKER_MISSING")
        _require(marker.get("first_jom_page") == page, "LDO_MARKER_PAGE_MISMATCH")

    g = candidate.get("guardrails") or {}
    for key in ("complete_ldo_parse_claim", "fiscal_compliance_conclusion", "mde_fundeb_compliance_conclusion", "gold_authorized"):
        _require(g.get(key) is False, f"LDO_GUARDRAIL_{key.upper()}_WEAKENED")
    _require(g.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "LDO_EITI_IDENTITY_WEAKENED")


def validate_evidence(evidence: dict[str, Any], task040: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "BASE_SHA_MISMATCH")

    source_policy = evidence.get("source_policy") or {}
    _require(source_policy.get("primary_source") == "JORNAL_OFICIAL_LIMEIRA_FULL_EDITION_PDF", "PRIMARY_SOURCE_POLICY_MISMATCH")
    _require(source_policy.get("standalone_copy_role") == "OFFICIAL_COMPLEMENTARY_COPY", "STANDALONE_COPY_ROLE_MISMATCH")
    _require(source_policy.get("silent_cross_source_substitution") is False, "SILENT_CROSS_SOURCE_SUBSTITUTION_FORBIDDEN")

    ppa = evidence.get("ppa_candidate") or {}
    ldo = evidence.get("ldo_candidate") or {}
    _validate_ppa(ppa)
    _validate_ldo(ldo)
    _require(canonical_sha256(ppa) == PPA_CANDIDATE_SHA256, "PPA_CANDIDATE_CANONICAL_HASH_MISMATCH")
    _require(evidence.get("ppa_candidate_sha256") == PPA_CANDIDATE_SHA256, "PPA_CANDIDATE_PIN_MISMATCH")
    _require(canonical_sha256(ldo) == LDO_CANDIDATE_SHA256, "LDO_CANDIDATE_CANONICAL_HASH_MISMATCH")
    _require(evidence.get("ldo_candidate_sha256") == LDO_CANDIDATE_SHA256, "LDO_CANDIDATE_PIN_MISMATCH")

    _require(task040.get("task") == "TASK_040_LOA_SCOPED_SILVER_CREATE_ONLY_READBACK", "TASK040_ID_MISMATCH")
    _require(task040.get("result") == "PASS_TASK040_SCOPED_SILVER_CREATE_ONLY_READBACK_VERIFIED", "TASK040_RESULT_MISMATCH")
    _require((task040.get("candidate") or {}).get("sha256") == LOA_SCOPED_SHA256, "TASK040_LOA_SHA_MISMATCH")
    _require((task040.get("readback") or {}).get("verified") is True, "TASK040_READBACK_NOT_VERIFIED")
    _require((task040.get("promotion") or {}).get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK040_F01_STATUS_MISMATCH")

    effects = evidence.get("observed_effects") or {}
    _require(effects.get("drive_reads") == 2, "TASK041_DRIVE_READ_COUNT_MISMATCH")
    for key in ("drive_writes", "source_network", "ocr", "bronze", "silver", "gold", "serving", "publication"):
        _require(effects.get(key) == 0, f"TASK041_EFFECT_{key.upper()}_NONZERO")

    readiness = evidence.get("readiness") or {}
    expected_ready = "READY_FOR_SCOPED_SILVER_CREATE_ONLY_SEPARATE_AUTH_REQUIRED"
    _require(readiness.get("ppa") == expected_ready, "PPA_READINESS_MISMATCH")
    _require(readiness.get("ldo") == expected_ready, "LDO_READINESS_MISMATCH")
    _require(readiness.get("loa") == "SILVER_SCOPED_PARTIAL_VALIDATED", "LOA_READINESS_MISMATCH")

    promotion = evidence.get("promotion") or {}
    _require(promotion.get("ppa_silver") is False and promotion.get("ldo_silver") is False, "TASK041_NEW_SILVER_PROMOTION_FORBIDDEN")
    _require(promotion.get("loa_silver_existing") is True, "TASK041_EXISTING_LOA_SILVER_LOST")
    for key in ("gold", "serving", "publication"):
        _require(promotion.get(key) is False, f"TASK041_{key.upper()}_PROMOTION_FORBIDDEN")

    _require(
        evidence.get("result") == "PASS_TASK041_JOM_NATIVE_PPA_LDO_SCOPED_SILVER_CANDIDATES_READY_NO_WRITE",
        "RESULT_MISMATCH",
    )
    return {
        "status": "PASS_TASK041_JOM_NATIVE_PPA_LDO_SCOPED_SILVER_CANDIDATES_READY_NO_WRITE",
        "ppa_candidate_sha256": PPA_CANDIDATE_SHA256,
        "ldo_candidate_sha256": LDO_CANDIDATE_SHA256,
        "ldo_boundary": "JOM_PAGES_5_38",
        "ppa_boundary": "JOM_PAGES_5_64",
        "loa_status": "SILVER_SCOPED_PARTIAL_VALIDATED",
        "new_remote_write": False,
    }
