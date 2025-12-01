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

### Docker / Production
1. Create a Service Account in your Google Cloud Console.
2. Grant necessary roles (e.g., `Pub/Sub Editor`, `Logging Log Writer`).
3. Create and download a JSON key file for the service account.
4. Save the key file in the project directory (e.g., as `gcp-key.json`).
5. Update `docker-compose.yml` to mount the key and set the environment variable:

   ```yaml
   services:
     adk-agent:
       # ...
       environment:
         - GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-key.json
       volumes:
         - ./gcp-key.json:/app/gcp-key.json
   ```

## Features

- 🤖 **Gemini Integration**: Powered by `gemini-2.0-flash-exp`
- 🛠️ **Custom Tools**: Includes weather and time checking capabilities
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
   The `.env` file is already configured with your API key.
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

## Usage

### Command Line Interface (CLI)

Run the agent in your terminal:

```bash
adk run my_agent
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
- `get_weather(city)`: Get weather information for a city
- `get_current_time(city)`: Get current time for a city
