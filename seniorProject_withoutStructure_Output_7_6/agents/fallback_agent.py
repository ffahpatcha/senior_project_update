from state_schema import AgentState

def fallback_agent(state: AgentState) -> AgentState:
    state.response = "ขออภัย เราไม่สามารถตอบคำถามนี้ได้ในขณะนี้"
    return state
