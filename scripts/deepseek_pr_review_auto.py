#!/usr/bin/env python3
"""Automatic read-only DeepSeek PR review after trusted CI completion.

The worker is loaded from the default branch via `workflow_run`, never checks out
or executes pull-request code, and makes no GitHub/Drive mutations. The validated
review is written only to local runtime files consumed by the Actions job summary.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.automation.deepseek_review import (  # noqa: E402
    DeepSeekClient,
    DeepSeekReviewError,
    build_context_pack,
    render_markdown,
)

POLICY_PATH = ROOT / "config/deepseek_auto_review_policy.v1.json"
PASS_AUTO = "PASS_DEEPSEEK_AUTOMATIC_PR_REVIEW_READONLY"
SKIP_NOT_OPEN = "SKIP_DEEPSEEK_AUTOMATIC_PR_NOT_OPEN"
SKIP_DRAFT = "SKIP_DEEPSEEK_AUTOMATIC_PR_DRAFT"


def _stop(code: str) -> None:
    raise DeepSeekReviewError(f"STOP_DEEPSEEK_AUTO_{code}")


def load_auto_policy(path: str | Path = POLICY_PATH) -> dict[str, Any]:
    try:
        policy = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise DeepSeekReviewError("STOP_DEEPSEEK_AUTO_INVALID_POLICY") from exc
    if policy.get("schema") != "ROBO_DADOS_PUBLICOS_DEEPSEEK_AUTO_REVIEW_POLICY_V1":
        _stop("INVALID_POLICY")
    trigger = policy.get("trigger_contract")
    perms = policy.get("github_permissions")
    api = policy.get("api")
    if not isinstance(trigger, dict) or not isinstance(perms, dict) or not isinstance(api, dict):
        _stop("INVALID_POLICY")
    if trigger.get("event") != "workflow_run":
        _stop("INVALID_POLICY")
    if trigger.get("upstream_workflow_name") != "CI offline 0.8.0 candidate M7":
        _stop("INVALID_POLICY")
    if trigger.get("same_repository_head_required") is not True:
        _stop("INVALID_POLICY")
    if trigger.get("checkout_default_branch_only") is not True:
        _stop("INVALID_POLICY")
    if trigger.get("execute_pull_request_code") is not False:
        _stop("INVALID_POLICY")
    if trigger.get("pull_request_target") is not False:
        _stop("INVALID_POLICY")
    if trigger.get("schedule") is not False or trigger.get("recurrence") is not False:
        _stop("INVALID_POLICY")
    if perms != {"contents": "read", "pull_requests": "read", "issues": "write"}:
        _stop("INVALID_POLICY")
    allowed = api.get("allowed_models")
    if not isinstance(allowed, list) or api.get("default_model") not in allowed:
        _stop("INVALID_POLICY")
    if policy.get("secret_contract", {}).get("github_secret_name") != "DEEPSEEK_API_KEY":
        _stop("INVALID_POLICY")
    return policy


def _github_request(
    url: str,
    token: str,
    *,
    accept: str = "application/vnd.github+json",
) -> bytes:
    if not token:
        _stop("GITHUB_TOKEN_MISSING")
    headers = {
        "Accept": accept,
        "Authorization": f"Bearer {token}",
        "User-Agent": "robo-dados-publicos-deepseek-auto/0.8.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    req = request.Request(url, method="GET", headers=headers)
    try:
        with request.urlopen(req, timeout=60) as response:
            return response.read()
    except error.HTTPError as exc:
        raise DeepSeekReviewError(f"STOP_DEEPSEEK_AUTO_GITHUB_HTTP_{exc.code}") from exc
    except (error.URLError, TimeoutError, OSError) as exc:
        raise DeepSeekReviewError("STOP_DEEPSEEK_AUTO_GITHUB_TRANSPORT") from exc


def fetch_pr(repository: str, pr_number: int, token: str) -> tuple[dict[str, Any], str]:
    if "/" not in repository or pr_number <= 0:
        _stop("INVALID_PR_REFERENCE")
    base = f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
    meta_raw = _github_request(base, token)
    diff_raw = _github_request(base, token, accept="application/vnd.github.v3.diff")
    try:
        meta = json.loads(meta_raw.decode("utf-8"))
        diff = diff_raw.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as exc:
        raise DeepSeekReviewError("STOP_DEEPSEEK_AUTO_INVALID_GITHUB_RESPONSE") from exc
    if not isinstance(meta, dict):
        _stop("INVALID_GITHUB_RESPONSE")
    return meta, diff


def validate_same_repo_head(meta: dict[str, Any], *, repository: str, expected_head_sha: str) -> None:
    head = meta.get("head")
    if not isinstance(head, dict):
        _stop("INVALID_PR_HEAD")
    repo = head.get("repo")
    if not isinstance(repo, dict) or repo.get("full_name") != repository:
        _stop("FORK_OR_FOREIGN_HEAD_BLOCKED")
    if head.get("sha") != expected_head_sha:
        _stop("HEAD_SHA_MISMATCH")


# Compatibility-only formatters retained for the existing focused tests. They
# are not used by the automatic execution path and perform no remote effects.
def comment_marker(head_sha: str) -> str:
    return f"<!-- deepseek-auto-review:{head_sha} -->"


def build_comment(review: dict[str, Any], *, head_sha: str, model: str, upstream_conclusion: str) -> str:
    body = render_markdown(review)
    return (
        f"{comment_marker(head_sha)}\n"
        "## DeepSeek automatic review\n\n"
        f"Reviewed head: `{head_sha}`  \n"
        f"Model: `{model}`  \n"
        f"Upstream CI: `{upstream_conclusion}`\n\n"
        f"{body}"
        "\n---\n"
        "Automated review only. It cannot write code, merge, access Drive, or publish data.\n"
    )


def build_report(review: dict[str, Any], *, head_sha: str, model: str, upstream_conclusion: str) -> str:
    body = render_markdown(review)
    return (
        "## DeepSeek automatic review\n\n"
        f"Reviewed head: `{head_sha}`  \n"
        f"Model: `{model}`  \n"
        f"Upstream CI: `{upstream_conclusion}`\n\n"
        f"{body}"
        "\n---\n"
        "Automatic read-only review. No code, PR, Drive, source, or publication write occurred.\n"
    )


def write_outputs(output: Path, summary_path: Path, body: str, summary: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(body, encoding="utf-8")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--expected-head-sha", required=True)
    parser.add_argument("--upstream-conclusion", required=True)
    parser.add_argument("--model")
    parser.add_argument("--output", default="runtime/deepseek_auto_review.md")
    parser.add_argument("--summary-json", default="runtime/deepseek_auto_review_summary.json")
    args = parser.parse_args()

    try:
        policy = load_auto_policy()
        model = args.model or policy["api"]["default_model"]
        if model not in policy["api"]["allowed_models"]:
            _stop("MODEL_NOT_ALLOWED")
        github_token = os.getenv("GITHUB_TOKEN") or ""
        meta, diff = fetch_pr(args.repository, args.pr_number, github_token)
        validate_same_repo_head(meta, repository=args.repository, expected_head_sha=args.expected_head_sha)

        if meta.get("state") != "open":
            print(SKIP_NOT_OPEN)
            return 0
        if meta.get("draft") is True:
            print(SKIP_DRAFT)
            return 0

        api_key = os.getenv("DEEPSEEK_API_KEY") or ""
        if not api_key:
            _stop("API_KEY_MISSING")
        context = build_context_pack(
            pr_title=str(meta.get("title") or ""),
            pr_body=str(meta.get("body") or ""),
            pr_diff=diff,
            policy=policy,
        )
        review = DeepSeekClient(api_key=api_key, policy=policy).review(context, model=model)
        report = build_report(
            review,
            head_sha=args.expected_head_sha,
            model=model,
            upstream_conclusion=args.upstream_conclusion,
        )
        summary = {
            "status": PASS_AUTO,
            "model": model,
            "head_sha": args.expected_head_sha,
            "context_sha256": context.sha256,
            "context_chars": context.chars,
            "context_truncated": context.truncated,
            "deepseek_requests": 1,
            "github_reads": 2,
            "github_writes": 0,
            "drive_reads": 0,
            "drive_writes": 0,
            "publication": False,
            "verdict": review["verdict"],
        }
        write_outputs(Path(args.output), Path(args.summary_json), report, summary)
        print(PASS_AUTO)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 0
    except DeepSeekReviewError as exc:
        print(str(exc), file=sys.stderr)
        return 13


if __name__ == "__main__":
    raise SystemExit(main())
