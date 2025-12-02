#!/bin/bash
set -e

# Configuration
PROJECT_ID="gen-lang-client-0741140892"
REGION="us-central1"
SERVICE_NAME="adk-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying ADK Agent to Cloud Run..."
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check for API key file
if [ ! -f "api-key" ]; then
    echo "❌ Error: api-key file not found!"
    echo "Please create a file named 'api-key' containing your Google Gemini API key."
    exit 1
fi

# Read API Key
API_KEY=$(cat api-key | tr -d '\n')
if [ -z "$API_KEY" ]; then
    echo "❌ Error: api-key file is empty!"
    exit 1
fi

# Set project
echo "📋 Setting project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs (ignore errors if already enabled/permission denied)
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com || echo "⚠️  Warning: Could not enable APIs. Assuming they are already enabled."

# Build and push image
echo "🏗️  Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCP_LOCATION=${REGION},GOOGLE_API_KEY=${API_KEY}" \
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
echo ""
echo "Next steps:"
echo "  1. Test the endpoint above"
echo "  2. Run: python register_agent.py to register with Agent Engine"
echo "  3. The UI is available at: ${SERVICE_URL}/static/index.html"
