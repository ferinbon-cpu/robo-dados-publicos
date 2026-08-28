#!/usr/bin/env python3
"""Policy layer for hosted GitHub public-surface auditing.

GitHub's Actions log/artifact download endpoints are negotiated through the normal
REST media type and then redirect to ZIP bytes.  The generic scanner accepts a
media-type argument; this gate deliberately normalizes all GitHub API requests to
`application/vnd.github+json` so the pre-public audit does not fail with HTTP 415.

The underlying scanner remains read-only and never emits matched secret values.
"""
from __future__ import annotations

import github_public_surface_audit as base


_original_request = base._request


def _request(url: str, *, accept: str = "application/vnd.github+json") -> bytes:
    del accept
    return _original_request(url, accept="application/vnd.github+json")


base._request = _request
run = base.run
main = base.main
scan_zip_bytes = base.scan_zip_bytes


if __name__ == "__main__":
    raise SystemExit(main())
