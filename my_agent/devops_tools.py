import os
from google.api_core import exceptions
from google.cloud import pubsub_v1
from google.cloud import logging

def create_pubsub_topic(project_id: str, topic_id: str) -> dict:
    """Creates a Pub/Sub topic in the specified project.
    
    Args:
        project_id (str): The Google Cloud project ID.
        topic_id (str): The ID of the topic to create.
        
    Returns:
        dict: status and result or error msg.
    """
    try:
        region = os.getenv("PUBSUB_REGION") or os.getenv("GCP_LOCATION")
        client_options = None
        if region:
            client_options = {"api_endpoint": f"{region}-pubsub.googleapis.com"}

        publisher = pubsub_v1.PublisherClient(client_options=client_options)
        topic_path = publisher.topic_path(project_id, topic_id)

        topic = publisher.create_topic(request={"name": topic_path}, timeout=10)

        return {
            "status": "success",
            "report": f"Created topic: {topic.name}"
        }
    except exceptions.AlreadyExists:
        return {
            "status": "success",
            "report": f"Topic already exists: {topic_path}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to create topic: {str(e)}"
        }

def write_log_entry(log_name: str, text_payload: str, severity: str = "INFO") -> dict:
    """Writes a log entry to Cloud Logging.
    
    Args:
        log_name (str): The name of the log to write to.
        text_payload (str): The text content of the log entry.
        severity (str): The severity of the log entry (e.g., INFO, WARNING, ERROR).
        
    Returns:
        dict: status and result or error msg.
    """
    try:
        logging_client = logging.Client()
        logger = logging_client.logger(log_name)

        logger.log_text(text_payload, severity=severity)

        return {
            "status": "success",
            "report": f"Wrote log entry to {log_name} with severity {severity}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to write log entry: {str(e)}"
        }
