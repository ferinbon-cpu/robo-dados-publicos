from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Task170Stop(RuntimeError):
    pass


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "config/limeira_tda_accounting_discovery_gate.v1.json"


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task170Stop(code)


def load_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "LIMEIRA_TDA_ACCOUNTING_DISCOVERY_GATE_V1", "TASK170_SCHEMA")
    _stop(obj.get("mode") == "T0_OFFLINE_SOURCE_SELECTION_ONLY", "TASK170_MODE")
    auth = obj["authorization_boundary"]
    _stop(auth["task170_network_requests"] == 0, "TASK170_NETWORK")
    _stop(auth["live_discovery_authorized_now"] is False, "TASK170_LIVE_BOUNDARY")
    _stop(auth["fresh_explicit_owner_authorization_required"] is True, "TASK170_AUTH_REQUIRED")
    return obj


def validate_source_selection(obj: dict[str, Any]) -> None:
    src = obj["selected_source"]
    _stop(src["source_id"] == "LIMEIRA_TDA_PORTAL", "TASK170_SOURCE")
    _stop(src["authority"] == "MUNICIPAL_PRIMARY", "TASK170_AUTHORITY")
    _stop(src["host"] == "transparencia.limeira.sp.gov.br", "TASK170_HOST")
    _stop(src["known_official_route"].startswith("https://transparencia.limeira.sp.gov.br/"), "TASK170_ROUTE")
    _stop(src["registry_status"] == "BLOCKED_NO_PUBLIC_ENDPOINT_PROVEN", "TASK170_REGISTRY_STATE")
    _stop("empenho_liquidacao_pagamento" in src["declared_capabilities"], "TASK170_EXECUTION_CAPABILITY")


def validate_future_gate(obj: dict[str, Any]) -> None:
    gate = obj["future_live_discovery_gate"]
    budget = gate["request_budget"]
    _stop(budget["initial_entry_get_max"] == 1, "TASK170_ENTRY_BUDGET")
    _stop(budget["follow_declared_machine_readable_route_max"] == 1, "TASK170_FOLLOW_BUDGET")
    _stop(budget["total_requests_max"] <= 2, "TASK170_TOTAL_BUDGET")
    _stop(budget["retry"] == 0 and budget["redirect_follow"] == 0, "TASK170_RETRY_REDIRECT")
    forbidden = set(gate["forbidden_discovery"])
    for item in (
        "endpoint_guessing",
        "javascript_execution",
        "form_submission",
        "authentication",
        "captcha_bypass",
        "automatic_retry",
    ):
        _stop(item in forbidden, "TASK170_FORBIDDEN_DISCOVERY_MISSING")
    semantics = gate["access_barrier_semantics"]
    _stop(semantics["redirect_to_login_logout_root_or_session_barrier"] == "SOURCE_ACCESS_SURFACE_BLOCKED", "TASK170_ACCESS_SEMANTICS")
    _stop(semantics["transport_failure"] == "SOURCE_TRANSPORT_UNAVAILABLE", "TASK170_TRANSPORT_SEMANTICS")
    _stop(semantics["none_of_these_equal"] == "NO_DATA", "TASK170_NO_DATA_GUARD")


def validate_scientific_guards(obj: dict[str, Any]) -> None:
    guards = obj["scientific_guards"]
    _stop(guards["current_financial_identity"] == "UNKNOWN", "TASK170_FINANCIAL_STATE")
    _stop(guards["current_payment"] == "NOT_PROVEN", "TASK170_PAYMENT_STATE")
    _stop(guards["tda_surface_selection_promotes_identity"] is False, "TASK170_SELECTION_PROMOTION")
    _stop(guards["tce_can_replace_unresolved_municipal_policy_identity"] is False, "TASK170_TCE_GUARD")
    weak = set(obj["promotion_preconditions_after_future_route_discovery"]["weak_joins_forbidden"])
    for item in ("program_2001_alone", "capl_2607004_alone", "same_or_similar_value", "chronology", "semantic_similarity"):
        _stop(item in weak, "TASK170_WEAK_JOIN_GUARD")


def validate_contract(path: str | Path = DEFAULT_CONTRACT) -> dict[str, Any]:
    obj = load_contract(path)
    validate_source_selection(obj)
    validate_future_gate(obj)
    validate_scientific_guards(obj)
    return {
        "schema": "TASK170_VALIDATION_RESULT_V1",
        "status": "PASS",
        "selected_source": obj["selected_source"]["source_id"],
        "live_authorized": obj["authorization_boundary"]["live_discovery_authorized_now"],
        "network_requests": obj["authorization_boundary"]["task170_network_requests"],
        "result": obj["result"],
    }


if __name__ == "__main__":
    print(json.dumps(validate_contract(), ensure_ascii=False, sort_keys=True))
