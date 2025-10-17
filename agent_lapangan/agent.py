from google.adk.agents.llm_agent import Agent
from .prompt import REVIEW_PROMPT

root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="Review",
    instruction=REVIEW_PROMPT,
)
