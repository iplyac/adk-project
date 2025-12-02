#!/bin/bash
set -e

# Configuration
PROJECT_ID="gen-lang-client-0741140892"
REGION="us-central1"
SERVICE_NAME="adk-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
BOT_SERVICE_NAME="adk-telegram-bot"
BUILD_TIMEOUT="1200s" # allow up to 20 minutes in Cloud Build

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

# Read Telegram bot token
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
    BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
elif [ -f ".telegram_bot" ]; then
    RAW_BOT_TOKEN=$(cat .telegram_bot)
    BOT_TOKEN=$(printf "%s" "$RAW_BOT_TOKEN" | sed -n 's/.*TELEGRAM_BOT_TOKEN=//p' | head -n1 | tr -d '\r')
    if [ -z "$BOT_TOKEN" ]; then
        BOT_TOKEN=$(printf "%s" "$RAW_BOT_TOKEN" | grep -Eo '[0-9]+:[A-Za-z0-9_-]+' | head -n1)
    fi
fi
if [ -z "$BOT_TOKEN" ]; then
    echo "❌ Error: Telegram bot token not found. Set TELEGRAM_BOT_TOKEN or add .telegram_bot"
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
echo "⏳ Cloud Build can take several minutes, please wait..."
gcloud builds submit --tag ${IMAGE_NAME} --timeout=${BUILD_TIMEOUT}

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
# Deploy Telegram bot (reuses same image). We run bot + uvicorn for health/metrics on :8080.
echo ""
echo "🤖 Deploying Telegram bot to Cloud Run..."
gcloud run deploy ${BOT_SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --command "/bin/sh" \
  --args "/app/start_bot_service.sh" \
  --set-env-vars "TELEGRAM_BOT_TOKEN=${BOT_TOKEN},AGENT_API_URL=${SERVICE_URL}" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300

BOT_URL=$(gcloud run services describe ${BOT_SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Telegram bot deployed!"
echo "🌐 Bot Service URL (for health): ${BOT_URL}"
echo ""
echo "Next steps:"
echo "  1. Test the agent: curl ${SERVICE_URL}/health"
echo "  2. Test the bot health: curl ${BOT_URL}/health"
echo "  3. Run: python register_agent.py to register with Agent Engine"
echo "  4. UI: ${SERVICE_URL}/static/index.html"
