# main_graph.py

# =====================
# Built-in Imports
# =====================
import os
import asyncio
import json
from config.settings import OPENAI_API_KEY
from agents import GuardrailFunctionOutput, input_guardrail, Runner,InputGuardrailTripwireTriggered

# =====================
# LangGraph Imports
# =====================
from langgraph.graph import StateGraph, END

# =====================
# Custom Agent Logic
# =====================
from state_schema import AgentState
from my_agents.query_classification_agent import run_classification_pipeline
from my_agents.fallback_agent import fallback_agent
from my_agents.clarification_response_agent import clarification_response_agent
# from my_agents.context_retrieval_agent import dummy_retrieval_agent
from router_logic import guardrail_router, routing_node



# =====================
# Graph Definition
# =====================

builder = StateGraph(AgentState)

# builder.add_node("input_guardrail", input_guardrail_node)
builder.add_node("classify_query", run_classification_pipeline)
builder.add_node("clarification_response_agent", clarification_response_agent)
builder.add_node("fallback_response", fallback_agent)
# builder.add_node("retrieval_context_agent", dummy_retrieval_agent)

builder.set_entry_point("classify_query")


# builder.add_conditional_edges(
#     "input_guardrail",
#     guardrail_router,
#     {
#         "continue": "classify_query",
#         "end": END
#     }
# )

builder.add_conditional_edges(
    "classify_query",
    routing_node,
    {
        "fallback_handler": "fallback_response",
        "clarification_response_agent": "clarification_response_agent",
        "retrieval_context_agent": END
    }
)

graph = builder.compile()
