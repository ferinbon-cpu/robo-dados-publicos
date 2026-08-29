#!/usr/bin/env python3
"""Fail-closed T0 gate for TASK 010A's offline-only inspector."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "siope_2025_metadata_inspector_010a.v1.json"
INSPECTOR = ROOT / "robo_dados_publicos" / "sources" / "siope_2025_metadata_inspector.py"
CLI = ROOT / "scripts" / "inspect_siope_2025_metadata_offline.py"
PASS = "PASS_TASK_010A_SIOPE_METADATA_INSPECTOR_T0"
IMPORT_ALLOWLISTS = {
    "INSPECTOR": {
        "__future__", "hashlib", "json", "re", "stat", "zipfile", "dataclasses", "pathlib",
    },
    "CLI": {
        "__future__", "argparse", "sys", "pathlib",
        "robo_dados_publicos.sources.siope_2025_metadata_inspector",
    },
}


class GateError(RuntimeError):
    pass


def _stop(ok: bool, code: str) -> None:
    if not ok:
        raise GateError(f"STOP_TASK_010A_GATE_{code}")


def _validate_import_allowlist(path: Path, surface: str) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise GateError(f"STOP_TASK_010A_GATE_UNREADABLE_{surface}") from exc
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    unexpected = imported - IMPORT_ALLOWLISTS[surface]
    _stop(not unexpected, f"{surface}_IMPORT_NOT_ALLOWLISTED")


def validate(
    contract_path: Path = CONTRACT,
    inspector_path: Path = INSPECTOR,
    cli_path: Path = CLI,
) -> dict:
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise GateError("STOP_TASK_010A_GATE_UNREADABLE") from exc
    _stop(contract.get("schema") == "SIOPE_2025_METADATA_INSPECTOR_010A_V1", "SCHEMA")
    _stop(contract.get("task") == "TASK_010A" and contract.get("tier") == "T0_OFFLINE", "TASK_TIER")
    for key in ("official_acquisition_performed", "official_bytes_present", "network_enabled",
                "phase_010b_authorized", "schedule_or_recurrence_enabled", "promotions_authorized",
                "output_is_evidence"):
        _stop(contract.get(key) is False, key.upper())
    for key in ("source_get_count", "sharepoint_access_count", "drive_read_count", "drive_write_count",
                "installer_execution_count", "financial_value_queries"):
        _stop(contract.get(key) == 0, key.upper())
    _stop(contract.get("fixtures_are_synthetic_only") is True, "FIXTURES")
    expected = {
        "release_0_7_0": "ACTIVE", "release_0_8_0": "CANDIDATE",
        "year_2025": "PROVEN_STRUCTURAL_RECENT", "S1_NUM_POPU": "NOT_PROVEN",
        "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN", "annual_closure_status": "UNKNOWN",
        "semantic_comparability_status": "UNKNOWN", "gold_metrics_status": "UNKNOWN/BLOCKED",
        "closed_annual_series": "2016-2024", "year_2026": "UNPROVEN_CURRENT_YEAR",
    }
    _stop(contract.get("canonical_state") == expected, "CANONICAL_STATE")
    _stop(contract.get("next_gate") == "PREPARE_AND_REVIEW_010B_BOUNDED_REMOTE_ACQUISITION_NOT_AUTHORIZED", "NEXT_GATE")
    _validate_import_allowlist(inspector_path, "INSPECTOR")
    _validate_import_allowlist(cli_path, "CLI")
    return {"status": PASS, "tier": "T0_OFFLINE", "remote_effects": 0, "phase_010b_authorized": False}


def main() -> int:
    try:
        result = validate()
    except GateError as exc:
        print(exc)
        return 13
    print(PASS)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
