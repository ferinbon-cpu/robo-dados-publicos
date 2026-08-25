#!/usr/bin/env python3
"""Fail-closed preflight for the SIOPE Chrome/CDP runtime dependency."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as package_version
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = "websocket-client==1.9.0"
EXPECTED_VERSION = "1.9.0"


def run_preflight() -> tuple[dict, int]:
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    try:
        installed_version = package_version("websocket-client")
    except PackageNotFoundError:
        installed_version = None

    try:
        import websocket  # type: ignore
        module_ready = callable(getattr(websocket, "create_connection", None))
    except Exception:
        module_ready = False

    checks = {
        "requirements_pin": PIN in requirements,
        "pyproject_pin": PIN in pyproject,
        "installed_version": installed_version == EXPECTED_VERSION,
        "websocket_module_ready": module_ready,
    }
    failed = sorted(key for key, value in checks.items() if not value)
    payload = {
        "gate_id": "M7_SIOPE_RUNTIME_DEPENDENCY_PREFLIGHT_0_8_0",
        "software_version": "0.8.0",
        "dependency": "websocket-client",
        "expected_version": EXPECTED_VERSION,
        "checks": checks,
        "failed_checks": failed,
        "network_called": False,
        "collection_authorized": False,
        "processing_authorized": False,
        "remote_writes": "NONE",
        "status": "PASS_M7_SIOPE_RUNTIME_DEPENDENCY_PREFLIGHT" if not failed else "STOP_M7_SIOPE_RUNTIME_DEPENDENCY_PREFLIGHT",
    }
    return payload, 0 if not failed else 36


if __name__ == "__main__":
    result, code = run_preflight()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(code)
