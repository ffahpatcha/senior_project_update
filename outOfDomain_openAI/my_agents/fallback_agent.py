from state_schema import AgentState

def fallback_agent(state: AgentState) -> AgentState:
    state.response = "เพื่อให้แนะนำได้ตรงจุด รบกวนระบุสิ่งที่คุณอยากปรึกษาเพิ่มเติมค่ะ"
    return state
