import json

from langgraph.graph import StateGraph, END
from state_schema import AgentState
from agents.query_classification_agent import classification_node

builder = StateGraph(AgentState)
builder.add_node("classify_query", classification_node)
builder.set_entry_point("classify_query")
builder.add_edge("classify_query", END)
graph = builder.compile()

if __name__ == "__main__":
    initial_state = AgentState(user_query="หลังถอนฟันกินอะไรได้บ้าง")
    final_state = graph.invoke(initial_state)
    result = final_state["classification_result"]
    
    # ✅ แสดงผลอย่างสวยงาม
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))

