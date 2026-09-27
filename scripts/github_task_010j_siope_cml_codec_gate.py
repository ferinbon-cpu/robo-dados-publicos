#!/usr/bin/env python3
"""Fail-closed static gate for the T0-only TASK 010J decoder surface."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "siope_2025_cml_czip_codec_contract.v1.json"
SURFACES = (
    ROOT / "robo_dados_publicos" / "sources" / "siope_cml_codec.py",
    ROOT / "scripts" / "inspect_siope_cml_czip_offline.py",
)
ALLOWED_IMPORT_ROOTS = {
    "__future__", "argparse", "cryptography", "dataclasses", "hashlib", "io", "json",
    "pathlib", "robo_dados_publicos", "stat", "sys", "zipfile",
}
FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp", "cffi", "ctypes", "ftplib", "httpx", "requests", "socket",
    "subprocess", "urllib",
}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "system", "popen", "run", "call", "check_call", "check_output"}
EXPECTED_STATE = {
    "release_0_7_0": "ACTIVE",
    "release_0_8_0": "CANDIDATE",
    "year_2025": "PROVEN_STRUCTURAL_RECENT",
    "S1_NUM_POPU": "NOT_PROVEN",
    "S2_FINANCIAL_ALIAS_BRIDGE": "NOT_PROVEN",
    "annual_closure_status": "UNKNOWN",
    "semantic_comparability_status": "UNKNOWN",
    "gold_metrics_status": "UNKNOWN/BLOCKED",
    "closed_annual_series": "2016-2024",
    "year_2026": "UNPROVEN_CURRENT_YEAR",
}


def _fail(message: str) -> None:
    raise SystemExit(f"TASK_010J_GATE_FAIL: {message}")


def _class_default(tree: ast.AST, class_name: str, field_name: str) -> float | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for statement in node.body:
                if (
                    isinstance(statement, ast.AnnAssign)
                    and isinstance(statement.target, ast.Name)
                    and statement.target.id == field_name
                    and isinstance(statement.value, ast.Constant)
                ):
                    return statement.value.value
    return None


def main() -> int:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("schema") != "SIOPE_2025_CML_CZIP_CODEC_CONTRACT_V1":
        _fail("canonical contract schema drift")
    if contract.get("canonical_state") != EXPECTED_STATE:
        _fail("S1/S2, closure, Gold, annual-series, release or 2026 state promotion")
    if contract.get("network_authorized") is not False or contract.get("binary_execution_authorized") is not False:
        _fail("network or execution authorization expanded")
    stream = contract.get("streaming_contract", {})
    if stream.get("read_chunk_size_bytes") != 1025 or stream.get("partial_tail_advances_carried_cv") is not False:
        _fail("pinned streaming contract drift")
    for path in SURFACES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if path.name == "siope_cml_codec.py" and (
            _class_default(tree, "OuterZipLimits", "max_compression_ratio") != 100.0
            or _class_default(tree, "InnerZipLimits", "max_compression_ratio") != 150.0
        ):
            _fail("outer/inner compression-ratio policies are not explicitly pinned to 100/150")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                roots = {(node.module or "").split(".")[0]}
            else:
                roots = set()
            if roots & FORBIDDEN_IMPORT_ROOTS:
                _fail(f"forbidden import in {path.name}: {sorted(roots & FORBIDDEN_IMPORT_ROOTS)}")
            if roots - ALLOWED_IMPORT_ROOTS:
                _fail(f"import outside allowlist in {path.name}: {sorted(roots - ALLOWED_IMPORT_ROOTS)}")
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr if isinstance(node.func, ast.Attribute) else ""
                if name in FORBIDDEN_CALLS:
                    _fail(f"execution/subprocess-like call in {path.name}: {name}")
    workflows = "\n".join(path.read_text(encoding="utf-8").lower() for path in (ROOT / ".github" / "workflows").glob("*010j*"))
    if "schedule:" in workflows or "recurrence" in workflows:
        _fail("schedule or recurrence enabled")
    print("TASK_010J_GATE_PASS: pinned literal offline decoder; semantic promotions remain blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
