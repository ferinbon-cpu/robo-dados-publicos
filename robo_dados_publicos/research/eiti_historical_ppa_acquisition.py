from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


EXPECTED_PERIODS = ("2018-2021", "2022-2025")
EXPECTED_LAWS = {
    "2018-2021": "LEI_MUNICIPAL_5947_2017",
    "2022-2025": "LEI_MUNICIPAL_6659_2021",
}
EXPECTED_SIGNALS = {
    "2018-2021": "escolas com programas em tempo integral",
    "2022-2025": "ÍNDICE DE ALUNOS EM EDUCACAO INTEGRAL",
}
REQUIRED_EVIDENCE = {
    "PRIMARY_PPA_DOCUMENT_IDENTITY",
    "STABLE_SOURCE_HASH_OR_EQUIVALENT_IDENTITY",
    "TYPED_LOCATOR_FOR_THE_RELEVANT_PLANNING_SIGNAL",
    "DIRECT_TEXT_OR_VISUAL_EVIDENCE",
}
REQUIRED_SEMANTIC_GUARDS = {
    "NO_MATCH_IS_SCOPED_TO_BOUNDED_SEARCH",
    "PLANNING_SIGNAL_DOES_NOT_CREATE_FINANCIAL_IDENTITY",
    "INDICATOR_SIMILARITY_DOES_NOT_CREATE_ACCOUNTING_IDENTITY",
    "PLANNING_TARGET_DOES_NOT_PROVE_IMPLEMENTATION",
    "PLANNING_TARGET_DOES_NOT_PROVE_CAUSAL_OUTCOME",
    "TWO_HISTORICAL_PPA_MATCHES_DO_NOT_AUTOMATICALLY_PROVE_THREE_PPA_POLICY_CONTINUITY",
}


class HistoricalPpaAcquisitionDesignStop(RuntimeError):
    """Fail-closed TASK 103 acquisition-contract validation error."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise HistoricalPpaAcquisitionDesignStop(code)


def _host(url: str) -> str:
    parsed = urlparse(url)
    _require(parsed.scheme == "https", "TASK103_URL_SCHEME")
    _require(bool(parsed.hostname), "TASK103_URL_HOST")
    return str(parsed.hostname).lower()


def validate_acquisition_design(data: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(data, dict), "TASK103_OBJECT")
    _require(data.get("schema") == "EITI_HISTORICAL_PPA_PRIMARY_ACQUISITION_V1", "TASK103_SCHEMA")
    _require(data.get("version") == 1, "TASK103_VERSION")
    _require(data.get("mode") == "T0_OFFLINE_ACQUISITION_CONTRACT_DESIGN", "TASK103_MODE")
    _require(data.get("policy_id") == "POLICY:EITI_LIMEIRA", "TASK103_POLICY")
    _require(data.get("execution_tier") == "T1_REMOTE_READONLY_SEPARATE", "TASK103_EXECUTION_TIER")
    _require(data.get("future_execution_authorized_by_design") is False, "TASK103_SELF_AUTHORIZATION")

    effects = data.get("design_remote_effects")
    _require(isinstance(effects, dict) and effects, "TASK103_REMOTE_EFFECT_OBJECT")
    _require(all(value is False for value in effects.values()), "TASK103_REMOTE_EFFECT")

    required = data.get("required_before_promotion")
    _require(isinstance(required, list), "TASK103_REQUIRED_EVIDENCE")
    _require(set(required) == REQUIRED_EVIDENCE, "TASK103_REQUIRED_EVIDENCE_DRIFT")

    guards = set(data.get("semantic_guards") or [])
    _require(REQUIRED_SEMANTIC_GUARDS.issubset(guards), "TASK103_SEMANTIC_GUARDS")

    live = data.get("live_contract")
    _require(isinstance(live, dict), "TASK103_LIVE_CONTRACT")
    hosts = live.get("allowed_hosts")
    _require(isinstance(hosts, list) and hosts, "TASK103_ALLOWED_HOSTS")
    normalized_hosts = [str(item).strip().lower() for item in hosts]
    _require(len(normalized_hosts) == len(set(normalized_hosts)), "TASK103_DUPLICATE_HOST")
    _require(
        set(normalized_hosts)
        == {"www.limeira.sp.gov.br", "limeira.sp.gov.br", "consulta.limeira.sp.leg.br"},
        "TASK103_ALLOWED_HOST_DRIFT",
    )
    _require(live.get("allowed_methods") == ["GET"], "TASK103_METHODS")
    _require(live.get("maximum_http_requests_total") == 6, "TASK103_TOTAL_BUDGET")
    _require(live.get("maximum_http_requests_per_period") == 3, "TASK103_PERIOD_BUDGET")
    _require(live.get("pagination_allowed") is False, "TASK103_PAGINATION")
    _require(live.get("retry_allowed") is False, "TASK103_RETRY")
    _require(live.get("redirects_must_remain_on_allowlisted_host") is True, "TASK103_REDIRECT_POLICY")
    _require(live.get("source_bytes_sha256_required") is True, "TASK103_HASH_REQUIREMENT")
    _require(live.get("locator_coordinate_system_required") is True, "TASK103_LOCATOR_REQUIREMENT")

    statuses = live.get("allowed_result_statuses")
    _require(isinstance(statuses, list) and statuses, "TASK103_RESULT_STATUSES")
    _require("PRIMARY_MATCH" in statuses and "NO_MATCH" in statuses, "TASK103_RESULT_STATUS_CORE")
    _require(all(isinstance(item, str) and item for item in statuses), "TASK103_RESULT_STATUS_ITEM")

    periods = data.get("periods")
    _require(isinstance(periods, list), "TASK103_PERIODS")
    _require(tuple(item.get("period") for item in periods) == EXPECTED_PERIODS, "TASK103_PERIOD_ORDER")

    allowset = set(normalized_hosts)
    for item in periods:
        period = item["period"]
        _require(item.get("law_identity") == EXPECTED_LAWS[period], f"TASK103_{period}_LAW")
        _require(item.get("expected_signal") == EXPECTED_SIGNALS[period], f"TASK103_{period}_SIGNAL")
        anchors = item.get("official_anchors")
        _require(isinstance(anchors, list) and anchors, f"TASK103_{period}_ANCHORS")
        for anchor in anchors:
            _require(isinstance(anchor, dict), f"TASK103_{period}_ANCHOR_OBJECT")
            _require(_host(str(anchor.get("url") or "")) in allowset, f"TASK103_{period}_ANCHOR_HOST")

        candidate = item.get("primary_pdf_candidate_url")
        if candidate is None:
            _require(
                item.get("primary_pdf_resolution_required") is True,
                f"TASK103_{period}_UNRESOLVED_PRIMARY_MUST_REMAIN_EXPLICIT",
            )
        else:
            _require(isinstance(candidate, str), f"TASK103_{period}_PRIMARY_URL_TYPE")
            _require(_host(candidate) in allowset, f"TASK103_{period}_PRIMARY_HOST")
            _require(candidate.lower().endswith(".pdf"), f"TASK103_{period}_PRIMARY_EXTENSION")
            _require(
                item.get("primary_pdf_resolution_required") is False,
                f"TASK103_{period}_PRIMARY_RESOLUTION_FLAG",
            )

    by_period = {item["period"]: item for item in periods}
    _require(
        by_period["2018-2021"]["primary_pdf_candidate_url"] is None,
        "TASK103_2018_PRIMARY_NOT_YET_PROVEN",
    )
    _require(
        by_period["2022-2025"]["primary_pdf_candidate_url"]
        == "https://www.limeira.sp.gov.br/sitenovo/downloads/9d8dd63f39cc3b51ef032a4c96210a07.pdf",
        "TASK103_2022_PRIMARY_CANDIDATE",
    )

    return {
        "status": "PASS_TASK103_HISTORICAL_PPA_ACQUISITION_DESIGN_OFFLINE",
        "period_count": 2,
        "resolved_primary_pdf_candidates": 1,
        "unresolved_primary_pdf_candidates": 1,
        "maximum_http_requests_total": 6,
        "maximum_http_requests_per_period": 3,
        "live_execution_performed": False,
        "financial_identity_created": False,
        "causal_effect_created": False,
        "remote_effects": 0,
    }


def load_and_validate_acquisition_design(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_acquisition_design(data)
