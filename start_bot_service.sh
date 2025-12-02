#!/bin/sh
# Start Telegram bot and the FastAPI server so Cloud Run has an HTTP port.
set -e

python -m my_agent.telegram_bot &
exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-8080}"
