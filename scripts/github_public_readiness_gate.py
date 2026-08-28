#!/usr/bin/env python3
"""Policy layer for the repository public-readiness scanner.

`github_public_readiness_audit.py` provides generic scanner primitives.  This gate
adds repository-specific, fail-closed decisions needed before public visibility:
- blank `.env.example` assignments cannot bleed into the next line;
- environment-variable *names* and explicit test non-propagation sentinels are
  treated as placeholders, not credential values;
- synthetic binary fixtures are allowlisted only by exact Git blob identity.

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

scan_text = base.scan_text
run = base.run
main = base.main


if __name__ == "__main__":
    raise SystemExit(main())
