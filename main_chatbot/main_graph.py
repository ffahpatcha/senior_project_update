from typing import Optional
from langgraph.graph import StateGraph
from state_schema import AgentState, RetrievalHit
from my_agents.query_classification_agent import check_clarity, classify_categories
from my_agents.hybrid_searcher import hybrid_search_node, QDRANT_URL, QDRANT_API_KEY
from my_agents.generate_agent import generate_node  

NODE_CLARITY = "clarity_check"
NODE_CLASSIFY = "classify_categories"
NODE_HYBRID = "hybrid_search"
NODE_TERMINATE = "terminate"
NODE_GENERATE = "generate"
COLLECTION_NAME = "dental_chunks"


# ---------- helpers ป้องกัน AttributeError ----------
def _latest_text(state: AgentState) -> str:
    # ถ้าไม่มีฟิลด์ (รุ่นเก่า) ให้ fallback ไป user_query
    return getattr(state, "user_query_latest", None) or getattr(state, "user_query", "") or ""

# ---------- nodes ----------
def check_clarity_node(state: AgentState) -> AgentState:
    print("[clarity_check] ตรวจสอบคำถาม")
    text = _latest_text(state)
    result = check_clarity(text)
    state.classification_result.clarification_needed = result.clarification_needed
    state.classification_result.clarification_reason = getattr(result, "clarification_reason", None)
    print(f"[clarity_check] need={state.classification_result.clarification_needed}")
    return state

def classify_categories_node(state: AgentState) -> AgentState:
    print("[classify_categories] จัดหมวดหมู่")
    text = _latest_text(state)
    assignments = classify_categories(text)
    state.classification_result = state.classification_result.model_copy(
        update={"categories": assignments}
    )
    cats_txt = ", ".join(
        f"{a.level_1}>{a.level_2}:{a.score:.2f}" for a in state.classification_result.categories
    ) or "ไม่พบ"
    state.response = f"หมวดที่พบ: {cats_txt}"
    print(f"[classify_categories] {cats_txt}")
    return state

def route_after_clarity(state: AgentState) -> str:
    return NODE_TERMINATE if state.classification_result.clarification_needed else NODE_CLASSIFY

def terminate_node(state: AgentState) -> AgentState:
    print("[terminate] จบการประมวลผล")
    if getattr(state.classification_result, "clarification_needed", False):
        reason = getattr(state.classification_result, "clarification_reason", None)
        state.response = f"รบกวนขอข้อมูลเพิ่มเติม: {reason}" if reason else "รบกวนขอข้อมูลเพิ่มเติม"
    state.terminated = True
    return state


# ===== Graph definition =====
workflow = StateGraph(AgentState)
workflow.add_node(NODE_CLARITY,   check_clarity_node)
workflow.add_node(NODE_CLASSIFY,  classify_categories_node)
workflow.add_node(NODE_HYBRID,    hybrid_search_node)
workflow.add_node(NODE_TERMINATE, terminate_node)
workflow.add_node(NODE_GENERATE,  generate_node)

workflow.add_conditional_edges(NODE_CLARITY, route_after_clarity)
workflow.add_edge(NODE_CLASSIFY, NODE_HYBRID)
workflow.add_edge(NODE_HYBRID,    NODE_GENERATE)
workflow.add_edge(NODE_GENERATE,  NODE_TERMINATE)

workflow.set_entry_point(NODE_CLARITY)
workflow.set_finish_point(NODE_TERMINATE)

graph = workflow.compile()
