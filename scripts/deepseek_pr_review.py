#!/usr/bin/env python3
"""Manual/bootstrap DeepSeek PR reviewer.

Default mode is dry-run and performs no DeepSeek request. Live mode requires
both DEEPSEEK_API_KEY and the exact LIVE_DEEPSEEK_REVIEW confirmation.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robo_dados_publicos.automation.deepseek_review import (  # noqa: E402
    DeepSeekClient,
    DeepSeekReviewError,
    PASS_LIVE,
    build_context_pack,
    dry_run_summary,
    live_review_allowed,
    load_policy,
    render_markdown,
)


def _github_get(url: str, token: str | None, *, accept: str) -> bytes:
    headers = {
        "Accept": accept,
        "User-Agent": "robo-dados-publicos-deepseek-bootstrap/0.8.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, method="GET", headers=headers)
    try:
        with request.urlopen(req, timeout=60) as response:
            return response.read()
    except error.HTTPError as exc:
        raise DeepSeekReviewError(f"STOP_DEEPSEEK_GITHUB_HTTP_{exc.code}") from exc
    except (error.URLError, TimeoutError, OSError) as exc:
        raise DeepSeekReviewError("STOP_DEEPSEEK_GITHUB_TRANSPORT") from exc


def fetch_pr(repository: str, pr_number: int, token: str | None) -> tuple[dict, str]:
    if "/" not in repository or pr_number <= 0:
        raise DeepSeekReviewError("STOP_DEEPSEEK_INVALID_PR_REFERENCE")
    base = f"https://api.github.com/repos/{repository}/pulls/{pr_number}"
    meta_raw = _github_get(base, token, accept="application/vnd.github+json")
    diff_raw = _github_get(base, token, accept="application/vnd.github.v3.diff")
    try:
        meta = json.loads(meta_raw.decode("utf-8"))
        diff = diff_raw.decode("utf-8")
    except (UnicodeDecodeError, ValueError) as exc:
        raise DeepSeekReviewError("STOP_DEEPSEEK_INVALID_GITHUB_RESPONSE") from exc
    if not isinstance(meta, dict):
        raise DeepSeekReviewError("STOP_DEEPSEEK_INVALID_GITHUB_RESPONSE")
    return meta, diff


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--model")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--confirmation", default="")
    parser.add_argument("--output", default="runtime/deepseek_review.md")
    parser.add_argument("--summary-json", default="runtime/deepseek_review_summary.json")
    args = parser.parse_args()

    try:
        policy = load_policy()
        model = args.model or policy["api"]["default_model"]
        meta, diff = fetch_pr(args.repository, args.pr_number, os.getenv("GITHUB_TOKEN"))
        context = build_context_pack(
            pr_title=str(meta.get("title") or ""),
            pr_body=str(meta.get("body") or ""),
            pr_diff=diff,
            policy=policy,
        )
        output_path = Path(args.output)
        summary_path = Path(args.summary_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.parent.mkdir(parents=True, exist_ok=True)

        if not args.live:
            summary = dry_run_summary(context, model=model, policy=policy)
            output_path.write_text(
                "# DeepSeek PR Review Bootstrap\n\n"
                "Dry-run only. Context was built and redacted; no DeepSeek API "
                "request or GitHub write occurred.\n",
                encoding="utf-8",
            )
        else:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            live_review_allowed(confirmation=args.confirmation, api_key=api_key)
            review = DeepSeekClient(api_key=api_key or "", policy=policy).review(
                context, model=model
            )
            output_path.write_text(render_markdown(review), encoding="utf-8")
            summary = {
                "status": PASS_LIVE,
                "model": model,
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
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(summary["status"])
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 0
    except DeepSeekReviewError as exc:
        print(str(exc), file=sys.stderr)
        return 13


if __name__ == "__main__":
    raise SystemExit(main())
