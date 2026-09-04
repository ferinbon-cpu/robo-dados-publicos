from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable

from robo_dados_publicos.research.ontology import ASSERTION_STATUSES


EVENT_TYPES = (
    "AUTHORIZATION_INITIAL",
    "AUTHORIZATION_SUPPLEMENT",
    "AUTHORIZATION_CANCEL",
    "COMMITMENT",
    "COMMITMENT_CANCEL",
    "LIQUIDATION",
    "LIQUIDATION_CANCEL",
    "PAYMENT",
    "PAYMENT_CANCEL",
)

IDENTITY_DIMENSIONS = (
    "entity",
    "fiscal_year",
    "org",
    "unit",
    "function",
    "subfunction",
    "program",
    "action",
    "subaction",
    "economic_category",
    "expense_group",
    "application_mode",
    "expense_nature",
    "element",
    "subelement",
    "funding_source",
    "destination",
    "fund",
    "cost_center",
    "accounting_key",
)

DEFAULT_CANONICAL_STATUSES = ("PROVEN", "CORROBORATED")
_MONEY_RE = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]{1,2})?$")
_TYPED_ID_RE = re.compile(r"^[A-Z_]+:[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")


class BudgetLedgerStop(RuntimeError):
    """Fail-closed structural or accounting invariant violation."""


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise BudgetLedgerStop(code)


def _canonical_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _date(value: object, *, code: str) -> str:
    text = str(value or "")
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise BudgetLedgerStop(code) from exc
    return text


def _typed_id(value: object, *, prefix: str, code: str) -> str:
    text = str(value or "")
    _require(bool(_TYPED_ID_RE.fullmatch(text)), code)
    _require(text.startswith(prefix + ":"), code)
    return text


def _money_decimal(value: object, *, code: str) -> Decimal:
    _require(not isinstance(value, (bool, float)), code)
    text = str(value)
    _require(bool(_MONEY_RE.fullmatch(text)), code)
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise BudgetLedgerStop(code) from exc
    _require(amount > Decimal("0"), code)
    return amount


def _money_text(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01')):.2f}"


def _evidence_ids(value: object, *, code: str) -> list[str]:
    _require(isinstance(value, list), code)
    out: list[str] = []
    for item in value:
        text = _typed_id(item, prefix="EVIDENCE", code=code)
        _require(text not in out, code)
        out.append(text)
    return out


def normalize_budget_identity(identity: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(identity, dict), "TASK094_IDENTITY_OBJECT")
    unknown = sorted(set(identity) - set(IDENTITY_DIMENSIONS))
    _require(not unknown, "TASK094_IDENTITY_UNKNOWN_DIMENSION")

    entity = str(identity.get("entity") or "").strip()
    _require(entity != "", "TASK094_IDENTITY_ENTITY")

    year = identity.get("fiscal_year")
    _require(
        isinstance(year, int) and not isinstance(year, bool) and 1900 <= year <= 2200,
        "TASK094_IDENTITY_FISCAL_YEAR",
    )

    normalized: dict[str, Any] = {}
    for key in IDENTITY_DIMENSIONS:
        if key == "entity":
            normalized[key] = entity
        elif key == "fiscal_year":
            normalized[key] = year
        else:
            raw = identity.get(key)
            if raw is None:
                normalized[key] = None
            else:
                _require(
                    isinstance(raw, (str, int)) and not isinstance(raw, bool),
                    f"TASK094_IDENTITY_{key.upper()}",
                )
                text = str(raw).strip()
                normalized[key] = text if text else None
    return normalized


def budget_identity_sha256(identity: dict[str, Any]) -> str:
    normalized = normalize_budget_identity(identity)
    return sha256(_canonical_bytes(normalized)).hexdigest()


def validate_budget_event(record: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(record, dict), "TASK094_EVENT_OBJECT")
    event_id = _typed_id(
        record.get("event_id"),
        prefix="BUDGET_EVENT",
        code="TASK094_EVENT_ID",
    )
    event_type = str(record.get("event_type") or "")
    _require(event_type in EVENT_TYPES, "TASK094_EVENT_TYPE")
    effective_date = _date(record.get("effective_date"), code="TASK094_EFFECTIVE_DATE")

    sequence = record.get("sequence", 0)
    _require(
        isinstance(sequence, int) and not isinstance(sequence, bool) and sequence >= 0,
        "TASK094_SEQUENCE",
    )

    amount = _money_decimal(record.get("amount"), code="TASK094_AMOUNT")
    assertion_status = str(record.get("assertion_status") or "")
    _require(assertion_status in ASSERTION_STATUSES, "TASK094_ASSERTION_STATUS")
    evidence_ids = _evidence_ids(record.get("evidence_ids", []), code="TASK094_EVIDENCE_IDS")
    if assertion_status in DEFAULT_CANONICAL_STATUSES:
        _require(bool(evidence_ids), "TASK094_CANONICAL_EVENT_EVIDENCE_REQUIRED")

    source_document_id = _typed_id(
        record.get("source_document_id"),
        prefix="DOC",
        code="TASK094_SOURCE_DOCUMENT_ID",
    )
    identity = normalize_budget_identity(record.get("identity"))
    identity_hash = budget_identity_sha256(identity)

    attributes = record.get("attributes", {})
    _require(isinstance(attributes, dict), "TASK094_EVENT_ATTRIBUTES")

    return {
        "event_id": event_id,
        "event_type": event_type,
        "effective_date": effective_date,
        "sequence": sequence,
        "amount": _money_text(amount),
        "assertion_status": assertion_status,
        "evidence_ids": evidence_ids,
        "source_document_id": source_document_id,
        "identity": identity,
        "budget_identity_sha256": identity_hash,
        "attributes": deepcopy(attributes),
    }


def _apply_event(state: dict[str, Decimal], event: dict[str, Any]) -> None:
    amount = Decimal(event["amount"])
    event_type = event["event_type"]

    if event_type in {"AUTHORIZATION_INITIAL", "AUTHORIZATION_SUPPLEMENT"}:
        state["authorization_current"] += amount
    elif event_type == "AUTHORIZATION_CANCEL":
        state["authorization_current"] -= amount
    elif event_type == "COMMITMENT":
        state["committed"] += amount
    elif event_type == "COMMITMENT_CANCEL":
        state["committed"] -= amount
    elif event_type == "LIQUIDATION":
        state["liquidated"] += amount
    elif event_type == "LIQUIDATION_CANCEL":
        state["liquidated"] -= amount
    elif event_type == "PAYMENT":
        state["paid"] += amount
    elif event_type == "PAYMENT_CANCEL":
        state["paid"] -= amount
    else:  # pragma: no cover - validation prevents this branch
        raise BudgetLedgerStop("TASK094_UNREACHABLE_EVENT_TYPE")

    _require(
        all(value >= Decimal("0") for value in state.values()),
        "TASK094_NEGATIVE_NET_BALANCE",
    )
    _require(
        state["committed"] <= state["authorization_current"],
        "TASK094_COMMITTED_EXCEEDS_AUTHORIZATION",
    )
    _require(
        state["liquidated"] <= state["committed"],
        "TASK094_LIQUIDATED_EXCEEDS_COMMITTED",
    )
    _require(
        state["paid"] <= state["liquidated"],
        "TASK094_PAID_EXCEEDS_LIQUIDATED",
    )


def reconstruct_budget_snapshot(
    events: Iterable[dict[str, Any]],
    *,
    as_of: str | None = None,
    canonical_statuses: Iterable[str] = DEFAULT_CANONICAL_STATUSES,
) -> dict[str, Any]:
    normalized = [validate_budget_event(event) for event in events]
    _require(bool(normalized), "TASK094_EVENTS_EMPTY")

    event_ids = [event["event_id"] for event in normalized]
    _require(len(event_ids) == len(set(event_ids)), "TASK094_DUPLICATE_EVENT_ID")

    identity_hashes = {event["budget_identity_sha256"] for event in normalized}
    _require(len(identity_hashes) == 1, "TASK094_MIXED_BUDGET_IDENTITIES")
    identity_hash = next(iter(identity_hashes))
    identity = normalized[0]["identity"]

    accepted = tuple(str(status) for status in canonical_statuses)
    _require(bool(accepted), "TASK094_CANONICAL_STATUSES_EMPTY")
    _require(
        len(accepted) == len(set(accepted))
        and all(status in ASSERTION_STATUSES for status in accepted),
        "TASK094_CANONICAL_STATUSES_INVALID",
    )

    cutoff = _date(as_of, code="TASK094_AS_OF_DATE") if as_of is not None else None
    ordered = sorted(
        normalized,
        key=lambda event: (
            event["effective_date"],
            event["sequence"],
            event["event_id"],
        ),
    )

    state = {
        "authorization_current": Decimal("0"),
        "committed": Decimal("0"),
        "liquidated": Decimal("0"),
        "paid": Decimal("0"),
    }
    applied: list[str] = []
    excluded_status: list[str] = []
    after_cutoff: list[str] = []
    history: list[dict[str, Any]] = []

    for event in ordered:
        if cutoff is not None and event["effective_date"] > cutoff:
            after_cutoff.append(event["event_id"])
            continue
        if event["assertion_status"] not in accepted:
            excluded_status.append(event["event_id"])
            continue

        _apply_event(state, event)
        applied.append(event["event_id"])
        history.append(
            {
                "event_id": event["event_id"],
                "event_type": event["event_type"],
                "effective_date": event["effective_date"],
                "amount": event["amount"],
                "assertion_status": event["assertion_status"],
                "authorization_current": _money_text(state["authorization_current"]),
                "committed": _money_text(state["committed"]),
                "liquidated": _money_text(state["liquidated"]),
                "paid": _money_text(state["paid"]),
                "available_authorization": _money_text(
                    state["authorization_current"] - state["committed"]
                ),
            }
        )

    snapshot_core = {
        "schema": "POLICY_BUDGET_SNAPSHOT_V1",
        "budget_identity_sha256": identity_hash,
        "identity": identity,
        "as_of": cutoff,
        "canonical_statuses": list(accepted),
        "authorization_current": _money_text(state["authorization_current"]),
        "committed": _money_text(state["committed"]),
        "liquidated": _money_text(state["liquidated"]),
        "paid": _money_text(state["paid"]),
        "available_authorization": _money_text(
            state["authorization_current"] - state["committed"]
        ),
        "applied_event_ids": applied,
        "excluded_noncanonical_event_ids": excluded_status,
        "after_as_of_event_ids": after_cutoff,
        "history": history,
        "policy_attribution_inferred": False,
    }
    return {
        **snapshot_core,
        "snapshot_sha256": sha256(_canonical_bytes(snapshot_core)).hexdigest(),
    }


def budget_event_to_research_entity(event: dict[str, Any]) -> dict[str, Any]:
    normalized = validate_budget_event(event)
    return {
        "id": normalized["event_id"],
        "type": "BUDGET_EVENT",
        "label": f"{normalized['event_type']} {normalized['amount']}",
        "aliases": [],
        "valid_from": normalized["effective_date"],
        "valid_to": None,
        "attributes": {
            "amount": normalized["amount"],
            "assertion_status": normalized["assertion_status"],
            "source_document_id": normalized["source_document_id"],
            "budget_identity_sha256": normalized["budget_identity_sha256"],
        },
    }


def load_budget_ledger_contract(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    _require(data.get("schema") == "POLICY_BUDGET_LEDGER_V1", "TASK094_CONTRACT_SCHEMA")
    _require(tuple(data.get("event_types") or ()) == EVENT_TYPES, "TASK094_CONTRACT_EVENT_TYPES")
    _require(
        tuple(data.get("identity_dimensions") or ()) == IDENTITY_DIMENSIONS,
        "TASK094_CONTRACT_IDENTITY_DIMENSIONS",
    )
    _require(
        tuple(data.get("default_canonical_statuses") or ()) == DEFAULT_CANONICAL_STATUSES,
        "TASK094_CONTRACT_CANONICAL_STATUSES",
    )
    money = data.get("money") or {}
    _require(money.get("currency") == "BRL", "TASK094_CONTRACT_CURRENCY")
    _require(money.get("max_decimal_places") == 2, "TASK094_CONTRACT_DECIMALS")
    _require(money.get("negative_amounts_forbidden") is True, "TASK094_CONTRACT_NEGATIVE")
    _require(
        money.get("cancellations_use_explicit_event_types") is True,
        "TASK094_CONTRACT_CANCELLATION_SEMANTICS",
    )
    remote = data.get("remote_effects") or {}
    _require(remote and all(value is False for value in remote.values()), "TASK094_CONTRACT_REMOTE_EFFECT")
    return data
