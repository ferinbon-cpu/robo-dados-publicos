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
M8_REUSABLE = ROOT / ".github/workflows/m8-siope-historical-gold-product-output-readonly-reusable.yml"
M8_LIVE_EVIDENCE = ROOT / "docs/evidence/M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY_RUN_2_0.8.0.json"
OAUTH_BOOTSTRAP = ROOT / "scripts/oauth_bootstrap_drive.py"
M8_CAPABILITY_GATE = ROOT / "scripts/github_m8_readonly_credential_capability_gate.py"
AGENTS = ROOT / "AGENTS.md"


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def _load_live_evidence() -> dict:
    _require(M8_LIVE_EVIDENCE.is_file(), "STOP_M8_FIRST_LIVE_EVIDENCE_MISSING")
    return json.loads(M8_LIVE_EVIDENCE.read_text(encoding="utf-8"))


def run() -> dict:
    policy = load_policy(ROOT)
    structural = validate_policy(policy)
    m8 = evaluate_gate(policy, M8_GATE_ID)

    workflow = M8_WORKFLOW.read_text(encoding="utf-8")
    reusable = M8_REUSABLE.read_text(encoding="utf-8")
    oauth = OAUTH_BOOTSTRAP.read_text(encoding="utf-8")
    capability = M8_CAPABILITY_GATE.read_text(encoding="utf-8")
    agents = AGENTS.read_text(encoding="utf-8")
    evidence = _load_live_evidence()

    # Manual wrapper remains the only directly triggered M8 entry point.
    _require("workflow_dispatch:" in workflow, "STOP_M8_MANUAL_TRIGGER_MISSING")
    _require(
        "confirm_m8_siope_historical_gold_product_output_readonly" in workflow,
        "STOP_M8_EXPLICIT_CONFIRMATION_MISSING",
    )
    _require("workflow_call:" not in workflow, "STOP_M8_MANUAL_WRAPPER_HAS_WORKFLOW_CALL")
    for forbidden in ("schedule:", "workflow_run:", "pull_request:", "push:"):
        _require(forbidden not in workflow, f"STOP_M8_MANUAL_WRAPPER_AUTO_TRIGGER_{forbidden.rstrip(':').upper()}")
    _require("permissions:\n  contents: read" in workflow, "STOP_M8_GITHUB_PERMISSION_NOT_READONLY")
    _require(
        "uses: ./.github/workflows/m8-siope-historical-gold-product-output-readonly-reusable.yml" in workflow,
        "STOP_M8_REUSABLE_WORKER_NOT_CALLED",
    )
    _require("secrets: inherit" not in workflow, "STOP_M8_SECRETS_INHERIT_FORBIDDEN")
    for name in (
        "GOOGLE_DRIVE_READONLY_CLIENT_ID",
        "GOOGLE_DRIVE_READONLY_CLIENT_SECRET",
        "GOOGLE_DRIVE_READONLY_REFRESH_TOKEN",
    ):
        _require(
            f"{name}: ${{{{ secrets.{name} }}}}" in workflow,
            f"STOP_M8_MANUAL_WRAPPER_SECRET_NOT_EXPLICIT_{name}",
        )

    # Reusable worker is callable but has no independent automatic trigger.
    _require("workflow_call:" in reusable, "STOP_M8_REUSABLE_WORKFLOW_CALL_MISSING")
    _require("workflow_dispatch:" not in reusable, "STOP_M8_REUSABLE_HAS_MANUAL_TRIGGER")
    for forbidden in ("schedule:", "workflow_run:", "pull_request:", "push:"):
        _require(forbidden not in reusable, f"STOP_M8_REUSABLE_AUTO_TRIGGER_{forbidden.rstrip(':').upper()}")
    _require("permissions:\n  contents: read" in reusable, "STOP_M8_REUSABLE_PERMISSION_NOT_READONLY")
    _require("secrets: inherit" not in reusable, "STOP_M8_REUSABLE_SECRETS_INHERIT_FORBIDDEN")
    for name in (
        "GOOGLE_DRIVE_READONLY_CLIENT_ID",
        "GOOGLE_DRIVE_READONLY_CLIENT_SECRET",
        "GOOGLE_DRIVE_READONLY_REFRESH_TOKEN",
    ):
        _require(f"      {name}:\n        required: true" in reusable, f"STOP_M8_REUSABLE_SECRET_CONTRACT_{name}")
    _require(
        "GOOGLE_DRIVE_CLIENT_ID: ${{ secrets.GOOGLE_DRIVE_READONLY_CLIENT_ID }}" in reusable,
        "STOP_M8_READONLY_CLIENT_ID_NOT_WIRED",
    )
    _require(
        "GOOGLE_DRIVE_CLIENT_SECRET: ${{ secrets.GOOGLE_DRIVE_READONLY_CLIENT_SECRET }}" in reusable,
        "STOP_M8_READONLY_CLIENT_SECRET_NOT_WIRED",
    )
    _require(
        "GOOGLE_DRIVE_REFRESH_TOKEN: ${{ secrets.GOOGLE_DRIVE_READONLY_REFRESH_TOKEN }}" in reusable,
        "STOP_M8_READONLY_REFRESH_TOKEN_NOT_WIRED",
    )
    _require("${{ secrets.GOOGLE_DRIVE_REFRESH_TOKEN }}" not in reusable, "STOP_M8_BROAD_REFRESH_TOKEN_STILL_BOUND")
    _require("${{ secrets.GOOGLE_DRIVE_CLIENT_ID }}" not in reusable, "STOP_M8_BROAD_CLIENT_ID_STILL_BOUND")
    _require("${{ secrets.GOOGLE_DRIVE_CLIENT_SECRET }}" not in reusable, "STOP_M8_BROAD_CLIENT_SECRET_STILL_BOUND")

    proof_call = "python scripts/github_m8_readonly_credential_capability_gate.py"
    live_step = "- name: Reler 9 Gold e gerar bundle local"
    _require(proof_call in reusable, "STOP_M8_RUNTIME_CAPABILITY_PROOF_MISSING")
    _require(live_step in reusable, "STOP_M8_LIVE_STEP_MISSING")
    _require(reusable.index(proof_call) < reusable.index(live_step), "STOP_M8_CAPABILITY_PROOF_NOT_BEFORE_DRIVE_READ")
    _require("https://www.googleapis.com/auth/drive.readonly" in oauth, "STOP_OAUTH_READONLY_SCOPE_NOT_SUPPORTED")
    _require("oauth_refresh_and_tokeninfo_exact" in capability, "STOP_M8_RUNTIME_SCOPE_PROOF_NOT_EXACT")
    _require("www.googleapis.com/drive/" not in capability, "STOP_M8_CAPABILITY_GATE_CALLS_DRIVE_API")
    _require("Na dúvida, a decisão é `BLOCK`" in agents, "STOP_AGENTS_DEFAULT_DENY_MISSING")

    # First live proof remains pinned and immutable as prerequisite evidence.
    _require(evidence.get("status") == "PASS_M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY", "STOP_M8_LIVE_EVIDENCE_STATUS")
    _require(evidence.get("run", {}).get("id") == 33136736495, "STOP_M8_LIVE_EVIDENCE_RUN_ID")
    _require(evidence.get("run", {}).get("head_sha") == "8f80edcae45a373f85b84c03880842363661d870", "STOP_M8_LIVE_EVIDENCE_HEAD")
    _require(evidence.get("oauth_capability", {}).get("scope") == "https://www.googleapis.com/auth/drive.readonly", "STOP_M8_LIVE_EVIDENCE_SCOPE")
    _require(evidence.get("oauth_capability", {}).get("scope_proof") == "oauth_refresh_and_tokeninfo_exact", "STOP_M8_LIVE_EVIDENCE_SCOPE_PROOF")
    _require(evidence.get("oauth_capability", {}).get("proof_occurs_before_first_drive_lookup") is True, "STOP_M8_LIVE_EVIDENCE_PROOF_ORDER")
    effects = evidence.get("bounded_effects", {})
    _require(effects.get("source_get_count") == 0, "STOP_M8_LIVE_EVIDENCE_SOURCE_GET")
    _require(effects.get("drive_lookup_count") == 9, "STOP_M8_LIVE_EVIDENCE_LOOKUP_COUNT")
    _require(effects.get("drive_download_count") == 9, "STOP_M8_LIVE_EVIDENCE_DOWNLOAD_COUNT")
    _require(effects.get("drive_write_count") == 0, "STOP_M8_LIVE_EVIDENCE_WRITE_COUNT")
    _require(effects.get("publication_authorized") is False, "STOP_M8_LIVE_EVIDENCE_PUBLICATION")
    _require(effects.get("future_batch_execution_authorized") is False, "STOP_M8_LIVE_EVIDENCE_FUTURE_BATCH")
    _require(evidence.get("product", {}).get("gold_metric_observations") == 72, "STOP_M8_LIVE_EVIDENCE_OBSERVATIONS")
    _require(evidence.get("artifact", {}).get("id") == 9672319372, "STOP_M8_LIVE_EVIDENCE_ARTIFACT_ID")
    _require(
        evidence.get("artifact", {}).get("digest")
        == "sha256:a3afeed9c1449ab4806127024d044d177e76e8097894786b0e68bbbfffc60b51",
        "STOP_M8_LIVE_EVIDENCE_ARTIFACT_DIGEST",
    )

    # Reusable preparation does not lower the current no-click decision.
    _require(m8["decision"] == "BLOCK", "STOP_M8_NO_CLICK_PREMATURELY_ALLOWED")
    blockers = set(m8.get("blockers", []))
    _require("CURRENT_MANUAL_WRAPPER_REQUIRES_EXPLICIT_CONFIRMATION" in blockers, "STOP_M8_MANUAL_BLOCKER_MISSING")
    _require("MAIN_BRANCH_NOT_PROTECTED_FOR_SECRET_BEARING_AUTOMATION" in blockers, "STOP_M8_TRUST_BOUNDARY_BLOCKER_MISSING")
    _require("NO_CLICK_REQUIRES_TRUSTED_ORCHESTRATOR_REVIEW" in blockers, "STOP_M8_ORCHESTRATOR_BLOCKER_MISSING")
    _require("FIRST_LIVE_M8_READONLY_PRODUCT_GATE_NOT_YET_PROVEN" not in blockers, "STOP_M8_STALE_FIRST_LIVE_BLOCKER")

    return {
        "status": "PASS_AUTOMATION_POLICY_OFFLINE",
        "policy_status": structural["status"],
        "gate_count": structural["gate_count"],
        "default_decision": structural["default_decision"],
        "m8_no_click_decision": m8["decision"],
        "m8_no_click_reason": m8["reason"],
        "m8_blockers": m8.get("blockers", []),
        "m8_credential_capability": "READONLY_EXACT_SCOPE_FIRST_LIVE_GATE_PROVEN",
        "m8_first_live_proof_pinned": True,
        "m8_first_live_run_id": 33136736495,
        "m8_reusable_worker_present": True,
        "m8_reusable_explicit_secrets": True,
        "m8_secrets_inherit": False,
        "m8_automatic_secret_bearing_trigger_present": False,
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
