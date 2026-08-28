#!/usr/bin/env python3
"""Validate automation policy and current M8 no-click blockers offline."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.automation.policy import evaluate_gate, load_policy, validate_policy


M8_GATE_ID = "M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY"
M8_WORKFLOW = ROOT / ".github/workflows/m8-siope-historical-gold-product-output-readonly-gate.yml"
OAUTH_BOOTSTRAP = ROOT / "scripts/oauth_bootstrap_drive.py"
M8_CAPABILITY_GATE = ROOT / "scripts/github_m8_readonly_credential_capability_gate.py"
AGENTS = ROOT / "AGENTS.md"


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def run() -> dict:
    policy = load_policy(ROOT)
    structural = validate_policy(policy)
    m8 = evaluate_gate(policy, M8_GATE_ID)

    workflow = M8_WORKFLOW.read_text(encoding="utf-8")
    oauth = OAUTH_BOOTSTRAP.read_text(encoding="utf-8")
    capability = M8_CAPABILITY_GATE.read_text(encoding="utf-8")
    agents = AGENTS.read_text(encoding="utf-8")

    _require("workflow_dispatch:" in workflow, "STOP_M8_MANUAL_TRIGGER_MISSING")
    _require(
        "confirm_m8_siope_historical_gold_product_output_readonly" in workflow,
        "STOP_M8_EXPLICIT_CONFIRMATION_MISSING",
    )
    _require("workflow_call:" not in workflow, "STOP_M8_WORKFLOW_CALL_PREMATURELY_ENABLED")
    _require("permissions:\n  contents: read" in workflow, "STOP_M8_GITHUB_PERMISSION_NOT_READONLY")
    _require(
        "GOOGLE_DRIVE_CLIENT_ID: ${{ secrets.GOOGLE_DRIVE_READONLY_CLIENT_ID }}" in workflow,
        "STOP_M8_READONLY_CLIENT_ID_NOT_WIRED",
    )
    _require(
        "GOOGLE_DRIVE_CLIENT_SECRET: ${{ secrets.GOOGLE_DRIVE_READONLY_CLIENT_SECRET }}" in workflow,
        "STOP_M8_READONLY_CLIENT_SECRET_NOT_WIRED",
    )
    _require(
        "GOOGLE_DRIVE_REFRESH_TOKEN: ${{ secrets.GOOGLE_DRIVE_READONLY_REFRESH_TOKEN }}" in workflow,
        "STOP_M8_READONLY_REFRESH_TOKEN_NOT_WIRED",
    )
    _require(
        "${{ secrets.GOOGLE_DRIVE_REFRESH_TOKEN }}" not in workflow,
        "STOP_M8_BROAD_REFRESH_TOKEN_STILL_BOUND",
    )
    _require(
        "${{ secrets.GOOGLE_DRIVE_CLIENT_ID }}" not in workflow,
        "STOP_M8_BROAD_CLIENT_ID_STILL_BOUND",
    )
    _require(
        "${{ secrets.GOOGLE_DRIVE_CLIENT_SECRET }}" not in workflow,
        "STOP_M8_BROAD_CLIENT_SECRET_STILL_BOUND",
    )
    proof_call = "python scripts/github_m8_readonly_credential_capability_gate.py"
    live_step = "- name: Reler 9 Gold e gerar bundle local"
    _require(proof_call in workflow, "STOP_M8_RUNTIME_CAPABILITY_PROOF_MISSING")
    _require(live_step in workflow, "STOP_M8_LIVE_STEP_MISSING")
    _require(workflow.index(proof_call) < workflow.index(live_step), "STOP_M8_CAPABILITY_PROOF_NOT_BEFORE_DRIVE_READ")
    _require("https://www.googleapis.com/auth/drive.readonly" in oauth, "STOP_OAUTH_READONLY_SCOPE_NOT_SUPPORTED")
    _require("oauth_refresh_and_tokeninfo_exact" in capability, "STOP_M8_RUNTIME_SCOPE_PROOF_NOT_EXACT")
    _require("www.googleapis.com/drive/" not in capability, "STOP_M8_CAPABILITY_GATE_CALLS_DRIVE_API")
    _require("Na dúvida, a decisão é `BLOCK`" in agents, "STOP_AGENTS_DEFAULT_DENY_MISSING")
    _require(m8["decision"] == "BLOCK", "STOP_M8_NO_CLICK_PREMATURELY_ALLOWED")

    return {
        "status": "PASS_AUTOMATION_POLICY_OFFLINE",
        "policy_status": structural["status"],
        "gate_count": structural["gate_count"],
        "default_decision": structural["default_decision"],
        "m8_no_click_decision": m8["decision"],
        "m8_no_click_reason": m8["reason"],
        "m8_blockers": m8.get("blockers", []),
        "m8_credential_capability": "READONLY_PROVISIONED_TOKENINFO_PROVEN_AWAITING_FIRST_LIVE_GATE",
        "oauth_readonly_bootstrap_supported": True,
        "current_m8_readonly_secret_wired": True,
        "readonly_runtime_capability_proof_step_present": True,
        "source_network_count": 0,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "publication_authorized": False,
        "future_batch_execution_authorized": False,
    }


def main() -> int:
    try:
        print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "STOP_AUTOMATION_POLICY_OFFLINE", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 41
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
