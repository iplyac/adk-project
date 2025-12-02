"""Integration tests for the FastAPI endpoints."""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test the /health endpoint."""
    
    def test_health_check(self, client):
        """Test that health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data
        assert "timestamp" in data
        assert data["uptime_seconds"] >= 0


class TestStatsEndpoint:
    """Test the /stats endpoint."""
    
    def test_stats_endpoint(self, client):
        """Test that stats endpoint returns correct data."""
        response = client.get("/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "request_count" in data
        assert "error_count" in data
        assert "uptime_seconds" in data
        assert "agent_name" in data
        assert "model" in data
        assert "latency_avg_ms" in data
        assert "latency_p95_ms" in data
        assert "tool_calls_total" in data
        assert "tool_calls_by_name" in data
        
        assert data["agent_name"] == "gemini_adk_agent"
        assert "gemini" in data["model"].lower()


class TestChatEndpoint:
    """Test the /api/chat endpoint."""
    
    def test_chat_endpoint_basic(self, client, sample_chat_request):
        """Test basic chat functionality."""
        response = client.post("/api/chat", json=sample_chat_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert isinstance(data["response"], str)
    
    def test_chat_endpoint_increments_request_count(self, client, sample_chat_request, reset_stats):
        """Test that chat endpoint increments request count."""
        from app import stats
        
        initial_count = stats["request_count"]
        response = client.post("/api/chat", json=sample_chat_request)
        assert response.status_code == 200
        assert stats["request_count"] == initial_count + 1
    
    def test_chat_endpoint_missing_message(self, client):
        """Test chat endpoint with missing message field."""
        response = client.post("/api/chat", json={"session_id": "test"})
        assert response.status_code == 422  # Validation error
    
    def test_chat_endpoint_missing_session_id(self, client):
        """Test chat endpoint with missing session_id field."""
        response = client.post("/api/chat", json={"message": "Hello"})
        assert response.status_code == 422  # Validation error
    
    def test_chat_endpoint_empty_message(self, client):
        """Test chat endpoint with empty message."""
        response = client.post("/api/chat", json={
            "message": "",
            "session_id": "test_session"
        })
        # Should still return 200, but might have an error response
        assert response.status_code == 200
    
    def test_chat_endpoint_multiple_sessions(self, client):
        """Test chat endpoint with different session IDs."""
        request1 = {"message": "Hello", "session_id": "session_1"}
        request2 = {"message": "Hi", "session_id": "session_2"}
        
        response1 = client.post("/api/chat", json=request1)
        response2 = client.post("/api/chat", json=request2)
        
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestRootEndpoint:
    """Test the root endpoint."""
    
    def test_root_returns_html(self, client):
        """Test that root endpoint returns the index.html file."""
        response = client.get("/")
        assert response.status_code == 200
        # Should return HTML content
        assert "text/html" in response.headers.get("content-type", "")
