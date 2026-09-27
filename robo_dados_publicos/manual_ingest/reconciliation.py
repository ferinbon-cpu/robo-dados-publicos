from __future__ import annotations

from pathlib import Path
import json


class F01ReconciliationStop(ValueError):
    """Fail-closed stop for supervised F01 staging reconciliation."""


def load_reconciliation_contract(path: str | Path) -> dict:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("mode") != "T0_OFFLINE_RECONCILIATION":
        raise F01ReconciliationStop("STOP_F01_RECONCILIATION_BAD_MODE")
    if raw.get("source_task") != "TASK_025_MANUAL_SUPERVISED_INGEST_F01":
        raise F01ReconciliationStop("STOP_F01_RECONCILIATION_BAD_SOURCE_TASK")
    return raw


def _stop(code: str, detail: object | None = None) -> None:
    if detail is None:
        raise F01ReconciliationStop(code)
    raise F01ReconciliationStop(f"{code}: {json.dumps(detail, ensure_ascii=False, sort_keys=True)}")


def reconcile_f01_bundle(contract: dict, bundle: dict) -> dict:
    staging = bundle.get("staging") or {}
    qa = bundle.get("qa") or {}
    hashes = bundle.get("derived_hashes") or {}

    if staging.get("promotion_status") != contract.get("allowed_promotion_status"):
        _stop("STOP_F01_UNAUTHORIZED_PROMOTION", staging.get("promotion_status"))

    required_sources = contract.get("required_source_facts", {})
    sources = staging.get("sources", {})
    for family in ("PPA", "LDO", "LOA"):
        expected = required_sources.get(family) or {}
        observed = sources.get(family) or {}
        if observed.get("sha256") != expected.get("sha256"):
            _stop("STOP_F01_SOURCE_HASH_DRIFT", {"family": family})
        if int(observed.get("page_count", -1)) != int(expected.get("pages", -2)):
            _stop("STOP_F01_SOURCE_PAGE_DRIFT", {"family": family})

    expected_hashes = contract.get("expected_derived_hashes", {})
    if hashes != expected_hashes:
        missing = sorted(set(expected_hashes) - set(hashes))
        extra = sorted(set(hashes) - set(expected_hashes))
        mismatched = sorted(
            name for name in set(expected_hashes) & set(hashes)
            if hashes.get(name) != expected_hashes.get(name)
        )
        _stop(
            "STOP_F01_DERIVED_HASH_CLOSURE_MISMATCH",
            {"missing": missing, "extra": extra, "mismatched": mismatched},
        )

    ppa = staging.get("ppa", {})
    indicator = ppa.get("indicator_eiti", {})
    observed_targets = [
        indicator.get("recent"),
        indicator.get("2026"),
        indicator.get("2027"),
        indicator.get("2028"),
        indicator.get("2029"),
        indicator.get("final_ppa"),
    ]
    if observed_targets != contract.get("required_ppa_targets"):
        _stop("STOP_F01_PPA_TARGET_DRIFT", observed_targets)
    if ppa.get("program_code") != "2001" or ppa.get("responsible_unit_code") != "10.00.00":
        _stop("STOP_F01_PPA_IDENTITY_DRIFT")
    actions = ppa.get("selected_actions") or []
    if not actions or any(row.get("eiti_specific") is not False for row in actions):
        _stop("STOP_F01_PPA_ACTION_FALSE_EITI_PROMOTION")
    if any(row.get("parse_status") != "VERIFIED_TEXT_ROW" for row in actions):
        _stop("STOP_F01_PPA_ACTION_NOT_VERIFIED")
    review_rows = ppa.get("review_required_rows") or []
    if not review_rows or any(row.get("promoted") is not False for row in review_rows):
        _stop("STOP_F01_REVIEW_ROW_PROMOTED")

    required_markers = set(contract.get("required_ldo_markers", []))
    marker_rows = staging.get("ldo", {}).get("structural_markers") or []
    observed_markers = {row.get("section_key") for row in marker_rows if row.get("found") is True}
    if observed_markers != required_markers:
        _stop(
            "STOP_F01_LDO_MARKER_DRIFT",
            {"expected": sorted(required_markers), "observed": sorted(observed_markers)},
        )

    loa = staging.get("loa", {})
    loa_header = loa.get("header", {})
    boundary = contract.get("loa_boundary", {})
    if loa_header.get("current_pdf_text_layer") != boundary.get("current_pdf_text_layer"):
        _stop("STOP_F01_LOA_TEXT_LAYER_DRIFT")
    parse_status = str(loa_header.get("full_structured_parse_status", ""))
    if not parse_status.startswith(str(boundary.get("full_structured_parse_status_prefix", "BLOCKED_"))):
        _stop("STOP_F01_LOA_FULL_PARSE_NOT_BLOCKED")
    if loa.get("program_bridge_from_v10", {}).get("financial_attribution_to_eiti") != "NOT_VALIDATED":
        _stop("STOP_F01_LOA_BRIDGE_PROMOTED_TO_FINANCIAL_IDENTITY")
    prior = loa.get("prior_action_evidence") or []
    if not prior:
        _stop("STOP_F01_LOA_PRIOR_EVIDENCE_MISSING")
    for row in prior:
        if row.get("current_raw_reparse") != boundary.get("prior_bridge_current_raw_reparse"):
            _stop("STOP_F01_LOA_PRIOR_REPARSE_STATE_DRIFT")
        if row.get("status") != boundary.get("prior_bridge_status"):
            _stop("STOP_F01_LOA_PRIOR_EVIDENCE_STATUS_DRIFT")
        if row.get("eiti_specific") is not False:
            _stop("STOP_F01_LOA_PRIOR_EVIDENCE_FALSE_EITI_PROMOTION")

    financial = staging.get("financial_identity", {})
    if financial.get("eiti_specific_status") != contract.get("required_financial_identity_status"):
        _stop("STOP_F01_FINANCIAL_IDENTITY_PROMOTED")
    if financial.get("program_2001_total_attribution_forbidden") is not True:
        _stop("STOP_F01_PROGRAM_TOTAL_GUARDRAIL_MISSING")

    checks = qa.get("checks") or []
    if qa.get("pass_count") != 10 or qa.get("fail_count") != 0:
        _stop("STOP_F01_QA_COUNTS")
    if qa.get("result") != "PASS_STAGING_ONLY":
        _stop("STOP_F01_QA_RESULT")
    if qa.get("promotion_decision") != "DO_NOT_PROMOTE_LOA_FULL_PARSE_INCOMPLETE":
        _stop("STOP_F01_QA_PROMOTION_DECISION")
    if len(checks) != 10 or any(row.get("result") != "PASS" for row in checks):
        _stop("STOP_F01_QA_CHECK_FAILURE")

    return {
        "status": "PASS_F01_STAGING_RECONCILED_OFFLINE",
        "batch": contract.get("batch"),
        "source_count": 3,
        "derived_hash_count": len(hashes),
        "ppa_targets": observed_targets,
        "ldo_markers": sorted(observed_markers),
        "loa_full_parse": "BLOCKED",
        "financial_identity": contract.get("required_financial_identity_status"),
        "promotion": "BLOCKED_NOT_SILVER",
    }
