"""Tests for SessionMonitor."""
import time

import pytest

from my_agent.session_monitor import SessionMonitor


@pytest.fixture
def monitor():
    return SessionMonitor(max_events=5)


def test_log_event_and_summary(monitor):
    monitor.log_event("s1", "u1", "agent", "created", "created session")
    monitor.record_message("s1", "u1", "agent")
    monitor.log_event("s1", "u1", "agent", "completed", "done")

    summary = monitor.get_summary()
    assert "s1" in summary
    assert "messages=1" in summary
    assert "status=completed" in summary


def test_details_and_alerts(monitor):
    monitor.log_event("s2", "u2", "agent", "error", error="boom")
    monitor.log_event("s2", "u2", "agent", "active", "recovered")

    details = monitor.get_details("s2")
    assert "boom" in details
    assert "recovered" in details

    alerts = monitor.pop_alerts("s2")
    assert len(alerts) == 2
    assert monitor.pop_alerts("s2") == []


def test_unknown_session_detail(monitor):
    assert "No session found" in monitor.get_details("missing")
