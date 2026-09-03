#!/usr/bin/env python3
"""Policy layer for the repository public-readiness scanner.

`github_public_readiness_audit.py` provides generic scanner primitives.  This gate
adds repository-specific, fail-closed decisions needed before public visibility:
- blank `.env.example` assignments cannot bleed into the next line;
- environment-variable *names* and explicit test non-propagation sentinels are
  treated as placeholders, not credential values;
- synthetic binary fixtures are allowlisted only by exact Git blob identity;
- the TASK 080/082 DeepSeek `workflow_run` review is closed only while its exact
  trusted-default-branch, read-only and no-PR-code trust boundary remains intact.

No matched secret value is emitted.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

import github_public_readiness_audit as base


base.ENV_ASSIGNMENT_PATTERN = re.compile(
    r"(?m)^\s*(?:export[ \t]+)?([A-Z][A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY)[A-Z0-9_]*)"
    r"[ \t]*=[ \t]*([^\s#]{16,})[ \t]*$"
)
base.PLACEHOLDER_MARKERS = tuple(base.PLACEHOLDER_MARKERS) + (
    "not-propagate",
    "must-not-propagate",
)

_original_is_placeholder = base._is_placeholder


def _is_placeholder(value: str) -> bool:
    candidate = value.strip().strip("\"'")
    if re.fullmatch(r"[A-Z][A-Z0-9_]{5,}", candidate):
        return True
    return _original_is_placeholder(value)


base._is_placeholder = _is_placeholder


def _distribution_allowlist() -> dict[str, dict]:
    if not base.ALLOWLIST_PATH.exists():
        return {}
    payload = json.loads(base.ALLOWLIST_PATH.read_text(encoding="utf-8"))
    entries = payload.get("entries") or []
    out: dict[str, dict] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        blob = str(item.get("git_blob_sha1") or "").strip().lower()
        if path and re.fullmatch(r"[0-9a-f]{40}", blob):
            out[path] = item
    return out


def _current_binary_review() -> list[dict]:
    result: list[dict] = []
    allowlist = _distribution_allowlist()
    for path in sorted(base._git("ls-files").splitlines()):
        p = base.ROOT / path
        parts = {part.lower() for part in Path(path).parts}
        if p.suffix.lower() in base.BINARY_REVIEW_SUFFIXES:
            entry = allowlist.get(path)
            if entry and p.is_file():
                blob = base._git("hash-object", "--", path).strip().lower()
                if blob == str(entry.get("git_blob_sha1", "")).lower():
                    continue
            result.append({
                "severity": "REVIEW",
                "detector": "DISTRIBUTION_RIGHTS_BINARY",
                "path": path,
            })
        elif parts & base.THIRD_PARTY_DIR_MARKERS:
            result.append({
                "severity": "REVIEW",
                "detector": "THIRD_PARTY_TREE",
                "path": path,
            })
    return result


base._distribution_allowlist = _distribution_allowlist
base._current_binary_review = _current_binary_review


_DEEPSEEK_AUTO_WORKFLOW = base.ROOT / ".github/workflows/deepseek-pr-review-auto.yml"
_DEEPSEEK_AUTO_POLICY = base.ROOT / "config/deepseek_auto_review_policy.v1.json"
_DEEPSEEK_AUTO_REL = ".github/workflows/deepseek-pr-review-auto.yml"
_original_workflow_findings = base._workflow_findings


def _deepseek_auto_workflow_is_exactly_bounded() -> bool:
    try:
        workflow = _DEEPSEEK_AUTO_WORKFLOW.read_text(encoding="utf-8")
        policy = json.loads(_DEEPSEEK_AUTO_POLICY.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return False

    if policy.get("schema") != "ROBO_DADOS_PUBLICOS_DEEPSEEK_AUTO_REVIEW_POLICY_V1":
        return False
    trigger = policy.get("trigger_contract") or {}
    if trigger.get("event") != "workflow_run":
        return False
    if trigger.get("upstream_workflow_name") != "CI offline 0.8.0 candidate M7":
        return False
    if trigger.get("same_repository_head_required") is not True:
        return False
    if trigger.get("checkout_default_branch_only") is not True:
        return False
    if trigger.get("execute_pull_request_code") is not False:
        return False
    if trigger.get("pull_request_target") is not False:
        return False
    if trigger.get("schedule") is not False or trigger.get("recurrence") is not False:
        return False
    if policy.get("github_permissions") != {
        "contents": "read",
        "pull_requests": "read",
    }:
        return False
    gate = policy.get("review_gate_contract") or {}
    if gate.get("model_verdict_alone_is_not_a_merge_gate") is not True:
        return False
    if gate.get("blocking_signal") != "NONEMPTY_BLOCKING_FINDINGS":
        return False
    if gate.get("full_sanitized_review_must_be_logged") is not True:
        return False

    required_text = (
        "workflow_run:",
        '"CI offline 0.8.0 candidate M7"',
        "github.event.workflow_run.event == 'pull_request'",
        "github.event.workflow_run.head_repository.full_name == github.repository",
        "ref: ${{ github.event.repository.default_branch }}",
        "persist-credentials: false",
        "contents: read",
        "pull-requests: read",
        "DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}",
        "python scripts/deepseek_pr_review_auto.py",
    )
    if any(item not in workflow for item in required_text):
        return False

    forbidden = (
        r"(?m)^\s*pull_request_target\s*:",
        r"(?m)^\s*pull_request\s*:",
        r"(?m)^\s*schedule\s*:",
        r"(?m)^\s*contents\s*:\s*write\s*$",
        r"(?m)^\s*pull-requests\s*:\s*write\s*$",
        r"(?m)^\s*issues\s*:\s*write\s*$",
        r"(?m)^\s*id-token\s*:\s*write\s*$",
    )
    if any(re.search(pattern, workflow, flags=re.I) for pattern in forbidden):
        return False
    if "secrets: inherit" in workflow.lower():
        return False

    uses = [line.strip() for line in workflow.splitlines() if line.strip().startswith("uses:")]
    if not uses:
        return False
    for line in uses:
        ref = line.rsplit("@", 1)[-1].split()[0]
        if not re.fullmatch(r"[0-9a-f]{40}", ref):
            return False

    blocked = set(policy.get("blocked_capabilities") or [])
    required_blocked = {
        "direct_main_write",
        "branch_write",
        "github_code_write",
        "github_issue_write",
        "github_pull_request_comment_write",
        "self_merge",
        "drive_read",
        "drive_write",
        "publication",
        "schedule",
        "recurrence",
    }
    return required_blocked <= blocked


def _workflow_findings() -> tuple[list[dict], list[dict]]:
    blockers, reviews = _original_workflow_findings()
    if not _deepseek_auto_workflow_is_exactly_bounded():
        return blockers, reviews
    reviews = [
        item
        for item in reviews
        if not (
            item.get("detector") == "WORKFLOW_RUN_TRIGGER"
            and item.get("path") == _DEEPSEEK_AUTO_REL
        )
    ]
    return blockers, reviews


base._workflow_findings = _workflow_findings

scan_text = base.scan_text
run = base.run
main = base.main


if __name__ == "__main__":
    raise SystemExit(main())
