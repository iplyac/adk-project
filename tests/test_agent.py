"""Unit tests for the agent's exposed tools."""

from my_agent.agent import (
    agent,
    ask_devops,
    get_session_details,
    get_session_summary,
)
from my_agent.session_monitor import session_monitor


class TestAgentTools:
    """Validate the configured toolset for the primary agent."""

    def test_tools_do_not_include_removed_utilities(self):
        tool_names = {tool.__name__ for tool in agent.tools}

        assert "get_weather" not in tool_names
        assert "get_current_time" not in tool_names
        assert "ask_devops" in tool_names
        assert "get_session_summary" in tool_names
        assert "get_session_details" in tool_names

    def test_ask_devops_respects_test_mode(self, monkeypatch):
        monkeypatch.setenv("ADK_TEST_MODE", "true")

        result = ask_devops("create a topic")

        assert "devops-test-mode" in result


class TestSessionUtilities:
    """Ensure session helpers return expected structures."""

    def test_get_session_summary_defaults_to_empty_message(self):
        session_monitor.sessions.clear()

        result = get_session_summary()

        assert result["status"] == "success"
        assert result["report"] == "No sessions recorded."

    def test_get_session_details_reports_missing_session(self):
        session_monitor.sessions.clear()

        session_id = "unknown_session"
        result = get_session_details(session_id)

        assert result["status"] == "success"
        assert session_id in result["report"]
        assert "No session found" in result["report"]
