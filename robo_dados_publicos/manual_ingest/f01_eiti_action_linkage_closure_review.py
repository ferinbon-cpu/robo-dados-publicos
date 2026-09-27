"""Fail-closed offline review of explicit EITI action linkage in PPA Program 2001."""
from __future__ import annotations

import re
import unicodedata
from typing import Any

TASK = "TASK_049_F01_EITI_ACTION_LINKAGE_CLOSURE_REVIEW"
MODE = "T0_OFFLINE_LINKAGE_CLOSURE_REVIEW"
BASE_SHA = "b4d7d9bc1a4ded4d60fcf8e70bdf19c66c82559e"
PPA_SHA = "cb65f29c772eb7133c902e827884a4ed19d8c09f64586b8de9d6483023d9133a"
PPA15_IMAGE_SHA = "5875d51e0acf2b2e9750f75f441ccbbde22c4f35e1d0c1d5594ba39a16b68ab1"
PPA16_IMAGE_SHA = "456f5ca66ea75216616099634c053cbb31a2e57a192ae5ed5cece4368f6e4932"
EXPECTED_ACTION_ROWS = 27


class Task049Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task049Error(code)


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", value.upper()).strip()


def _has_explicit_eiti_term(label: str) -> bool:
    normalized = _norm(label)
    if "EDUCACAO INTEGRAL" in normalized or "TEMPO INTEGRAL" in normalized:
        return True
    words = set(re.findall(r"[A-Z0-9]+", normalized))
    return bool(words & {"EITI", "ETI", "INTEGRAL"})


def validate_task049_evidence(evidence: dict[str, Any], task045: dict[str, Any], task048: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK049_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK049_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK049_BASE_SHA_MISMATCH")

    _require(task045.get("task") == "TASK_045_F01_BOUNDED_EXISTING_CUSTODY_READONLY_REVIEW", "TASK049_TASK045_ID_MISMATCH")
    _require((task045.get("source_verification") or {}).get("ppa", {}).get("sha256") == PPA_SHA, "TASK049_PPA_HASH_MISMATCH")
    render = task045.get("render_review") or {}
    page_hashes = render.get("page_image_sha256") or {}
    _require(page_hashes.get("PPA_15") == PPA15_IMAGE_SHA, "TASK049_PPA15_RENDER_HASH_MISMATCH")
    _require(page_hashes.get("PPA_16") == PPA16_IMAGE_SHA, "TASK049_PPA16_RENDER_HASH_MISMATCH")
    _require(render.get("ocr_used") is False, "TASK049_OCR_NOT_ALLOWED")

    _require(task048.get("task") == "TASK_048_F01_LOA_SCOPED_SILVER_V2_CANDIDATE_REVIEW", "TASK049_TASK048_ID_MISMATCH")
    _require((task048.get("promotion") or {}).get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK049_TASK048_EITI_STATUS_MISMATCH")

    scope = evidence.get("scope") or {}
    _require(scope.get("journal_edition") == 7119, "TASK049_EDITION_MISMATCH")
    _require(scope.get("program_code") == "2001", "TASK049_PROGRAM_MISMATCH")
    _require(scope.get("pages") == [15, 16], "TASK049_PAGE_SCOPE_MISMATCH")
    _require(scope.get("claim_boundary") == "PROGRAM_2001_ACTION_LABELS_ONLY_NOT_ALL_MUNICIPAL_DOCUMENTS", "TASK049_CLAIM_BOUNDARY_WEAKENED")

    explicit = evidence.get("explicit_program_signals") or {}
    _require(explicit.get("objective_mentions_educacao_integral") is True, "TASK049_OBJECTIVE_SIGNAL_MISSING")
    _require(explicit.get("indicator_name") == "INDICE DE ALUNOS EM EDUCACAO INTEGRAL", "TASK049_INDICATOR_SIGNAL_MISSING")

    rows = evidence.get("action_rows") or []
    _require(len(rows) == EXPECTED_ACTION_ROWS, "TASK049_ACTION_ROW_COUNT_MISMATCH")
    for row in rows:
        _require(bool(row.get("action_code")) and bool(row.get("label")), "TASK049_ACTION_ROW_INCOMPLETE")
    matches = [row for row in rows if _has_explicit_eiti_term(str(row["label"]))]
    _require(matches == [], "TASK049_EXPLICIT_EITI_ACTION_LABEL_FOUND")
    _require(evidence.get("explicit_eiti_action_label_matches") == [], "TASK049_DECLARED_MATCHES_MISMATCH")

    conclusion = evidence.get("conclusion") or {}
    _require(conclusion.get("indicator_to_program_linkage") == "PROVEN", "TASK049_INDICATOR_PROGRAM_STATUS_MISMATCH")
    _require(conclusion.get("program_to_explicit_eiti_action_linkage") == "NOT_PROVEN", "TASK049_ACTION_LINKAGE_OVERCLAIM")
    _require(conclusion.get("program_or_generic_action_financial_attribution_to_eiti") == "FORBIDDEN", "TASK049_ATTRIBUTION_GUARDRAIL_WEAKENED")
    _require(conclusion.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK049_EITI_STATUS_MISMATCH")
    _require(conclusion.get("f01_action_label_search_status") == "CLOSED_NO_EXPLICIT_EITI_ACTION_LABEL_IN_PROGRAM_2001_TABLE", "TASK049_CLOSURE_STATUS_MISMATCH")

    next_evidence = evidence.get("next_evidence_boundary") or {}
    _require(next_evidence.get("do_not_expand_ppa_action_label_search") is True, "TASK049_PPA_SEARCH_NOT_CLOSED")
    _require(next_evidence.get("requires_more_granular_execution_or_accounting_source_if_pursued") is True, "TASK049_NEXT_SOURCE_BOUNDARY_MISSING")
    _require(next_evidence.get("automatic_next_live_read_authorized") is False, "TASK049_FUTURE_LIVE_READ_PREAUTHORIZED")

    expected_effects = {"source_network":0,"drive_read":0,"drive_write":0,"ocr":0,"bronze":0,"silver":0,"gold":0,"serving":0,"publication":0}
    _require((evidence.get("effects") or {}) == expected_effects, "TASK049_EFFECTS_MISMATCH")
    _require(evidence.get("result") == "PASS_TASK049_EITI_ACTION_LINKAGE_CLOSURE_NO_EXPLICIT_ACTION_LABEL", "TASK049_RESULT_MISMATCH")

    return {
        "status": "PASS_TASK049_EITI_ACTION_LINKAGE_CLOSURE_REVIEW",
        "action_rows_reviewed": EXPECTED_ACTION_ROWS,
        "explicit_eiti_action_label_matches": 0,
        "program_to_explicit_eiti_action_linkage": "NOT_PROVEN",
        "eiti_financial_identity": "EVIDENCIA_INSUFICIENTE",
        "gold_authorized": False,
    }
