from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Task170Stop(RuntimeError):
    pass


ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT / "config/task170_limeira_tda_primary_accounting_discovery_gate.v1.json"


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task170Stop(code)


def load_gate(path: str | Path = DEFAULT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "TASK170_LIMEIRA_TDA_PRIMARY_ACCOUNTING_DISCOVERY_GATE_V1", "TASK170_SCHEMA")
    _stop(obj.get("mode") == "T0_OFFLINE_SELECTION_ONLY", "TASK170_MODE")
    source = obj["selected_source"]
    _stop(source["source_id"] == "LIMEIRA_TDA_PORTAL", "TASK170_SOURCE")
    _stop(source["host"] == "transparencia.limeira.sp.gov.br", "TASK170_HOST")
    _stop(source["source_role"] == "ACCOUNTING_EXECUTION_PRIMARY", "TASK170_ROLE")
    live = obj["future_live_gate"]
    _stop(live["authorized_now"] is False, "TASK170_LIVE_NOT_AUTHORIZED")
    _stop(live["fresh_explicit_owner_authorization_required"] is True, "TASK170_AUTH_REQUIRED")
    _stop(live["request_budget"]["max_requests"] == 1, "TASK170_REQUEST_BUDGET")
    _stop(live["request_budget"]["max_redirects_followed"] == 0, "TASK170_REDIRECT_BOUNDARY")
    _stop(live["request_budget"]["retry_max"] == 0, "TASK170_RETRY")
    _stop(live["exact_first_request"]["method"] == "GET", "TASK170_METHOD")
    _stop(
        live["exact_first_request"]["url"]
        == "https://transparencia.limeira.sp.gov.br/tdaportalclient.aspx?418",
        "TASK170_EXACT_URL",
    )
    _stop(obj["remote_effects_this_task"] == {"network": 0, "drive": 0, "publication": 0}, "TASK170_REMOTE_EFFECTS")
    return obj


def validate_declared_route_policy(obj: dict[str, Any]) -> None:
    live = obj["future_live_gate"]
    _stop(
        "literally declared" in live["machine_readable_candidate_rule"],
        "TASK170_DECLARED_ROUTE_RULE",
    )
    forbidden = set(obj["forbidden_actions"])
    required = {
        "FOLLOW_REDIRECT",
        "AUTHENTICATE",
        "SUBMIT_FORM",
        "EXECUTE_JAVASCRIPT",
        "BYPASS_CAPTCHA",
        "GUESS_ENDPOINT",
        "BRUTE_FORCE_PATHS",
        "INFER_NO_DATA_FROM_ACCESS_BARRIER",
        "PROMOTE_FINANCIAL_IDENTITY",
        "PROMOTE_TRANSACTION_IDENTITY",
    }
    _stop(required <= forbidden, "TASK170_FORBIDDEN_ACTION_MISSING")
    _stop(
        live["if_3xx_or_login_barrier"] == "SOURCE_ACCESS_SURFACE_BLOCKED",
        "TASK170_ACCESS_BARRIER_SEMANTICS",
    )
    _stop(
        live["transport_failure"] == "SOURCE_TRANSPORT_UNAVAILABLE_NOT_NO_MATCH",
        "TASK170_TRANSPORT_SEMANTICS",
    )


def validate_tce_fallback(obj: dict[str, Any]) -> None:
    tce = obj["fallback_after_blocked_tda"]["TCE_SP_DESPESAS"]
    _stop(tce["role"] == "CONTROL_PRIMARY_CORROBORATION_ONLY", "TASK170_TCE_ROLE")
    missing = set(tce["missing_for_policy_discovery"])
    _stop({"policy_marker", "program_action_subaction", "ficha_or_dotacao"} <= missing, "TASK170_TCE_MISSING_FIELDS")
    _stop("Do not use TCE alone" in tce["rule"], "TASK170_TCE_NO_REPLACEMENT")


def validate_gate(path: str | Path = DEFAULT) -> dict[str, Any]:
    obj = load_gate(path)
    validate_declared_route_policy(obj)
    validate_tce_fallback(obj)
    return {
        "schema": "TASK170_GATE_VALIDATION_RESULT_V1",
        "status": "PASS",
        "selected_source": obj["selected_source"]["source_id"],
        "live_authorized": obj["future_live_gate"]["authorized_now"],
        "request_budget": obj["future_live_gate"]["request_budget"]["max_requests"],
        "redirects_followed_max": obj["future_live_gate"]["request_budget"]["max_redirects_followed"],
    }


if __name__ == "__main__":
    print(json.dumps(validate_gate(), ensure_ascii=False, sort_keys=True))
