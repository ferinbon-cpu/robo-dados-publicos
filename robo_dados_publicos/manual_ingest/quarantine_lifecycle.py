from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_quarantine_contract(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "QUARANTINE_STATE_NEVER_AUTHORIZES_CONTENT_READ" not in data.get("invariants", []):
        raise ValueError("STOP_QUARANTINE_CONTENT_BOUNDARY_MISSING")
    return data


def next_quarantine_state(cause: str, contract: dict[str, Any]) -> str:
    item = contract.get("causes", {}).get(cause)
    if not item:
        return "QUARANTINED"
    return str(item["default_next"])


def can_release(*, cause_resolved: bool, rule_version: str | None, provenance_recorded: bool, authorized_scope_confirmed: bool) -> bool:
    return bool(cause_resolved and rule_version and provenance_recorded and authorized_scope_confirmed)


def can_release_to_routing(*, release_ok: bool, family_known: bool, controller_rule_match: bool, maturity_entry_exists: bool) -> bool:
    return bool(release_ok and family_known and controller_rule_match and maturity_entry_exists)


def content_read_allowed_by_quarantine_state(state: str) -> bool:
    return False
