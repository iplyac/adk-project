# ADK Agent Setup Guide

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Gemini API Key** from [AI Studio](https://aistudio.google.com/app/apikey)
3. **gcloud CLI** installed from [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)

## Quick Start

### 1. Clone and Setup

```bash
cd adk-project
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Key

Create `api-key` file with your Gemini API key:
```bash
echo "YOUR_GEMINI_API_KEY" > api-key
```

### 3. Configure Environment

Copy and edit the environment file:
```bash
cp .env.example .env
```

Edit `.env`:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
GCP_PROJECT_ID=gen-lang-client-0741140892
GCP_LOCATION=europe-west4
# Telegram webhook (for Cloud Run)
# TELEGRAM_WEBHOOK_URL=https://your-bot-service/telegram/webhook
```

### 4. Run Locally

```bash
uvicorn app:app --reload --port 8000
```

Access at: http://localhost:8000/static/index.html

## Cloud Run Deployment

### 1. Authenticate

```bash
gcloud auth login
gcloud config set project gen-lang-client-0741140892
```

### 2. Deploy

```bash
chmod +x deploy.sh
./deploy.sh
```

The script will:
- Build optimized Docker image
- Push to Container Registry
- Deploy to Cloud Run
- Output the service URL

### 3. Verify

```bash
curl https://adk-agent-3qblthn7ba-uc.a.run.app/health
```

## Configuration Details

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Gemini API key | `AIza...` |
| `GCP_PROJECT_ID` | GCP project ID | `gen-lang-client-0741140892` |
| `GCP_LOCATION` | GCP region | `europe-west4` |

### Optional Environment Variables

| Variable | Description | Required For |
|----------|-------------|--------------|
| `VERTEX_SEARCH_DATA_STORE_ID` | Vertex AI Search data store | Knowledge base search |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account key path | Local DevOps features |
| `GOOGLE_API_KEY_SECRET_ID` | Secret Manager ID for Gemini key | Cloud Run |
| `TELEGRAM_BOT_TOKEN_SECRET_ID` | Secret Manager ID for Telegram token | Cloud Run |
| `TELEGRAM_WEBHOOK_URL` | Full webhook URL `https://<bot-service>/telegram/webhook` | Telegram webhook mode |
| `TELEGRAM_WEBHOOK_PATH` | Webhook path (default `/telegram/webhook`) | Custom path |

## Service Account Setup (Optional)

For DevOps features (Pub/Sub, Logging), create a service account:

```bash
# Create service account
gcloud iam service-accounts create adk-agent-sa \
  --display-name="ADK Agent Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding gen-lang-client-0741140892 \
  --member="serviceAccount:adk-agent-sa@gen-lang-client-0741140892.iam.gserviceaccount.com" \
  --role="roles/pubsub.editor"

gcloud projects add-iam-policy-binding gen-lang-client-0741140892 \
  --member="serviceAccount:adk-agent-sa@gen-lang-client-0741140892.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

# Create key (for local development)
gcloud iam service-accounts keys create key.json \
  --iam-account=adk-agent-sa@gen-lang-client-0741140892.iam.gserviceaccount.com
```

## Vertex AI Search Setup (Optional)

1. Go to [Vertex AI Search Console](https://console.cloud.google.com/gen-app-builder/engines)
2. Create a new Data Store
3. Copy the Data Store ID
4. Add to `.env`:
   ```bash
   VERTEX_SEARCH_DATA_STORE_ID=your_data_store_id
   ```

## Troubleshooting

### API Key Issues
- Verify key is valid: https://aistudio.google.com/app/apikey
- Check `.env` file has correct key
- Ensure no extra spaces or newlines in `api-key` file

### Permission Errors
- Verify you're authenticated: `gcloud auth list`
- Check project is set: `gcloud config get-value project`
- Ensure required APIs are enabled:
  ```bash
  gcloud services enable run.googleapis.com
  gcloud services enable cloudbuild.googleapis.com
  ```

### Docker Build Issues
- Check `.dockerignore` excludes unnecessary files
- Verify `requirements.txt` is up to date
- Clear Docker cache: `docker system prune -a`

## Testing

Run unit tests:
```bash
pytest tests/ -v
```

Test specific features:
```bash
# Weather
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Weather in London?", "session_id": "test"}'

# DevOps
curl -X POST http://localhost:8000/api/chat \
  -d '{"message": "Create pubsub topic test-topic", "session_id": "test"}'
```

## Production Checklist

- [ ] API key configured
- [ ] GCP project set up
- [ ] Service account created (if using DevOps)
- [ ] `.dockerignore` excludes secrets
- [ ] Environment variables set in Cloud Run
- [ ] Health check passing
- [ ] UI accessible
- [ ] Chat functionality tested
- [ ] DevOps features tested (if enabled)

## Support

For issues or questions:
- Check logs: `gcloud run services logs read adk-agent --region us-central1`
- Review documentation in `README.md`
- Verify configuration in `config.example.yaml`
