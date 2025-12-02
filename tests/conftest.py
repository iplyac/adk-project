import pytest
from fastapi.testclient import TestClient
from app import app, stats


@pytest.fixture(autouse=True)
def enable_test_mode(monkeypatch):
    """Force the API into test mode to avoid real model calls."""
    monkeypatch.setenv("ADK_TEST_MODE", "true")
    yield


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_stats():
    """Reset stats before each test."""
    stats["request_count"] = 0
    stats["error_count"] = 0
    yield
    # Cleanup after test
    stats["request_count"] = 0
    stats["error_count"] = 0


@pytest.fixture
def sample_chat_request():
    """Sample chat request payload."""
    return {
        "message": "Summarize recent session activity",
        "session_id": "test_session_123"
    }


@pytest.fixture
def sample_session_id():
    """Sample session ID for testing."""
    return "test_session_456"
