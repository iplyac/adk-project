"""Unit tests for the DevOps agent tools."""
import pytest
from unittest.mock import MagicMock, patch
from my_agent.devops_tools import create_pubsub_topic, write_log_entry

class TestDevOpsTools:
    """Test the DevOps tools."""
    
    @patch("my_agent.devops_tools.pubsub_v1")
    def test_create_pubsub_topic_success(self, mock_pubsub):
        """Test successful topic creation."""
        # Setup mock
        mock_publisher = MagicMock()
        mock_pubsub.PublisherClient.return_value = mock_publisher
        mock_publisher.topic_path.return_value = "projects/test-project/topics/test-topic"
        mock_topic = MagicMock()
        mock_topic.name = "projects/test-project/topics/test-topic"
        mock_publisher.create_topic.return_value = mock_topic
        
        # Call function
        result = create_pubsub_topic("test-project", "test-topic")
        
        # Verify
        assert result["status"] == "success"
        assert "Created topic" in result["report"]
        mock_publisher.create_topic.assert_called_once()
        
    @patch("my_agent.devops_tools.pubsub_v1")
    def test_create_pubsub_topic_failure(self, mock_pubsub):
        """Test failed topic creation."""
        # Setup mock to raise exception
        mock_publisher = MagicMock()
        mock_pubsub.PublisherClient.return_value = mock_publisher
        mock_publisher.create_topic.side_effect = Exception("API Error")
        
        # Call function
        result = create_pubsub_topic("test-project", "test-topic")
        
        # Verify
        assert result["status"] == "error"
        assert "API Error" in result["error_message"]

    @patch("my_agent.devops_tools.logging")
    def test_write_log_entry_success(self, mock_logging):
        """Test successful log writing."""
        # Setup mock
        mock_client = MagicMock()
        mock_logging.Client.return_value = mock_client
        mock_logger = MagicMock()
        mock_client.logger.return_value = mock_logger
        
        # Call function
        result = write_log_entry("test-log", "test message", "INFO")
        
        # Verify
        assert result["status"] == "success"
        assert "Wrote log entry" in result["report"]
        mock_logger.log_text.assert_called_once_with("test message", severity="INFO")

    @patch("my_agent.devops_tools.logging")
    def test_write_log_entry_failure(self, mock_logging):
        """Test failed log writing."""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_logging.Client.return_value = mock_client
        mock_client.logger.side_effect = Exception("Log Error")
        
        # Call function
        result = write_log_entry("test-log", "test message")
        
        # Verify
        assert result["status"] == "error"
        assert "Log Error" in result["error_message"]
