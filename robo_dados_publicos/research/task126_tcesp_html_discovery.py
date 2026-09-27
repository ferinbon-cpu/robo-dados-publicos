from __future__ import annotations
import json
from pathlib import Path
from typing import Any

class Task126Stop(RuntimeError):
    pass

def _r(condition: bool, code: str) -> None:
    if not condition:
        raise Task126Stop(code)

def validate_task126_contract(data: dict[str, Any]) -> dict[str, Any]:
    _r(data.get("schema") == "TASK126_TCESP_HTML_INDEX_DISCOVERY_V1", "TASK126_SCHEMA")
    _r(data.get("mode") == "T1_BOUNDED_WEB_INDEX_DISCOVERY", "TASK126_MODE")
    _r(data.get("scope_authority") == "ISSUE_449_PROSPECTIVE_BOUNDARY", "TASK126_SCOPE")
    _r(data.get("preflight_ci_before_search") is False, "TASK126_PREFLIGHT_HISTORY")
    source=data.get("source") or {}
    _r(source.get("host") == "transparencia.tce.sp.gov.br", "TASK126_HOST")
    _r(source.get("municipality") == "Limeira" and source.get("fiscal_year") == 2026, "TASK126_SCOPE_TARGET")
    _r(source.get("source_role") == "SECONDARY_AGGREGATOR", "TASK126_ROLE")
    _r(len(data.get("query_families") or []) == 8, "TASK126_QUERY_FAMILIES")
    actual=data.get("actual_execution") or {}
    _r(actual.get("web_search_queries") == 15, "TASK126_SEARCH_COUNT")
    _r(actual.get("direct_open_attempts") == 1 and actual.get("direct_open_successes") == 0, "TASK126_OPEN_COUNT")
    _r(actual.get("raw_zip_requests") == 0 and actual.get("drive_reads") == 0 and actual.get("ocr") == 0, "TASK126_FORBIDDEN_READ")
    rules=data.get("evidence_rules") or {}
    _r(rules.get("index_absence_is_global_no_match") is False, "TASK126_GLOBAL_ABSENCE")
    _r(rules.get("other_municipality_is_limeira_evidence") is False, "TASK126_OTHER_MUNI")
    _r(rules.get("code_2607004_alone_is_policy_bridge") is False, "TASK126_CODE_GUARD")
    _r(rules.get("text_similarity_can_create_candidate") is False, "TASK126_TEXT_GUARD")
    _r(rules.get("exact_policy_marker_required_for_policy_candidate") is True, "TASK126_EXACT_MARKER")
    _r(rules.get("primary_municipal_verification_required") is True, "TASK126_PRIMARY_VERIFY")
    expected=data.get("expected_outcome") or {}
    _r(expected.get("limeira_explicit_policy_candidate_count") == 0, "TASK126_EXPECTED_CANDIDATES")
    _r(expected.get("bounded_index_status") == "NO_INDEXED_LIMEIRA_POLICY_CANDIDATE_OBSERVED", "TASK126_EXPECTED_STATUS")
    _r(expected.get("financial_identity_change") is False and expected.get("transaction_identity_change") is False, "TASK126_PROMOTION")
    return data

def load_task126_contract(path: str|Path) -> dict[str, Any]:
    try:
        data=json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Task126Stop("TASK126_MISSING") from exc
    except json.JSONDecodeError as exc:
        raise Task126Stop("TASK126_JSON") from exc
    _r(isinstance(data,dict),"TASK126_OBJECT")
    return validate_task126_contract(data)
