#!/usr/bin/env python3
"""Audit hosted GitHub surfaces that become broadly readable when repo is public.

Scopes covered with the repository-scoped GITHUB_TOKEN:
- issue/PR titles and bodies;
- issue comments, PR review comments, commit comments;
- retained GitHub Actions logs;
- non-expired GitHub Actions artifacts (text entries are scanned; opaque/binary
  entries are reported for review).

Matched values are never emitted. Reports contain only detector names and stable
resource identifiers. The script performs GitHub read-only requests only.

GitHub's log/artifact download endpoints redirect to short-lived object-store URLs.
The repository token is sent only to api.github.com and is deliberately NOT
forwarded to the redirected host.
"""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
import re
from typing import Any, Iterable
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
import zipfile

import github_public_readiness_audit as local_audit


REPO = os.environ.get("GITHUB_REPOSITORY", "ferinbon-cpu/robo-dados-publicos")
API = "https://api.github.com"
CURRENT_RUN_ID = os.environ.get("GITHUB_RUN_ID", "").strip()
MAX_TEXT_ENTRY_BYTES = 5_000_000
MAX_ARCHIVE_BYTES = 200_000_000
TEXT_SUFFIXES = {
    ".txt", ".log", ".json", ".jsonl", ".md", ".csv", ".tsv", ".html", ".htm",
    ".xml", ".yml", ".yaml", ".py", ".sh", ".ps1", ".ini", ".cfg", ".toml",
}
OPAQUE_SUFFIXES = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".sqlite", ".sqlite3",
    ".db", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".zip", ".rar", ".7z", ".gz",
    ".tar", ".tgz", ".bin", ".pkl", ".pickle",
}


class SurfaceAuditError(RuntimeError):
    pass


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _token() -> str:
    value = os.environ.get("GITHUB_TOKEN", "").strip()
    if not value:
        raise SurfaceAuditError("STOP_GITHUB_TOKEN_MISSING")
    return value


def _request_headers(*, include_auth: bool, accept: str) -> dict[str, str]:
    headers = {
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "robo-dados-publicos-public-readiness-audit",
    }
    if include_auth:
        headers["Authorization"] = f"Bearer {_token()}"
    return headers


def _read_bounded(resp) -> bytes:  # noqa: ANN001
    data = resp.read(MAX_ARCHIVE_BYTES + 1)
    if len(data) > MAX_ARCHIVE_BYTES:
        raise SurfaceAuditError("STOP_GITHUB_SURFACE_RESPONSE_TOO_LARGE")
    return data


def _request(url: str, *, accept: str = "application/vnd.github+json") -> bytes:
    """GET a GitHub API resource, safely following one archive redirect.

    Authentication is attached only to api.github.com.  If GitHub returns a
    redirect for a log/artifact archive, the signed destination is fetched with
    no Authorization header, preventing repository-token disclosure to the
    object-store host.
    """
    req = Request(url, headers=_request_headers(include_auth=True, accept=accept))
    opener = build_opener(_NoRedirect())
    try:
        with opener.open(req, timeout=120) as resp:
            return _read_bounded(resp)
    except HTTPError as exc:
        if exc.code in {404, 410}:
            return b""
        if exc.code in {301, 302, 303, 307, 308}:
            location = exc.headers.get("Location", "").strip()
            if not location.startswith("https://"):
                raise SurfaceAuditError("STOP_GITHUB_REDIRECT_LOCATION_INVALID") from exc
            redirected = Request(
                location,
                headers=_request_headers(include_auth=False, accept=accept),
            )
            try:
                with urlopen(redirected, timeout=120) as resp:
                    return _read_bounded(resp)
            except HTTPError as redirect_exc:
                if redirect_exc.code in {404, 410}:
                    return b""
                raise SurfaceAuditError(
                    f"STOP_GITHUB_REDIRECT_HTTP_{redirect_exc.code}"
                ) from redirect_exc
        raise SurfaceAuditError(f"STOP_GITHUB_API_HTTP_{exc.code}") from exc


def _json(url: str) -> dict[str, Any] | list[Any]:
    raw = _request(url)
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SurfaceAuditError("STOP_GITHUB_API_JSON_INVALID") from exc


def _paginate(path: str, key: str | None = None) -> Iterable[dict[str, Any]]:
    page = 1
    while True:
        sep = "&" if "?" in path else "?"
        payload = _json(f"{API}{path}{sep}per_page=100&page={page}")
        if key:
            if not isinstance(payload, dict):
                raise SurfaceAuditError("STOP_GITHUB_API_PAGE_SHAPE")
            items = payload.get(key) or []
        else:
            items = payload
        if not isinstance(items, list):
            raise SurfaceAuditError("STOP_GITHUB_API_PAGE_ITEMS")
        for item in items:
            if isinstance(item, dict):
                yield item
        if len(items) < 100:
            break
        page += 1
        if page > 100:
            raise SurfaceAuditError("STOP_GITHUB_API_PAGINATION_BOUND")


def _redacted_findings(text: str, *, surface: str, resource_id: str, entry: str | None = None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for detector, line in local_audit.scan_text(text):
        item: dict[str, Any] = {
            "severity": "BLOCKER",
            "surface": surface,
            "resource_id": resource_id,
            "detector": detector,
            "line": line,
        }
        if entry:
            item["entry"] = entry
        out.append(item)
    return out


def scan_zip_bytes(raw: bytes, *, surface: str, resource_id: str) -> tuple[list[dict], list[dict], dict]:
    blockers: list[dict] = []
    reviews: list[dict] = []
    text_entries = 0
    opaque_entries = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename
            suffix = Path(name).suffix.lower()
            if info.file_size > MAX_TEXT_ENTRY_BYTES:
                reviews.append({
                    "severity": "REVIEW", "surface": surface, "resource_id": resource_id,
                    "detector": "ARTIFACT_ENTRY_TOO_LARGE_FOR_TEXT_AUDIT", "entry": name,
                    "bytes": info.file_size,
                })
                continue
            data = zf.read(info)
            if b"\x00" in data[:8192] or suffix in OPAQUE_SUFFIXES:
                opaque_entries += 1
                reviews.append({
                    "severity": "REVIEW", "surface": surface, "resource_id": resource_id,
                    "detector": "OPAQUE_ARTIFACT_ENTRY", "entry": name, "bytes": len(data),
                })
                continue
            if suffix not in TEXT_SUFFIXES and data:
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    opaque_entries += 1
                    reviews.append({
                        "severity": "REVIEW", "surface": surface, "resource_id": resource_id,
                        "detector": "NON_UTF8_ARTIFACT_ENTRY", "entry": name, "bytes": len(data),
                    })
                    continue
            else:
                text = data.decode("utf-8", errors="replace")
            text_entries += 1
            blockers.extend(_redacted_findings(text, surface=surface, resource_id=resource_id, entry=name))
    return blockers, reviews, {"text_entries": text_entries, "opaque_entries": opaque_entries}


def _scan_metadata() -> tuple[list[dict], dict]:
    blockers: list[dict] = []
    scanned = 0
    owner_repo = f"/repos/{REPO}"

    for issue in _paginate(f"{owner_repo}/issues?state=all"):
        number = str(issue.get("number") or "unknown")
        for field in ("title", "body"):
            value = issue.get(field)
            if isinstance(value, str) and value:
                blockers.extend(_redacted_findings(value, surface=f"issue_or_pr_{field}", resource_id=number))
                scanned += 1

    for path, surface in (
        (f"{owner_repo}/issues/comments", "issue_comment"),
        (f"{owner_repo}/pulls/comments", "pull_review_comment"),
        (f"{owner_repo}/comments", "commit_comment"),
    ):
        for item in _paginate(path):
            value = item.get("body")
            if isinstance(value, str) and value:
                blockers.extend(_redacted_findings(value, surface=surface, resource_id=str(item.get("id") or "unknown")))
                scanned += 1
    return blockers, {"metadata_text_records_scanned": scanned}


def _scan_actions_logs() -> tuple[list[dict], list[dict], dict]:
    blockers: list[dict] = []
    reviews: list[dict] = []
    scanned_runs = 0
    unavailable_runs = 0
    for run in _paginate(f"/repos/{REPO}/actions/runs", key="workflow_runs"):
        run_id = str(run.get("id") or "")
        if not run_id or run_id == CURRENT_RUN_ID or run.get("status") != "completed":
            continue
        raw = _request(f"{API}/repos/{REPO}/actions/runs/{run_id}/logs", accept="application/zip")
        if not raw:
            unavailable_runs += 1
            continue
        try:
            b, r, _stats = scan_zip_bytes(raw, surface="actions_log", resource_id=run_id)
        except zipfile.BadZipFile:
            reviews.append({
                "severity": "REVIEW", "surface": "actions_log", "resource_id": run_id,
                "detector": "ACTIONS_LOG_ARCHIVE_INVALID",
            })
            continue
        blockers.extend(b)
        reviews.extend(r)
        scanned_runs += 1
    return blockers, reviews, {
        "completed_actions_runs_scanned": scanned_runs,
        "completed_actions_runs_unavailable_or_expired": unavailable_runs,
    }


def _scan_actions_artifacts() -> tuple[list[dict], list[dict], dict]:
    blockers: list[dict] = []
    reviews: list[dict] = []
    scanned = 0
    expired = 0
    text_entries = 0
    opaque_entries = 0
    for artifact in _paginate(f"/repos/{REPO}/actions/artifacts", key="artifacts"):
        artifact_id = str(artifact.get("id") or "")
        if not artifact_id:
            continue
        if artifact.get("expired"):
            expired += 1
            continue
        raw = _request(f"{API}/repos/{REPO}/actions/artifacts/{artifact_id}/zip", accept="application/zip")
        if not raw:
            reviews.append({
                "severity": "REVIEW", "surface": "actions_artifact", "resource_id": artifact_id,
                "detector": "ARTIFACT_UNAVAILABLE_DURING_AUDIT",
            })
            continue
        try:
            b, r, stats = scan_zip_bytes(raw, surface="actions_artifact", resource_id=artifact_id)
        except zipfile.BadZipFile:
            reviews.append({
                "severity": "REVIEW", "surface": "actions_artifact", "resource_id": artifact_id,
                "detector": "ARTIFACT_ARCHIVE_INVALID",
            })
            continue
        blockers.extend(b)
        reviews.extend(r)
        text_entries += stats["text_entries"]
        opaque_entries += stats["opaque_entries"]
        scanned += 1
    return blockers, reviews, {
        "nonexpired_artifacts_scanned": scanned,
        "expired_artifacts_skipped": expired,
        "artifact_text_entries_scanned": text_entries,
        "artifact_opaque_entries_for_review": opaque_entries,
    }


def run() -> dict[str, Any]:
    metadata_blockers, metadata_stats = _scan_metadata()
    log_blockers, log_reviews, log_stats = _scan_actions_logs()
    artifact_blockers, artifact_reviews, artifact_stats = _scan_actions_artifacts()
    blockers = metadata_blockers + log_blockers + artifact_blockers
    reviews = log_reviews + artifact_reviews
    status = "PASS_PUBLIC_HOSTED_SURFACES" if not blockers and not reviews else (
        "STOP_PUBLIC_HOSTED_SURFACES_BLOCKERS" if blockers else "REVIEW_PUBLIC_HOSTED_SURFACES"
    )
    return {
        "schema": "ROBO_DADOS_PUBLICOS_PUBLIC_HOSTED_SURFACE_AUDIT_V1",
        "status": status,
        "ready_for_public_visibility": not blockers and not reviews,
        "repository": REPO,
        "scope": {
            "github_hosted_issue_pr_metadata": True,
            "github_actions_retained_logs": True,
            "github_actions_nonexpired_artifacts": True,
            "github_read_only": True,
            "drive_access": False,
            "source_data_network": False,
            "secret_values_emitted": False,
        },
        "stats": {**metadata_stats, **log_stats, **artifact_stats},
        "blocker_count": len(blockers),
        "review_count": len(reviews),
        "blockers": blockers,
        "reviews": reviews,
        "repository_visibility_change_executed": False,
        "publication_authorized": False,
        "future_batch_execution_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = run()
    except Exception as exc:
        report = {
            "schema": "ROBO_DADOS_PUBLICOS_PUBLIC_HOSTED_SURFACE_AUDIT_V1",
            "status": "STOP_PUBLIC_HOSTED_SURFACE_AUDIT_ERROR",
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
    if report.get("status") == "PASS_PUBLIC_HOSTED_SURFACES":
        return 0
    if report.get("status") == "REVIEW_PUBLIC_HOSTED_SURFACES":
        return 43
    return 42


if __name__ == "__main__":
    raise SystemExit(main())
