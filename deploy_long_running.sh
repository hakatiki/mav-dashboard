#!/bin/bash

# MAV Scraper Long-Running Cloud Deployment Script
# Deploys the automated scraper as a Cloud Run Job for long-running tasks

set -e

# Configuration - UPDATED FOR ETI-INDUSTRIES PROJECT
PROJECT_ID="eti-industries"                # Your Google Cloud project ID
BUCKET_NAME="mpt-all-sources"              # Your GCS bucket name
JOB_NAME="mav-scraper-job"                 # Cloud Run Job name
REGION="us-central1"                       # Google Cloud region
IMAGE_NAME="gcr.io/$PROJECT_ID/$JOB_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE} MAV Scraper Long-Running Cloud Deployment for ETI-Industries${NC}"
echo "=================================================="

# Check if we're in the right directory (should be in project root)
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED} ERROR: Dockerfile not found. Please run this script from the project root directory.${NC}"
    echo "Current directory: $(pwd)"
    echo "Expected: fuck_lazar/"
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED} ERROR: gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

# Set the project
echo -e "${YELLOW} Setting Google Cloud project to eti-industries...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW} Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable run.googleapis.com

# Clean up any previous failed deployments
echo -e "${YELLOW} Cleaning up previous deployments...${NC}"
gcloud run jobs delete $JOB_NAME --region $REGION --quiet || echo "No existing job to delete"
gcloud scheduler jobs delete mav-scraper-job-daily --quiet || echo "No existing scheduler job to delete"

# Build and push Docker image (from root directory now)
echo -e "${YELLOW} Building Docker image from root directory...${NC}"
gcloud builds submit --tag $IMAGE_NAME .

# Deploy to Cloud Run Jobs (for long-running tasks)
echo -e "${YELLOW} Deploying to Cloud Run Jobs for long-running tasks...${NC}"
gcloud run jobs create $JOB_NAME \
    --image $IMAGE_NAME \
    --region $REGION \
    --memory 4Gi \
    --cpu 2 \
    --timeout 3600 \
    --max-retries 3 \
    --task-timeout 3600 \
    --set-env-vars="BUCKET_NAME=$BUCKET_NAME,PROJECT_ID=$PROJECT_ID" \
    --command="python" \
    --args="scraper/automated_scraper.py,./scraper/data/route_station_pairs.csv,--bucket,$BUCKET_NAME,--project,$PROJECT_ID"

# Create Cloud Scheduler job for daily execution at 10:30 PM
echo -e "${YELLOW} Setting up Cloud Scheduler for 10:30 PM...${NC}"

# Create scheduler job (runs daily at 10:30 PM UTC)
gcloud scheduler jobs create http mav-scraper-job-daily \
    --location=$REGION \
    --schedule="30 19 * * *" \
    --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run" \
    --http-method=POST \
    --headers="Content-Type=application/json,Authorization=Bearer $(gcloud auth print-access-token)" \
    --message-body='{}' \
    --time-zone="UTC" \
    --description="Daily MAV scraper execution at 21:30 CEST (19:30 UTC) via Cloud Run Jobs - LONG RUNNING" \
    --max-retry-attempts=3 \
    --min-backoff=30s \
    --max-backoff=300s \
    --max-doublings=3 \
    || echo "Scheduler job might already exist"

echo -e "${GREEN} Long-running deployment complete for ETI-Industries!${NC}"
echo ""
echo " Deployment Summary:"
echo "  • Project: eti-industries"
echo "  • Job: $JOB_NAME (LONG RUNNING)"
echo "  • Region: $REGION"
echo "  • Bucket: gs://mpt-all-sources/blog/mav/json_output/"
echo "  • Image: $IMAGE_NAME"
echo "  • Schedule: Daily at 21:30 CEST (19:30 UTC)"
echo "  • Resources: 4GB RAM, 2 CPU cores"
echo "  • Timeout: 3600 seconds (1 hour)"
echo ""
echo " Next steps:"
echo "  1. Test the deployment:"
echo "     gcloud run jobs execute $JOB_NAME --region $REGION"
echo ""
echo "  2. Check job status:"
echo "     gcloud run jobs executions list --job=$JOB_NAME --region $REGION"
echo ""
echo "  3. Monitor scheduler:"
echo "     gcloud scheduler jobs list"
echo ""
echo "  4. Manual trigger:"
echo "     gcloud scheduler jobs run mav-scraper-job-daily"
echo ""
echo "  5. Check uploaded files:"
echo "     gsutil ls gs://mpt-all-sources/blog/mav/json_output/" 