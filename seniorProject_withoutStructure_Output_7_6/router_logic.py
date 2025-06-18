#router_logic.py
from state_schema import AgentState

def is_out_of_domain(state: AgentState) -> bool:
    return state.classification_result.out_of_domain is True
