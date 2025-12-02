from google.adk.agents import Agent
from my_agent.devops_tools import create_pubsub_topic, write_log_entry

# Create the DevOps Agent
devops_agent = Agent(
    name="devops_agent",
    model="gemini-2.0-flash-exp",
    description=(
        "A specialized agent that handles DevOps tasks on Google Cloud Platform."
    ),
    instruction=(
        "You are a DevOps specialist agent. Your goal is to help users manage their "
        "Google Cloud Platform resources. You can create Pub/Sub topics and write "
        "logs to Cloud Logging. Always confirm the action you took."
    ),
    tools=[create_pubsub_topic, write_log_entry],
)
