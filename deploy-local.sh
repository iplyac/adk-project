#!/bin/bash
set -e

# Configuration
PROJECT_ID="gen-lang-client-0741140892"
REGION="us-central1"
SERVICE_NAME="adk-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying ADK Agent to Cloud Run (Local Build)..."
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Set PATH
export PATH="/Users/iosifplyats/Downloads/google-cloud-sdk/bin:$PATH"

# Set project
echo "📋 Setting project..."
gcloud config set project ${PROJECT_ID}

# Configure Docker to use gcloud as credential helper
echo "🔧 Configuring Docker..."
gcloud auth configure-docker --quiet

# Build image locally
echo "🏗️  Building Docker image locally..."
docker build -t ${IMAGE_NAME} .

# Push to Container Registry
echo "📤 Pushing image to GCR..."
docker push ${IMAGE_NAME}

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCP_LOCATION=${REGION}" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "Test the deployment:"
echo "  curl ${SERVICE_URL}/health"
echo "  curl -X POST ${SERVICE_URL}/api/chat -H 'Content-Type: application/json' -d '{\"message\": \"Hello\", \"session_id\": \"test\"}'"
