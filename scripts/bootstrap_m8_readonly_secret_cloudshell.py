#!/usr/bin/env python3
"""Provision dedicated M8 Google Drive read-only OAuth secrets from Cloud Shell.

This helper is intentionally interactive and fail-closed. It avoids the current
`gcloud --no-launch-browser --client-id-file` incompatibility by using a
standard OAuth 2.0 Web application client with a callback served through the
authenticated Cloud Shell Web Preview proxy.

Security properties:
- OAuth client secret is entered with getpass and never printed.
- callback state is random and verified exactly.
- requested and proven scope is exactly Google Drive read-only.
- client id, client secret and refresh token are sent to GitHub Actions secrets
  through stdin, never placed in CLI arguments or committed to Git.
- no token file is written to disk.
- this helper does not run M8, authorize no-click execution, publish data, or
  authorize future batch execution.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import secrets
import shutil
import subprocess
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


REPO = "ferinbon-cpu/robo-dados-publicos"
READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORT = 8080
CALLBACK_PATH = "/oauth2callback"
SECRET_NAMES = {
    "client_id": "GOOGLE_DRIVE_READONLY_CLIENT_ID",
    "client_secret": "GOOGLE_DRIVE_READONLY_CLIENT_SECRET",
    "refresh_token": "GOOGLE_DRIVE_READONLY_REFRESH_TOKEN",
}


class CloudShellReadonlyBootstrapError(RuntimeError):
    pass


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise CloudShellReadonlyBootstrapError(code)


def _require_tool(name: str) -> str:
    path = shutil.which(name)
    _require(path is not None, f"STOP_REQUIRED_TOOL_MISSING_{name.upper()}")
    return path


def _run(
    cmd: list[str],
    *,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        input=input_text,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )


def cloudshell_redirect_uri(*, port: int = DEFAULT_PORT, web_host: str | None = None) -> str:
    host = (web_host if web_host is not None else os.environ.get("WEB_HOST", "")).strip()
    _require(bool(host), "STOP_CLOUDSHELL_WEB_HOST_MISSING")
    _require("/" not in host and "://" not in host, "STOP_CLOUDSHELL_WEB_HOST_INVALID")
    _require(host.endswith("cloudshell.dev"), "STOP_CLOUDSHELL_WEB_HOST_UNEXPECTED")
    _require(2000 <= port <= 65000, "STOP_CLOUDSHELL_PREVIEW_PORT_INVALID")
    return f"https://{port}-{host}{CALLBACK_PATH}"


def build_authorization_url(*, client_id: str, redirect_uri: str, state: str) -> str:
    _require(bool(client_id.strip()), "STOP_GOOGLE_DRIVE_READONLY_CLIENT_ID_MISSING")
    _require(client_id.strip().endswith(".apps.googleusercontent.com"), "STOP_GOOGLE_DRIVE_READONLY_CLIENT_ID_INVALID")
    _require(bool(state), "STOP_OAUTH_STATE_MISSING")
    return AUTH_URL + "?" + urlencode(
        {
            "client_id": client_id.strip(),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": READONLY_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
    )


def _post_form(url: str, body: dict[str, str]) -> dict[str, Any]:
    req = Request(
        url,
        data=urlencode(body).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def validate_token_payload(payload: dict[str, Any]) -> tuple[str, str]:
    _require(isinstance(payload, dict), "STOP_READONLY_TOKEN_PAYLOAD_INVALID")
    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    _require(isinstance(access_token, str) and access_token.strip(), "STOP_READONLY_ACCESS_TOKEN_MISSING")
    _require(isinstance(refresh_token, str) and refresh_token.strip(), "STOP_READONLY_REFRESH_TOKEN_MISSING")
    scope = payload.get("scope")
    if scope is not None:
        _require(isinstance(scope, str) and scope.strip(), "STOP_READONLY_TOKEN_SCOPE_INVALID")
        scopes = {item.strip() for item in scope.split() if item.strip()}
        _require(scopes == {READONLY_SCOPE}, "STOP_READONLY_TOKEN_SCOPE_NOT_EXACT")
    return access_token, refresh_token


def prove_exact_readonly_scope(access_token: str) -> None:
    tokeninfo = _get_json(TOKENINFO_URL + "?" + urlencode({"access_token": access_token}))
    scope = tokeninfo.get("scope")
    _require(isinstance(scope, str) and scope.strip(), "STOP_READONLY_TOKENINFO_SCOPE_MISSING")
    scopes = {item.strip() for item in scope.split() if item.strip()}
    _require(scopes == {READONLY_SCOPE}, "STOP_READONLY_TOKENINFO_SCOPE_NOT_EXACT")


def _wait_for_callback(*, port: int, expected_state: str, timeout_seconds: int = 600) -> str:
    result: dict[str, str] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path != CALLBACK_PATH:
                self.send_response(404)
                self.end_headers()
                return
            query = parse_qs(parsed.query)
            for key in ("state", "code", "error"):
                values = query.get(key)
                if values:
                    result[key] = values[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<h2>Autorização recebida.</h2><p>Você pode fechar esta aba e voltar ao Cloud Shell.</p>".encode("utf-8")
            )

        def log_message(self, *_args: Any) -> None:
            return

    server = HTTPServer(("0.0.0.0", port), Handler)
    server.timeout = 1
    deadline = time.monotonic() + timeout_seconds
    try:
        while time.monotonic() < deadline and "code" not in result and "error" not in result:
            server.handle_request()
    finally:
        server.server_close()

    _require(result.get("state") == expected_state, "STOP_OAUTH_STATE_MISMATCH")
    _require("error" not in result, "STOP_OAUTH_USER_DENIED_OR_ERROR")
    code = result.get("code")
    _require(isinstance(code, str) and code.strip(), "STOP_OAUTH_AUTHORIZATION_CODE_MISSING")
    return code


def _set_secret(gh: str, *, repo: str, name: str, value: str) -> None:
    result = _run(
        [gh, "secret", "set", name, "--repo", repo, "--app", "actions"],
        input_text=value,
    )
    _require(result.returncode == 0, f"STOP_GITHUB_SECRET_SET_FAILED_{name}")


def run(*, repo: str = REPO, port: int = DEFAULT_PORT) -> dict[str, Any]:
    gh = _require_tool("gh")
    gh_auth = _run([gh, "auth", "status", "--hostname", "github.com"])
    _require(gh_auth.returncode == 0, "STOP_GH_NOT_AUTHENTICATED")

    redirect_uri = cloudshell_redirect_uri(port=port)
    print("URI de redirecionamento exigido para o novo OAuth Web client:")
    print(redirect_uri)
    print("\nUse exatamente esse URI no Google Cloud, no cliente OAuth do tipo Aplicativo da Web.\n")

    client_id = input("Google OAuth Web Client ID: ").strip()
    client_secret = getpass.getpass("Google OAuth Web Client Secret (hidden): ")
    _require(bool(client_secret), "STOP_GOOGLE_DRIVE_READONLY_CLIENT_SECRET_MISSING")

    state = secrets.token_urlsafe(32)
    authorization_url = build_authorization_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        state=state,
    )
    print("\nAbra esta URL no navegador e autorize SOMENTE leitura do Google Drive:\n")
    print(authorization_url)
    print("\nAguardando o retorno seguro pelo Cloud Shell Web Preview...\n")

    code = _wait_for_callback(port=port, expected_state=state)
    token_payload = _post_form(
        TOKEN_URL,
        {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
    )
    access_token, refresh_token = validate_token_payload(token_payload)
    prove_exact_readonly_scope(access_token)

    _set_secret(gh, repo=repo, name=SECRET_NAMES["client_id"], value=client_id)
    _set_secret(gh, repo=repo, name=SECRET_NAMES["client_secret"], value=client_secret)
    _set_secret(gh, repo=repo, name=SECRET_NAMES["refresh_token"], value=refresh_token)

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
    _require(set(SECRET_NAMES.values()).issubset(names), "STOP_GITHUB_READONLY_SECRETS_NOT_VISIBLE_BY_NAME")

    return {
        "status": "PASS_M8_READONLY_SECRETS_PROVISIONED",
        "environment": "google_cloud_shell_web_preview",
        "repository": repo,
        "secret_names": sorted(SECRET_NAMES.values()),
        "scope": READONLY_SCOPE,
        "scope_proof": "token_response_and_tokeninfo_exact",
        "secret_values_exposed": False,
        "token_file_persistent": False,
        "m8_executed": False,
        "m8_no_click_authorized": False,
        "publication_authorized": False,
        "future_batch_execution_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision M8 Drive read-only OAuth secrets from Google Cloud Shell.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--print-redirect-uri", action="store_true")
    args = parser.parse_args()
    try:
        if args.print_redirect_uri:
            print(cloudshell_redirect_uri(port=args.port))
            return 0
        result = run(port=args.port)
    except Exception as exc:
        print(json.dumps({"status": "STOP_M8_READONLY_SECRET_PROVISIONING", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 43
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
