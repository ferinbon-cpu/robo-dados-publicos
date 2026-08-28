"""Fail-closed authorization contract for the first SIOPE 2025 T1 live run."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re

STOP = "STOP_LIVE_NOT_AUTHORIZED"
ERROR = "STOP_SIOPE_2025_T1_AUTHORIZATION"
AUTH_SCHEMA = "SIOPE_2025_T1_FIRST_LIVE_AUTHORIZATION_V1"
AUTH_PATH = "config/siope_2025_t1_first_live_authorization.v1.json"
_PREP_SCHEMA = "SIOPE_2025_T1_FIRST_LIVE_PREPARATION_V1"
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_AUTH_ID = re.compile(r"^SIOPE2025-T1-[A-Z0-9_-]{8,64}$")


class Siope2025T1AuthorizationError(RuntimeError):
    pass


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Siope2025T1AuthorizationError(STOP if code == STOP else f"{ERROR}_{code}")


@dataclass(frozen=True)
class AuthorizationGrant:
    authorization_id: str
    approved_by: str
    approved_at_utc: str
    expires_at_utc: str
    authorized_base_sha: str


def _parse_utc(value: object, code: str) -> datetime:
    _stop(isinstance(value, str) and value.endswith("Z"), code)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise Siope2025T1AuthorizationError(f"{ERROR}_{code}") from None
    _stop(parsed.tzinfo is not None, code)
    return parsed.astimezone(timezone.utc)


def validate_preparation_contract(preparation: dict, design: dict, automation_policy: dict) -> None:
    _stop(preparation.get("schema") == _PREP_SCHEMA, "PREPARATION_SCHEMA")
    _stop(preparation.get("task") == "TASK_004A", "PREPARATION_TASK")
    _stop(preparation.get("task_phase") == "OFFLINE_PREPARATION_ONLY", "PREPARATION_PHASE")
    _stop(preparation.get("tier_design_target") == "T1_REMOTE_READONLY", "PREPARATION_TARGET_TIER")
    _stop(preparation.get("current_task_execution_tier") == "T0_OFFLINE", "PREPARATION_CURRENT_TIER")
    _stop(preparation.get("live_execution_authorized_by_task_004a") is False, "TASK004A_LIVE_AUTH")
    _stop(preparation.get("source_get_authorized_by_task_004a") is False, "TASK004A_SOURCE_GET")
    _stop(preparation.get("future_batch_execution_authorized") is False, "TASK004A_BATCH")
    _stop(preparation.get("authorization", {}).get("fixed_artifact_path") == AUTH_PATH, "AUTH_PATH")
    _stop(preparation.get("authorization", {}).get("artifact_must_be_absent_in_task_004a") is True, "AUTH_ABSENCE_004A")
    _stop(preparation.get("authorization", {}).get("one_shot_required") is True, "ONE_SHOT")
    _stop(preparation.get("authorization", {}).get("max_live_runs") == 1, "MAX_LIVE_RUNS")

    target = preparation.get("target", {})
    _stop(target == {"year": 2025, "state": "SP", "municipality_code": 352690, "municipality_name": "Limeira"}, "TARGET")
    request = preparation.get("request_contract", {})
    expected_request = {
        "method": "GET",
        "host": "www.fnde.gov.br",
        "path": "/olinda-ide/servico/DADOS_ABERTOS_SIOPE/versao/v1/odata/Dados_Gerais_Siope(Ano_Consulta=@Ano_Consulta,Num_Peri=@Num_Peri,Sig_UF=@Sig_UF)",
        "periods": [1, 2, 3, 4, 5, 6],
        "phase_a_request_count": 6,
        "phase_b_period": 6,
        "phase_b_request_count_max": 1,
        "phase_b_precondition": "PHASE_A_PERIOD_6_OBSERVED_EXACT_IDENTITY",
        "maximum_source_get_count": 7,
        "maximum_requests_per_period": 1,
        "timeout_seconds": 60,
        "max_response_bytes": 262144,
        "max_attempts": 1,
        "retry_authorized": False,
        "follow_redirects": False,
        "pagination_authorized": False,
        "follow_nextlink": False,
    }
    _stop(request == expected_request, "REQUEST_CONTRACT")

    effects = preparation.get("effects_task_004a", {})
    _stop(effects == {
        "source_get_count": 0,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "response_persistence": False,
        "bronze_silver_gold_creation": False,
        "publication": False,
    }, "TASK004A_EFFECTS")

    semantic = preparation.get("semantic_guards", {})
    _stop(semantic.get("year_status") == "UNPROVEN_RECENT", "YEAR_STATUS")
    _stop(semantic.get("annual_period_status") == "CANDIDATE_NOT_PROVEN", "PERIOD_STATUS")
    _stop(semantic.get("resource_status") == "UNPROVEN_FOR_2025", "RESOURCE_STATUS")
    _stop(semantic.get("annual_closure_status") == "UNKNOWN", "CLOSURE_STATUS")
    _stop(semantic.get("metric_status_required") == "UNKNOWN", "METRIC_STATUS")
    _stop(semantic.get("promote_2025_to_proven") is False, "PROMOTION")
    _stop(semantic.get("include_2026_authorized") is False, "YEAR_2026")
    _stop(semantic.get("gold_calculation_authorized") is False, "GOLD")
    _stop(semantic.get("compliance_claims_authorized") is False, "COMPLIANCE")

    _stop(design.get("target", {}).get("year") == 2025, "DESIGN_YEAR")
    _stop(design.get("target", {}).get("resource_status") == "UNPROVEN_FOR_2025", "DESIGN_RESOURCE")
    _stop(design.get("target", {}).get("annual_period_status") == "CANDIDATE_NOT_PROVEN", "DESIGN_PERIOD")
    _stop(design.get("target", {}).get("annual_closure_status") == "UNKNOWN", "DESIGN_CLOSURE")
    _stop(design.get("promotion_contract", {}).get("promote_2025_to_proven") is False, "DESIGN_PROMOTION")
    _stop(design.get("future_batch_execution_authorized") is False, "DESIGN_BATCH")

    _stop(automation_policy.get("default_decision") == "BLOCK", "POLICY_DEFAULT")
    invariants = automation_policy.get("policy_invariants", {})
    _stop(invariants.get("agent_may_authorize_remote_execution") is False, "POLICY_AGENT_AUTH")
    _stop(invariants.get("future_batch_execution_authorized") is False, "POLICY_BATCH")
    t1 = automation_policy.get("tiers", {}).get("T1_REMOTE_READONLY", {})
    _stop(t1.get("human_confirmation_required") == "UNTIL_LIVE_PROOF_AND_TRUST_BOUNDARY_PASS", "POLICY_HUMAN_CONFIRMATION")


def validate_authorization_document(
    authorization: dict | None,
    preparation: dict,
    *,
    current_head_sha: str,
    current_parent_sha: str,
    changed_paths_since_base: list[str],
    now_utc: datetime | None = None,
) -> AuthorizationGrant:
    if not authorization:
        raise Siope2025T1AuthorizationError(STOP)

    _stop(authorization.get("schema") == AUTH_SCHEMA, "SCHEMA")
    _stop(authorization.get("authorized") is True, STOP)
    authorization_id = authorization.get("authorization_id")
    _stop(isinstance(authorization_id, str) and _AUTH_ID.fullmatch(authorization_id) is not None, "AUTHORIZATION_ID")
    _stop(authorization.get("approval_kind") == "OWNER_EXPLICIT_SINGLE_BOUNDED_RUN", "APPROVAL_KIND")
    _stop(authorization.get("approved_by") == "ferinbon-cpu", "APPROVED_BY")
    _stop(authorization.get("one_shot") is True, "ONE_SHOT")
    _stop(authorization.get("max_live_runs") == 1, "MAX_LIVE_RUNS")

    authorized_base_sha = authorization.get("authorized_base_sha")
    _stop(isinstance(authorized_base_sha, str) and _SHA40.fullmatch(authorized_base_sha) is not None, "BASE_SHA")
    _stop(isinstance(current_head_sha, str) and _SHA40.fullmatch(current_head_sha) is not None, "HEAD_SHA")
    _stop(isinstance(current_parent_sha, str) and _SHA40.fullmatch(current_parent_sha) is not None, "PARENT_SHA")
    _stop(current_parent_sha == authorized_base_sha, "PARENT_NOT_AUTHORIZED_BASE")
    _stop(current_head_sha != authorized_base_sha, "AUTHORIZATION_COMMIT_REQUIRED")
    _stop(changed_paths_since_base == [AUTH_PATH], "AUTHORIZATION_ONLY_DIFF")

    _stop(authorization.get("target") == preparation.get("target"), "TARGET")
    request = authorization.get("request_contract", {})
    prep_request = preparation.get("request_contract", {})
    _stop(request == {
        "maximum_source_get_count": prep_request.get("maximum_source_get_count"),
        "timeout_seconds": prep_request.get("timeout_seconds"),
        "max_response_bytes": prep_request.get("max_response_bytes"),
        "max_attempts": prep_request.get("max_attempts"),
        "retry_authorized": False,
        "follow_redirects": False,
        "pagination_authorized": False,
        "follow_nextlink": False,
    }, "REQUEST_CONTRACT")
    _stop(authorization.get("effects") == {
        "drive_read_count": 0,
        "drive_write_count": 0,
        "response_persistence": False,
        "bronze_silver_gold_creation": False,
        "publication": False,
        "future_batch_execution_authorized": False,
    }, "EFFECTS")
    _stop(authorization.get("semantic_guards") == {
        "annual_closure_status": "UNKNOWN",
        "promote_2025_to_proven": False,
        "metric_status_required": "UNKNOWN",
        "include_2026_authorized": False,
    }, "SEMANTIC_GUARDS")

    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    approved_at = _parse_utc(authorization.get("approved_at_utc"), "APPROVED_AT")
    expires_at = _parse_utc(authorization.get("expires_at_utc"), "EXPIRES_AT")
    _stop(approved_at <= now, "APPROVAL_IN_FUTURE")
    _stop(expires_at > now, "AUTHORIZATION_EXPIRED")
    _stop(expires_at > approved_at, "EXPIRY_ORDER")

    return AuthorizationGrant(
        authorization_id=authorization_id,
        approved_by="ferinbon-cpu",
        approved_at_utc=authorization["approved_at_utc"],
        expires_at_utc=authorization["expires_at_utc"],
        authorized_base_sha=authorized_base_sha,
    )
