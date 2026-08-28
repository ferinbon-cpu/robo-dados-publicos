#!/usr/bin/env python3
"""Offline gate for TASK 004A. Never imports or invokes a live transport."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.sources.siope_2025_request_plan import materialize_request_plan  # noqa: E402
from robo_dados_publicos.sources.siope_2025_t1_authorization import (  # noqa: E402
    AUTH_PATH,
    validate_preparation_contract,
)

PASS = "PASS_SIOPE_2025_T1_PREPARATION_T0"


def load(path: str) -> dict:
    with (ROOT / path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SystemExit(f"STOP_OBJECT_REQUIRED:{path}")
    return value


def main() -> int:
    preparation = load("config/siope_2025_t1_first_live_preparation.v1.json")
    template = load("config/siope_2025_t1_first_live_authorization.template.v1.json")
    design = load("config/siope_2025_readonly_discovery_design.v1.json")
    policy = load("config/automation_policy.v1.json")
    validate_preparation_contract(preparation, design, policy)

    auth_file = ROOT / AUTH_PATH
    if auth_file.exists():
        raise SystemExit("STOP_TASK004A_AUTHORIZATION_ARTIFACT_PRESENT")
    if template.get("authorized") is not False:
        raise SystemExit("STOP_TEMPLATE_AUTHORIZED")
    if template.get("authorized_base_sha") is not None:
        raise SystemExit("STOP_TEMPLATE_BASE_SHA_SET")

    workflow_path = ROOT / preparation["workflow"]["path"]
    text = workflow_path.read_text(encoding="utf-8")
    required = [
        "workflow_dispatch:",
        "permissions:\n  contents: read",
        "persist-credentials: false",
        "fetch-depth: 0",
        "STOP_LIVE_NOT_AUTHORIZED",
        "--mode live",
        "config/siope_2025_t1_first_live_authorization.v1.json",
    ]
    for needle in required:
        if needle not in text:
            raise SystemExit(f"STOP_WORKFLOW_REQUIRED:{needle}")
    forbidden = ["schedule:", "repository_dispatch:", "workflow_run:", "workflow_call:", "push:", "pull_request:", "secrets:"]
    for needle in forbidden:
        if needle in text:
            raise SystemExit(f"STOP_WORKFLOW_TRIGGER_OR_SECRET:{needle}")

    plan = materialize_request_plan(design)
    result = {
        "status": PASS,
        "task_phase": "TASK_004A",
        "request_plan_count": len(plan),
        "live_execution_authorized": False,
        "source_get_count": 0,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "publication": False,
        "authorization_artifact_present": False,
        "workflow_manual_only": True,
        "future_batch_execution_authorized": False,
    }
    print(PASS)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
