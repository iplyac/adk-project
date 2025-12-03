"""
Telegram bot bridge to the ADK chat agent.

Reads token from TELEGRAM_BOT_TOKEN env or .telegram_bot file.
Sends user messages to the FastAPI /api/chat endpoint and returns responses.
"""
import os
import asyncio
import logging
from functools import partial

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

from my_agent.secret_manager import load_secret_into_env

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Load environment variables
load_dotenv()
load_secret_into_env("TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN_SECRET_ID", logger=logger)


def read_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        return token.strip()
    path = ".telegram_bot"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    raise RuntimeError("Telegram bot token not found. Set TELEGRAM_BOT_TOKEN or create .telegram_bot")


API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hi! Send me a message and I'll ask the ADK agent.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, client: httpx.AsyncClient) -> None:
    if not update.message or not update.message.text:
        return
    user_text = update.message.text.strip()
    session_id = f"tg_{update.effective_user.id}"

    try:
        resp = await client.post(
            f"{API_URL}/api/chat",
            json={"message": user_text, "session_id": session_id},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        reply = data.get("response", "(no response)")
    except Exception as exc:
        logger.error("Error talking to agent: %s", exc)
        reply = "Sorry, I could not reach the agent."

    await update.message.reply_text(reply)


async def main() -> None:
    token = read_token()
    client = httpx.AsyncClient()
    app = (
        Application.builder()
        .token(token)
        .rate_limiter(None)  # no built-in rate limit; keep it simple
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(
            filters.TEXT & (~filters.COMMAND),
            partial(handle_message, client=client),
        )
    )

    logger.info("Starting Telegram bot; forwarding to %s", API_URL)
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()
    await app.stop()
    await client.aclose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
