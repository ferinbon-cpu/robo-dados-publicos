from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "config" / "codex_engineer_policy.v1.json"

PASS = "PASS_CODEX_ENGINEER_POLICY"


class CodexEngineerPolicyError(RuntimeError):
    pass


def _require(actual, expected, code: str) -> None:
    if actual != expected:
        raise CodexEngineerPolicyError(code)


def validate_policy(path: Path = POLICY) -> dict:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise CodexEngineerPolicyError("CODEX_POLICY_UNREADABLE") from exc

    _require(policy.get("schema"), "ROBO_DADOS_PUBLICOS_CODEX_ENGINEER_POLICY_V1", "CODEX_POLICY_SCHEMA")
    _require(policy.get("mode"), "PR_ENGINEER", "CODEX_MODE")
    _require(policy.get("backend"), "CODEX_CLOUD_CHATGPT_ACCOUNT", "CODEX_BACKEND")
    _require(policy.get("default_decision"), "BLOCK", "CODEX_DEFAULT_DECISION")
    _require(policy.get("direct_main_write_allowed"), False, "CODEX_DIRECT_MAIN_WRITE")
    _require(policy.get("self_merge_allowed"), False, "CODEX_SELF_MERGE")
    _require(policy.get("github_secrets_required"), [], "CODEX_GITHUB_SECRETS")
    _require(policy.get("openai_api_key_required"), False, "CODEX_API_KEY")
    _require(policy.get("remote_data_credentials_exposed_to_agent"), False, "CODEX_REMOTE_DATA_CREDENTIALS")
    _require(policy.get("drive_credentials_exposed_to_agent"), False, "CODEX_DRIVE_CREDENTIALS")

    blocked = set(policy.get("blocked_capabilities") or [])
    required_blocked = {
        "source_collection_live",
        "drive_read_with_operational_credentials",
        "drive_write",
        "publication",
        "overwrite",
        "replace",
        "delete",
        "schedule",
        "recurrence",
        "branch_protection_change",
        "ruleset_change",
        "secret_read",
        "secret_create",
        "secret_update",
        "secret_delete",
        "self_authorize_t2",
        "self_authorize_t3",
        "financial_identity_promotion",
        "mde_or_fundeb_compliance_conclusion",
    }
    if not required_blocked.issubset(blocked):
        raise CodexEngineerPolicyError("CODEX_BLOCKED_CAPABILITIES_DRIFT")

    required = set(policy.get("required_before_pr_ready") or [])
    expected_commands = {
        "read_AGENTS.md",
        "read_config/automation_policy.v1.json",
        "read_config/codex_engineer_policy.v1.json",
        "run_python_scripts/github_preflight.py",
        "run_python_scripts/github_automation_policy_gate.py",
        "run_python_scripts/github_codex_engineer_policy_gate.py",
        "run_python_-m_compileall_-q_.",
        "run_python_-m_unittest_discover_-s_tests_-v",
        "run_python_main.py_selftest",
    }
    if not expected_commands.issubset(required):
        raise CodexEngineerPolicyError("CODEX_REQUIRED_VALIDATION_DRIFT")

    pr = policy.get("pull_request_contract") or {}
    _require(pr.get("branch_required"), True, "CODEX_BRANCH_REQUIRED")
    _require(pr.get("protected_main_required"), True, "CODEX_PROTECTED_MAIN")
    _require(pr.get("required_status_checks_remain_authoritative"), True, "CODEX_STATUS_CHECKS")
    _require(pr.get("report_unrun_checks_as_unobserved"), True, "CODEX_UNRUN_CHECKS")
    _require(pr.get("fabricated_run_ids_or_hashes_forbidden"), True, "CODEX_FABRICATED_EVIDENCE")
    _require(pr.get("remote_effects_must_be_declared"), True, "CODEX_REMOTE_EFFECTS")
    _require(pr.get("blocked_items_must_be_listed"), True, "CODEX_BLOCKED_ITEMS")

    first_mission = ROOT / str(policy.get("first_mission") or "")
    if not first_mission.is_file():
        raise CodexEngineerPolicyError("CODEX_FIRST_MISSION_MISSING")

    return {
        "status": PASS,
        "mode": policy["mode"],
        "backend": policy["backend"],
        "github_secrets_required": 0,
        "remote_data_credentials_exposed_to_agent": False,
        "drive_credentials_exposed_to_agent": False,
        "blocked_capability_count": len(blocked),
        "first_mission": str(first_mission.relative_to(ROOT)),
    }


def main() -> int:
    try:
        result = validate_policy()
    except CodexEngineerPolicyError as exc:
        print(f"STOP_CODEX_ENGINEER_POLICY:{exc}")
        return 13
    print(result["status"])
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
