"""Unit tests for the Vertex AI tools."""
import pytest
from unittest.mock import MagicMock, patch
from my_agent.vertex_tools import search_knowledge_base

class TestVertexTools:
    """Test the Vertex AI tools."""
    
    @patch("my_agent.vertex_tools.discoveryengine")
    @patch("my_agent.vertex_tools.os")
    def test_search_knowledge_base_success(self, mock_os, mock_discoveryengine):
        """Test successful search."""
        # Setup mock env
        mock_os.getenv.side_effect = lambda key, default=None: {
            "GCP_PROJECT_ID": "test-project",
            "GCP_LOCATION": "europe-west4",
            "VERTEX_SEARCH_DATA_STORE_ID": "test-store"
        }.get(key, default)
        
        # Setup mock client
        mock_client = MagicMock()
        mock_discoveryengine.SearchServiceClient.return_value = mock_client
        
        # Setup mock response
        mock_result = MagicMock()
        mock_result.document.derived_struct_data = {
            "title": "Test Doc",
            "snippets": [{"snippet": "This is a test snippet."}],
            "link": "http://example.com"
        }
        mock_response = MagicMock()
        mock_response.results = [mock_result]
        mock_client.search.return_value = mock_response
        
        # Call function
        result = search_knowledge_base("test query")
        
        # Verify
        assert result["status"] == "success"
        assert "Test Doc" in result["report"]
        assert "This is a test snippet" in result["report"]
        
    @patch("my_agent.vertex_tools.os")
    def test_search_knowledge_base_missing_config(self, mock_os):
        """Test search with missing configuration."""
        # Setup mock env to return None
        mock_os.getenv.return_value = None
        
        # Call function
        result = search_knowledge_base("test query")
        
        # Verify
        assert result["status"] == "error"
        assert "not configured" in result["error_message"]

    @patch("my_agent.vertex_tools.discoveryengine")
    @patch("my_agent.vertex_tools.os")
    def test_search_knowledge_base_failure(self, mock_os, mock_discoveryengine):
        """Test failed search."""
        # Setup mock env
        mock_os.getenv.side_effect = lambda key, default=None: {
            "GCP_PROJECT_ID": "test-project",
            "GCP_LOCATION": "europe-west4",
            "VERTEX_SEARCH_DATA_STORE_ID": "test-store"
        }.get(key, default)
        
        # Setup mock client to raise exception
        mock_client = MagicMock()
        mock_discoveryengine.SearchServiceClient.return_value = mock_client
        mock_client.search.side_effect = Exception("Search API Error")
        
        # Call function
        result = search_knowledge_base("test query")
        
        # Verify
        assert result["status"] == "error"
        assert "Search API Error" in result["error_message"]
