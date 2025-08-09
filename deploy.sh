#!/bin/bash

# MAV Scraper Cloud Deployment Script
# Deploys the automated scraper to Google Cloud Run

set -e

# Configuration - UPDATED FOR ETI-INDUSTRIES PROJECT
PROJECT_ID="eti-industries"                # Your Google Cloud project ID
BUCKET_NAME="mpt-all-sources"              # Your GCS bucket name
SERVICE_NAME="mav-scraper"                 # Cloud Run service name
REGION="us-central1"                       # Google Cloud region
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE} MAV Scraper Cloud Deployment for ETI-Industries${NC}"
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

# Clean up any previous failed deployments
echo -e "${YELLOW} Cleaning up previous deployments...${NC}"
gcloud run services delete $SERVICE_NAME --region $REGION --quiet || echo "No existing service to delete"
gcloud scheduler jobs delete mav-scraper-daily --quiet || echo "No existing scheduler job to delete"

# Build and push Docker image (from root directory now)
echo -e "${YELLOW} Building Docker image from root directory...${NC}"
gcloud builds submit --tag $IMAGE_NAME .

# Deploy to Cloud Run
echo -e "${YELLOW} Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --memory 2Gi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 1 \
    --allow-unauthenticated \
    --set-env-vars="BUCKET_NAME=$BUCKET_NAME,PROJECT_ID=$PROJECT_ID"

# Create Cloud Scheduler job for daily execution at 10:30 PM
echo -e "${YELLOW} Setting up Cloud Scheduler for 10:30 PM...${NC}"

# Get the Cloud Run service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

# Create scheduler job (runs daily at 10:30 PM UTC)
# Updated to work with web service endpoint
gcloud scheduler jobs create http mav-scraper-daily \
    --schedule="30 19 * * *" \
    --uri="$SERVICE_URL" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --message-body='{"action": "run_daily"}' \
    --time-zone="UTC" \
    --description="Daily MAV scraper execution at 21:30 CEST (19:30 UTC) via web service" \
    --max-retry-attempts=3 \
    --min-backoff=30s \
    --max-backoff=300s \
    --max-doublings=3 \
    || echo "Scheduler job might already exist"

echo -e "${GREEN} Deployment complete for ETI-Industries!${NC}"
echo ""
echo " Deployment Summary:"
echo "  • Project: eti-industries"
echo "  • Service: $SERVICE_NAME"
echo "  • Region: $REGION"
echo "  • Bucket: gs://mpt-all-sources/blog/mav/json_output/"
echo "  • Image: $IMAGE_NAME"
echo "  • URL: $SERVICE_URL"
echo "  • Schedule: Daily at 21:30 CEST (19:30 UTC)"
echo ""
echo " Next steps:"
echo "  1. Test the deployment:"
echo "     gcloud run services invoke $SERVICE_NAME --region $REGION"
echo ""
echo "  2. Check logs:"
echo "     gcloud logs read --service $SERVICE_NAME --limit 50"
echo ""
echo "  3. Monitor scheduler:"
echo "     gcloud scheduler jobs list"
echo ""
echo "  4. Manual trigger:"
echo "     gcloud scheduler jobs run mav-scraper-daily"
echo ""
echo "  5. Check uploaded files:"
echo "     gsutil ls gs://mpt-all-sources/blog/mav/json_output/" 