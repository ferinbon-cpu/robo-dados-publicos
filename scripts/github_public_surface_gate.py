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

The underlying scanner remains read-only and never emits matched secret values.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile

import github_public_surface_audit as base


ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = ROOT / "config" / "public_hosted_surface_allowlist.v1.json"
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


base._request = _request
base.scan_zip_bytes = scan_zip_bytes
run = base.run
main = base.main


if __name__ == "__main__":
    raise SystemExit(main())
