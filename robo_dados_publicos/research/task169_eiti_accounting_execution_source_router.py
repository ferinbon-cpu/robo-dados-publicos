from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Task169Stop(RuntimeError):
    pass


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROUTER = ROOT / "config/eiti_accounting_execution_source_router.v1.json"


def _stop(condition: bool, code: str) -> None:
    if not condition:
        raise Task169Stop(code)


def load_router(path: str | Path = DEFAULT_ROUTER) -> dict[str, Any]:
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    _stop(obj.get("schema") == "EITI_ACCOUNTING_EXECUTION_SOURCE_ROUTER_V1", "TASK169_SCHEMA")
    _stop(obj.get("mode") == "T0_OFFLINE_SOURCE_ROUTER_ONLY", "TASK169_MODE")
    auth = obj["authorization_boundary"]
    _stop(auth["new_non_pncp_live_read_authorized"] is False, "TASK169_LIVE_BOUNDARY")
    _stop(auth["fresh_explicit_source_scope_authorization_required"] is True, "TASK169_AUTH_REQUIRED")
    _stop(auth["t0_network_requests"] == 0, "TASK169_NETWORK")
    _stop(auth["t0_drive_reads"] == 0 and auth["t0_drive_writes"] == 0, "TASK169_DRIVE")
    return obj


def validate_source_ranking(router: dict[str, Any]) -> None:
    sources = router["source_classes"]
    ranks = [x["rank"] for x in sources]
    _stop(ranks == list(range(1, len(sources) + 1)), "TASK169_RANK_SEQUENCE")
    ids = [x["id"] for x in sources]
    _stop(len(ids) == len(set(ids)), "TASK169_DUPLICATE_SOURCE_ID")
    _stop(ids[0] == "LIMEIRA_PRIMARY_TRANSPARENCY_EXPENSE_DETAIL", "TASK169_PRIMARY_SOURCE_RANK")
    _stop(sources[-1]["role"] == "CONTROL_PRIMARY", "TASK169_CONTROL_LAST")


def validate_identity_bundle(router: dict[str, Any]) -> None:
    bundle = router["minimum_policy_financial_identity_bundle"]
    required = set(bundle["all_required"])
    expected = {
        "entity_cnpj_exact",
        "fiscal_year_exact",
        "policy_link_basis_explicit",
        "institutional_unit_explicit",
        "program_or_action_explicit",
        "stable_budget_key_explicit",
        "amount_semantic_explicit",
        "source_role_accounting_or_budget_primary",
    }
    _stop(expected <= required, "TASK169_IDENTITY_BUNDLE_INCOMPLETE")
    weak = set(bundle["not_sufficient"])
    for required_guard in (
        "program_2001_alone",
        "unit_10_00_00_similarity",
        "capl_2607004_alone",
        "same_or_similar_value",
        "chronology",
        "semantic_similarity",
        "pncp_purchase_or_contract_without_accounting_link",
    ):
        _stop(required_guard in weak, "TASK169_WEAK_JOIN_GUARD_MISSING")


def validate_transaction_gates(router: dict[str, Any]) -> None:
    gates = router["transaction_stage_gates"]
    _stop([x["stage"] for x in gates] == ["COMMITMENT", "LIQUIDATION", "PAYMENT"], "TASK169_STAGE_ORDER")
    _stop(
        [x["amount_semantic"] for x in gates]
        == ["COMMITTED_VALUE", "LIQUIDATED_VALUE", "PAID_VALUE"],
        "TASK169_AMOUNT_SEMANTICS",
    )
    _stop("empenho_number_explicit" in gates[0]["requires"], "TASK169_COMMITMENT_KEY")
    _stop("payment_record_or_explicit_paid_amount" in gates[2]["requires"], "TASK169_PAYMENT_EVIDENCE")


def validate_direct_json_policy(router: dict[str, Any]) -> None:
    order = router["direct_json_first"]
    _stop(order[0] == "DIRECT_OFFICIAL_JSON_API_GET", "TASK169_JSON_FIRST")
    _stop(order[-1] == "HTML_DOM_JS_INTERNAL_PATH_REVERSE_ENGINEERING_FALLBACK_ONLY", "TASK169_REVERSE_ENGINEERING_POSITION")
    _stop(
        router["future_live_gate_contract"]["if_transport_fails"]
        == "SOURCE_TRANSPORT_UNAVAILABLE_NOT_NO_MATCH",
        "TASK169_TRANSPORT_SEMANTICS",
    )


def validate_forbidden_promotions(router: dict[str, Any]) -> None:
    guards = set(router["forbidden_promotions"])
    required = {
        "PNCP_TO_PAYMENT",
        "PROGRAM_TOTAL_TO_EITI",
        "SAME_AMOUNT_TO_IDENTITY",
        "CHRONOLOGY_TO_IDENTITY",
        "TEXT_SIMILARITY_TO_IDENTITY",
        "TRANSPORT_FAILURE_TO_NO_MATCH",
        "COMMITMENT_TO_LIQUIDATION",
        "LIQUIDATION_TO_PAYMENT",
    }
    _stop(required <= guards, "TASK169_FORBIDDEN_PROMOTION_MISSING")


def validate_router(path: str | Path = DEFAULT_ROUTER) -> dict[str, Any]:
    router = load_router(path)
    validate_source_ranking(router)
    validate_identity_bundle(router)
    validate_transaction_gates(router)
    validate_direct_json_policy(router)
    validate_forbidden_promotions(router)
    return {
        "schema": "TASK169_ROUTER_VALIDATION_RESULT_V1",
        "status": "PASS",
        "source_class_count": len(router["source_classes"]),
        "transaction_gate_count": len(router["transaction_stage_gates"]),
        "live_authorized": router["authorization_boundary"]["new_non_pncp_live_read_authorized"],
        "next_live_rule": router["next_live_source_selection_rule"],
    }


if __name__ == "__main__":
    print(json.dumps(validate_router(), ensure_ascii=False, sort_keys=True))
