"""
Telegram bot bridge to the ADK chat agent.

Reads token from TELEGRAM_BOT_TOKEN env or .telegram_bot file.
Only supported command: /chat <text>. Forwards the text to /api/chat and returns the agent reply.
"""
import os
import re
import time
import logging

import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def _extract_token(raw: str) -> str:
    """Try to extract a Telegram token from raw env/file content."""
    if not raw:
        return ""
    raw = raw.strip()
    # Look for explicit markers first
    for marker in ["TELEGRAM_BOT_TOKEN=", "BOT_TOKEN=", "TOKEN="]:
        if marker in raw:
            return raw.split(marker, 1)[1].strip()
    # Try regex token pattern
    m = re.search(r"\\b(\\d+:[A-Za-z0-9_-]+)", raw)
    if m:
        return m.group(1)
    # Fallback: if there are lines, use first non-empty after '=' if present
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if "=" in line:
            _, val = line.split("=", 1)
            return val.strip()
        return line
    return ""


def read_token() -> str:
    token_raw = os.getenv("TELEGRAM_BOT_TOKEN", "")
    token = _extract_token(token_raw)
    if token:
        return token
    path = ".telegram_bot"
    if os.path.exists(path):
        content = open(path, "r", encoding="utf-8").read()
        token = _extract_token(content)
        if token:
            return token
    raise RuntimeError("Telegram bot token not found. Set TELEGRAM_BOT_TOKEN or create .telegram_bot")


API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")
WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL")
WEBHOOK_PATH = os.getenv("TELEGRAM_WEBHOOK_PATH", "/telegram/webhook")
PORT = int(os.getenv("PORT", "8080"))


async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /chat <message> and forward to the agent."""
    if not update.message:
        return
    text = update.message.text or ""
    # Remove the command part and keep the rest as the prompt
    user_text = text.partition(" ")[2].strip()
    if not user_text:
        await update.message.reply_text("Используй: /chat <текст для агента>")
        return

    session_id = f"tg_{update.effective_user.id}"

    try:
        t0 = time.monotonic()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{API_URL}/api/chat",
                json={"message": user_text, "session_id": session_id},
                timeout=30,
            )
        t1 = time.monotonic()
        resp.raise_for_status()
        data = resp.json()
        reply = data.get("response", "(no response)")
        trace_id = resp.headers.get("X-Trace-Id")
        logger.info(
            "agent_call session=%s latency_ms=%.2f trace_id=%s status=%s",
            session_id,
            (t1 - t0) * 1000,
            trace_id,
            resp.status_code,
        )
    except Exception as exc:
        logger.error("Error talking to agent: %s", exc)
        reply = "Sorry, I could not reach the agent."
        t1 = time.monotonic()
        trace_id = None

    t_send_start = time.monotonic()
    await update.message.reply_text(reply)
    t_send_end = time.monotonic()
    logger.info(
        "telegram_send session=%s trace_id=%s send_latency_ms=%.2f total_latency_ms=%.2f",
        session_id,
        trace_id,
        (t_send_end - t_send_start) * 1000,
        (t_send_end - t0) * 1000,
    )


def main() -> None:
    token = read_token()
    app = (
        Application.builder()
        .token(token)
        .rate_limiter(None)  # no built-in rate limit; keep it simple
        .build()
    )

    app.add_handler(CommandHandler("chat", chat_command))

    if WEBHOOK_URL:
        # Webhook mode (Cloud Run friendly, avoids polling conflicts)
        logger.info(
            "Starting Telegram bot in webhook mode; forwarding to %s webhook=%s",
            API_URL,
            WEBHOOK_URL,
        )
        # Ensure webhook is set
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=WEBHOOK_PATH.lstrip("/"),
            webhook_url=WEBHOOK_URL.rstrip("/"),
        )
    else:
        logger.info("Starting Telegram bot in polling mode; forwarding to %s", API_URL)
        app.run_polling()


if __name__ == "__main__":
    main()
