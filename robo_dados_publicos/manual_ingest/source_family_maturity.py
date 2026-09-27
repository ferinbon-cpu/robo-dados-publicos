from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FamilyMaturityStop(ValueError):
    pass


def validate_maturity_registry(data: dict[str, Any]) -> dict[str, Any]:
    levels = set(data.get("levels", []))
    if levels != {"EXECUTION_READY_BOUNDED", "ROUTING_ONLY_SUPERVISED_EXECUTION", "BLOCKED_PENDING_CONTRACT"}:
        raise FamilyMaturityStop("STOP_BAD_MATURITY_LEVELS")
    families = data.get("families", {})
    if not families:
        raise FamilyMaturityStop("STOP_EMPTY_MATURITY_REGISTRY")
    for family, item in families.items():
        if item.get("level") not in levels:
            raise FamilyMaturityStop(f"STOP_BAD_FAMILY_LEVEL:{family}")
    return data


def load_maturity_registry(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_maturity_registry(data)


def execution_maturity(family: str | None, registry: dict[str, Any]) -> str:
    if not family or family not in registry["families"]:
        return "BLOCKED_PENDING_CONTRACT"
    return str(registry["families"][family]["level"])


def auto_execution_allowed_by_maturity(family: str | None, registry: dict[str, Any]) -> bool:
    return execution_maturity(family, registry) == "EXECUTION_READY_BOUNDED"


def assert_controller_family_coverage(controller: dict[str, Any], registry: dict[str, Any]) -> None:
    controller_families = set(controller.get("known_document_families", {}))
    registry_families = set(registry.get("families", {}))
    if controller_families != registry_families:
        missing = sorted(controller_families - registry_families)
        extra = sorted(registry_families - controller_families)
        raise FamilyMaturityStop(f"STOP_FAMILY_COVERAGE_DRIFT:missing={missing}:extra={extra}")
