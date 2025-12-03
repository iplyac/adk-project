# Google ADK Agent with Gemini

This project implements an AI agent using Google's [Agent Development Kit (ADK)](https://google.github.io/adk-docs/) and Gemini LLM.

## GCP Authentication

The DevOps agent requires Google Cloud credentials to interact with Pub/Sub and Cloud Logging.

### Local Development
1. Install the Google Cloud SDK.
2. Run the following command to set up Application Default Credentials (ADC):
   ```bash
   gcloud auth application-default login
   ```
   This creates a credentials file that the client libraries will automatically discover.

### Docker / Production (Cloud Run)
- Секреты: храните ключи в Secret Manager (`GOOGLE_API_KEY`, `TELEGRAM_BOT_TOKEN`) и прокидывайте в Cloud Run через `--set-secrets` или `GOOGLE_API_KEY_SECRET_ID` / `TELEGRAM_BOT_TOKEN_SECRET_ID`.
- Рекомендованный регион для меньшей задержки с Telegram: `europe-west4`.
- Webhook для бота: задайте `TELEGRAM_WEBHOOK_URL=https://<bot-service-url>/telegram/webhook` (путь можно переопределить `TELEGRAM_WEBHOOK_PATH`).

## Features

- 🤖 **Gemini Integration**: Powered by `gemini-2.0-flash-exp`
- 🛠️ **Custom Tools**: Delegates DevOps tasks, searches documentation, and exposes session insights
- 🖥️ **Multiple Interfaces**: Run via CLI or Web UI
- 🐍 **Python-based**: Built with the official `google-adk` package

## Prerequisites

- Python 3.10+
- Google Gemini API Key

## Installation

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure API Key:
   - **Recommended (production):** Store secrets in [Google Secret Manager](https://cloud.google.com/secret-manager). Set the environment variable `GOOGLE_API_KEY_SECRET_ID` to the secret name (or full resource path). At startup the app will fetch the value into `GOOGLE_API_KEY`. You can also set `TELEGRAM_BOT_TOKEN_SECRET_ID` to hydrate the Telegram token.
   - **Local development:** You can still use a `.env` file with raw values if Secret Manager is not configured.
   - Webhook mode: set `TELEGRAM_WEBHOOK_URL` (`https://<bot-service>/telegram/webhook`).

## Usage

### Command Line Interface (CLI)

Run the agent in your terminal:

```bash
adk run my_agent
```

To avoid external calls during local testing, set:

```bash
export ADK_TEST_MODE=true
```

### Web Interface

Run the agent with a web-based chat interface:

```bash
adk run my_agent --web
```

## Project Structure

```
adk-project/
├── my_agent/           # Agent package
│   ├── __init__.py     # Exports the agent
│   └── agent.py        # Agent implementation and tools
├── .env                # API key configuration
├── requirements.txt    # Python dependencies
└── README.md           # Documentation
```

## Tools

The agent has access to the following tools:
- `ask_devops(request)`: Delegate DevOps requests to the specialized DevOps agent
- `search_knowledge_base(query)`: Search the knowledge base for documentation answers
- `get_session_summary(scope="active")`: Return a summary of known sessions
- `get_session_details(session_id)`: Return details for a specific session
