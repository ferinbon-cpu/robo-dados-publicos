#!/usr/bin/env python3
"""Prove the M8 OAuth credential is capability-limited to Drive read-only.

This gate performs only Google OAuth token exchange + tokeninfo inspection.
It does not call the Drive API, read source data, write Drive, publish, or
authorize no-click execution.
"""
from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
TOKEN_URL = "https://oauth2.googleapis.com/token"
TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class ReadonlyCredentialCapabilityError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ReadonlyCredentialCapabilityError(code)


def _safe_http_error(exc: HTTPError, code: str) -> ReadonlyCredentialCapabilityError:
    try:
        payload = json.loads(exc.read().decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        payload = {}
    public_error = str(payload.get("error") or "oauth_http_error")
    return ReadonlyCredentialCapabilityError(f"{code}:{public_error}")


def _post_form(url: str, body: dict[str, str]) -> dict[str, Any]:
    req = Request(
        url,
        data=urlencode(body).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        raise _safe_http_error(exc, "STOP_READONLY_TOKEN_EXCHANGE_FAILED") from exc


def _get_json(url: str) -> dict[str, Any]:
    try:
        with urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        raise _safe_http_error(exc, "STOP_READONLY_TOKENINFO_FAILED") from exc


def exact_scope(scope: Any) -> bool:
    if not isinstance(scope, str) or not scope.strip():
        return False
    scopes = {item.strip() for item in scope.split() if item.strip()}
    return scopes == {READONLY_SCOPE}


def prove_capability(*, client_id: str, client_secret: str, refresh_token: str) -> dict[str, Any]:
    _require(bool(client_id.strip()), "STOP_READONLY_CLIENT_ID_MISSING")
    _require(bool(client_secret.strip()), "STOP_READONLY_CLIENT_SECRET_MISSING")
    _require(bool(refresh_token.strip()), "STOP_READONLY_REFRESH_TOKEN_MISSING")

    token_payload = _post_form(
        TOKEN_URL,
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )
    access_token = token_payload.get("access_token")
    _require(isinstance(access_token, str) and access_token.strip(), "STOP_READONLY_ACCESS_TOKEN_MISSING")

    if token_payload.get("scope") is not None:
        _require(exact_scope(token_payload.get("scope")), "STOP_READONLY_TOKEN_RESPONSE_SCOPE_NOT_EXACT")

    tokeninfo = _get_json(TOKENINFO_URL + "?" + urlencode({"access_token": access_token}))
    _require(exact_scope(tokeninfo.get("scope")), "STOP_READONLY_TOKENINFO_SCOPE_NOT_EXACT")

    return {
        "status": "PASS_M8_READONLY_CREDENTIAL_CAPABILITY",
        "scope": READONLY_SCOPE,
        "scope_proof": "oauth_refresh_and_tokeninfo_exact",
        "secret_values_exposed": False,
        "oauth_request_count": 2,
        "drive_api_request_count": 0,
        "source_get_count": 0,
        "drive_write_count": 0,
        "publication_authorized": False,
        "m8_no_click_authorized": False,
        "future_batch_execution_authorized": False,
    }


def run_from_env() -> dict[str, Any]:
    return prove_capability(
        client_id=os.getenv("GOOGLE_DRIVE_CLIENT_ID", ""),
        client_secret=os.getenv("GOOGLE_DRIVE_CLIENT_SECRET", ""),
        refresh_token=os.getenv("GOOGLE_DRIVE_REFRESH_TOKEN", ""),
    )


def main() -> int:
    try:
        print(json.dumps(run_from_env(), ensure_ascii=False, sort_keys=True))
    except Exception as exc:
        print(json.dumps({"status": "STOP_M8_READONLY_CREDENTIAL_CAPABILITY", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 44
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
