import time
import asyncio
import logging
from typing import Dict, List, Optional
from fastapi import FastAPI, Request
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
    "error_count": 0
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
    return {
        "request_count": stats["request_count"],
        "error_count": stats["error_count"],
        "uptime_seconds": uptime,
        "agent_name": agent.name,
        "model": str(agent.model)
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
async def chat_endpoint(request: ChatRequest):
    stats["request_count"] += 1
    session_id = request.session_id
    user_id = "default_user"
    user_message = request.message
    
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
            # Collect model response text
            # We look for events authored by the agent (or 'model') that have content
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
        
        return ChatResponse(response=response_text)
        
    except Exception as e:
        # Log detailed error information with stack trace
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        logger.error(f"Session ID: {session_id}, User ID: {user_id}, Message: {user_message}")
        stats["error_count"] += 1
        return ChatResponse(response="I'm sorry, I encountered an error processing your request.")
