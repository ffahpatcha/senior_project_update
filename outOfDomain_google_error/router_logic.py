# 📁 router_logic.py
from state_schema import AgentState


def is_out_of_domain(state: AgentState) -> bool:
    return state.classification_result.out_of_domain is True


def is_clarification_needed(state: AgentState) -> bool:
    return state.classification_result.clarification_needed is True


def has_classifier_category(state: AgentState, threshold: float = 0.5) -> bool:
    # ตรวจสอบว่ามี category ที่ classifier มั่นใจพอ
    categories = state.classification_result.category_level_1
    return categories is not None and any(cat.confidence >= threshold for cat in categories)


def has_user_selected_category(state: AgentState) -> bool:
    # ถ้ามีการให้ผู้ใช้เลือก category เอง เพิ่ม logic นี้ในอนาคต
    # ตัวอย่าง: return state.user_selected_category is not None
    return False  # กำหนดไว้ก่อน เพราะยังไม่มี field นี้ใน AgentState


def route(state: AgentState) -> str:
    intent = (state.classification_result.intent or "").lower()

    if intent == "greeting":
        return "greeting_handler"
    if intent == "farewell":
        return "farewell_handler"

    if is_out_of_domain(state):
        return "fallback_handler"
    
    if is_clarification_needed(state):
        return "clarification_response_agent"

    if has_user_selected_category(state):
        return "retrieval_context_agent"

    if has_classifier_category(state):
        return "clarification_response_agent"

    return "retrieval_context_agent"

