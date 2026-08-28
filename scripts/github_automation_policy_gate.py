#!/usr/bin/env python3
"""Validate automation policy and M8 T1 no-click trust boundary offline."""
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
M8_AUTO = ROOT / ".github/workflows/m8-siope-historical-gold-product-output-readonly-auto.yml"
M8_LIVE_EVIDENCE = ROOT / "docs/evidence/M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY_RUN_2_0.8.0.json"
OAUTH_BOOTSTRAP = ROOT / "scripts/oauth_bootstrap_drive.py"
M8_CAPABILITY_GATE = ROOT / "scripts/github_m8_readonly_credential_capability_gate.py"
M8_TRUST_GATE = ROOT / "scripts/github_m8_t1_no_click_trust_boundary_gate.py"
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
    gate = next(row for row in policy["gates"] if row["id"] == M8_GATE_ID)

    workflow = M8_WORKFLOW.read_text(encoding="utf-8")
    reusable = M8_REUSABLE.read_text(encoding="utf-8")
    automatic = M8_AUTO.read_text(encoding="utf-8")
    oauth = OAUTH_BOOTSTRAP.read_text(encoding="utf-8")
    capability = M8_CAPABILITY_GATE.read_text(encoding="utf-8")
    trust_gate = M8_TRUST_GATE.read_text(encoding="utf-8")
    agents = AGENTS.read_text(encoding="utf-8")
    evidence = _load_live_evidence()

    # Manual backstop remains explicit and cannot auto-trigger.
    _require("workflow_dispatch:" in workflow, "STOP_M8_MANUAL_TRIGGER_MISSING")
    _require("confirm_m8_siope_historical_gold_product_output_readonly" in workflow, "STOP_M8_EXPLICIT_CONFIRMATION_MISSING")
    _require("workflow_call:" not in workflow, "STOP_M8_MANUAL_WRAPPER_HAS_WORKFLOW_CALL")
    for forbidden in ("schedule:", "workflow_run:", "pull_request:", "push:"):
        _require(forbidden not in workflow, f"STOP_M8_MANUAL_WRAPPER_AUTO_TRIGGER_{forbidden.rstrip(':').upper()}")
    _require("permissions:\n  contents: read" in workflow, "STOP_M8_GITHUB_PERMISSION_NOT_READONLY")
    _require("secrets: inherit" not in workflow, "STOP_M8_SECRETS_INHERIT_FORBIDDEN")

    # Worker remains workflow_call-only and binds only the dedicated readonly secrets.
    _require("workflow_call:" in reusable, "STOP_M8_REUSABLE_WORKFLOW_CALL_MISSING")
    for forbidden in ("workflow_dispatch:", "schedule:", "workflow_run:", "pull_request:", "push:"):
        _require(forbidden not in reusable, f"STOP_M8_REUSABLE_FORBIDDEN_TRIGGER_{forbidden.rstrip(':').upper()}")
    _require("permissions:\n  contents: read" in reusable, "STOP_M8_REUSABLE_PERMISSION_NOT_READONLY")
    _require("secrets: inherit" not in reusable, "STOP_M8_REUSABLE_SECRETS_INHERIT_FORBIDDEN")
    for name in (
        "GOOGLE_DRIVE_READONLY_CLIENT_ID",
        "GOOGLE_DRIVE_READONLY_CLIENT_SECRET",
        "GOOGLE_DRIVE_READONLY_REFRESH_TOKEN",
    ):
        _require(f"      {name}:\n        required: true" in reusable, f"STOP_M8_REUSABLE_SECRET_CONTRACT_{name}")
        _require(f"{name}: ${{{{ secrets.{name} }}}}" in workflow, f"STOP_M8_MANUAL_SECRET_NOT_EXPLICIT_{name}")
        _require(f"{name}: ${{{{ secrets.{name} }}}}" in automatic, f"STOP_M8_AUTO_SECRET_NOT_EXPLICIT_{name}")
    _require("${{ secrets.GOOGLE_DRIVE_REFRESH_TOKEN }}" not in reusable + workflow + automatic, "STOP_M8_BROAD_REFRESH_TOKEN_BOUND")
    _require("secrets: inherit" not in automatic, "STOP_M8_AUTO_SECRETS_INHERIT_FORBIDDEN")

    # Automatic caller is push-only on protected main, bounded by paths and a secretless trust job.
    _require("push:" in automatic, "STOP_M8_AUTO_PUSH_TRIGGER_MISSING")
    for forbidden in ("workflow_dispatch:", "workflow_run:", "pull_request:", "schedule:"):
        _require(forbidden not in automatic, f"STOP_M8_AUTO_FORBIDDEN_TRIGGER_{forbidden.rstrip(':').upper()}")
    _require("      - main" in automatic, "STOP_M8_AUTO_MAIN_BRANCH_MISSING")
    _require("paths:" in automatic, "STOP_M8_AUTO_PATH_BOUNDARY_MISSING")
    _require("docs/evidence/M8_T1_NO_CLICK_ACTIVATION_0.8.0.json" in automatic, "STOP_M8_AUTO_ACTIVATION_PATH_MISSING")
    _require("docs/evidence/M7_SIOPE_*.json" in automatic, "STOP_M8_AUTO_M7_EVIDENCE_PATH_MISSING")
    _require("permissions:\n  contents: read" in automatic, "STOP_M8_AUTO_PERMISSION_NOT_READONLY")
    _require("needs: trust-boundary" in automatic, "STOP_M8_AUTO_WORKER_NOT_GATED_BY_TRUST_BOUNDARY")
    _require("python scripts/github_automation_policy_gate.py" in automatic, "STOP_M8_AUTO_POLICY_PREFLIGHT_MISSING")
    _require("python scripts/github_m8_t1_no_click_trust_boundary_gate.py" in automatic, "STOP_M8_AUTO_TRUST_GATE_MISSING")
    _require("${{ github.ref_protected }}" in automatic, "STOP_M8_AUTO_REF_PROTECTED_CONTEXT_MISSING")
    _require("${{ github.event.repository.private }}" in automatic, "STOP_M8_AUTO_REPOSITORY_VISIBILITY_CONTEXT_MISSING")

    # Existing OAuth exact-scope proof remains before any Drive read in the reusable worker.
    proof_call = "python scripts/github_m8_readonly_credential_capability_gate.py"
    live_step = "- name: Reler 9 Gold e gerar bundle local"
    _require(proof_call in reusable and live_step in reusable, "STOP_M8_RUNTIME_PROOF_OR_LIVE_STEP_MISSING")
    _require(reusable.index(proof_call) < reusable.index(live_step), "STOP_M8_CAPABILITY_PROOF_NOT_BEFORE_DRIVE_READ")
    _require("https://www.googleapis.com/auth/drive.readonly" in oauth, "STOP_OAUTH_READONLY_SCOPE_NOT_SUPPORTED")
    _require("oauth_refresh_and_tokeninfo_exact" in capability, "STOP_M8_RUNTIME_SCOPE_PROOF_NOT_EXACT")
    _require("www.googleapis.com/drive/" not in capability, "STOP_M8_CAPABILITY_GATE_CALLS_DRIVE_API")
    _require("STOP_M8_T1_MAIN_NOT_PROTECTED" in trust_gate, "STOP_M8_TRUST_GATE_MAIN_PROTECTION_CHECK_MISSING")
    _require("Na dúvida, a decisão é `BLOCK`" in agents, "STOP_AGENTS_DEFAULT_DENY_MISSING")

    # First live manual proof is still immutable prerequisite evidence.
    _require(evidence.get("status") == "PASS_M8_SIOPE_HISTORICAL_GOLD_PRODUCT_OUTPUT_READONLY", "STOP_M8_LIVE_EVIDENCE_STATUS")
    _require(evidence.get("run", {}).get("id") == 33136736495, "STOP_M8_LIVE_EVIDENCE_RUN_ID")
    _require(evidence.get("oauth_capability", {}).get("scope") == "https://www.googleapis.com/auth/drive.readonly", "STOP_M8_LIVE_EVIDENCE_SCOPE")
    effects = evidence.get("bounded_effects", {})
    _require(effects.get("source_get_count") == 0, "STOP_M8_LIVE_EVIDENCE_SOURCE_GET")
    _require(effects.get("drive_lookup_count") == 9, "STOP_M8_LIVE_EVIDENCE_LOOKUP_COUNT")
    _require(effects.get("drive_download_count") == 9, "STOP_M8_LIVE_EVIDENCE_DOWNLOAD_COUNT")
    _require(effects.get("drive_write_count") == 0, "STOP_M8_LIVE_EVIDENCE_WRITE_COUNT")
    _require(effects.get("publication_authorized") is False, "STOP_M8_LIVE_EVIDENCE_PUBLICATION")
    _require(evidence.get("product", {}).get("gold_metric_observations") == 72, "STOP_M8_LIVE_EVIDENCE_OBSERVATIONS")

    # Human-created public/protected boundary is pinned before policy can return AUTO_ALLOWED.
    _require(m8["decision"] == "AUTO_ALLOWED", "STOP_M8_T1_AUTO_NOT_ALLOWED_AFTER_TRUST_BOUNDARY")
    _require(gate.get("credential_capability") == "READ_ONLY_PROVEN", "STOP_M8_T1_POLICY_CREDENTIAL_CAPABILITY")
    _require(gate.get("human_authorization") == "OWNER_COMPLETED_PUBLIC_REPO_AND_ACTIVE_MAIN_RULESET_FOR_T1_NO_CLICK", "STOP_M8_T1_HUMAN_AUTHORIZATION")
    trust = gate.get("trust_boundary_observation") or {}
    _require(trust.get("repository_visibility") == "public", "STOP_M8_T1_POLICY_REPOSITORY_NOT_PUBLIC")
    _require(trust.get("main_protected") is True, "STOP_M8_T1_POLICY_MAIN_NOT_PROTECTED")
    _require(trust.get("ruleset_id") == 21728151, "STOP_M8_T1_POLICY_RULESET_ID")
    _require(trust.get("ruleset_name") == "main-protection-v1", "STOP_M8_T1_POLICY_RULESET_NAME")
    _require(trust.get("ruleset_enforcement") == "active", "STOP_M8_T1_POLICY_RULESET_NOT_ACTIVE")
    _require(trust.get("bypass_actors") == [], "STOP_M8_T1_POLICY_BYPASS_ACTORS")
    _require(trust.get("required_status_checks") == ["Audit full Git history safely", "Validar sem Drive"], "STOP_M8_T1_POLICY_REQUIRED_CHECKS")
    _require(gate.get("blockers") == [], "STOP_M8_T1_STALE_BLOCKERS")

    return {
        "status": "PASS_AUTOMATION_POLICY_OFFLINE",
        "policy_status": structural["status"],
        "gate_count": structural["gate_count"],
        "default_decision": structural["default_decision"],
        "m8_no_click_decision": m8["decision"],
        "m8_no_click_reason": m8["reason"],
        "m8_blockers": gate.get("blockers", []),
        "m8_credential_capability": gate["credential_capability"],
        "m8_first_live_proof_pinned": True,
        "m8_first_live_run_id": 33136736495,
        "m8_reusable_worker_present": True,
        "m8_reusable_explicit_secrets": True,
        "m8_secrets_inherit": False,
        "m8_automatic_secret_bearing_trigger_present": True,
        "m8_trust_boundary_public": True,
        "m8_trust_boundary_main_protected": True,
        "m8_ruleset_id": 21728151,
        "m8_ruleset_active": True,
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
