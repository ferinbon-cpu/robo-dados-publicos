#!/usr/bin/env python3
"""Provision the dedicated M8 Drive read-only refresh token into GitHub.

This helper intentionally runs on the user's local machine. It launches the
existing browser OAuth bootstrap with the Drive read-only scope, validates the
returned token metadata, sends only the refresh token to `gh secret set` via
stdin, verifies only the secret name is visible, and deletes the temporary token
file. It never prints token values.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


REPO = "ferinbon-cpu/robo-dados-publicos"
SECRET_NAME = "GOOGLE_DRIVE_READONLY_REFRESH_TOKEN"
READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
ROOT = Path(__file__).resolve().parents[1]
OAUTH_BOOTSTRAP = ROOT / "scripts" / "oauth_bootstrap_drive.py"


class ReadonlySecretBootstrapError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ReadonlySecretBootstrapError(code)


def validate_token_payload(payload: dict[str, Any]) -> str:
    """Return the refresh token only after proving requested scope metadata."""
    _require(isinstance(payload, dict), "STOP_READONLY_TOKEN_PAYLOAD_INVALID")
    refresh_token = payload.get("refresh_token")
    _require(isinstance(refresh_token, str) and refresh_token.strip(), "STOP_READONLY_REFRESH_TOKEN_MISSING")

    scope = payload.get("scope")
    _require(isinstance(scope, str) and scope.strip(), "STOP_READONLY_TOKEN_SCOPE_MISSING")
    scopes = {item.strip() for item in scope.split() if item.strip()}
    _require(scopes == {READONLY_SCOPE}, "STOP_READONLY_TOKEN_SCOPE_NOT_EXACT")
    return refresh_token


def _run(cmd: list[str], *, input_text: str | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
        env=env,
        cwd=ROOT,
    )


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    _require(path is not None, f"STOP_REQUIRED_TOOL_MISSING_{name.upper()}")
    return path


def run(*, repo: str = REPO) -> dict[str, Any]:
    gh = _require_tool("gh")
    _require(OAUTH_BOOTSTRAP.is_file(), "STOP_OAUTH_BOOTSTRAP_MISSING")
    _require(bool(os.environ.get("GOOGLE_DRIVE_CLIENT_ID")), "STOP_GOOGLE_DRIVE_CLIENT_ID_MISSING")
    _require(bool(os.environ.get("GOOGLE_DRIVE_CLIENT_SECRET")), "STOP_GOOGLE_DRIVE_CLIENT_SECRET_MISSING")

    auth = _run([gh, "auth", "status", "--hostname", "github.com"])
    _require(auth.returncode == 0, "STOP_GH_NOT_AUTHENTICATED")

    with tempfile.TemporaryDirectory(prefix="robo_m8_readonly_") as tmp:
        token_path = Path(tmp) / "tokens_readonly.json"
        env = os.environ.copy()
        oauth = _run(
            [
                sys.executable,
                str(OAUTH_BOOTSTRAP),
                "--scope",
                "drive.readonly",
                "--output",
                str(token_path),
            ],
            env=env,
        )
        if oauth.returncode != 0:
            raise ReadonlySecretBootstrapError("STOP_READONLY_OAUTH_BOOTSTRAP_FAILED")
        _require(token_path.is_file(), "STOP_READONLY_TOKEN_FILE_MISSING")

        try:
            payload = json.loads(token_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ReadonlySecretBootstrapError("STOP_READONLY_TOKEN_FILE_INVALID") from exc

        refresh_token = validate_token_payload(payload)

        # `gh secret set` reads from stdin when --body is omitted. GitHub CLI
        # encrypts the secret locally before sending it to GitHub.
        set_secret = _run(
            [gh, "secret", "set", SECRET_NAME, "--repo", repo, "--app", "actions"],
            input_text=refresh_token,
        )
        _require(set_secret.returncode == 0, "STOP_GITHUB_SECRET_SET_FAILED")

        listed = _run(
            [
                gh,
                "secret",
                "list",
                "--repo",
                repo,
                "--app",
                "actions",
                "--json",
                "name",
                "--jq",
                ".[].name",
            ]
        )
        _require(listed.returncode == 0, "STOP_GITHUB_SECRET_LIST_FAILED")
        names = {line.strip() for line in listed.stdout.splitlines() if line.strip()}
        _require(SECRET_NAME in names, "STOP_GITHUB_READONLY_SECRET_NOT_VISIBLE_BY_NAME")

        # No token value is returned or printed. TemporaryDirectory deletes the
        # token JSON when this context exits.
        return {
            "status": "PASS_M8_READONLY_SECRET_PROVISIONED",
            "repository": repo,
            "secret_name": SECRET_NAME,
            "scope": READONLY_SCOPE,
            "secret_value_exposed": False,
            "token_file_persistent": False,
            "m8_executed": False,
            "m8_no_click_authorized": False,
            "publication_authorized": False,
            "future_batch_execution_authorized": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a Drive read-only refresh token locally and store it as the dedicated GitHub Actions secret without printing its value."
    )
    parser.add_argument("--repo", default=REPO)
    args = parser.parse_args()
    try:
        result = run(repo=args.repo)
    except Exception as exc:
        print(json.dumps({"status": "STOP_M8_READONLY_SECRET_PROVISIONING", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 43
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
