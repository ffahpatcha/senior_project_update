# agents/clarification_response_agent.py

from state_schema import AgentState
from utils.clarification import get_clarification_reply

def clarification_response_agent(state: AgentState) -> AgentState:
    if state.classification_result.clarification_needed:
        reason = state.classification_result.clarification_reason
        state.response = get_clarification_reply(reason)
    else:
        state.response = "ไม่พบเหตุผลต้องขอข้อมูลเพิ่มเติม"
    return state
