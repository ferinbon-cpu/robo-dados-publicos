#!/usr/bin/env python3
"""Fail-closed audit before changing this repository from private to public.

The scanner is intentionally local/offline: it reads the checked-out Git history and
current workflow files, never calls Drive/source systems, and never prints matched
secret values. Findings contain only detector names, paths, blob OIDs and line
numbers so the report itself is safe to retain as evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
MAX_BLOB_BYTES = 2_000_000
ALLOWLIST_PATH = ROOT / "config" / "public_distribution_allowlist.v1.json"

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("GITHUB_TOKEN_PREFIX", re.compile(r"gh[pousr]_[A-Za-z0-9]{30,255}")),
    ("GITHUB_FINE_GRAINED_PAT", re.compile(r"github_pat_[A-Za-z0-9_]{40,255}")),
    ("GOOGLE_API_KEY", re.compile(r"AIza[0-9A-Za-z_-]{30,50}")),
    ("GOOGLE_OAUTH_CLIENT_SECRET", re.compile(r"GOCSPX-[0-9A-Za-z_-]{20,}")),
    ("AWS_ACCESS_KEY_ID", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("SLACK_TOKEN", re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}")),
    (
        "PRIVATE_KEY_HEADER",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    ),
)

# Generic secret assignments are intentionally conservative.  The first pattern
# only treats literal quoted values as possible secrets; the second is limited to
# upper-case environment variables.  This avoids classifying ordinary Python
# variable-to-variable assignments (for example credentials.client_secret) as a
# leak while still catching common .env/JSON/source hardcoding mistakes.
QUOTED_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)[\"']?\b(refresh_token|client_secret|password|api[_-]?key)\b[\"']?"
    r"\s*[:=]\s*([\"'])([^\"'\r\n]{16,})\2"
)
ENV_ASSIGNMENT_PATTERN = re.compile(
    r"(?m)^\s*(?:export\s+)?([A-Z][A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY)[A-Z0-9_]*)"
    r"\s*=\s*([^\s#]{16,})\s*$"
)

SUSPICIOUS_BASENAMES = re.compile(
    r"(?i)^(?:\.env(?:\..+)?|credentials.*\.json|client_secret.*\.json|"
    r"tokens?\.json|application_default_credentials\.json)$"
)
SUSPICIOUS_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
BINARY_REVIEW_SUFFIXES = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".tgz",
}
THIRD_PARTY_DIR_MARKERS = {"vendor", "third_party", "third-party", "external"}
PLACEHOLDER_MARKERS = (
    "example", "fixture", "placeholder", "changeme", "your_", "your-", "${", "<", ">",
    "***", "xxxxx", "dummy", "sample", "not-a-secret", "redacted", "test-value", "test_value",
)


def _git(*args: str, input_text: str | None = None) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"STOP_PUBLIC_READINESS_GIT_{args[0].upper()}: {proc.stderr.strip()}")
    return proc.stdout


def _is_placeholder(value: str) -> bool:
    lowered = value.lower()
    if any(marker in lowered for marker in PLACEHOLDER_MARKERS):
        return True
    stripped = value.strip("_-.")
    return not stripped or len(set(stripped.lower())) <= 2


def scan_text(text: str) -> list[tuple[str, int]]:
    """Return only detector code and 1-based line; never return the matched value."""
    findings: list[tuple[str, int]] = []
    for code, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            findings.append((code, text.count("\n", 0, match.start()) + 1))
    for match in QUOTED_ASSIGNMENT_PATTERN.finditer(text):
        value = match.group(3)
        if not _is_placeholder(value):
            findings.append(
                ("SENSITIVE_LITERAL_" + match.group(1).upper().replace("-", "_"),
                 text.count("\n", 0, match.start()) + 1)
            )
    for match in ENV_ASSIGNMENT_PATTERN.finditer(text):
        value = match.group(2).strip("\"'")
        if not _is_placeholder(value):
            findings.append(
                ("SENSITIVE_ENV_ASSIGNMENT", text.count("\n", 0, match.start()) + 1)
            )
    return sorted(set(findings))


def _object_inventory() -> list[tuple[str, int, str]]:
    objects = _git("rev-list", "--objects", "--all")
    checked = _git(
        "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize) %(rest)",
        input_text=objects,
    )
    inventory: list[tuple[str, int, str]] = []
    for line in checked.splitlines():
        parts = line.split(" ", 3)
        if len(parts) < 3 or parts[1] != "blob":
            continue
        oid = parts[0]
        size = int(parts[2])
        path = parts[3] if len(parts) == 4 else "<unknown>"
        inventory.append((oid, size, path))
    return inventory


def _scan_history_blobs(inventory: Iterable[tuple[str, int, str]]) -> tuple[list[dict], dict]:
    findings: list[dict] = []
    scanned = 0
    skipped_large = 0
    skipped_binary = 0
    for oid, size, path in inventory:
        if size > MAX_BLOB_BYTES:
            skipped_large += 1
            continue
        data = subprocess.run(
            ["git", "cat-file", "blob", oid], cwd=ROOT, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, check=False,
        ).stdout
        if b"\x00" in data[:8192]:
            skipped_binary += 1
            continue
        text = data.decode("utf-8", errors="replace")
        scanned += 1
        for detector, line in scan_text(text):
            findings.append(
                {"severity": "BLOCKER", "detector": detector, "path": path,
                 "blob_oid": oid, "line": line}
            )
    return findings, {
        "unique_text_blobs_scanned": scanned,
        "blobs_skipped_over_size_limit": skipped_large,
        "binary_blobs_skipped_from_text_scan": skipped_binary,
        "max_blob_bytes": MAX_BLOB_BYTES,
    }


def _historical_paths() -> set[str]:
    raw = _git("log", "--all", "--pretty=format:", "--name-only", "--diff-filter=AMCR")
    return {line.strip() for line in raw.splitlines() if line.strip()}


def _suspicious_path_findings(paths: Iterable[str]) -> list[dict]:
    result: list[dict] = []
    for path in sorted(set(paths)):
        p = Path(path)
        if path == ".env.example":
            continue
        if SUSPICIOUS_BASENAMES.match(p.name) or p.suffix.lower() in SUSPICIOUS_SUFFIXES:
            result.append({"severity": "REVIEW", "detector": "SENSITIVE_FILENAME_HISTORY", "path": path})
    return result


def _distribution_allowlist() -> dict[str, dict]:
    if not ALLOWLIST_PATH.exists():
        return {}
    payload = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    entries = payload.get("entries") or []
    out: dict[str, dict] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "").strip()
        sha256 = str(item.get("sha256") or "").strip().lower()
        if path and re.fullmatch(r"[0-9a-f]{64}", sha256):
            out[path] = item
    return out


def _current_binary_review() -> list[dict]:
    result: list[dict] = []
    allowlist = _distribution_allowlist()
    for path in sorted(_git("ls-files").splitlines()):
        p = ROOT / path
        parts = {part.lower() for part in Path(path).parts}
        if p.suffix.lower() in BINARY_REVIEW_SUFFIXES:
            entry = allowlist.get(path)
            if entry and p.is_file():
                digest = hashlib.sha256(p.read_bytes()).hexdigest()
                if digest == str(entry.get("sha256", "")).lower():
                    continue
            result.append({"severity": "REVIEW", "detector": "DISTRIBUTION_RIGHTS_BINARY", "path": path})
        elif parts & THIRD_PARTY_DIR_MARKERS:
            result.append({"severity": "REVIEW", "detector": "THIRD_PARTY_TREE", "path": path})
    return result


def _workflow_findings() -> tuple[list[dict], list[dict]]:
    blockers: list[dict] = []
    reviews: list[dict] = []
    workflow_dir = ROOT / ".github" / "workflows"
    if not workflow_dir.exists():
        return blockers, reviews
    for path in sorted(workflow_dir.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = str(path.relative_to(ROOT))
        lower = text.lower()
        if re.search(r"(?m)^\s*pull_request_target\s*:", text):
            blockers.append({"severity": "BLOCKER", "detector": "PULL_REQUEST_TARGET", "path": rel})
        if re.search(r"(?m)^\s*permissions\s*:\s*write-all\s*$", text, flags=re.I):
            blockers.append({"severity": "BLOCKER", "detector": "WORKFLOW_WRITE_ALL", "path": rel})
        if "secrets: inherit" in lower:
            blockers.append({"severity": "BLOCKER", "detector": "SECRETS_INHERIT", "path": rel})
        if re.search(r"(?m)^\s*workflow_run\s*:", text):
            reviews.append({"severity": "REVIEW", "detector": "WORKFLOW_RUN_TRIGGER", "path": rel})
        if re.search(r"(?m)^\s*contents\s*:\s*write\s*$", text, flags=re.I):
            reviews.append({"severity": "REVIEW", "detector": "CONTENTS_WRITE_PERMISSION", "path": rel})
        if re.search(r"(?m)^\s*id-token\s*:\s*write\s*$", text, flags=re.I):
            reviews.append({"severity": "REVIEW", "detector": "OIDC_WRITE_PERMISSION", "path": rel})
    return blockers, reviews


def _commit_identity_summary() -> dict:
    raw = _git("log", "--all", "--format=%ae%n%ce")
    emails = {line.strip().lower() for line in raw.splitlines() if "@" in line}
    non_noreply = {e for e in emails if "noreply" not in e}
    domains: dict[str, int] = {}
    for email in non_noreply:
        domain = email.rsplit("@", 1)[-1]
        domains[domain] = domains.get(domain, 0) + 1
    return {
        "unique_commit_emails": len(emails),
        "unique_non_noreply_commit_emails": len(non_noreply),
        "non_noreply_domains": dict(sorted(domains.items())),
        "note": "Commit identity metadata becomes public with history; exact addresses are intentionally omitted here.",
    }


def _governance_summary() -> dict:
    files = set(_git("ls-files").splitlines())
    return {
        "license_present": any(name in files for name in ("LICENSE", "LICENSE.md", "LICENSE.txt")),
        "security_policy_present": "SECURITY.md" in files or ".github/SECURITY.md" in files,
        "contributing_present": "CONTRIBUTING.md" in files or ".github/CONTRIBUTING.md" in files,
        "readme_present": any(name.lower().startswith("readme") for name in files),
        "license_note": "Public visibility does not itself grant an open-source license; license choice remains an explicit owner decision.",
    }


def run() -> dict:
    inventory = _object_inventory()
    secret_findings, history_stats = _scan_history_blobs(inventory)
    path_reviews = _suspicious_path_findings(_historical_paths())
    binary_reviews = _current_binary_review()
    workflow_blockers, workflow_reviews = _workflow_findings()

    blockers = secret_findings + workflow_blockers
    reviews = path_reviews + binary_reviews + workflow_reviews
    current_head = _git("rev-parse", "HEAD").strip()
    current_tree_fingerprint = hashlib.sha256(
        _git("ls-files", "-s").encode("utf-8")
    ).hexdigest()

    status = "PASS_PUBLIC_READINESS" if not blockers and not reviews else (
        "STOP_PUBLIC_READINESS_BLOCKERS" if blockers else "REVIEW_PUBLIC_READINESS"
    )
    report = {
        "schema": "ROBO_DADOS_PUBLICOS_PUBLIC_READINESS_AUDIT_V1",
        "status": status,
        "ready_for_public_visibility": not blockers and not reviews,
        "repository": "ferinbon-cpu/robo-dados-publicos",
        "head_sha": current_head,
        "tracked_tree_fingerprint_sha256": current_tree_fingerprint,
        "scope": {
            "full_reachable_git_history": True,
            "current_workflows": True,
            "current_binary_distribution_candidates": True,
            "commit_identity_metadata": True,
            "github_hosted_pr_issue_database": False,
            "github_actions_history_logs_artifacts": False,
            "secret_values_emitted": False,
            "drive_access": False,
            "source_data_network": False,
        },
        "history_scan": history_stats,
        "blocker_count": len(blockers),
        "review_count": len(reviews),
        "blockers": blockers,
        "reviews": reviews,
        "commit_identity": _commit_identity_summary(),
        "governance": _governance_summary(),
        "publication_authorized": False,
        "repository_visibility_change_executed": False,
        "future_batch_execution_authorized": False,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = run()
    except Exception as exc:
        report = {
            "schema": "ROBO_DADOS_PUBLICOS_PUBLIC_READINESS_AUDIT_V1",
            "status": "STOP_PUBLIC_READINESS_AUDIT_ERROR",
            "error": str(exc),
            "ready_for_public_visibility": False,
            "secret_values_emitted": False,
        }
    encoded = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps({
        "status": report.get("status"),
        "ready_for_public_visibility": report.get("ready_for_public_visibility", False),
        "blocker_count": report.get("blocker_count"),
        "review_count": report.get("review_count"),
        "secret_values_emitted": False,
    }, ensure_ascii=False, sort_keys=True))
    if report.get("status") == "PASS_PUBLIC_READINESS":
        return 0
    if report.get("status") == "REVIEW_PUBLIC_READINESS":
        return 43
    return 42


if __name__ == "__main__":
    raise SystemExit(main())
