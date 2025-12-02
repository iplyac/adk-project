import os
import time
import asyncio
import logging
import math
import uuid
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from my_agent.agent import agent
from my_agent.session_monitor import session_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="ADK Agent with Monitoring")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global stats
stats = {
    "start_time": time.time(),
    "request_count": 0,
    "error_count": 0,
    "latencies": [],
    "tool_calls_total": 0,
    "tool_calls_by_name": {}
}

# Mount static files for dashboard
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    uptime = time.time() - stats["start_time"]
    return {
        "status": "healthy",
        "uptime_seconds": uptime,
        "timestamp": time.time()
    }

@app.get("/stats")
async def get_stats():
    uptime = time.time() - stats["start_time"]
    latencies = stats.get("latencies", [])
    latency_avg = sum(latencies) / len(latencies) if latencies else 0.0
    latency_p95 = 0.0
    if latencies:
        sorted_lats = sorted(latencies)
        idx = min(len(sorted_lats) - 1, math.ceil(0.95 * len(sorted_lats)) - 1)
        latency_p95 = sorted_lats[idx]
    return {
        "request_count": stats["request_count"],
        "error_count": stats["error_count"],
        "uptime_seconds": uptime,
        "agent_name": agent.name,
        "model": str(agent.model),
        "latency_avg_ms": round(latency_avg * 1000, 2),
        "latency_p95_ms": round(latency_p95 * 1000, 2),
        "tool_calls_total": stats.get("tool_calls_total", 0),
        "tool_calls_by_name": stats.get("tool_calls_by_name", {}),
    }

# Middleware to count requests
@app.middleware("http")
async def count_requests(request: Request, call_next):
    # Request count for /api/chat is handled within the endpoint
    # This middleware now primarily handles error counting for other endpoints
    
    try:
        response = await call_next(request)
        if response.status_code >= 500:
            stats["error_count"] += 1
        return response
    except Exception as e:
        stats["error_count"] += 1
        raise e

# --- ADK Runner Setup ---

session_service = InMemorySessionService()
runner = Runner(
    app_name="adk_agent_app",
    agent=agent,
    session_service=session_service
)

# --- Chat Implementation ---

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, response: Response):
    stats["request_count"] += 1
    session_id = request.session_id
    user_id = "default_user"
    user_message = request.message
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    response.headers["X-Trace-Id"] = trace_id

    # Monitor session creation/message
    session_monitor.log_event(
        session_id=session_id,
        user_id=user_id,
        agent_name=agent.name,
        event_type="message_received",
        detail="User message received",
    )
    session_monitor.record_message(session_id, user_id, agent.name)

    logger.info(
        "chat_request",
        extra={
            "trace_id": trace_id,
            "session_id": session_id,
            "user_id": user_id,
            "agent_name": agent.name,
        },
    )

    # In test mode, short-circuit to avoid real model calls
    if os.getenv("ADK_TEST_MODE", "").lower() == "true":
        return ChatResponse(response=f"[test-mode] {user_message or ''}")
    
    try:
        # Ensure session exists
        session = await session_service.get_session(
            app_name="adk_agent_app",
            user_id=user_id,
            session_id=session_id
        )
        if not session:
            await session_service.create_session(
                app_name="adk_agent_app",
                user_id=user_id,
                session_id=session_id
            )

        # Run the agent
        response_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=user_message)]
            )
        ):
            tool_name = None
            tool_attr = getattr(event, "tool", None)
            if tool_attr:
                tool_name = getattr(tool_attr, "name", None) or str(tool_attr)
            tool_call = getattr(event, "tool_call", None)
            if not tool_name and tool_call:
                tool_name = getattr(tool_call, "name", None)
            if tool_name:
                stats["tool_calls_total"] += 1
                stats["tool_calls_by_name"][tool_name] = stats["tool_calls_by_name"].get(tool_name, 0) + 1
                logger.info(
                    "tool_call",
                    extra={
                        "trace_id": trace_id,
                        "session_id": session_id,
                        "user_id": user_id,
                        "tool": tool_name,
                    },
                )

            # Collect model response text
            # We look for events authored by the agent (or 'model') that have content
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
        latency = time.time() - start_time
        stats["latencies"].append(latency)
        if len(stats["latencies"]) > 200:
            stats["latencies"] = stats["latencies"][-200:]
        session_monitor.log_event(
            session_id=session_id,
            user_id=user_id,
            agent_name=agent.name,
            event_type="completed",
            detail="Chat response generated",
        )
        logger.info(
            "chat_response",
            extra={
                "trace_id": trace_id,
                "session_id": session_id,
                "user_id": user_id,
                "latency_ms": round(latency * 1000, 2),
                "tool_calls": stats.get("tool_calls_total", 0),
            },
        )
        # Drain alerts so they don't accumulate, but keep user response clean
        session_monitor.pop_alerts(session_id)
        return ChatResponse(response=response_text)
        
    except Exception as e:
        # Log detailed error information with stack trace
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        logger.error(f"Session ID: {session_id}, User ID: {user_id}, Message: {user_message}")
        stats["error_count"] += 1
        session_monitor.log_event(
            session_id=session_id,
            user_id=user_id,
            agent_name=agent.name,
            event_type="error",
            error=str(e),
        )
        logger.error(
            "chat_error",
            extra={
                "trace_id": trace_id,
                "session_id": session_id,
                "user_id": user_id,
                "error": str(e),
            },
        )
        return ChatResponse(response="I'm sorry, I encountered an error processing your request.")
