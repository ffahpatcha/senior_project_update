#greeting_farewell_agents.py
from tools.say_hello_goodbye import say_hello, say_goodbye
from google.adk.agents import Agent

# Greeting Agent
greeting_agent = Agent(
    model="gemini-2.0-flash",
    name="greeting_agent",
    instruction=(
        "You are the Greeting Agent. "
        "Your ONLY task is to provide a friendly greeting using the 'say_hello' tool."
    ),
    description="Handles greetings like 'Hi', 'Hello'.",
    tools=[say_hello]
)

# Farewell Agent
farewell_agent = Agent(
    model="gemini-2.0-flash",
    name="farewell_agent",
    instruction=(
        "You are the Farewell Agent."
        "Your ONLY task is to say goodbye politely using the 'say_goodbye' tool."
    ),
    description="Handles farewells like 'Bye', 'See you'.",
    tools=[say_goodbye]
)
