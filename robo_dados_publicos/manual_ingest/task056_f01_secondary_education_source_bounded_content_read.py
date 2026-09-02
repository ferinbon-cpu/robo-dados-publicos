"""Fail-closed validation for TASK 056 MAVS bounded content read."""
from __future__ import annotations

from typing import Any

TASK = "TASK_056_F01_SECONDARY_EDUCATION_SOURCE_BOUNDED_CONTENT_READ"
MODE = "T1_EXISTING_CUSTODY_SINGLE_SOURCE_CONTENT_READ_WITH_ONTOLOGY"
BASE_SHA = "b8a3b373b31740efeab22deeacccb10e8b331520"
SELECTED_ID = "17Fl8opb1pkqdFa485-bkQR3j6LnApnE-"
UPSTREAM_RESULT = "PASS_TASK055A_EITI_TERMINOLOGY_ONTOLOGY_READY_TASK056_REQUIRES_ONTOLOGY"
RESULT = "PASS_TASK056_MAVS_FOMENTO_ETI_REPORTING_IDENTITY_PARTIAL_NO_TRANSACTION_LINKAGE_NO_PROMOTION"


class Task056Error(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise Task056Error(code)


def validate_task056_evidence(evidence: dict[str, Any], task055a: dict[str, Any]) -> dict[str, Any]:
    _require(evidence.get("task") == TASK, "TASK056_TASK_MISMATCH")
    _require(evidence.get("mode") == MODE, "TASK056_MODE_MISMATCH")
    _require(evidence.get("base_sha") == BASE_SHA, "TASK056_BASE_SHA_MISMATCH")

    _require(task055a.get("task") == "TASK_055A_F01_EITI_TERMINOLOGY_ONTOLOGY", "TASK056_UPSTREAM_TASK_MISMATCH")
    _require(task055a.get("result") == UPSTREAM_RESULT, "TASK056_UPSTREAM_RESULT_MISMATCH")
    upstream_contract = task055a.get("future_task056_contract") or {}
    _require(upstream_contract.get("selected_drive_file_id") == SELECTED_ID, "TASK056_UPSTREAM_SOURCE_MISMATCH")
    _require(upstream_contract.get("ontology_required") is True, "TASK056_ONTOLOGY_REQUIREMENT_WEAKENED")
    _require(upstream_contract.get("search_all_five_term_families") is True, "TASK056_FIVE_FAMILY_REQUIREMENT_WEAKENED")

    auth = evidence.get("authorization") or {}
    _require(auth.get("owner_authorized") is True, "TASK056_OWNER_AUTH_MISSING")
    _require(auth.get("owner_message") == "Prossiga", "TASK056_OWNER_MESSAGE_MISMATCH")
    _require(auth.get("authorization_consumed") is True, "TASK056_AUTH_NOT_CONSUMED")
    _require(auth.get("future_blanket_authorizations_accepted") is False, "TASK056_BLANKET_AUTH_FORBIDDEN")

    contract = evidence.get("read_contract") or {}
    _require(contract.get("max_source_content_reads") == 1, "TASK056_READ_BOUND_MISMATCH")
    _require(contract.get("allowed_drive_file_ids") == [SELECTED_ID], "TASK056_ALLOWED_SOURCE_SET_MISMATCH")
    _require(contract.get("search_all_five_ontology_families") is True, "TASK056_ONTOLOGY_SCAN_MISSING")
    for key in ("public_source_network_allowed", "drive_write_allowed", "ocr_allowed", "promotion_allowed"):
        _require(contract.get(key) is False, f"TASK056_POLICY_{key.upper()}_WEAKENED")

    source = evidence.get("observed_source") or {}
    _require(source.get("drive_file_id") == SELECTED_ID, "TASK056_OBSERVED_SOURCE_MISMATCH")
    _require(source.get("funding_family") == "FUNDEB", "TASK056_FUNDING_FAMILY_MISMATCH")
    _require(source.get("period") == "1º Bimestre/2026", "TASK056_PERIOD_MISMATCH")
    _require(source.get("execution_column_marker") == "DESPESA LIQUIDADA/EMPENHADA", "TASK056_EXECUTION_MARKER_MISMATCH")

    scan = evidence.get("ontology_scan") or {}
    expected_families = {
        "A_CANONICAL_POLICY_IDENTIFIERS",
        "B_LOCAL_PLANNING_AND_NORMATIVE_ALIASES",
        "C_OPERATIONAL_OFFER_AND_JOURNEY_SIGNALS",
        "D_FINANCING_AND_INDUCTION_SIGNALS",
        "E_ACCOUNTING_AND_PLANNING_LINKAGE_KEYS",
    }
    _require(expected_families.issubset(scan.keys()), "TASK056_ONTOLOGY_FAMILY_MISSING")
    new_alias = scan.get("new_alias_discovered") or {}
    _require(new_alias.get("term") == "FOMENTO ETI", "TASK056_FOMENTO_ETI_ALIAS_MISSING")
    _require(new_alias.get("classification") == "STRONG_POLICY_FINANCE_REPORTING_ALIAS", "TASK056_ALIAS_CLASSIFICATION_MISMATCH")
    _require(new_alias.get("must_be_added_to_future_matching") is True, "TASK056_ALIAS_NOT_PROPAGATED")

    findings = evidence.get("fomento_eti_reporting_findings") or {}
    _require(findings.get("dedicated_reporting_bucket_found") is True, "TASK056_DEDICATED_BUCKET_NOT_FOUND")
    _require(findings.get("line_10_1_applied_amount_brl") == 0.0, "TASK056_LINE_10_1_AMOUNT_MISMATCH")
    _require(findings.get("line_15_1_required_amount_brl") == 1315673.39, "TASK056_REQUIRED_AMOUNT_MISMATCH")
    _require(findings.get("line_15_2_applied_after_deductions_brl") == 0.0, "TASK056_APPLIED_AMOUNT_MISMATCH")
    _require(findings.get("dedicated_policy_finance_reporting_identity_proven") is True, "TASK056_REPORTING_IDENTITY_NOT_PROVEN")
    _require(findings.get("transaction_level_eiti_financial_identity_proven") is False, "TASK056_TRANSACTION_IDENTITY_FALSE_POSITIVE")

    interpretation = evidence.get("interpretation") or {}
    _require(interpretation.get("zero_value_must_not_be_generalized_beyond_fundeb_fomento_eti_bucket_and_period") is True, "TASK056_ZERO_VALUE_OVERCLAIM")
    _require(interpretation.get("reporting_identity_is_not_transaction_identity") is True, "TASK056_REPORTING_TRANSACTION_CONFLATION")

    effects = evidence.get("effects") or {}
    _require(effects.get("source_content_reads") == 1, "TASK056_SOURCE_READ_COUNT_MISMATCH")
    _require(effects.get("other_source_content_reads") == 0, "TASK056_OTHER_SOURCE_READ_OCCURRED")
    for key in ("public_source_network", "drive_write", "ocr", "bronze", "silver", "gold", "serving", "publication"):
        _require(effects.get(key) == 0, f"TASK056_EFFECT_{key.upper()}_NONZERO")

    promotion = evidence.get("promotion") or {}
    _require(promotion.get("eiti_financial_reporting_identity") == "PARTIALLY_PROVEN_DEDICATED_FUNDEB_FOMENTO_ETI_BUCKET", "TASK056_REPORTING_STATUS_MISMATCH")
    _require(promotion.get("eiti_transaction_level_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK056_TRANSACTION_STATUS_MISMATCH")
    _require(promotion.get("eiti_financial_identity") == "EVIDENCIA_INSUFICIENTE", "TASK056_OVERALL_EITI_STATUS_MISMATCH")
    _require(promotion.get("f01_status") == "SILVER_SCOPED_PARTIAL_VALIDATED", "TASK056_F01_STATUS_MISMATCH")
    _require(promotion.get("gold") is False and promotion.get("serving") is False and promotion.get("publication") is False, "TASK056_DOWNSTREAM_PROMOTION_ENABLED")

    next_gate = evidence.get("next_bounded_gate") or {}
    _require(next_gate.get("name") == "TASK_057_F01_FUNDEB_FOMENTO_ETI_LINKAGE_CANDIDATE_SELECTION", "TASK056_NEXT_GATE_MISMATCH")
    _require(next_gate.get("metadata_only") is True, "TASK056_NEXT_GATE_NOT_METADATA_ONLY")
    _require(next_gate.get("no_source_content_read") is True, "TASK056_NEXT_GATE_CONTENT_READ_ENABLED")
    _require(next_gate.get("future_content_read_requires_fresh_owner_authorization") is True, "TASK056_FUTURE_AUTH_REQUIREMENT_WEAKENED")

    _require(evidence.get("result") == RESULT, "TASK056_RESULT_MISMATCH")

    return {
        "status": RESULT,
        "reporting_identity": promotion["eiti_financial_reporting_identity"],
        "transaction_identity": promotion["eiti_transaction_level_financial_identity"],
        "next_gate": next_gate["name"],
    }
