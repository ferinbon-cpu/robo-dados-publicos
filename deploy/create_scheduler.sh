#!/usr/bin/env bash
set -euo pipefail
PROJECT_ID="${PROJECT_ID:-robo-dados-publicos-pessoal}"
REGION="${REGION:-us-central1}"
JOB_NAME="${JOB_NAME:-robo-dados-publicos}"
SCHEDULER_NAME="${SCHEDULER_NAME:-robo-dados-publicos-diario}"
SCHEDULE="${SCHEDULE:-0 3 * * *}"
TIME_ZONE="${TIME_ZONE:-America/Sao_Paulo}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:?Defina SERVICE_ACCOUNT com uma conta que possa executar o Cloud Run Job}"

gcloud services enable cloudscheduler.googleapis.com
URI="https://run.googleapis.com/v2/projects/${PROJECT_ID}/locations/${REGION}/jobs/${JOB_NAME}:run"

gcloud scheduler jobs create http "$SCHEDULER_NAME" \
  --location "$REGION" \
  --schedule "$SCHEDULE" \
  --time-zone "$TIME_ZONE" \
  --uri "$URI" \
  --http-method POST \
  --oauth-service-account-email "$SERVICE_ACCOUNT"
