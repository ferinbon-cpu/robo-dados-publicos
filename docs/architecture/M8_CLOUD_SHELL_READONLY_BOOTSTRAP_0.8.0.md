# M8 Cloud Shell read-only bootstrap — 0.8.0

## Purpose

Provide the dedicated `GOOGLE_DRIVE_READONLY_REFRESH_TOKEN` for the M8 historical SIOPE read-only product gate without requiring a local repository or localhost callback on the user's Windows PC.

## Supported environment

Google Cloud Shell in project `robo-dados-publicos-pessoal`, with `gcloud` available and GitHub CLI (`gh`) authenticated to `ferinbon-cpu/robo-dados-publicos`.

## Security contract

- OAuth scope must resolve exactly to `https://www.googleapis.com/auth/drive.readonly`.
- The OAuth Desktop Client Secret is entered only in Cloud Shell with hidden input.
- `gcloud auth application-default login --no-launch-browser --client-id-file=...` is used so the remote shell can complete the official browser authorization-code flow without a localhost listener.
- `CLOUDSDK_CONFIG` is redirected to a temporary directory; the temporary ADC file is deleted at process exit.
- The granted access token is checked against Google's tokeninfo endpoint; any missing or extra scope fails closed.
- The refresh token is sent to `gh secret set GOOGLE_DRIVE_READONLY_REFRESH_TOKEN` via stdin and is never printed or placed in a command-line argument.
- The helper does not execute M8, does not authorize no-click execution, does not publish data, and does not authorize future batch execution.

## Operator command

From Cloud Shell:

```bash
git clone https://github.com/ferinbon-cpu/robo-dados-publicos.git 2>/dev/null || true
cd robo-dados-publicos
git fetch origin main
git checkout main
git pull --ff-only origin main
python3 scripts/bootstrap_m8_readonly_secret_cloudshell.py
```

If `gh auth status` is not authenticated, authenticate GitHub CLI first and rerun the Python helper.

Expected final status:

```text
PASS_M8_READONLY_SECRET_PROVISIONED
```

Do not paste the Client Secret, refresh token, ADC JSON, or authorization code into chat, issue comments, commits, or logs.
