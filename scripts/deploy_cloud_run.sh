#!/usr/bin/env bash
# Deploy Continuity to Google Cloud Run
# Prerequisites:
#   - gcloud authenticated
#   - Project set: gcloud config set project YOUR_PROJECT
#   - APIs enabled: run, cloudbuild, artifactregistry

set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project)}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="continuity-agent"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "▶ Building and deploying Continuity to Cloud Run..."
echo "  Project: ${PROJECT_ID}"
echo "  Region:  ${REGION}"

# Build
gcloud builds submit --tag "${IMAGE}" .

# Deploy
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-secrets "CLICKHOUSE_HOST=CLICKHOUSE_HOST:latest,CLICKHOUSE_PASSWORD=CLICKHOUSE_PASSWORD:latest,CLICKHOUSE_USER=CLICKHOUSE_USER:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest" \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 3

echo ""
echo "✅ Deployed. Service URL:"
gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)'
