#!/usr/bin/env python3
"""Offline structural gate for TASK 004A/004B. Never invokes live transport."""

from __future__ import annotations

import json
from pathlib import Path
import re
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
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def load(path: str) -> dict:
    with (ROOT / path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise SystemExit(f"STOP_OBJECT_REQUIRED:{path}")
    return value


def _validate_present_authorization(auth: dict, preparation: dict) -> None:
    if auth.get("schema") != "SIOPE_2025_T1_FIRST_LIVE_AUTHORIZATION_V1":
        raise SystemExit("STOP_AUTH_SCHEMA")
    if auth.get("authorized") is not True:
        raise SystemExit("STOP_AUTH_NOT_AUTHORIZED")
    if auth.get("approval_kind") != "OWNER_EXPLICIT_SINGLE_BOUNDED_RUN" or auth.get("approved_by") != "ferinbon-cpu":
        raise SystemExit("STOP_AUTH_OWNER")
    if auth.get("one_shot") is not True or auth.get("max_live_runs") != 1:
        raise SystemExit("STOP_AUTH_ONE_SHOT")
    base = auth.get("authorized_base_sha")
    if not isinstance(base, str) or _SHA40.fullmatch(base) is None:
        raise SystemExit("STOP_AUTH_BASE_SHA")
    if not isinstance(auth.get("authorized_workflow_run_number"), int) or auth["authorized_workflow_run_number"] < 1:
        raise SystemExit("STOP_AUTH_RUN_NUMBER")
    if auth.get("authorized_workflow_run_attempt") != 1:
        raise SystemExit("STOP_AUTH_RUN_ATTEMPT")
    if auth.get("authorized_workflow_ref") != "refs/heads/main":
        raise SystemExit("STOP_AUTH_REF")
    if auth.get("target") != preparation.get("target"):
        raise SystemExit("STOP_AUTH_TARGET")
    effects = auth.get("effects", {})
    if effects != {
        "drive_read_count": 0,
        "drive_write_count": 0,
        "response_persistence": False,
        "bronze_silver_gold_creation": False,
        "publication": False,
        "future_batch_execution_authorized": False,
    }:
        raise SystemExit("STOP_AUTH_EFFECTS")
    if auth.get("semantic_guards") != {
        "annual_closure_status": "UNKNOWN",
        "promote_2025_to_proven": False,
        "metric_status_required": "UNKNOWN",
        "include_2026_authorized": False,
    }:
        raise SystemExit("STOP_AUTH_SEMANTICS")


def main() -> int:
    preparation = load("config/siope_2025_t1_first_live_preparation.v1.json")
    template = load("config/siope_2025_t1_first_live_authorization.template.v1.json")
    design = load("config/siope_2025_readonly_discovery_design.v1.json")
    policy = load("config/automation_policy.v1.json")
    validate_preparation_contract(preparation, design, policy)

    if template.get("authorized") is not False or template.get("authorized_base_sha") is not None:
        raise SystemExit("STOP_TEMPLATE_AUTHORIZED_OR_BASE_SET")
    if template.get("authorized_workflow_run_number") is not None:
        raise SystemExit("STOP_TEMPLATE_RUN_NUMBER_SET")
    if template.get("authorized_workflow_run_attempt") != 1 or template.get("authorized_workflow_ref") != "refs/heads/main":
        raise SystemExit("STOP_TEMPLATE_ONE_SHOT_IDENTITY")

    auth_file = ROOT / AUTH_PATH
    authorization_present = auth_file.exists()
    if authorization_present:
        _validate_present_authorization(load(AUTH_PATH), preparation)

    workflow_path = ROOT / preparation["workflow"]["path"]
    text = workflow_path.read_text(encoding="utf-8")
    required = [
        "workflow_dispatch:",
        "permissions:\n  contents: read",
        "persist-credentials: false",
        "fetch-depth: 0",
        "STOP_LIVE_NOT_AUTHORIZED",
        "--mode live",
        "--workflow-run-number",
        "--workflow-run-attempt",
        "--workflow-ref",
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
        "task_phase": "TASK_004B_READY" if authorization_present else "TASK_004A_PREPARED",
        "request_plan_count": len(plan),
        "source_get_count": 0,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "publication": False,
        "authorization_artifact_present": authorization_present,
        "workflow_manual_only": True,
        "one_shot_run_identity_required": True,
        "future_batch_execution_authorized": False,
    }
    print(PASS)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
