import asyncio
import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent

def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.
    
    Args:
        city (str): The name of the city for which to retrieve the weather report.
        
    Returns:
        dict: status and result or error msg.
    """
    # Mock weather data for demonstration
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    elif city.lower() == "london":
        return {
            "status": "success",
            "report": (
                "The weather in London is rainy with a temperature of 15 degrees"
                " Celsius (59 degrees Fahrenheit)."
            ),
        }
    else:
        return {
            "status": "success", 
            "report": f"The weather in {city} is partly cloudy with a temperature of 20 degrees Celsius."
        }

def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city.
    
    Args:
        city (str): The name of the city for which to retrieve the current time.
        
    Returns:
        dict: status and result or error msg.
    """
    # Simple timezone mapping for demonstration
    timezones = {
        "new york": "America/New_York",
        "london": "Europe/London",
        "tokyo": "Asia/Tokyo",
        "sydney": "Australia/Sydney",
        "los angeles": "America/Los_Angeles",
    }
    
    tz_identifier = timezones.get(city.lower())
    
    if not tz_identifier:
        # Default to UTC if unknown
        tz_identifier = "UTC"
        
    try:
        tz = ZoneInfo(tz_identifier)
        now = datetime.datetime.now(tz)
        report = (
            f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
        )
        return {"status": "success", "report": report}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from my_agent.devops_agent import devops_agent
from my_agent.session_monitor import session_monitor

# Reuse one session service/runner so delegated calls can retain history per session_id
_devops_session_service = InMemorySessionService()
_devops_runner = Runner(
    app_name="devops_app",
    agent=devops_agent,
    session_service=_devops_session_service,
)

async def ask_devops(
    request: str,
    session_id: str | None = None,
    user_id: str = "main_agent",
    timeout_seconds: float = 30.0,
) -> str:
    """Delegate a request to the DevOps agent (async tool-friendly).

    Uses a stable session id per user when one is not provided so multi-turn
    delegations keep their context instead of spawning new sessions.
    """
    session = session_id or f"delegation_{user_id}"

    # Ensure session exists so multi-turn delegations can reuse history
    existing = await _devops_session_service.get_session(
        app_name="devops_app",
        user_id=user_id,
        session_id=session,
    )
    if not existing:
        await _devops_session_service.create_session(
            app_name="devops_app",
            user_id=user_id,
            session_id=session,
        )

    async def _run() -> str:
        response_text = ""
        async for event in _devops_runner.run_async(
            user_id=user_id,
            session_id=session,
            new_message=types.Content(role="user", parts=[types.Part(text=request)]),
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
        return response_text

    try:
        return await asyncio.wait_for(_run(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        return "DevOps agent timed out while processing the request."
    except Exception as exc:  # pragma: no cover - defensive
        import logging
        logging.getLogger(__name__).error("Error in ask_devops", exc_info=True)
        return f"Error calling DevOps agent: {exc}"

def get_session_summary(scope: str = "active") -> dict:
    """Return a summary of known sessions."""
    return {"status": "success", "report": session_monitor.get_summary()}


def get_session_details(session_id: str) -> dict:
    """Return details for a specific session."""
    return {"status": "success", "report": session_monitor.get_details(session_id)}

from google.adk.models.google_llm import GoogleLLMVariant
from my_agent.vertex_tools import search_knowledge_base

# Create the ADK Agent
# Note: Vertex AI backend is configured via GOOGLE_APPLICATION_CREDENTIALS
# and GCP_PROJECT_ID/GCP_LOCATION environment variables
agent = Agent(
    name="gemini_adk_agent",
    model="gemini-2.0-flash-exp",
    description=(
        "A helpful agent that can answer questions, check weather/time, and search the knowledge base. "
        "It can also delegate DevOps tasks to a specialized DevOps agent."
    ),
    instruction=(
        "You are a helpful AI assistant built with Google ADK. "
        "You can answer general questions and use your tools to provide specific information "
        "about weather and time when asked. "
        "Use 'search_knowledge_base' if the user asks for information that might be in the docs. "
        "If the user asks for DevOps tasks like creating Pub/Sub topics or writing logs, "
        "use the 'ask_devops' tool to delegate the request. "
        "Always be polite and concise."
    ),
    tools=[
        get_weather,
        get_current_time,
        ask_devops,
        search_knowledge_base,
        get_session_summary,
        get_session_details,
    ],
)
