#main_graph.py
from langgraph.graph import StateGraph, END
from state_schema import AgentState
from agents.query_classification_agent import run_classification_pipeline
from agents.fallback_agent import fallback_agent
from agents.clarification_response_agent import clarification_response_agent
from agents.greeting_farewell_agents import greeting_agent, farewell_agent
# from agents.context_retrieval_agent import dummy_retrieval_agent  # หรือ agent จริง
from router_logic import route
import json

# Routing function
def routing_node(state: AgentState) -> str:
    return route(state)

# สร้างกราฟ
builder = StateGraph(AgentState)
builder.add_node("classify_query", run_classification_pipeline)
builder.add_node("clarification_response_agent", clarification_response_agent)
builder.add_node("fallback_response", fallback_agent)
builder.add_node("greeting_agent", greeting_agent)
builder.add_node("farewell_agent", farewell_agent)

# builder.add_node("retrieval_context_agent", dummy_retrieval_agent)  # หรือตัวจริง

builder.add_conditional_edges(
    "classify_query",
    routing_node,
    {
        "greeting_handler": "greeting_agent",
        "farewell_handler": "farewell_agent",
        "clarification_response_agent": "clarification_response_agent",
        "fallback_handler": "fallback_response",
        "retrieval_context_agent": END
    }
)


builder.set_entry_point("classify_query")
graph = builder.compile()

if __name__ == "__main__":
    initial_state = AgentState(user_query="สวัสดี")
    raw_state = graph.invoke(initial_state)
    final_state = AgentState(**raw_state)
    print(json.dumps(final_state.model_dump(), indent=2, ensure_ascii=False))
