#!/usr/bin/env python3
"""Policy layer for hosted GitHub public-surface auditing.

GitHub's Actions log/artifact download endpoints are negotiated through the normal
REST media type and then redirect to ZIP bytes. The generic scanner accepts a
media-type argument; this gate deliberately normalizes all GitHub API requests to
`application/vnd.github+json` so the pre-public audit does not fail with HTTP 415.

Opaque artifact entries remain fail-closed unless an exact resource-id + entry-name
+ byte-count + SHA-256 tuple is present in the reviewed hosted-surface allowlist.
This permits specifically reviewed generated PDFs without weakening review of any
future or changed binary artifact.

A previously completed exhaustive hosted-surface baseline may be supplied via
PUBLIC_HOSTED_BASELINE_CUTOFF_UTC. In that mode, issue/PR text metadata is still
rescanned in full, while Actions logs/artifacts are downloaded only when their
updated/created timestamps are at or after an intentional overlap cutoff. This
keeps the audit fail-closed without repeatedly downloading more than a thousand
already-reviewed workflow logs on every PR amendment.

The underlying scanner remains read-only and never emits matched secret values.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

import github_public_surface_audit as base


ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = ROOT / "config" / "public_hosted_surface_allowlist.v1.json"
BASELINE_CUTOFF_RAW = os.environ.get("PUBLIC_HOSTED_BASELINE_CUTOFF_UTC", "").strip()
_original_request = base._request
_original_scan_zip_bytes = base.scan_zip_bytes


def _request(url: str, *, accept: str = "application/vnd.github+json") -> bytes:
    del accept
    return _original_request(url, accept="application/vnd.github+json")


def _allowlist() -> dict[tuple[str, str, str], dict]:
    if not ALLOWLIST_PATH.exists():
        return {}
    payload = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    entries = payload.get("entries") or []
    result: dict[tuple[str, str, str], dict] = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        surface = str(item.get("surface") or "").strip()
        resource_id = str(item.get("resource_id") or "").strip()
        entry = str(item.get("entry") or "").strip()
        sha256 = str(item.get("sha256") or "").strip().lower()
        byte_count = item.get("bytes")
        if surface and resource_id and entry and len(sha256) == 64 and isinstance(byte_count, int):
            result[(surface, resource_id, entry)] = item
    return result


def _review_is_exactly_allowlisted(review: dict, archive: zipfile.ZipFile, allowlist: dict) -> bool:
    if review.get("detector") not in {"OPAQUE_ARTIFACT_ENTRY", "NON_UTF8_ARTIFACT_ENTRY"}:
        return False
    surface = str(review.get("surface") or "")
    resource_id = str(review.get("resource_id") or "")
    entry = str(review.get("entry") or "")
    item = allowlist.get((surface, resource_id, entry))
    if not item:
        return False
    try:
        data = archive.read(entry)
    except KeyError:
        return False
    return (
        len(data) == int(item["bytes"])
        and hashlib.sha256(data).hexdigest() == str(item["sha256"]).lower()
    )


def scan_zip_bytes(raw: bytes, *, surface: str, resource_id: str):
    blockers, reviews, stats = _original_scan_zip_bytes(raw, surface=surface, resource_id=resource_id)
    if not reviews:
        return blockers, reviews, stats

    allowlist = _allowlist()
    retained: list[dict] = []
    allowed = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for review in reviews:
            if _review_is_exactly_allowlisted(review, archive, allowlist):
                allowed += 1
            else:
                retained.append(review)

    adjusted = dict(stats)
    adjusted["opaque_entries_allowlisted"] = allowed
    if "opaque_entries" in adjusted:
        adjusted["opaque_entries"] = max(0, int(adjusted["opaque_entries"]) - allowed)
    return blockers, retained, adjusted


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise base.SurfaceAuditError("STOP_PUBLIC_HOSTED_BASELINE_CUTOFF_INVALID") from exc
    if parsed.tzinfo is None:
        raise base.SurfaceAuditError("STOP_PUBLIC_HOSTED_BASELINE_CUTOFF_TZ_MISSING")
    return parsed.astimezone(timezone.utc)


def _at_or_after_cutoff(value: object, cutoff: datetime) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    if parsed.tzinfo is None:
        return False
    return parsed.astimezone(timezone.utc) >= cutoff


def _scan_actions_logs_incremental(cutoff: datetime):
    blockers: list[dict] = []
    reviews: list[dict] = []
    listed = list(base._paginate(f"/repos/{base.REPO}/actions/runs", key="workflow_runs"))
    candidates = [
        str(run.get("id"))
        for run in listed
        if run.get("id")
        and str(run.get("id")) != base.CURRENT_RUN_ID
        and run.get("status") == "completed"
        and _at_or_after_cutoff(run.get("updated_at"), cutoff)
    ]
    scanned_runs = 0
    unavailable_runs = 0
    with ThreadPoolExecutor(max_workers=base.MAX_DOWNLOAD_WORKERS) as pool:
        futures = {pool.submit(base._scan_one_log, run_id): run_id for run_id in candidates}
        for future in as_completed(futures):
            b, r, available = future.result()
            blockers.extend(b)
            reviews.extend(r)
            if available:
                scanned_runs += 1
            else:
                unavailable_runs += 1
    return base._sort_findings(blockers), base._sort_findings(reviews), {
        "baseline_overlap_cutoff_utc": cutoff.isoformat().replace("+00:00", "Z"),
        "actions_runs_metadata_listed": len(listed),
        "completed_actions_runs_considered": len(candidates),
        "completed_actions_runs_scanned": scanned_runs,
        "completed_actions_runs_unavailable_or_expired": unavailable_runs,
        "download_workers": base.MAX_DOWNLOAD_WORKERS,
        "incremental_from_pinned_exhaustive_baseline": True,
    }


def _scan_actions_artifacts_incremental(cutoff: datetime):
    blockers: list[dict] = []
    reviews: list[dict] = []
    artifacts = list(base._paginate(f"/repos/{base.REPO}/actions/artifacts", key="artifacts"))
    expired = sum(1 for item in artifacts if item.get("expired"))
    candidates = [
        str(item.get("id"))
        for item in artifacts
        if item.get("id")
        and not item.get("expired")
        and _at_or_after_cutoff(item.get("created_at"), cutoff)
    ]
    scanned = 0
    text_entries = 0
    opaque_entries = 0
    with ThreadPoolExecutor(max_workers=base.MAX_DOWNLOAD_WORKERS) as pool:
        futures = {pool.submit(base._scan_one_artifact, artifact_id): artifact_id for artifact_id in candidates}
        for future in as_completed(futures):
            b, r, stats, available = future.result()
            blockers.extend(b)
            reviews.extend(r)
            text_entries += stats["text_entries"]
            opaque_entries += stats["opaque_entries"]
            if available:
                scanned += 1
    return base._sort_findings(blockers), base._sort_findings(reviews), {
        "baseline_overlap_cutoff_utc": cutoff.isoformat().replace("+00:00", "Z"),
        "actions_artifacts_metadata_listed": len(artifacts),
        "nonexpired_artifacts_considered": len(candidates),
        "nonexpired_artifacts_scanned": scanned,
        "expired_artifacts_skipped": expired,
        "artifact_text_entries_scanned": text_entries,
        "artifact_opaque_entries_for_review": opaque_entries,
        "download_workers": base.MAX_DOWNLOAD_WORKERS,
        "incremental_from_pinned_exhaustive_baseline": True,
    }


base._request = _request
base.scan_zip_bytes = scan_zip_bytes

if BASELINE_CUTOFF_RAW:
    _cutoff = _parse_utc(BASELINE_CUTOFF_RAW)
    base._scan_actions_logs = lambda: _scan_actions_logs_incremental(_cutoff)
    base._scan_actions_artifacts = lambda: _scan_actions_artifacts_incremental(_cutoff)

run = base.run
main = base.main


if __name__ == "__main__":
    raise SystemExit(main())
