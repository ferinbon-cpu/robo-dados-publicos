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
    agents = AGENTS.read_text(encoding="utf-8")

    _require("workflow_dispatch:" in workflow, "STOP_M8_MANUAL_TRIGGER_MISSING")
    _require(
        "confirm_m8_siope_historical_gold_product_output_readonly" in workflow,
        "STOP_M8_EXPLICIT_CONFIRMATION_MISSING",
    )
    _require("permissions:\n  contents: read" in workflow, "STOP_M8_GITHUB_PERMISSION_NOT_READONLY")
    _require("GOOGLE_DRIVE_REFRESH_TOKEN" in workflow, "STOP_M8_CURRENT_REFRESH_TOKEN_BINDING_MISSING")
    _require(
        "GOOGLE_DRIVE_READONLY_REFRESH_TOKEN" not in workflow,
        "STOP_M8_POLICY_STALE_READONLY_SECRET_ALREADY_WIRED",
    )
    _require("https://www.googleapis.com/auth/drive.readonly" in oauth, "STOP_OAUTH_READONLY_SCOPE_NOT_SUPPORTED")
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
        "oauth_readonly_bootstrap_supported": True,
        "current_m8_readonly_secret_wired": False,
        "source_network_count": 0,
        "drive_read_count": 0,
        "drive_write_count": 0,
        "publication_authorized": False,
        "future_batch_execution_authorized": False,
    }


def main() -> int:
    try:
        print(json.dumps(run(), ensure_ascii=False, sort_keys=True))
    except Exception as exc:  # fail closed with stable single-line output
        print(json.dumps({"status": "STOP_AUTOMATION_POLICY_OFFLINE", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 41
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
