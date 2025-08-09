#!/usr/bin/env bash
set -euo pipefail

# Configuration (edit these)
PROJECT_ID="eti-industries"
REGION="us-central1"
IMAGE="gcr.io/${PROJECT_ID}/mav-maps-job:latest"
JOB_NAME="mav-maps-job"
BUCKET_NAME="mpt-all-sources"
SERVICE_ACCOUNT="cloud-run-exec@${PROJECT_ID}.iam.gserviceaccount.com"

# Build and push image from this folder
echo "Building and pushing image ${IMAGE}..."
gcloud builds submit --tag "${IMAGE}" "$(dirname "$0")"

# Enable required APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com cloudscheduler.googleapis.com storage.googleapis.com --project "${PROJECT_ID}"

# Create or update Cloud Run Job
echo "Creating/Updating Cloud Run Job ${JOB_NAME}..."
gcloud run jobs describe "${JOB_NAME}" --region "${REGION}" --project "${PROJECT_ID}" >/dev/null 2>&1 && EXISTS=1 || EXISTS=0

if [[ ${EXISTS} -eq 1 ]]; then
  gcloud run jobs update "${JOB_NAME}" \
    --image "${IMAGE}" \
    --region "${REGION}" \
    --project "${PROJECT_ID}" \
    --service-account "${SERVICE_ACCOUNT}" \
    --set-env-vars "BUCKET_NAME=${BUCKET_NAME}" \
    --max-retries 1 \
    --cpu 2 --memory 4Gi \
    --task-timeout 3600s
else
  gcloud run jobs create "${JOB_NAME}" \
    --image "${IMAGE}" \
    --region "${REGION}" \
    --project "${PROJECT_ID}" \
    --service-account "${SERVICE_ACCOUNT}" \
    --set-env-vars "BUCKET_NAME=${BUCKET_NAME}" \
    --max-retries 1 \
    --cpu 2 --memory 4Gi \
    --task-timeout 3600s
fi

echo "Cloud Run Job ready: ${JOB_NAME}"
echo "Run once with today's date:"
echo "  gcloud run jobs run ${JOB_NAME} --region ${REGION} --project ${PROJECT_ID} --args --only=all"
echo "Run for a specific date (example):"
echo "  gcloud run jobs run ${JOB_NAME} --region ${REGION} --project ${PROJECT_ID} --args --date=2025-08-08 --args --only=all"

echo "Optionally schedule daily via Cloud Scheduler (02:00 UTC example):"
echo "  gcloud scheduler jobs create http ${JOB_NAME}-daily \\
          --schedule '0 2 * * *' \\
          --uri https://REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run \\
          --oauth-service-account-email ${SERVICE_ACCOUNT} \\
          --http-method POST --location ${REGION}"


