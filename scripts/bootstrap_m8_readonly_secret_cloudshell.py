#!/usr/bin/env python3
"""Provision the dedicated M8 Google Drive read-only refresh token from Cloud Shell.

This helper is intentionally interactive and fail-closed. It uses the official
`gcloud auth application-default login --no-launch-browser --client-id-file`
flow so a remote Cloud Shell session can complete OAuth without a localhost
callback on the user's PC.

Security properties:
- OAuth client secret is entered with getpass and never printed.
- gcloud ADC state is isolated under a TemporaryDirectory via CLOUDSDK_CONFIG.
- the granted access token is checked with Google's tokeninfo endpoint and the
  scope must be exactly Drive read-only.
- the refresh token is sent to `gh secret set` through stdin, never a CLI arg.
- temporary client/ADC files are deleted when the helper exits.
- this helper does not run M8, authorize no-click execution, or publish data.
"""
from __future__ import annotations

import getpass
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


REPO = "ferinbon-cpu/robo-dados-publicos"
SECRET_NAME = "GOOGLE_DRIVE_READONLY_REFRESH_TOKEN"
READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
TOKEN_URL = "https://oauth2.googleapis.com/token"
TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
ROOT = Path(__file__).resolve().parents[1]


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
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        input=input_text,
        capture_output=capture_output,
        check=False,
        env=env,
        cwd=ROOT,
    )


def build_desktop_client_payload(client_id: str, client_secret: str, project_id: str) -> dict[str, Any]:
    _require(bool(client_id.strip()), "STOP_GOOGLE_DRIVE_CLIENT_ID_MISSING")
    _require(bool(client_secret.strip()), "STOP_GOOGLE_DRIVE_CLIENT_SECRET_MISSING")
    return {
        "installed": {
            "client_id": client_id.strip(),
            "project_id": project_id.strip() or "robo-dados-publicos-pessoal",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": TOKEN_URL,
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"],
        }
    }


def validate_adc_payload(payload: dict[str, Any], *, client_id: str) -> str:
    _require(isinstance(payload, dict), "STOP_READONLY_ADC_PAYLOAD_INVALID")
    _require(payload.get("type") == "authorized_user", "STOP_READONLY_ADC_TYPE_INVALID")
    _require(payload.get("client_id") == client_id, "STOP_READONLY_ADC_CLIENT_ID_MISMATCH")
    refresh_token = payload.get("refresh_token")
    _require(isinstance(refresh_token, str) and refresh_token.strip(), "STOP_READONLY_REFRESH_TOKEN_MISSING")
    return refresh_token


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


def prove_exact_readonly_scope(*, client_id: str, client_secret: str, refresh_token: str) -> None:
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

    tokeninfo = _get_json(TOKENINFO_URL + "?" + urlencode({"access_token": access_token}))
    scope = tokeninfo.get("scope")
    _require(isinstance(scope, str) and scope.strip(), "STOP_READONLY_TOKEN_SCOPE_MISSING")
    scopes = {item.strip() for item in scope.split() if item.strip()}
    _require(scopes == {READONLY_SCOPE}, "STOP_READONLY_TOKEN_SCOPE_NOT_EXACT")


def _find_adc(config_dir: Path) -> Path:
    direct = config_dir / "application_default_credentials.json"
    if direct.is_file():
        return direct
    matches = list(config_dir.rglob("application_default_credentials.json"))
    _require(len(matches) == 1, "STOP_READONLY_ADC_FILE_NOT_FOUND")
    return matches[0]


def run(*, repo: str = REPO) -> dict[str, Any]:
    gcloud = _require_tool("gcloud")
    gh = _require_tool("gh")

    gh_auth = _run([gh, "auth", "status", "--hostname", "github.com"])
    _require(gh_auth.returncode == 0, "STOP_GH_NOT_AUTHENTICATED")

    client_id = input("Google OAuth Desktop Client ID: ").strip()
    client_secret = getpass.getpass("Google OAuth Desktop Client Secret (hidden): ")
    _require(bool(client_id), "STOP_GOOGLE_DRIVE_CLIENT_ID_MISSING")
    _require(bool(client_secret), "STOP_GOOGLE_DRIVE_CLIENT_SECRET_MISSING")

    project_check = _run([gcloud, "config", "get-value", "project"])
    project_id = project_check.stdout.strip() if project_check.returncode == 0 else ""

    with tempfile.TemporaryDirectory(prefix="robo_m8_cloudshell_readonly_") as tmp:
        tmp_path = Path(tmp)
        config_dir = tmp_path / "gcloud"
        config_dir.mkdir(mode=0o700)
        client_file = tmp_path / "clientid.json"
        client_file.write_text(
            json.dumps(build_desktop_client_payload(client_id, client_secret, project_id), ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            os.chmod(client_file, 0o600)
        except OSError:
            pass

        env = os.environ.copy()
        env["CLOUDSDK_CONFIG"] = str(config_dir)

        print("\nOAuth read-only: o gcloud exibirá uma URL. Abra-a no navegador, autorize e cole o código SOMENTE neste terminal.\n")
        oauth = _run(
            [
                gcloud,
                "auth",
                "application-default",
                "login",
                f"--client-id-file={client_file}",
                f"--scopes={READONLY_SCOPE}",
                "--no-launch-browser",
                "--disable-quota-project",
            ],
            env=env,
            capture_output=False,
        )
        _require(oauth.returncode == 0, "STOP_READONLY_GCLOUD_OAUTH_FAILED")

        adc_path = _find_adc(config_dir)
        try:
            adc_payload = json.loads(adc_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CloudShellReadonlyBootstrapError("STOP_READONLY_ADC_FILE_INVALID") from exc

        refresh_token = validate_adc_payload(adc_payload, client_id=client_id)
        prove_exact_readonly_scope(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
        )

        # GitHub CLI reads the secret from stdin and encrypts it before sending.
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

        return {
            "status": "PASS_M8_READONLY_SECRET_PROVISIONED",
            "environment": "google_cloud_shell",
            "repository": repo,
            "secret_name": SECRET_NAME,
            "scope": READONLY_SCOPE,
            "scope_proof": "tokeninfo_exact",
            "secret_value_exposed": False,
            "temporary_adc_persistent": False,
            "temporary_client_file_persistent": False,
            "m8_executed": False,
            "m8_no_click_authorized": False,
            "publication_authorized": False,
            "future_batch_execution_authorized": False,
        }


def main() -> int:
    try:
        result = run()
    except Exception as exc:
        print(json.dumps({"status": "STOP_M8_READONLY_SECRET_PROVISIONING", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 43
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
