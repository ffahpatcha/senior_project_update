#router_logic.py
from state_schema import AgentState

def guardrail_router(state: AgentState) -> str:
    if state.classification_result.out_of_domain:
        return "end"
    return "continue"

def routing_node(state: AgentState) -> str:
    return route(state)

def is_out_of_domain(state: AgentState) -> bool:
    return state.classification_result.out_of_domain is True


def is_clarification_needed(state: AgentState) -> bool:
    return state.classification_result.clarification_needed is True


def has_classifier_category(state: AgentState, threshold: float = 0.5) -> bool:
    categories = state.classification_result.category_level_1
    return categories is not None and any(cat.confidence >= threshold for cat in categories)


# def has_user_selected_category(state: AgentState) -> bool:
#     return False  #  user เลือก category เอง


def route(state: AgentState) -> str:
    if is_out_of_domain(state):
        return "fallback_handler"
    
    if is_clarification_needed(state):
        return "clarification_response_agent"

    # ถ้ามี category มั่นใจพอ ให้จบ workflow เลย
    if has_classifier_category(state):
        return "retrieval_context_agent"

    return "retrieval_context_agent"
