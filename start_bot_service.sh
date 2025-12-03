#!/bin/sh
# Start Telegram bot in webhook mode (or polling if no webhook URL is set).
set -e

exec python -m my_agent.telegram_bot
