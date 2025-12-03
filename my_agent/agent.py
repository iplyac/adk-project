import asyncio
import logging
import os
import threading

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from my_agent.devops_agent import devops_agent
from my_agent.session_monitor import session_monitor
from my_agent.vertex_tools import search_knowledge_base


logger = logging.getLogger(__name__)


# Reuse a single Runner/SessionService for DevOps delegation to avoid repeatedly
# constructing them on every tool call.
_devops_session_service = InMemorySessionService()
_devops_runner = Runner(
    app_name="devops_app",
    agent=devops_agent,
    session_service=_devops_session_service,
)


def ask_devops(request: str) -> str:
    """Delegates a request to the DevOps agent."""

    if os.getenv("ADK_TEST_MODE", "").lower() == "true":
        return "[devops-test-mode] DevOps delegation is disabled."

    session_id = "delegation_session"
    user_id = "main_agent"
    response_text = ""

    async def run_devops():
        # Create session first
        await _devops_session_service.create_session(
            app_name="devops_app",
            user_id=user_id,
            session_id=session_id,
        )

        result = ""
        async for event in _devops_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=request)],
            ),
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        result += part.text
        return result

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop; safe to block with asyncio.run
            response_text = asyncio.run(run_devops())
        else:
            # When already in an event loop (e.g., called from async context),
            # offload to a dedicated thread to avoid "loop already running" errors.
            response_container: dict = {}

            def _runner():
                response_container["value"] = asyncio.run(run_devops())

            thread = threading.Thread(target=_runner)
            thread.start()
            thread.join()
            response_text = response_container.get("value", "")

    except Exception as e:  # pragma: no cover - defensive logging
        logger.error("Error in ask_devops: %s", e, exc_info=True)
        return f"Error calling DevOps agent: {str(e)}"

    return response_text


def get_session_summary(scope: str = "active") -> dict:
    """Return a summary of known sessions."""

    return {"status": "success", "report": session_monitor.get_summary()}


def get_session_details(session_id: str) -> dict:
    """Return details for a specific session."""

    return {"status": "success", "report": session_monitor.get_details(session_id)}


# Create the ADK Agent
# Note: Vertex AI backend is configured via GOOGLE_APPLICATION_CREDENTIALS
# and GCP_PROJECT_ID/GCP_LOCATION environment variables
agent = Agent(
    name="gemini_adk_agent",
    model="gemini-2.0-flash-exp",
    description=(
        "A helpful agent that can answer questions, search the knowledge base, provide "
        "session insights, and delegate DevOps tasks to a specialized DevOps agent."
    ),
    instruction=(
        "You are a helpful AI assistant built with Google ADK. "
        "Use 'search_knowledge_base' for documentation questions. "
        "If the user asks for DevOps tasks like creating Pub/Sub topics or writing logs, "
        "use the 'ask_devops' tool to delegate the request. "
        "Use session tools to share monitoring details when requested. "
        "Always be polite and concise."
    ),
    tools=[
        ask_devops,
        search_knowledge_base,
        get_session_summary,
        get_session_details,
    ],
)
