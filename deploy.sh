#!/bin/bash
set -e

# Configuration
PROJECT_ID="gen-lang-client-0741140892"
REGION="europe-west4"
SERVICE_NAME="adk-agent"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
BOT_SERVICE_NAME="adk-telegram-bot"
BUILD_TIMEOUT="1200s" # allow up to 20 minutes in Cloud Build
API_KEY_SECRET_ID_DEFAULT="GOOGLE_API_KEY"
BOT_TOKEN_SECRET_ID_DEFAULT="TELEGRAM_BOT_TOKEN"
BOT_WEBHOOK_PATH="${TELEGRAM_WEBHOOK_PATH:-/telegram/webhook}"

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

# Resolve secret IDs (default names)
API_KEY_SECRET_ID=${GOOGLE_API_KEY_SECRET_ID:-$API_KEY_SECRET_ID_DEFAULT}
BOT_TOKEN_SECRET_ID=${TELEGRAM_BOT_TOKEN_SECRET_ID:-$BOT_TOKEN_SECRET_ID_DEFAULT}

# Read API key only if no secret ID is provided (for local/compat)
API_KEY=""
if [ -z "$API_KEY_SECRET_ID" ]; then
    if [ ! -f "api-key" ]; then
        echo "❌ Error: api-key file not found and no GOOGLE_API_KEY_SECRET_ID provided!"
        exit 1
    fi
    API_KEY=$(cat api-key | tr -d '\n')
    if [ -z "$API_KEY" ]; then
        echo "❌ Error: api-key file is empty!"
        exit 1
    fi
fi

# Read Telegram bot token only if no secret ID is provided
BOT_TOKEN=""
if [ -z "$BOT_TOKEN_SECRET_ID" ]; then
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
        echo "❌ Error: Telegram bot token not found and no TELEGRAM_BOT_TOKEN_SECRET_ID provided!"
        exit 1
    fi
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

# Prepare env vars for agent
AGENT_ENVS="GCP_PROJECT_ID=${PROJECT_ID},GCP_LOCATION=${REGION}"
if [ -n "$API_KEY" ]; then
  AGENT_ENVS="${AGENT_ENVS},GOOGLE_API_KEY=${API_KEY}"
fi
if [ -n "$API_KEY_SECRET_ID" ]; then
  AGENT_ENVS="${AGENT_ENVS},GOOGLE_API_KEY_SECRET_ID=${API_KEY_SECRET_ID}"
fi

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --set-env-vars "${AGENT_ENVS}" \
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
# Deploy Telegram bot (webhook mode) so container listens on PORT=8080.
echo ""
echo "🤖 Deploying Telegram bot to Cloud Run (webhook)..."

# Compute default webhook URL using service name pattern
PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')
BOT_WEBHOOK_URL=${TELEGRAM_WEBHOOK_URL:-"https://${BOT_SERVICE_NAME}-${PROJECT_NUMBER}.${REGION}.run.app${BOT_WEBHOOK_PATH}"}

BOT_ENVS="AGENT_API_URL=${SERVICE_URL},GCP_PROJECT_ID=${PROJECT_ID},GCP_LOCATION=${REGION},TELEGRAM_WEBHOOK_URL=${BOT_WEBHOOK_URL},TELEGRAM_WEBHOOK_PATH=${BOT_WEBHOOK_PATH}"

if [ -n "$BOT_TOKEN_SECRET_ID" ]; then
  BOT_SECRET_FLAG="--set-secrets TELEGRAM_BOT_TOKEN=${BOT_TOKEN_SECRET_ID}:latest"
else
  BOT_SECRET_FLAG=""
  if [ -n "$BOT_TOKEN" ]; then
    BOT_ENVS="${BOT_ENVS},TELEGRAM_BOT_TOKEN=${BOT_TOKEN}"
  else
    echo "❌ Error: No TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN_SECRET_ID provided for the bot!"
    exit 1
  fi
fi

gcloud run deploy ${BOT_SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --command "/bin/sh" \
  --args "/app/start_bot_service.sh" \
  --set-env-vars "${BOT_ENVS}" \
  ${BOT_SECRET_FLAG} \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300

BOT_URL=$(gcloud run services describe ${BOT_SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Telegram bot deployed!"
echo "🌐 Bot Service URL (for webhook + health): ${BOT_URL}"
echo ""
echo "Next steps:"
echo "  1. Test the agent: curl ${SERVICE_URL}/health"
echo "  2. Test the bot health: curl ${BOT_URL}/health"
echo "  3. Run: python register_agent.py to register with Agent Engine"
echo "  4. UI: ${SERVICE_URL}/static/index.html"
