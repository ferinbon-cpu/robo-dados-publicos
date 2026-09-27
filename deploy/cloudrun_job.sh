#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-robo-dados-publicos-pessoal}"
REGION="${REGION:-us-central1}"
JOB_NAME="${JOB_NAME:-robo-dados-publicos}"
IMAGE="${IMAGE:-gcr.io/${PROJECT_ID}/robo-dados-publicos:0.4.0}"

: "${GOOGLE_DRIVE_CLIENT_ID_SECRET:=google-drive-client-id}"
: "${GOOGLE_DRIVE_CLIENT_SECRET_SECRET:=google-drive-client-secret}"
: "${GOOGLE_DRIVE_REFRESH_TOKEN_SECRET:=google-drive-refresh-token}"

gcloud config set project "$PROJECT_ID" >/dev/null

gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com artifactregistry.googleapis.com

gcloud builds submit --tag "$IMAGE" .

gcloud run jobs deploy "$JOB_NAME" \
  --image "$IMAGE" \
  --region "$REGION" \
  --tasks 1 \
  --max-retries 1 \
  --set-env-vars ROBO_DRIVE_AUTH=oauth-env \
  --set-secrets GOOGLE_DRIVE_CLIENT_ID=${GOOGLE_DRIVE_CLIENT_ID_SECRET}:latest,GOOGLE_DRIVE_CLIENT_SECRET=${GOOGLE_DRIVE_CLIENT_SECRET_SECRET}:latest,GOOGLE_DRIVE_REFRESH_TOKEN=${GOOGLE_DRIVE_REFRESH_TOKEN_SECRET}:latest

echo "Deploy concluído. Teste com:"
echo "gcloud run jobs execute $JOB_NAME --region $REGION --wait"
