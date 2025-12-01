#!/usr/bin/env python3
"""
Register the deployed agent with Vertex AI Agent Engine.

This script creates an Agent Engine instance that points to the Cloud Run deployment.
"""

import os
import sys
from google.cloud import aiplatform
import subprocess

# Configuration
PROJECT_ID = "gen-lang-client-0741140892"
LOCATION = "us-central1"
SERVICE_NAME = "adk-agent"

def get_cloud_run_url():
    """Get the Cloud Run service URL."""
    try:
        result = subprocess.run(
            [
                "gcloud", "run", "services", "describe", SERVICE_NAME,
                "--region", LOCATION,
                "--format", "value(status.url)"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting Cloud Run URL: {e}")
        print("Make sure you've deployed to Cloud Run first using ./deploy.sh")
        sys.exit(1)

def register_agent():
    """Register the agent with Vertex AI Agent Engine."""
    print("🤖 Registering agent with Vertex AI Agent Engine...")
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print()
    
    # Get Cloud Run URL
    agent_uri = get_cloud_run_url()
    print(f"Agent URI: {agent_uri}")
    print()
    
    # Initialize Vertex AI
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    
    # Note: The actual Agent Engine registration API may vary
    # This is a placeholder for the registration logic
    # You may need to use the REST API or gcloud commands
    
    print("⚠️  Note: Agent Engine registration via Python SDK is not yet fully available.")
    print("Please use the Google Cloud Console to register your agent:")
    print()
    print("1. Go to: https://console.cloud.google.com/vertex-ai/agents")
    print(f"2. Click 'Create Agent'")
    print(f"3. Select 'ADK' as the framework")
    print(f"4. Enter Agent URI: {agent_uri}")
    print(f"5. Configure settings and click 'Create'")
    print()
    print("Alternatively, use the gcloud CLI (if available):")
    print(f"  gcloud ai agents create --display-name='ADK DevOps Agent' \\")
    print(f"    --agent-uri='{agent_uri}' \\")
    print(f"    --region={LOCATION}")
    print()
    
    return agent_uri

if __name__ == "__main__":
    try:
        agent_uri = register_agent()
        print("✅ Registration information provided!")
        print(f"🌐 Your agent is running at: {agent_uri}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
