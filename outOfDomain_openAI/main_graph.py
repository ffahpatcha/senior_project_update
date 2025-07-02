# main_graph.py
from langgraph.graph import StateGraph, END
from state_schema import AgentState
from my_agents.query_classification_agent import run_classification_pipeline
from my_agents.fallback_agent import fallback_agent
from my_agents.clarification_response_agent import clarification_response_agent
# from agents.context_retrieval_agent import dummy_retrieval_agent
from router_logic import route
import json
from my_agents.dental_guardrail_function import dental_input_guardrail
import asyncio
import os
from openai import OpenAI

# ดึงคีย์จาก Environment Variable
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


async def input_guardrail_node(state: AgentState) -> AgentState:
    ctx = None
    agent = None
    result = await dental_input_guardrail(ctx, agent, state.user_query)
    if result.tripwire_triggered:
        state.response = (
            "ขอโทษค่ะ ระบบนี้ตอบได้เฉพาะคำถามเกี่ยวกับการดูแลหลังถอนฟันหรือผ่าฟันคุดเท่านั้น"
        )
        state.classification_result.out_of_domain = True
        state.classification_result.out_of_domain_reason = result.output_info["reasoning"]
    else:
        state.classification_result.out_of_domain = False
        state.classification_result.out_of_domain_reason = result.output_info["reasoning"]
    return state



# Routing function สำหรับ classify_query
def routing_node(state: AgentState) -> str:
    return route(state)

# 🚦 Router function เพื่อตัด flow ถ้าเจอ tripwire
def guardrail_router(state: AgentState) -> str:
    if state.classification_result.out_of_domain:
        return "end"
    return "continue"


# สร้างกราฟ
builder = StateGraph(AgentState)
builder.add_node("input_guardrail", input_guardrail_node)
builder.add_node("classify_query", run_classification_pipeline)
builder.add_node("clarification_response_agent", clarification_response_agent)
builder.add_node("fallback_response", fallback_agent)
# builder.add_node("retrieval_context_agent", dummy_retrieval_agent)

builder.set_entry_point("input_guardrail")

# ✅ ใช้ conditional edges แทน add_edge
builder.add_conditional_edges(
    "input_guardrail",
    guardrail_router,
    {
        "continue": "classify_query",
        "end": END
    }
)

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

if __name__ == "__main__":
    initial_state = AgentState(user_query="ช่วยแต่ง caption ให้รูปนี้หน่อย")
    raw_state = asyncio.run(graph.ainvoke(initial_state))
    final_state = AgentState(**raw_state)
    print(json.dumps(final_state.model_dump(), indent=2, ensure_ascii=False))
